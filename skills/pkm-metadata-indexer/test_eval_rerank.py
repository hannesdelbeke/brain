"""The judge speaks three dialects and gets to pick by model name alone.

Worth testing because every way this breaks is quiet. A request in the wrong
shape returns an error envelope that `judge_answer` reads as an empty string,
which `judge` reads as "unparseable", which the eval reads as "not relevant" —
so a dialect bug does not raise, it just moves every score down and looks like
a ranking result.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_rerank


class DialectTest(unittest.TestCase):
    def test_claude_goes_to_the_messages_route(self):
        url, body = eval_rerank.judge_request("claude-sonnet-5", "prompt")
        self.assertTrue(url.endswith("/v1/messages"), url)
        self.assertEqual(body["model"], "claude-sonnet-5")
        self.assertEqual(body["messages"], [{"role": "user", "content": "prompt"}])

    def test_claude_sends_no_temperature(self):
        """The current models 400 on it, so the other dialects' determinism
        knob is the one thing this request must not carry."""
        _, body = eval_rerank.judge_request("claude-sonnet-5", "prompt")
        self.assertNotIn("temperature", body)

    def test_claude_disables_thinking_rather_than_omitting_it(self):
        """Omitted means adaptive, and adaptive can spend the whole answer
        budget thinking and return no text at all."""
        _, body = eval_rerank.judge_request("claude-sonnet-5", "prompt")
        self.assertEqual(body["thinking"], {"type": "disabled"})

    def test_gemini_still_goes_to_the_generate_route(self):
        url, body = eval_rerank.judge_request("gemini-2.5-flash", "prompt")
        self.assertIn("/v1beta/models/gemini-2.5-flash:generateContent", url)
        self.assertEqual(body["generationConfig"]["temperature"], 0)

    def test_anything_else_is_openai_shaped(self):
        url, body = eval_rerank.judge_request("some-local-model", "prompt")
        self.assertTrue(url.endswith("/v1/chat/completions"), url)
        self.assertEqual(body["temperature"], 0)


class AnswerTest(unittest.TestCase):
    def test_claude_envelope_yields_the_text_blocks(self):
        data = {"content": [{"type": "text", "text": "YES"}]}
        self.assertEqual(eval_rerank.judge_answer("claude-sonnet-5", data), "YES")

    def test_claude_envelope_skips_non_text_blocks(self):
        data = {"content": [{"type": "thinking", "thinking": "hmm"},
                            {"type": "text", "text": "NO"}]}
        self.assertEqual(eval_rerank.judge_answer("claude-sonnet-5", data), "NO")

    def test_an_error_envelope_is_empty_rather_than_a_crash(self):
        """What a rejected request actually returns. It must reach `judge` as
        an unparseable answer, not as a KeyError halfway through a run."""
        data = {"type": "error", "error": {"message": "temperature is deprecated"}}
        for model in ("claude-sonnet-5", "gemini-2.5-flash", "some-local-model"):
            self.assertEqual(eval_rerank.judge_answer(model, data), "", model)

    def test_gemini_envelope_still_unwraps(self):
        data = {"candidates": [{"content": {"parts": [{"text": "YES"}]}}]}
        self.assertEqual(eval_rerank.judge_answer("gemini-2.5-flash", data), "YES")

    def test_openai_envelope_still_unwraps(self):
        data = {"choices": [{"message": {"content": "NO"}}]}
        self.assertEqual(eval_rerank.judge_answer("some-local-model", data), "NO")


if __name__ == "__main__":
    unittest.main()
