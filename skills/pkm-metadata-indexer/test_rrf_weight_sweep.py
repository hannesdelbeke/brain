"""The sweep's job is to say whether a weight is better. These test the part
that can say "no".

A sweep that only reports means will always name a winner, because one of nine
cells is always highest. The bootstrap and the held-out split exist to stop that
number being read as a result, so they are the part worth testing: if they were
broken in the direction of optimism, nothing downstream would notice.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rrf_weight_sweep as sweep


class PairedBootstrapTest(unittest.TestCase):
    def test_no_difference_gives_an_interval_on_zero(self):
        scores = [0.5, 1.0, 0.25, 0.0, 0.75] * 4
        result = sweep.paired_bootstrap(scores, scores, rounds=500)
        self.assertEqual(result["delta"], 0.0)
        self.assertEqual((result["low"], result["high"]), (0.0, 0.0))
        self.assertEqual((result["wins"], result["losses"]), (0, 0))

    def test_a_consistent_gain_clears_zero(self):
        base = [0.4, 0.5, 0.6, 0.3, 0.7] * 6
        better = [value + 0.1 for value in base]
        result = sweep.paired_bootstrap(base, better, rounds=2000)
        self.assertAlmostEqual(result["delta"], 0.1, places=6)
        self.assertGreater(result["low"], 0.0)
        self.assertEqual(result["wins"], len(base))
        self.assertEqual(result["losses"], 0)

    def test_a_concentrated_gain_with_no_regressions_still_clears_zero(self):
        """Concentration alone is not noise. Four queries out of sixty improve
        and none get worse, and that is a real if narrow win — the test exists
        so nobody later "fixes" the bootstrap into calling it noise."""
        base = [0.5] * 60
        candidate = list(base)
        for index in range(4):
            candidate[index] = 1.0
        result = sweep.paired_bootstrap(base, candidate, rounds=4000)
        self.assertGreater(result["delta"], 0.0)
        self.assertGreater(result["low"], 0.0)
        self.assertEqual((result["wins"], result["losses"]), (4, 0))

    def test_a_gain_paid_for_by_other_queries_does_not_clear_zero(self):
        """The shape the real sweep produced at 4:1 — a positive mean, but
        carried by a few queries while others lose. That must not read as a
        win, and it is the case the mean on its own gets wrong."""
        base = [0.5] * 60
        candidate = list(base)
        for index in range(8):
            candidate[index] = 1.0
        for index in range(8, 13):
            candidate[index] = 0.0
        result = sweep.paired_bootstrap(base, candidate, rounds=4000)
        self.assertGreater(result["delta"], 0.0)
        self.assertLessEqual(result["low"], 0.0)

    def test_wins_and_losses_count_queries_not_magnitude(self):
        result = sweep.paired_bootstrap([0.0, 1.0, 0.5], [1.0, 0.0, 0.5], rounds=200)
        self.assertEqual((result["wins"], result["losses"]), (1, 1))

    def test_the_same_seed_gives_the_same_interval(self):
        base = [0.1, 0.9, 0.4, 0.6, 0.2, 0.8]
        candidate = [0.2, 0.7, 0.5, 0.6, 0.3, 0.9]
        first = sweep.paired_bootstrap(base, candidate, rounds=500, seed=7)
        second = sweep.paired_bootstrap(base, candidate, rounds=500, seed=7)
        self.assertEqual(first, second)

    def test_no_queries_is_not_a_crash(self):
        result = sweep.paired_bootstrap([], [], rounds=100)
        self.assertEqual(result["n"], 0)
        self.assertEqual(result["delta"], 0.0)


class SplitTest(unittest.TestCase):
    def test_the_halves_are_disjoint_and_cover_everything(self):
        queries = [f"q{index}" for index in range(21)]
        train, test = sweep.split_queries(queries)
        self.assertEqual(train & test, set())
        self.assertEqual(train | test, set(range(21)))

    def test_the_split_is_repeatable(self):
        queries = [f"q{index}" for index in range(40)]
        self.assertEqual(sweep.split_queries(queries), sweep.split_queries(queries))

    def test_a_different_seed_splits_differently(self):
        queries = [f"q{index}" for index in range(40)]
        self.assertNotEqual(sweep.split_queries(queries, seed=1),
                            sweep.split_queries(queries, seed=2))


class HeldOutTest(unittest.TestCase):
    """A weight that only looks good on the half it was chosen from."""

    def setUp(self):
        # Eight queries. Indices 0-3 are train, 4-7 test, under the split below.
        self.train = {0, 1, 2, 3}
        self.test = {4, 5, 6, 7}
        self.result = {
            "grid": [
                {"w_vec": 1.0, "rr_by_query": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]},
                # wins on train, loses by the same amount on test
                {"w_vec": 4.0, "rr_by_query": [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]},
            ],
        }

    def test_it_picks_on_train(self):
        report = sweep.held_out(self.result, "rr_by_query", self.train, self.test)
        self.assertEqual(report["picked_w_vec"], 4.0)
        self.assertAlmostEqual(report["train"], 1.0)
        self.assertAlmostEqual(report["baseline_train"], 0.5)

    def test_it_reports_the_loss_on_the_half_it_did_not_pick_from(self):
        report = sweep.held_out(self.result, "rr_by_query", self.train, self.test)
        self.assertAlmostEqual(report["test"], 0.0)
        self.assertAlmostEqual(report["test_delta"], -0.5)

    def test_a_genuinely_better_weight_survives_the_split(self):
        self.result["grid"][1]["rr_by_query"] = [0.9] * 8
        report = sweep.held_out(self.result, "rr_by_query", self.train, self.test)
        self.assertEqual(report["picked_w_vec"], 4.0)
        self.assertAlmostEqual(report["test_delta"], 0.4)
        self.assertGreater(report["bootstrap"]["low"], 0.0)


if __name__ == "__main__":
    unittest.main()
