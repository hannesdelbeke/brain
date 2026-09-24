"""The FTS5 fallback must answer without paying for numpy or fastembed.

This lives apart from test_fts_fallback.py because the assertion only means
something in a clean interpreter. That module imports index_pkm_meta to build
its fixture, which pulls numpy and fastembed into sys.modules before the
fallback is ever called, so an in-process check there would pass no matter what
search_vault imported. The child process below imports search_vault and nothing
else, which is the only arrangement where a regression can actually fail.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)

# Runs in a fresh interpreter, so sys.modules reflects only what importing
# search_vault and calling the fallback actually cost.
CHILD = """
import json, sys
sys.path.insert(0, {skill!r})
import search_vault
results = search_vault.fast_fts_search("fallbackphrase", {database!r}, top=5)
neural = [name for name in ("numpy", "fastembed", "onnxruntime", "torch", "index_pkm_meta")
          if name in sys.modules]
print(json.dumps({{"count": len(results), "neural": neural}}))
"""


class FtsNoNeuralImportsTest(unittest.TestCase):
    def test_fallback_answers_without_importing_neural_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "alpha.md").write_text("## Result\nA distinctive fallbackphrase.\n", encoding="utf-8")
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            completed = subprocess.run(
                [sys.executable, "-c", CHILD.format(skill=str(SKILL), database=str(database))],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertGreater(payload["count"], 0, "fallback returned nothing on the fixture")
            self.assertEqual(payload["neural"], [], f"fallback imported neural dependencies: {payload['neural']}")


if __name__ == "__main__":
    unittest.main()
