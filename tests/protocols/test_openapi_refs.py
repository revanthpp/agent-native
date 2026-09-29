import unittest
from unittest.mock import patch
from agentnative.acquisition.fetcher import AcquisitionError

from agentnative.protocols.openapi.adapter import OpenAPIAdapter
from agentnative.protocols.openapi.refs import RemoteArtifact


class OpenAPIReferenceTests(unittest.TestCase):
    def setUp(self):
        self.root = {"openapi": "3.1.0", "paths": {"/orders": {"post": {"operationId": "create_order", "requestBody": {"$ref": "schemas.json#/components/schemas/Order"}}}}}

    def test_same_origin_remote_ref_is_resolved_with_provenance(self):
        def fetch(uri): return RemoteArtifact(uri, {"components": {"schemas": {"Order": {"type": "object"}}}}, "hash-order", uri)
        result = OpenAPIAdapter().parse(self.root, "https://business.test/openapi.json", fetch=fetch)
        self.assertFalse(result.errors)
        self.assertEqual(result.artifacts[-1].source_uri, "https://business.test/schemas.json") if hasattr(result.artifacts[-1], "source_uri") else self.assertEqual(result.artifacts[-1].uri, "https://business.test/schemas.json")

    def test_local_ref_is_resolved(self):
        document = {
            "openapi": "3.1.0",
            "components": {"responses": {"ok": {"description": "ok"}}},
            "paths": {"/x": {"get": {"responses": {"200": {"$ref": "#/components/responses/ok"}}}}},
        }
        result = OpenAPIAdapter().parse(document)
        self.assertFalse(result.errors)
        self.assertNotIn("OAS_REF_MISSING", {item.code for item in result.limitations})

    def test_cross_origin_private_and_redirect_refs_are_blocked(self):
        result = OpenAPIAdapter().parse({"openapi": "3.1.0", "paths": {"/x": {"get": {"operationId": "x", "responses": {"200": {"$ref": "http://127.0.0.1/schema"}}}}}}, "https://business.test/openapi.json", fetch=lambda uri: (_ for _ in ()).throw(AssertionError("unsafe ref fetched")))
        self.assertIn("OAS_REF_PRIVATE_NETWORK", {item.code for item in result.limitations})
        result = OpenAPIAdapter().parse({"openapi": "3.1.0", "paths": {"/x": {"get": {"operationId": "x", "responses": {"200": {"$ref": "https://business.test/schema"}}}}}}, "https://business.test/openapi.json", fetch=lambda uri: RemoteArtifact(uri, {}, final_uri="https://localhost/schema"))
        self.assertIn("OAS_REF_REDIRECT_BLOCKED", {item.code for item in result.limitations})

    def test_metadata_file_and_unsupported_scheme_refs_are_blocked_without_fetch(self):
        refs = {
            "metadata": "https://metadata.google.internal/schema",
            "file": "file:///etc/passwd",
            "ftp": "ftp://business.test/schema",
        }
        for name, ref in refs.items():
            with self.subTest(name=name):
                fetched = []
                document = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": ref}}}}}}
                result = OpenAPIAdapter().parse(document, "https://business.test/openapi.json", fetch=lambda uri: fetched.append(uri))
                codes = {item.code for item in result.limitations}
                self.assertFalse(fetched)
                self.assertTrue(codes & {"OAS_REF_PRIVATE_NETWORK", "OAS_REF_UNSUPPORTED_SCHEME"})

    def test_cycles_depth_and_document_budget_are_bounded(self):
        cycle_docs = {
            "https://business.test/a.json": RemoteArtifact("https://business.test/a.json", {"x": {"$ref": "b.json#/x"}}, "a"),
            "https://business.test/b.json": RemoteArtifact("https://business.test/b.json", {"x": {"$ref": "a.json#/x"}}, "b"),
        }
        root = {"$ref": "a.json#/x"}
        resolver = __import__("agentnative.protocols.openapi.refs", fromlist=["SafeRefResolver"]).SafeRefResolver(root, "https://business.test/root.json", fetch=cycle_docs.__getitem__)
        resolver.resolve(root)
        self.assertIn("OAS_REF_CYCLE", {item.code for item in resolver.limitations})

        deep = {"components": {}}
        for index in range(20):
            deep["components"][f"schema{index}"] = {"$ref": f"#/components/schema{index + 1}"}
        deep["components"]["schema20"] = {"type": "object"}
        depth_resolver = __import__("agentnative.protocols.openapi.refs", fromlist=["SafeRefResolver"]).SafeRefResolver(deep, "memory://root", max_depth=2)
        depth_resolver.resolve({"$ref": "#/components/schema0"})
        self.assertIn("OAS_REF_DEPTH", {item.code for item in depth_resolver.limitations})

        docs = {
            "https://business.test/one.json": RemoteArtifact("https://business.test/one.json", {}, "one"),
            "https://business.test/two.json": RemoteArtifact("https://business.test/two.json", {}, "two"),
        }
        budget_root = {"one": {"$ref": "one.json"}, "two": {"$ref": "two.json"}}
        budget_resolver = __import__("agentnative.protocols.openapi.refs", fromlist=["SafeRefResolver"]).SafeRefResolver(budget_root, "https://business.test/root.json", fetch=docs.__getitem__, max_documents=1)
        budget_resolver.resolve(budget_root)
        self.assertIn("OAS_REF_DOCUMENT_COUNT", {item.code for item in budget_resolver.limitations})

    def test_fetch_failures_timeout_oversize_and_malformed_docs_are_deterministic(self):
        document = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": "schema.json"}}}}}}
        for failure in (AcquisitionError("404"), TimeoutError("timeout"), ValueError("oversized")):
            with self.subTest(failure=type(failure).__name__):
                result = OpenAPIAdapter().parse(document, "https://business.test/openapi.json", fetch=lambda uri, failure=failure: (_ for _ in ()).throw(failure))
                self.assertIn("OAS_REF_FETCH_FAILED", {item.code for item in result.limitations})
        result = OpenAPIAdapter().parse(document, "https://business.test/openapi.json", fetch=lambda uri: RemoteArtifact(uri, []))
        self.assertIn("OAS_REF_PARSE_FAILED", {item.code for item in result.limitations})

    def test_nested_remote_refs_preserve_individual_provenance(self):
        root = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": "a.json#/response"}}}}}}
        docs = {
            "https://business.test/a.json": RemoteArtifact("https://business.test/a.json", {"response": {"$ref": "b.json#/response"}}, "hash-a"),
            "https://business.test/b.json": RemoteArtifact("https://business.test/b.json", {"response": {"description": "ok"}}, "hash-b"),
        }
        result = OpenAPIAdapter().parse(root, "https://business.test/openapi.json", fetch=docs.__getitem__)
        refs = result.artifacts[1:]
        self.assertEqual({item.content_hash for item in refs}, {"hash-a", "hash-b"})
        self.assertEqual(len({item.artifact_id for item in refs}), 2)
        self.assertTrue(all(item.source_uri.startswith("https://business.test/") and item.acquisition_evidence == "safe-acquisition-policy" for item in refs))

    def test_same_origin_redirect_uses_safe_fetcher_and_keeps_provenance(self):
        document = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": "schemas.json#/responses/ok"}}}}}}
        remote = RemoteArtifact(
            "https://business.test/redirected/schemas.json",
            {"responses": {"ok": {"description": "ok"}}},
            "hash-redirected",
            "https://business.test/redirected/schemas.json",
        )
        with patch("agentnative.protocols.openapi.refs.SafeFetcher.fetch", return_value=remote) as fetch:
            result = OpenAPIAdapter().parse(document, "https://business.test/openapi.json")
        fetch.assert_called_once_with("https://business.test/schemas.json")
        self.assertNotIn("OAS_REF_REDIRECT_BLOCKED", {item.code for item in result.limitations})
        self.assertEqual(result.artifacts[-1].uri, "https://business.test/redirected/schemas.json")


if __name__ == "__main__": unittest.main()
