"""Every knob the live ranking path turns, in one place, overridable by env var.

WHY THIS EXISTS. The ranking constants used to live wherever they were first
written: the RRF k in index_pkm_meta.py's fuser, the recency and fusion lambdas
in searchd.py's header, and a separate, unrelated set of argparse defaults in
recency_prior_experiment.py. Nothing tied them together, so the experiment
harness and the daemon drifted apart without anyone noticing. The recency paper
spent a week describing a "shipped" configuration of lambda=0.5, tau=30 days and
a symmetric time gap. Those three numbers are the argparse defaults of
recency_prior_experiment.py (lines 124, 325, 330). The daemon has never used
them: search_vault.py contains no recency term at all, and searchd.py's is a
6-hour hard cutoff at lambda=0.05. A week of measurement was reported against a
configuration that was not running anywhere.

Two rules follow, and this module exists to enforce them.

  1. ONE SOURCE OF TRUTH. A knob that the live path reads is defined here and
     nowhere else. searchd.py and index_pkm_meta.py bind their module-level
     names from this module, so the old names still resolve for callers and
     tests, but the value behind them has exactly one definition.

  2. TUNABLE WITHOUT AN EDIT. Every knob reads an env var. Sweeping a parameter
     must not require editing the module that uses it, because a sweep that
     needs an edit is a sweep whose result cannot be reproduced later. Call
     `snapshot()` and store what it returns alongside any measurement.

DEFAULTS ARE TODAY'S BEHAVIOUR. Every default below is the value the live path
already used before this module existed, so importing it changes no ranking.
Each carries its provenance, and where the 2026-09-16/17 research pass
undermined that provenance, the comment says so rather than quietly keeping the
number.
"""

from __future__ import annotations

import os


