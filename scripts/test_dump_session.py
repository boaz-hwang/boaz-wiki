"""Verify session provenance: original line numbers, full text, and Codex deduplication."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SessionReaderTests(unittest.TestCase):
    def run_reader(self, records, *args, alias=False):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.jsonl"
            path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", WIKI_CLAUDE_SESSIONS_DIR=folder)
            target = "/claude-sessions/sample.jsonl" if alias else str(path)
            return subprocess.run(
                [sys.executable, str(Path(__file__).with_name("dump_session.py")), target, *args],
                env=env, capture_output=True, text=True,
            )

    def test_claude_full_text_and_original_range(self):
        body = "근거" * 2000 + "끝"
        records = [{"type": "metadata"}, {"type": "user", "message": {"content": body}}]
        result = self.run_reader(records, "--start", "2", "--end", "2", alias=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("L2 [user]\n" + body, result.stdout)

    def test_tools_are_opt_in(self):
        records = [{"type": "user", "message": {"content": [{"type": "tool_result", "content": "proof"}]}}]
        self.assertEqual(self.run_reader(records).stdout, "")
        self.assertIn("L1 [tool_result]\nproof", self.run_reader(records, "--tools").stdout)

    def test_claude_mid_turn_user_input_is_not_lost(self):
        records = [
            {"type": "queue-operation", "operation": "enqueue", "content": "scope correction"},
            {"type": "attachment", "attachment": {"type": "queued_command", "origin": {"kind": "human"}, "prompt": "scope correction"}},
        ]
        result = self.run_reader(records)
        self.assertEqual(result.stdout.count("scope correction"), 1)
        self.assertIn("L2 [user]", result.stdout)

    def test_codex_event_and_response_not_duplicated(self):
        records = [
            {"type": "event_msg", "payload": {"type": "user_message", "message": "decision"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "decision"}]}},
        ]
        result = self.run_reader(records)
        self.assertEqual(result.stdout.count("decision"), 1)
        self.assertIn("L2 [user]", result.stdout)

    def test_old_codex_event_only(self):
        result = self.run_reader([{"type": "event_msg", "payload": {"type": "agent_message", "message": "proposal"}}])
        self.assertIn("L1 [assistant]\nproposal", result.stdout)

    def test_discovery_truncation_is_explicit(self):
        result = self.run_reader([{"type": "user", "message": {"content": "abcdef"}}], "--max-chars", "3")
        self.assertIn("abc\n[TRUNCATED:", result.stdout)
        self.assertNotIn("abcdef", result.stdout)

    def test_invalid_range_fails(self):
        self.assertNotEqual(self.run_reader([], "--start", "3", "--end", "1").returncode, 0)


if __name__ == "__main__":
    unittest.main()
