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


def collected_item(query: str, lexical: list[str], semantic: list[str]) -> dict:
    """One query's candidates, each retriever's list given as paths in rank order."""
    return {
        "query": query,
        "lexical": {path: {"path": path, "heading": "", "start_line": 1,
                           "lex_rank": rank, "snippet": ""}
                    for rank, path in enumerate(lexical)},
        "semantic": {path: {"path": path, "heading": "", "start_line": 1,
                            "vec_rank": rank, "raw_sim": 1.0}
                     for rank, path in enumerate(semantic)},
    }


class PowerCheckTest(unittest.TestCase):
    """Before believing a null, check the metric can see a change that is real."""

    def test_removing_the_retriever_that_was_carrying_it_is_detected(self):
        # The vector list puts the answer first every time; the lexical list
        # buries it under five wrong notes. At 1:1 the vector list wins and the
        # answer ranks first, so deleting the vector list has to register.
        filler = [f"w{j}.md" for j in range(5)]
        collected = [collected_item(f"q{i}", filler + ["right.md"], ["right.md"])
                     for i in range(30)]
        order = [item["query"] for item in collected]
        labels = {query: {"right.md"} for query in order}

        checks = sweep.power_check(collected, order, 5, labels)
        lexical_only = next(c for c in checks if c["ablation"] == "lexical only")
        self.assertLess(lexical_only["mrr"]["high"], 0.0)
        self.assertLess(lexical_only["ndcg"]["high"], 0.0)

    def test_a_corpus_the_ablation_cannot_move_reports_no_power(self):
        """Both retrievers return the same list, so no weighting of them can
        reorder anything. The check has to say so rather than report a clean
        null — on this corpus every sweep result is vacuous, and that is the
        one thing worth knowing before reading the table."""
        collected = [collected_item(f"q{i}", ["a.md", "b.md"], ["a.md", "b.md"])
                     for i in range(30)]
        order = [item["query"] for item in collected]
        labels = {query: {"a.md"} for query in order}

        for check in sweep.power_check(collected, order, 5, labels):
            for metric in ("mrr", "ndcg"):
                test = check[metric]
                self.assertEqual(test["delta"], 0.0)
                self.assertLessEqual(test["low"], 0.0)
                self.assertGreaterEqual(test["high"], 0.0)


class ShuffledNullTest(unittest.TestCase):
    def test_a_real_effect_does_not_survive_detaching_the_labels(self):
        """The corpus below has a genuine gain at 4:1. Permuting which query
        each label set belongs to must destroy it: if significance survives,
        the pipeline is scoring something other than relevance."""
        collected = [
            collected_item(f"q{i}", ["miss%d.md" % i, "x.md", "hit%d.md" % i],
                           ["hit%d.md" % i, "miss%d.md" % i])
            for i in range(24)
        ]
        order = [item["query"] for item in collected]
        labels = {f"q{i}": {"hit%d.md" % i} for i in range(24)}

        real = sweep.paired_bootstrap(
            sweep.scored_series(collected, order, 5, labels)[0],
            sweep.scored_series(collected, order, 5, labels, w_vec=4.0)[0],
        )
        self.assertGreater(real["low"], 0.0)

        null = sweep.shuffled_null(collected, order, 5, labels, 4.0, rounds=3)
        self.assertEqual(null["false_positives"], 0)
        self.assertEqual(len(null["trials"]), 3)


class LengthBinTest(unittest.TestCase):
    def test_the_boundaries_land_where_the_labels_say(self):
        self.assertEqual(sweep.length_bin("one two"), "1-2 words")
        self.assertEqual(sweep.length_bin("one two three"), "3-5 words")
        self.assertEqual(sweep.length_bin("a b c d e"), "3-5 words")
        self.assertEqual(sweep.length_bin("a b c d e f"), "6-9 words")
        self.assertEqual(sweep.length_bin("a b c d e f g h i"), "6-9 words")
        self.assertEqual(sweep.length_bin("a b c d e f g h i j"), "10+ words")


class BinnedDeltaTest(unittest.TestCase):
    def test_two_query_kinds_that_cancel_are_reported_separately(self):
        """Short queries gain exactly what long queries lose, so the average
        is zero and the honest answer is not "the weight does nothing" but
        "the weight wants to depend on the query"."""
        collected, labels = [], {}
        for i in range(4):
            short = f"s{i} q"
            collected.append(collected_item(
                short, [f"miss{i}.md", "x.md", f"hit{i}.md"],
                [f"hit{i}.md", f"miss{i}.md"]))
            labels[short] = {f"hit{i}.md"}

            # The mirror image: here the lexical list is the one that is right,
            # so leaning on the vector list costs the same half a rank.
            long = f"l{i} a b c d e"
            collected.append(collected_item(
                long,
                [f"HIT{i}.md"] + [f"f{j}.md" for j in range(7)] + [f"MISS{i}.md"],
                [f"MISS{i}.md", "y.md", "z.md", f"HIT{i}.md"]))
            labels[long] = {f"HIT{i}.md"}

        order = [item["query"] for item in collected]
        table = sweep.binned_delta(collected, order, [1.0, 4.0], 5, labels)
        by_bin = {entry["bin"]: entry for entry in table}

        self.assertAlmostEqual(by_bin["1-2 words"]["delta"][4.0], 0.5)
        self.assertAlmostEqual(by_bin["6-9 words"]["delta"][4.0], -0.5)

        overall = sweep.paired_bootstrap(
            sweep.scored_series(collected, order, 5, labels)[0],
            sweep.scored_series(collected, order, 5, labels, w_vec=4.0)[0],
        )
        self.assertAlmostEqual(overall["delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
