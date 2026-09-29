import unittest

from agentnative.protocols import A2AAdapter


class A2AAdapterTests(unittest.TestCase):
    def test_duplicate_skill_and_malformed_auth_are_explicit(self):
        result = A2AAdapter().parse({"name": "Agent", "skills": [{"id": "search"}, {"id": "search"}], "authentication": "bearer"})
        codes = {item.code for item in result.limitations}
        self.assertIn("A2A_DUPLICATE_SKILL", codes); self.assertIn("A2A_INVALID_AUTH", codes)


if __name__ == "__main__": unittest.main()
