import unittest

from agentnative.observability import TraceContext, TraceRecorder


class TraceTests(unittest.TestCase):
    def test_otel_export_preserves_root_and_redacts_attributes(self):
        context = TraceContext.new("corr:test")
        recorder = TraceRecorder(context)
        recorder.emit("policy_decided", {"decision": "ALLOW", "authorization": "Bearer SECRET_TOKEN_1234567890"})
        exported = recorder.export()
        self.assertEqual(exported["trace_id"], context.trace_id)
        self.assertEqual(exported["correlation_id"], "corr:test")
        self.assertNotIn("SECRET_TOKEN_1234567890", repr(exported))
        self.assertTrue(exported["otel"]["resourceSpans"])


if __name__ == "__main__":
    unittest.main()
