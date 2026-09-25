"""Tests for check_descriptiveness.py"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "check_descriptiveness.py"
SPEC = importlib.util.spec_from_file_location("check_descriptiveness", SCRIPT_PATH)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class DescriptivenessCheckerTest(unittest.TestCase):
    """Test the descriptiveness checker logic."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_short_label_filename_is_flagged(self):
        """Filenames that are too short or generic are flagged."""
        note = self.vault / "2026-09-25 notes.md"
        note.write_text("---\n---\n\nSome content here.", encoding="utf-8")

        findings = CHECKER.check_note(note, min_words=600)
        self.assertTrue(len(findings["non_descriptive_filename"]) > 0)
        # Should have both "too short" and "generic label" findings
        all_findings = " ".join(findings["non_descriptive_filename"])
        self.assertIn("generic label", all_findings)

    def test_long_descriptive_filename_is_not_flagged(self):
        """Descriptive filenames with sufficient words are not flagged."""
        note = self.vault / "2026-09-25 building a better search index for markdown.md"
        note.write_text("---\n---\n\nSome content here.", encoding="utf-8")

        findings = CHECKER.check_note(note, min_words=600)
        self.assertEqual(len(findings["non_descriptive_filename"]), 0)

    def test_catalog_card_exemption_suppresses_filename_finding(self):
        """Notes with both repo: and url: frontmatter are exempt from filename checks."""
        note = self.vault / "2026-09-25 notes.md"
        note.write_text(
            "---\nrepo: some-repo\nurl: https://example.com\n---\n\nContent.",
            encoding="utf-8"
        )

        findings = CHECKER.check_note(note, min_words=600)
        self.assertEqual(len(findings["non_descriptive_filename"]), 0)

    def test_day_log_exemption_suppresses_filename_finding(self):
        """Notes whose stem is entirely a date are exempt from filename checks."""
        note = self.vault / "2026-09-25.md"
        note.write_text("---\n---\n\nDay log content.", encoding="utf-8")

        findings = CHECKER.check_note(note, min_words=600)
        self.assertEqual(len(findings["non_descriptive_filename"]), 0)

    def test_concept_note_exemption_suppresses_filename_finding(self):
        """Notes with no leading date are exempt from filename checks."""
        note = self.vault / "search.md"
        note.write_text("---\n---\n\nConcept definition.", encoding="utf-8")

        findings = CHECKER.check_note(note, min_words=600)
        self.assertEqual(len(findings["non_descriptive_filename"]), 0)

    def test_structural_file_exemption_suppresses_filename_finding(self):
        """AGENTS.md, CLAUDE.md, README.md, SKILL.md are exempt."""
        for filename in ["AGENTS.md", "CLAUDE.md", "README.md", "SKILL.md"]:
            note = self.vault / filename
            note.write_text("---\n---\n\nStructural content.", encoding="utf-8")

            findings = CHECKER.check_note(note, min_words=600)
            self.assertEqual(len(findings["non_descriptive_filename"]), 0)

    def test_long_note_without_description_is_flagged(self):
        """Notes over the threshold without a description are flagged."""
        note = self.vault / "2026-09-25 test note.md"
        body = " ".join(["word"] * 700)
        note.write_text(f"---\n---\n\n{body}", encoding="utf-8")

        findings = CHECKER.check_note(note, min_words=600)
        self.assertTrue(findings["missing_description"])

    def test_short_note_without_description_is_not_flagged(self):
        """Notes below the threshold are not flagged for missing description."""
        note = self.vault / "2026-09-25 test note.md"
        body = " ".join(["word"] * 100)
        note.write_text(f"---\n---\n\n{body}", encoding="utf-8")

        findings = CHECKER.check_note(note, min_words=600)
        self.assertFalse(findings["missing_description"])

    def test_long_note_with_description_is_not_flagged(self):
        """Notes with a description are not flagged."""
        note = self.vault / "2026-09-25 test note.md"
        body = " ".join(["word"] * 700)
        note.write_text(
            f"---\ndescription: A good description\n---\n\n{body}",
            encoding="utf-8"
        )

        findings = CHECKER.check_note(note, min_words=600)
        self.assertFalse(findings["missing_description"])

    def test_generic_heading_is_flagged(self):
        """Generic headings from the label set are flagged."""
        note = self.vault / "2026-09-25 a descriptive filename here.md"
        note.write_text(
            "---\n---\n\n## Summary\nContent.\n\n## Notes\nMore content.",
            encoding="utf-8"
        )

        findings = CHECKER.check_note(note, min_words=600)
        self.assertGreater(len(findings["label_headings"]), 0)
        self.assertTrue(any("summary" in h.lower() for h in findings["label_headings"]))

    def test_catalog_card_exempt_from_description_requirement(self):
        """Catalog cards are exempt from missing description check."""
        note = self.vault / "2026-09-25 notes.md"
        body = " ".join(["word"] * 700)
        note.write_text(
            f"---\nrepo: some-repo\nurl: https://example.com\n---\n\n{body}",
            encoding="utf-8"
        )

        findings = CHECKER.check_note(note, min_words=600)
        self.assertFalse(findings["missing_description"])


class WalkBoundaryTest(unittest.TestCase):
    """The walk must stop at every boundary that holds a second copy of a vault.

    These are regression tests for a real miscount rather than hypotheticals. The
    first version of the walk excluded only `.obsidian`, `.git` and `.trash`, and
    reported 11,337 findings against a vault of 1,218 notes: it had descended into
    `.claude/worktrees/`, which holds a full checkout per agent worktree, and into
    a nested repository mounted inside the vault. Every check below is cheap and
    each one maps to one wrong number that shipped.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.bad_note = "2026-09-25 notes.md"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _plant(self, *parts):
        """Write a note that the checker would flag, at vault/<parts>."""
        target = self.vault.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("---\n---\n\nSome content here.", encoding="utf-8")
        return target

    def _findings(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(self.vault), "--warn-only", "--json"],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    def test_only_the_real_note_is_counted(self):
        self._plant(self.bad_note)

        # an agent worktree: a complete second checkout of this same vault
        self._plant(".claude", "worktrees", "wt", self.bad_note)
        # a nested repository: a different vault with its own conventions
        self._plant("nested", self.bad_note)
        (self.vault / "nested" / ".git").mkdir()
        # dependencies, which are not notes
        self._plant("node_modules", "pkg", self.bad_note)

        findings = self._findings()
        self.assertEqual(len(findings), 1, f"expected 1 finding, got {len(findings)}")
        self.assertEqual(Path(findings[0]["path"]).name, self.bad_note)

    def test_a_symlinked_directory_is_not_followed(self):
        # The same second repository is a symlink on one machine and a real clone
        # on another, so both forms have to be skipped.
        self._plant(self.bad_note)
        outside = Path(self.temp_dir.name).parent / f"{self.vault.name}-outside"
        outside.mkdir(exist_ok=True)
        try:
            (outside / self.bad_note).write_text("---\n---\n\nSome content here.",
                                                 encoding="utf-8")
            (self.vault / "linked").symlink_to(outside, target_is_directory=True)

            findings = self._findings()
            self.assertEqual(len(findings), 1, f"expected 1 finding, got {len(findings)}")
        finally:
            (outside / self.bad_note).unlink(missing_ok=True)
            outside.rmdir()

    def test_skip_dir_removes_a_machine_written_directory(self):
        self._plant(self.bad_note)
        self._plant("generated", self.bad_note)

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(self.vault),
             "--warn-only", "--json", "--skip-dir", "generated"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(len(json.loads(result.stdout)), 1)


if __name__ == "__main__":
    unittest.main()
