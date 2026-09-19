"""Tests for the branch corpus scanner.

The refs are built with `git update-ref refs/remotes/origin/<name>`, which makes
a remote-tracking ref without a remote to push to, so each case is a few commits
rather than a clone.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import index_branches  # noqa: E402


class BranchScannerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "test")
        self.git("config", "user.email", "test@localhost")

        self.write("shared.md", "# shared\noriginal\n")
        self.write("other.md", "# other\nalso on the default branch\n")
        self.git("add", ".")
        self.git("commit", "-qm", "first")
        self.first = self.head()
        self.set_remote_ref("main", "HEAD")

    def tearDown(self):
        self.temp_dir.cleanup()

    # helpers

    def git(self, *arguments):
        return subprocess.run(
            ["git", *arguments], cwd=self.root, check=True, capture_output=True, text=True
        )

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def set_remote_ref(self, name, revision):
        self.git("update-ref", f"refs/remotes/origin/{name}", revision)

    def advance_default(self):
        """Move the default branch on, so anything cut before it is now behind."""
        self.write("shared.md", "# shared\nthe default branch moved on\n")
        self.git("commit", "-qam", "advance the default branch")
        self.set_remote_ref("main", "HEAD")

    def paths(self):
        notes, _, _, errors = index_branches.scan_branches(self.root)
        self.assertEqual(errors, [], f"unexpected errors: {errors}")
        return {row[0] for row in notes}

    # the empty cases

    def test_not_a_git_repository_returns_empty(self):
        outside = Path(self.temp_dir.name) / "plain"
        outside.mkdir()
        self.assertEqual(index_branches.scan_branches(outside), ([], [], [], []))

    def test_no_default_branch_returns_empty(self):
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        self.set_remote_ref("some-branch", "HEAD")
        self.assertEqual(index_branches.scan_branches(self.root), ([], [], [], []))

    def test_no_remote_refs_besides_default_returns_empty(self):
        self.assertEqual(self.paths(), set())

    # the filter

    def test_identical_ref_contributes_nothing(self):
        self.set_remote_ref("identical", "HEAD")
        self.assertEqual(self.paths(), set())

    def test_ref_that_is_only_behind_contributes_nothing(self):
        """The case the naive blob-oid filter gets wrong.

        `behind` holds the original `shared.md`, which differs from the default
        branch's copy, but it is the older version and contributes nothing.
        """
        self.set_remote_ref("behind", self.first)
        self.advance_default()
        self.assertEqual(self.paths(), set())

    def test_new_note_on_a_ref_is_indexed_with_its_ref(self):
        self.git("checkout", "-qb", "ahead")
        self.write("only here.md", "# only here\na note the default branch has never seen\n")
        self.git("add", "only here.md")
        self.git("commit", "-qm", "add a branch-only note")
        self.set_remote_ref("ahead", "HEAD")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.paths(), {"ahead/only here.md"})

    def test_modified_note_on_a_ref_is_indexed(self):
        self.git("checkout", "-qb", "edited")
        self.write("other.md", "# other\nthis ref changed it\n")
        self.git("commit", "-qam", "edit a note")
        self.set_remote_ref("edited", "HEAD")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.paths(), {"edited/other.md"})

    def test_deleted_note_is_not_indexed(self):
        self.git("checkout", "-qb", "remover")
        self.git("rm", "-q", "other.md")
        self.git("commit", "-qm", "delete a note")
        self.set_remote_ref("remover", "HEAD")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.paths(), set())

    def test_conflicting_ref_falls_back_to_paths_the_default_lacks(self):
        """A conflicted merge has no usable tree, so only genuinely new paths go in.

        `shared.md` conflicts and must stay out, because the merged blob would
        carry conflict markers; `new on the conflicting ref.md` is new and goes in.
        """
        self.git("checkout", "-qb", "conflicting")
        self.write("shared.md", "# shared\nthe ref went one way\n")
        self.write("new on the conflicting ref.md", "# new\nonly here\n")
        self.git("add", ".")
        self.git("commit", "-qm", "diverge")
        self.set_remote_ref("conflicting", "HEAD")
        self.git("checkout", "-q", "main")
        self.advance_default()

        tree, conflicted = index_branches.merged_tree(self.root, "origin/main", "origin/conflicting")
        self.assertTrue(conflicted, "the fixture was meant to conflict")
        self.assertEqual(self.paths(), {"conflicting/new on the conflicting ref.md"})

    def test_every_indexed_path_is_prefixed_with_its_ref(self):
        self.git("checkout", "-qb", "first-ref")
        self.write("one.md", "# one\n")
        self.git("add", "one.md")
        self.git("commit", "-qm", "one")
        self.set_remote_ref("first-ref", "HEAD")
        self.git("checkout", "-q", "main")
        self.git("checkout", "-qb", "second-ref")
        self.write("two.md", "# two\n")
        self.git("add", "two.md")
        self.git("commit", "-qm", "two")
        self.set_remote_ref("second-ref", "HEAD")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.paths(), {"first-ref/one.md", "second-ref/two.md"})

    # the rows themselves

    def test_sections_and_links_carry_the_prefixed_path(self):
        self.git("checkout", "-qb", "linker")
        self.write("linking.md", "# linking\n\n## a section\n\nrefers to [[other]] here.\n")
        self.git("add", "linking.md")
        self.git("commit", "-qm", "a note with a wikilink")
        self.set_remote_ref("linker", "HEAD")
        self.git("checkout", "-q", "main")

        notes, sections, links, errors = index_branches.scan_branches(self.root)
        self.assertEqual(errors, [])
        self.assertEqual([row[0] for row in notes], ["linker/linking.md"])
        self.assertTrue(sections, "the note should have produced at least one section")
        self.assertTrue(all(section.path == "linker/linking.md" for section in sections))
        self.assertEqual([link.source_path for link in links], ["linker/linking.md"])

    def test_a_blob_shared_by_two_paths_is_not_collapsed(self):
        """Two notes with byte-identical content share one blob oid.

        Keying the read by oid and mapping back through it loses one of them, so
        the scanner keys by path.
        """
        self.git("checkout", "-qb", "twins")
        self.write("twin a.md", "# twin\nsame bytes\n")
        self.write("twin b.md", "# twin\nsame bytes\n")
        self.git("add", ".")
        self.git("commit", "-qm", "two identical notes")
        self.set_remote_ref("twins", "HEAD")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.paths(), {"twins/twin a.md", "twins/twin b.md"})

    def test_blob_text_is_read_whole(self):
        body = "# big\n\n" + "\n".join(f"line {number}" for number in range(500)) + "\n\n\n"
        self.git("checkout", "-qb", "bulky")
        self.write("bulky.md", body)
        self.git("add", "bulky.md")
        self.git("commit", "-qm", "a note with trailing newlines")
        self.set_remote_ref("bulky", "HEAD")
        self.git("checkout", "-q", "main")

        blobs = index_branches.tree_blobs(self.root, "origin/bulky")
        contents = index_branches.read_blobs(self.root, [blobs["bulky.md"]])
        self.assertEqual(contents[blobs["bulky.md"]], body)

    def test_self_check_passes(self):
        self.assertEqual(index_branches.self_check(), 0)


if __name__ == "__main__":
    unittest.main()
