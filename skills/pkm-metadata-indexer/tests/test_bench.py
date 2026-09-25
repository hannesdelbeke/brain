"""Tests for eval_bench.py two-arm benchmark."""

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))

import eval_bench  # noqa: E402
import eval_judge  # noqa: E402


class TestArmParamParser(unittest.TestCase):
    """Test the arm parameter string parser."""

    def test_parse_empty_string(self):
        self.assertEqual(eval_bench.parse_arm_params(""), {})
        self.assertEqual(eval_bench.parse_arm_params("  "), {})

    def test_parse_single_param(self):
        self.assertEqual(eval_bench.parse_arm_params("expand=1"), {"expand": "1"})

    def test_parse_multiple_params(self):
        result = eval_bench.parse_arm_params("expand=1,rerank=1")
        self.assertEqual(result, {"expand": "1", "rerank": "1"})

    def test_parse_with_spaces(self):
        result = eval_bench.parse_arm_params(" expand = 1 , rerank = 0 ")
        self.assertEqual(result, {"expand": "1", "rerank": "0"})

    def test_malformed_missing_equals_raises(self):
        with self.assertRaises(ValueError) as ctx:
            eval_bench.parse_arm_params("expand")
        self.assertIn("missing '='", str(ctx.exception))

    def test_malformed_empty_key_raises(self):
        with self.assertRaises(ValueError) as ctx:
            eval_bench.parse_arm_params("=1")
        self.assertIn("Empty key or value", str(ctx.exception))

    def test_malformed_empty_value_raises(self):
        with self.assertRaises(ValueError) as ctx:
            eval_bench.parse_arm_params("expand=")
        self.assertIn("Empty key or value", str(ctx.exception))


class TestOriginValidation(unittest.TestCase):
    """Test that origin prefix is enforced."""

    def test_valid_origin_passes(self):
        # Should not raise
        eval_bench.validate_origin("eval-bench")
        eval_bench.validate_origin("eval-foo")
        eval_bench.validate_origin("eval-")

    def test_invalid_origin_raises(self):
        with self.assertRaises(ValueError) as ctx:
            eval_bench.validate_origin("bench")
        self.assertIn("must start with 'eval-'", str(ctx.exception))

        with self.assertRaises(ValueError):
            eval_bench.validate_origin("test-bench")

        with self.assertRaises(ValueError):
            eval_bench.validate_origin("")

    def test_default_origin_is_valid(self):
        # The default origin used in main() must pass validation
        self.assertTrue(eval_bench.validate_origin("eval-bench") is None)


class TestPercentile(unittest.TestCase):
    """Test percentile computation."""

    def test_percentile_empty_list(self):
        self.assertEqual(eval_bench.percentile([], 0.5), 0.0)

    def test_percentile_single_value(self):
        self.assertEqual(eval_bench.percentile([10.0], 0.5), 10.0)

    def test_percentile_median_odd_count(self):
        # [1, 2, 3, 4, 5] -> median is 3
        self.assertEqual(eval_bench.percentile([1, 2, 3, 4, 5], 0.5), 3.0)

    def test_percentile_median_even_count(self):
        # [1, 2, 3, 4] -> median is 2.5 (interpolated)
        self.assertEqual(eval_bench.percentile([1, 2, 3, 4], 0.5), 2.5)

    def test_percentile_p95(self):
        # 100 values: p95 should be near 95th value
        values = list(range(1, 101))
        p95 = eval_bench.percentile(values, 0.95)
        # p95 of 1..100 should be 95.05 (linear interpolation)
        self.assertAlmostEqual(p95, 95.05, places=1)

    def test_percentile_unsorted_input(self):
        # Function should sort internally
        self.assertEqual(eval_bench.percentile([5, 1, 3, 2, 4], 0.5), 3.0)


