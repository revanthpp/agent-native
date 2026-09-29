import unittest

from agentnative.protocols import A2AAdapter, AdapterRegistry, MCPAdapter, OpenAPIAdapter, ProtocolAdapter
from agentnative.protocols.models import AdapterResult


class DummyProtocolAdapter(ProtocolAdapter):
    protocol_family = "DUMMY"
    protocol_version = "1"
    def detect(self, document): return document == {"dummy": True}
    def parse(self, document, uri="memory://dummy"):
        return AdapterResult("DUMMY", "1", self.adapter_version, "test", detected=True, validity="VALID")


class AdapterContractTests(unittest.TestCase):
    def test_extension_adapter_registers_without_builtin_changes(self):
        adapter = DummyProtocolAdapter(); registry = AdapterRegistry(); registry.register(adapter)
        result = registry.analyze([({"dummy": True}, "fixture://dummy")])[0]
        self.assertEqual(result.protocol_family, "DUMMY")
        for method in ("detect", "parse", "validate", "normalize", "enumerate_capabilities", "enumerate_auth_requirements", "enumerate_actions", "enumerate_errors", "enumerate_protocol_limitations"):
            self.assertTrue(callable(getattr(adapter, method)))

    def test_builtin_adapters_expose_and_execute_the_full_contract(self):
        fixtures = [
            (OpenAPIAdapter(), {"openapi": "3.1.0", "paths": {"/read": {"get": {"operationId": "read"}}}}),
            (MCPAdapter(), {"tools": [{"name": "read"}], "resources": [{"uri": "resource://one"}], "prompts": [{"name": "summarize"}]}),
            (A2AAdapter(), {"name": "Agent", "skills": [{"id": "read"}]}),
        ]
        for adapter, document in fixtures:
            with self.subTest(adapter=adapter.protocol_family):
                self.assertTrue(adapter.detect(document))
                result = adapter.parse(document)
                self.assertTrue(result.detected)
                self.assertNotEqual(result.validity, "NOT_DETECTED")
                for method in ("validate", "normalize", "enumerate_capabilities", "enumerate_auth_requirements", "enumerate_actions", "enumerate_errors", "enumerate_protocol_limitations"):
                    self.assertIsNotNone(getattr(adapter, method)(document))


if __name__ == "__main__": unittest.main()
