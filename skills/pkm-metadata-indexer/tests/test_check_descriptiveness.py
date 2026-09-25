"""Tests for check_descriptiveness.py"""
import importlib.util
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


if __name__ == "__main__":
    unittest.main()
