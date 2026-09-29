import os
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from agentnative.cli.main import main
from agentnative.protocols import A2AAdapter, AdapterRegistry, MCPAdapter, OpenAPIAdapter


HOSTILE_YAML = '!!python/object/apply:os.system ["echo unsafe"]'


class AdapterErrorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.adapter = OpenAPIAdapter()

    def test_json_and_yaml_success_paths_remain_valid(self):
        json_result = self.adapter.parse('{"openapi":"3.1.0","paths":{}}', "fixture://valid.json")
        yaml_result = self.adapter.parse("openapi: 3.1.0\npaths: {}\n", "fixture://valid.yaml")
        self.assertEqual(json_result.status, "VALID")
        self.assertEqual(yaml_result.status, "VALID")
        self.assertFalse(json_result.error_details)
        self.assertFalse(yaml_result.error_details)

    def test_expected_yaml_failures_are_normalized_without_construction(self):
        cases = [
            HOSTILE_YAML,
            "!!python/object/new:tuple []",
            "!!python/name:os.system",
            "!unknown-custom-tag value",
            "openapi: [",
        ]
        with patch.object(os, "system") as execute:
            for index, artifact in enumerate(cases):
                with self.subTest(index=index):
                    result = self.adapter.parse(artifact, f"fixture://hostile-{index}")
                    self.assertEqual(result.status, "INVALID")
                    self.assertFalse(result.detected)
                    self.assertTrue(result.error_details)
                    error = result.error_details[0]
                    self.assertEqual(error.error_code, "OPENAPI_YAML_PARSE_INVALID")
                    self.assertEqual(error.category, "TARGET_INPUT_INVALID")
                    self.assertEqual(error.protocol, "OPENAPI")
                    self.assertEqual(error.operation, "parse")
                    self.assertTrue(error.artifact_reference.startswith("artifact-"))
                    self.assertNotIn("ConstructorError", repr(result))
                    self.assertNotIn(artifact, repr(result))
            execute.assert_not_called()

    def test_all_direct_openapi_operations_fail_closed(self):
        operations = [
            ("detect", lambda: self.adapter.detect(HOSTILE_YAML)),
            ("parse", lambda: self.adapter.parse(HOSTILE_YAML, "fixture://direct")),
            ("validate", lambda: self.adapter.validate(HOSTILE_YAML)),
            ("normalize", lambda: self.adapter.normalize(HOSTILE_YAML, "fixture://direct")),
            ("enumerate_capabilities", lambda: self.adapter.enumerate_capabilities(HOSTILE_YAML, "fixture://direct")),
            ("enumerate_auth_requirements", lambda: self.adapter.enumerate_auth_requirements(HOSTILE_YAML, "fixture://direct")),
            ("enumerate_actions", lambda: self.adapter.enumerate_actions(HOSTILE_YAML, "fixture://direct")),
            ("enumerate_errors", lambda: self.adapter.enumerate_errors(HOSTILE_YAML, "fixture://direct")),
            ("enumerate_protocol_limitations", lambda: self.adapter.enumerate_protocol_limitations(HOSTILE_YAML, "fixture://direct")),
        ]
        for name, operation in operations:
            with self.subTest(operation=name):
                value = operation()
                if name == "detect":
                    self.assertFalse(value)
                elif name in {"parse", "normalize"}:
                    self.assertEqual(value.status, "INVALID")
                    self.assertTrue(value.error_details)
                elif name in {"validate", "enumerate_errors"}:
                    self.assertTrue(value)
                else:
                    self.assertIsInstance(value, list)

    def test_direct_and_registry_classification_are_consistent(self):
        direct = self.adapter.parse(HOSTILE_YAML, "fixture://consistency")
        registry_results = AdapterRegistry([OpenAPIAdapter()]).analyze([(HOSTILE_YAML, "fixture://consistency")])
        self.assertEqual(len(registry_results), 1)
        self.assertEqual(direct.status, registry_results[0].status)
        self.assertEqual(direct.error_details[0].error_code, registry_results[0].error_details[0].error_code)

    def test_public_cli_rendering_exposes_only_sanitized_error_evidence(self):
        output = StringIO()
        with patch("agentnative.cli.main.Path.read_text", return_value=HOSTILE_YAML), redirect_stdout(output):
            self.assertEqual(main(["protocols", "fixture://hostile"]), 5)
        rendered = output.getvalue()
        self.assertNotIn("ConstructorError", rendered)
        self.assertNotIn(HOSTILE_YAML, rendered)
        payload = json.loads(rendered)
        self.assertEqual(payload["status"], "INVALID")
        self.assertEqual(payload["error_details"][0]["error_code"], "OPENAPI_YAML_PARSE_INVALID")
        self.assertIn("content_hash", payload["error_details"][0]["sanitized_details"])

    def test_mcp_and_a2a_direct_malformed_inputs_are_structured(self):
        mcp = MCPAdapter().parse({"tools": "invalid"}, "fixture://mcp")
        a2a = A2AAdapter().parse({"skills": "invalid"}, "fixture://a2a")
        self.assertEqual(mcp.status, "INVALID")
        self.assertEqual(a2a.status, "INVALID")
        self.assertTrue(mcp.error_details)
        self.assertTrue(a2a.error_details)
        self.assertEqual(mcp.error_details[0].category, "TARGET_INPUT_INVALID")
        self.assertEqual(a2a.error_details[0].category, "TARGET_INPUT_INVALID")

    def test_mcp_oversized_text_is_a_limitation_not_an_exception(self):
        result = MCPAdapter().parse({"tools": [{"name": "large", "description": "x" * 1_000_001}]}, "fixture://mcp-large")
        self.assertEqual(result.status, "VALID_WITH_WARNINGS")
        self.assertIn("MCP_SCHEMA_SIZE", {item.code for item in result.limitations})


if __name__ == "__main__":
    unittest.main()