def _float(name: str, default: float) -> float:
    """Read a float knob from the environment, falling back to the default.

    A malformed value is a configuration error worth failing on rather than
    silently ignoring: a sweep that sets PKM_RRF_W_LEX=0,9 in a shell that eats
    the comma would otherwise record its results against the default weight and
    report them as the swept one, which is the exact failure this module is for.
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{name}={raw!r} is not a number") from None


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name}={raw!r} is not an integer") from None


# ---------------------------------------------------------------------------
# hybrid fusion, the /search path
# ---------------------------------------------------------------------------

# Reciprocal Rank Fusion's rank offset. 60 is the value from the original RRF
# paper (Cormack, Clarke & Buettcher 2009) and was never tuned on this corpus.
RRF_K = _float("PKM_RRF_K", 60.0)

# Per-list weights on the two fused rankings, lexical (BM25 over sections_fts)
# and semantic (cosine over the section vectors):
#
#     score = W_LEX / (K + lex_rank) + W_VEC / (K + vec_rank)
#
# Both default to 1.0, which is the unweighted sum the fuser has always
# computed, so the default ordering is unchanged to the last bit.
#
# THESE ARE THE KNOBS MOST WORTH SWEEPING. The recency pass found, across every
# fusion function it tried, that the WEIGHT dominates the functional form: a
# 22.4-point swing from the weight against 1.5 points from the timescale and
# 3.5-8.1 from the tail shape. Its sharpest case was RRF itself. An unweighted
# 1:1 fusion scored -6.69%, worse than not fusing at all, and re-weighting the
# same function to 9:1 recovered it monotonically to +5.02%: a 24-point swing
# with the functional form held fixed.
#
# DO NOT TRANSPLANT 9:1 HERE. That measurement fused a CONTENT ranking with a
# RECENCY ranking, which is a different pair of lists from the lexical/semantic
# pair below, and the week of 2026-09-17 was mostly spent killing exactly this
# kind of unsupported transfer. What carries over is the shape of the finding,
# not its argument: an unweighted 1:1 is an arbitrary choice, it happened to be
# the worst available choice in the one case anybody measured, and nobody has
# ever measured it here. rrf_weight_sweep.py is the instrument for doing so.
RRF_W_LEX = _float("PKM_RRF_W_LEX", 1.0)
RRF_W_VEC = _float("PKM_RRF_W_VEC", 1.0)

# How many fused candidates the cross-encoder reorders when rerank is on. Twenty
# because the sections that answered the sample query sat at fused rank 9 and
# 11, so a top-10 rerank would have found one and missed the other. Costs about
# 22ms per candidate, so roughly 533ms over 20.
RERANK_CANDIDATES = _int("PKM_RERANK_CANDIDATES", 20)


# ---------------------------------------------------------------------------
# recency, the /similar path only
# ---------------------------------------------------------------------------

# A hard cutoff, not a decay curve: proximity is 1.0 inside the window and 0.0
# outside it, added at RECENCY_LAMBDA.
#
# PROVENANCE, AND WHAT IS LEFT OF IT. These came from recency_prior_experiment.py
# against real wikilinks, reported as 5/5 seeds positive and +8.60% MRR. Two
# results from 2026-09-16/17 cut into that number and neither has been worked
# through the wired values yet:
#
#   - the wikilink ground truth overstates the recency advantage by 1.97x
#     [1.48, 2.55], measured over 56,820 query-candidate rows against 240
#     LLM-judged items. The +8.60% above is a wikilink-scored number.
#   - the four-vault replication collapsed. kepano and bramses are bulk-published
#     repositories where commit batching confounds the signal, and obsidian-help
#     flips sign. The origin vault's +7.73% holds at +6.50% held-out, and it is
#     now effectively the only corpus supporting the effect.
#
# The window stays where it is because it is opt-in (/similar?recency=1 or
# &fusion=1, never /search) and lambda=0.05 already sits near the safe corner
# the concentration analysis pointed at. It should not be promoted to /search
# on the strength of the provenance above. See the vault note
# "2026-09-17 the wikilink ground truth overstates the recency advantage by
# about two times".
RECENCY_TAU_HOURS = _float("PKM_RECENCY_TAU_HOURS", 6.0)
RECENCY_LAMBDA = _float("PKM_RECENCY_LAMBDA", 0.05)


# ---------------------------------------------------------------------------
# the stacked /similar?fusion=1 signals
# ---------------------------------------------------------------------------

# Calibrated in stacked_fusion_experiment.py --calibrate: a grid over the three
# lambdas on a 60% calibration fold, scored on the 40% held-out fold the grid
# never saw. The fixed combo beat the best single addition on every held-out
# fold across seeds 0/1/2: +19.6%/+16.6%/+20.6% against +15.4%/+14.8%/+14.0%.
# The recency term here reuses the hard cutoff above, so it is calibrated
# against the same signal shape that is wired, not the decay curve the
# experiment sweeps elsewhere.
#
# The same 1.97x wikilink caveat applies to these three, which were also scored
# against wikilinked pairs.
FUSION_LAMBDA_RECENCY = _float("PKM_FUSION_LAMBDA_RECENCY", 0.05)
FUSION_LAMBDA_COCOMMIT = _float("PKM_FUSION_LAMBDA_COCOMMIT", 1.5)
FUSION_LAMBDA_AA = _float("PKM_FUSION_LAMBDA_AA", 0.15)

# Zeroes a shared neighbour's whole Adamic-Adar term once that neighbour's own
# degree exceeds this, so a same-day batch of notes whose only wikilinks point
# at a shared catalog note stops scoring a relationship it does not have. A
# precision fix, confirmed NOT to improve MRR (a wash to negative on held-out
# MRR at every threshold tried). Do not cite it as a ranking win.
FUSION_Z_HUB_DEGREE = _int("PKM_FUSION_Z_HUB_DEGREE", 20)


# ---------------------------------------------------------------------------
# provenance
# ---------------------------------------------------------------------------

#: Knob name -> env var, for `snapshot()` and for anything that wants to sweep
#: without hardcoding the prefix.
ENV_VARS = {
    "RRF_K": "PKM_RRF_K",
    "RRF_W_LEX": "PKM_RRF_W_LEX",
    "RRF_W_VEC": "PKM_RRF_W_VEC",
    "RERANK_CANDIDATES": "PKM_RERANK_CANDIDATES",
    "RECENCY_TAU_HOURS": "PKM_RECENCY_TAU_HOURS",
    "RECENCY_LAMBDA": "PKM_RECENCY_LAMBDA",
    "FUSION_LAMBDA_RECENCY": "PKM_FUSION_LAMBDA_RECENCY",
    "FUSION_LAMBDA_COCOMMIT": "PKM_FUSION_LAMBDA_COCOMMIT",
    "FUSION_LAMBDA_AA": "PKM_FUSION_LAMBDA_AA",
    "FUSION_Z_HUB_DEGREE": "PKM_FUSION_Z_HUB_DEGREE",
}


def snapshot() -> dict:
    """The active value of every knob, plus which ones came from the environment.

    Store this next to any measurement. A result whose configuration was not
    recorded is the failure described at the top of this file: a number that
    cannot be matched to the code that produced it, and that therefore gets
    attributed to whatever the reader assumes is running.
    """
    values = globals()
    overridden = sorted(
        name for name, env in ENV_VARS.items()
        if os.environ.get(env) not in (None, "")
    )
    return {
        "values": {name: values[name] for name in ENV_VARS},
        "overridden": overridden,
    }


def describe() -> str:
    """One line per knob, marking the ones the environment is overriding."""
    state = snapshot()
    overridden = set(state["overridden"])
    lines = []
    for name, env in ENV_VARS.items():
        mark = f"  <- {env}" if name in overridden else ""
        lines.append(f"{name} = {state['values'][name]}{mark}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe())
