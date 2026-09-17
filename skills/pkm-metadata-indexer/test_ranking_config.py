"""The config module's job is that a knob can move without an edit, and that a
bad value is heard rather than swallowed. Both are tested here, because the
failure it exists to prevent - a measurement reported against a configuration
that was not running - is silent by nature."""

import importlib
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ranking_config


class EnvOverrideTest(unittest.TestCase):
    def setUp(self):
        self.saved = {
            env: os.environ.get(env) for env in ranking_config.ENV_VARS.values()
        }
        self.addCleanup(self.restore)

    def restore(self):
        for env, value in self.saved.items():
            if value is None:
                os.environ.pop(env, None)
            else:
                os.environ[env] = value
        importlib.reload(ranking_config)

    def reload_with(self, **env):
        for key, value in env.items():
            os.environ[key] = value
        return importlib.reload(ranking_config)

    def test_defaults_are_the_values_the_live_path_already_used(self):
        for env in ranking_config.ENV_VARS.values():
            os.environ.pop(env, None)
        config = importlib.reload(ranking_config)
        self.assertEqual(config.RRF_K, 60.0)
        self.assertEqual(config.RRF_W_LEX, 1.0)
        self.assertEqual(config.RRF_W_VEC, 1.0)
        self.assertEqual(config.RERANK_CANDIDATES, 20)
        self.assertEqual(config.RECENCY_TAU_HOURS, 6.0)
        self.assertEqual(config.RECENCY_LAMBDA, 0.05)
        self.assertEqual(config.FUSION_LAMBDA_RECENCY, 0.05)
        self.assertEqual(config.FUSION_LAMBDA_COCOMMIT, 1.5)
        self.assertEqual(config.FUSION_LAMBDA_AA, 0.15)
        self.assertEqual(config.FUSION_Z_HUB_DEGREE, 20)

    def test_an_env_var_moves_a_knob(self):
        config = self.reload_with(PKM_RRF_W_VEC="2.5", PKM_FUSION_Z_HUB_DEGREE="7")
        self.assertEqual(config.RRF_W_VEC, 2.5)
        self.assertEqual(config.FUSION_Z_HUB_DEGREE, 7)

    def test_an_empty_value_is_not_an_override(self):
        config = self.reload_with(PKM_RRF_W_VEC="")
        self.assertEqual(config.RRF_W_VEC, 1.0)

    def test_a_malformed_value_raises_instead_of_falling_back(self):
        os.environ["PKM_RRF_W_VEC"] = "0,9"
        with self.assertRaises(ValueError) as caught:
            importlib.reload(ranking_config)
        self.assertIn("PKM_RRF_W_VEC", str(caught.exception))
        os.environ.pop("PKM_RRF_W_VEC", None)
        importlib.reload(ranking_config)

    def test_snapshot_names_what_the_environment_changed(self):
        config = self.reload_with(PKM_RRF_W_LEX="3.0")
        state = config.snapshot()
        self.assertEqual(state["values"]["RRF_W_LEX"], 3.0)
        self.assertEqual(state["overridden"], ["RRF_W_LEX"])
        self.assertIn("RRF_W_LEX", config.describe())

    def test_snapshot_covers_every_knob(self):
        state = ranking_config.snapshot()
        self.assertEqual(set(state["values"]), set(ranking_config.ENV_VARS))


class ConsumersBindTheConfigTest(unittest.TestCase):
    """searchd and the indexer must read the config, not their own copies."""

    def test_the_indexer_and_the_daemon_agree_with_the_config(self):
        import index_pkm_meta
        import searchd

        self.assertEqual(index_pkm_meta.RERANK_CANDIDATES,
                         ranking_config.RERANK_CANDIDATES)
        for name in ("RECENCY_TAU_HOURS", "RECENCY_LAMBDA", "FUSION_LAMBDA_RECENCY",
                     "FUSION_LAMBDA_COCOMMIT", "FUSION_LAMBDA_AA", "FUSION_Z_HUB_DEGREE"):
            self.assertEqual(getattr(searchd, name), getattr(ranking_config, name), name)


if __name__ == "__main__":
    unittest.main()
