import json
import unittest
from pathlib import Path

from agentnative.protocols import A2AAdapter, MCPAdapter, OpenAPIAdapter


ROOT = Path(__file__).resolve().parents[2]


class Phase2ACorpusTests(unittest.TestCase):
    def test_corpus_covers_valid_invalid_ambiguous_adversarial_and_deceptive_surfaces(self):
        valid = OpenAPIAdapter().parse((ROOT / "evals/phase2a/corpus/openapi-valid.yaml").read_text(), "fixture://openapi-valid")
        invalid = OpenAPIAdapter().parse(json.loads((ROOT / "evals/phase2a/corpus/openapi-invalid.json").read_text()), "fixture://openapi-invalid")
        ambiguous = OpenAPIAdapter().parse((ROOT / "evals/phase2a/corpus/openapi-ambiguous.yaml").read_text(), "fixture://openapi-ambiguous")
        mcp = MCPAdapter().parse(json.loads((ROOT / "evals/phase2a/corpus/mcp-deceptive.json").read_text()), "fixture://mcp-deceptive")
        a2a = A2AAdapter().parse(json.loads((ROOT / "evals/phase2a/corpus/a2a-adversarial.json").read_text()), "fixture://a2a-adversarial")
        self.assertEqual(valid.validity, "VALID")
        self.assertEqual(invalid.validity, "INVALID")
        self.assertIn("OAS_VERSION_UNSUPPORTED", {item.code for item in ambiguous.limitations})
        self.assertIn("MCP_DECLARATION_CONTRADICTION", {item.code for item in mcp.limitations})
        self.assertIn("A2A_DUPLICATE_SKILL", {item.code for item in a2a.limitations})


if __name__ == "__main__":
    unittest.main()