class TestJudgeIntegration(unittest.TestCase):
    """Test that --no-judge skips precision and compute_metrics includes p3."""

    @patch("urllib.request.urlopen")
    @patch("eval_judge.judge_all")
    def test_no_judge_skips_precision(self, mock_judge_all, mock_urlopen):
        """--no-judge must perform zero judge calls."""
        # Mock the search endpoint
        mock_response = MagicMock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.read.return_value = b'{"results": [], "took_ms": 10}'
        mock_urlopen.return_value = mock_response

        # Mock load to avoid file I/O. main() prints a full report, which would
        # otherwise land in the middle of the suite's output and read as a failure.
        with patch("eval_judge.load_questions", return_value=[("q1", "holdout")]):
            with patch("sys.argv", ["eval_bench.py", "--vault", "test", "--questions", "q.json",
                                   "--arm-a", "expand=1", "--arm-b", "expand=0", "--no-judge"]):
                with contextlib.redirect_stdout(io.StringIO()):
                    eval_bench.main()

        # judge_all should never have been called
        mock_judge_all.assert_not_called()

    def test_compute_metrics_returns_p3_p5_p10(self):
        """compute_metrics must return p3, p5, and p10 for historical comparability."""
        verdicts = {"a.md": True, "b.md": False, "c.md": True, "d.md": None}
        ranked = ["a.md", "b.md", "c.md", "d.md"]

        metrics = eval_judge.compute_metrics(ranked, verdicts)

        # All three precision levels must exist
        self.assertIn("p3", metrics)
        self.assertIn("p5", metrics)
        self.assertIn("p10", metrics)

        # p3 should be (2, 3) - 2 useful in top 3, out of 3 slots
        self.assertEqual(metrics["p3"], (2, 3))
        # p5 should be (2, 4) - 2 useful in top 5, but only 4 results exist
        self.assertEqual(metrics["p5"], (2, 4))
        # p10 should be (2, 4) - same as p5 since we only have 4 results
        self.assertEqual(metrics["p10"], (2, 4))

        # Other keys must still exist
        self.assertIn("first_rank", metrics)
        self.assertIn("has_useful", metrics)


class TestJudgedContent(unittest.TestCase):
    """What text reaches the judge for one hit.

    The daemon returns `snippet: null` for about a quarter of hits, and the
    original `hit.get("snippet", "")` handed that None straight to str.format,
    which renders it as the word "None". These pin the field precedence so that
    regression cannot come back silently.
    """

    def test_text_is_preferred_over_snippet(self):
        hit = {"text": "the full section", "snippet": "a fragment"}
        self.assertEqual(eval_bench.judged_content(hit), "the full section")

    def test_null_snippet_falls_back_to_text(self):
        hit = {"text": "the full section", "snippet": None}
        self.assertEqual(eval_bench.judged_content(hit), "the full section")

    def test_null_text_falls_back_to_snippet(self):
        hit = {"text": None, "snippet": "a fragment"}
        self.assertEqual(eval_bench.judged_content(hit), "a fragment")

    def test_the_word_none_never_leaks_into_the_content(self):
        # The exact original bug: a null field must not stringify.
        for hit in ({"snippet": None}, {"text": None}, {"text": None, "snippet": None}, {}):
            self.assertEqual(eval_bench.judged_content(hit), "",
                             f"a hit with no text must yield empty, not 'None': {hit!r}")


class TestJudgePrecisionContent(unittest.TestCase):
    """The content selection as judge_precision actually applies it."""

    def search_returning(self, hits: list[dict]):
        """Patch urlopen so one /search call returns `hits`."""
        response = MagicMock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({"results": hits, "took_ms": 10}).encode()
        return patch("urllib.request.urlopen", return_value=response)

    def pending_prompts(self, hits: list[dict]) -> list[str]:
        """Run judge_precision over one question and collect the prompts it queued."""
        captured = []

        def fake_judge_all(pending, cached, failures, workers=8):
            captured.extend(prompt for _q, _p, _m, prompt in pending)

        with self.search_returning(hits):
            with patch("eval_judge.judge_all", side_effect=fake_judge_all):
                with contextlib.redirect_stdout(io.StringIO()):
                    eval_bench.judge_precision(
                        "v", [("a question", "g")], 10, "eval-test", {}, {}, {})
        return captured

    def test_a_null_snippet_is_judged_on_its_text(self):
        prompts = self.pending_prompts([{"path": "a.md", "line": 1,
                                         "snippet": None, "text": "real section body"}])
        self.assertEqual(len(prompts), 1)
        self.assertIn("real section body", prompts[0])

    def test_a_hit_with_no_text_is_not_sent_to_the_judge(self):
        # Spending a call to have the judge confirm that an empty note is useless
        # caches a verdict that drags down every later run on the same question.
        prompts = self.pending_prompts([{"path": "a.md", "line": 1,
                                         "snippet": None, "text": None}])
        self.assertEqual(prompts, [], "an empty hit must not be judged at all")


class TestSearchOriginPropagation(unittest.TestCase):
    """Test that every search call carries a non-empty origin."""

    @patch("urllib.request.urlopen")
    def test_search_includes_origin(self, mock_urlopen):
        """Every /search call must include the origin parameter."""
        mock_response = MagicMock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.read.return_value = b'{"results": [], "took_ms": 10}'
        mock_urlopen.return_value = mock_response

        # Call search directly
        eval_bench.search("test-vault", "test question", 10, "eval-test", {"expand": "1"})

        # Verify urlopen was called with a URL containing origin=eval-test
        self.assertEqual(mock_urlopen.call_count, 1)
        called_url = mock_urlopen.call_args[0][0]
        self.assertIn("origin=eval-test", called_url)
        self.assertIn("vault=test-vault", called_url)
        self.assertIn("expand=1", called_url)


if __name__ == "__main__":
    unittest.main()
