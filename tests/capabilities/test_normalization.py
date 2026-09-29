import unittest

from agentnative.capabilities import CapabilityGraph
from agentnative.protocols import A2AAdapter, MCPAdapter, OpenAPIAdapter


class NormalizationTests(unittest.TestCase):
    def test_create_reservation_equivalence_preserves_three_sources(self):
        graph = CapabilityGraph("reference")
        inputs = [({"openapi": "3.1.0", "paths": {"/reservations": {"post": {"operationId": "create_reservation", "description": "Create reservation"}}}}, OpenAPIAdapter(), "oas://reference"), ({"tools": [{"name": "create_reservation", "description": "Create reservation"}]}, MCPAdapter(), "mcp://reference"), ({"name": "Reference", "skills": [{"id": "create_reservation", "description": "Create reservation"}]}, A2AAdapter(), "a2a://reference")]
        for document, adapter, uri in inputs: graph.extend(adapter.parse(document, uri).capabilities)
        self.assertEqual(len(graph.values()), 1)
        self.assertEqual(set(graph.values()[0].protocol_sources), {"oas://reference", "mcp://reference", "a2a://reference"})


if __name__ == "__main__": unittest.main()
