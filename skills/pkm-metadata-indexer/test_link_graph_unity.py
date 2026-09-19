"""Tests for Unity GUID integration in link_graph.py

Tests verify that link_graph.py correctly integrates Unity GUID checking
while maintaining backward compatibility when no .meta files exist.

Run with:
    python skills/pkm-metadata-indexer/test_link_graph_unity.py
    ~/.venvs/pkm-indexer/bin/python skills/pkm-metadata-indexer/test_link_graph_unity.py
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

# Import from same directory
import sys
sys.path.insert(0, str(Path(__file__).parent))

from link_graph import orphan_assets
from unity_guid_parser import UnityGuidParser


class TestLinkGraphUnityIntegration(unittest.TestCase):
    """Test link_graph orphan detection with Unity GUID support."""

    def _create_test_db(self, images, edges=None):
        """Create an in-memory test database."""
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE notes (path TEXT PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE edges (source_path TEXT, raw_target TEXT, "
            "resolved_target_path TEXT, start_line INTEGER)"
        )

        # Add images as notes
        for img in images:
            conn.execute("INSERT INTO notes VALUES (?)", (img,))

        # Add edges if provided
        if edges:
            conn.executemany("INSERT INTO edges VALUES (?, ?, ?, ?)", edges)

        return conn

    def test_orphan_without_unity_root(self):
        """Test that orphan detection works without Unity root (backward compat)."""
        conn = self._create_test_db(
            images=["docs/img/used.png", "docs/img/orphan.png"],
            edges=[("docs/readme.md", "img/used.png", "docs/img/used.png", 5)]
        )

        orphans, total = orphan_assets(conn, [".png"], unity_root=None)

        self.assertEqual(total, 2)
        self.assertEqual(len(orphans), 1)
        self.assertIn("docs/img/orphan.png", orphans)
        self.assertNotIn("docs/img/used.png", orphans)

    def test_orphan_with_unity_guid_references(self):
        """Test that GUID-referenced images are not considered orphaned."""
        # Create Unity project fixture
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        assets = root / "Assets"
        assets.mkdir()

        # Create an image with .meta file and GUID reference
        img_path = assets / "sprite.png"
        img_path.touch()
        (assets / "sprite.png.meta").write_text("guid: aaaaaaaa000000000000000000000000\n")

        # Create prefab that references the sprite
        prefab = assets / "Player.prefab"
        prefab.write_text("sprite: {guid: aaaaaaaa000000000000000000000000}")

        # Create database with the image but no markdown edges
        conn = self._create_test_db(images=["Assets/sprite.png"])

        # Without Unity root: should be orphaned (no markdown refs)
        orphans_no_unity, total = orphan_assets(conn, [".png"], unity_root=None)
        self.assertEqual(len(orphans_no_unity), 1)
        self.assertIn("Assets/sprite.png", orphans_no_unity)

        # With Unity root: should NOT be orphaned (has GUID ref)
        orphans_with_unity, total = orphan_assets(conn, [".png"], unity_root=str(root))
        self.assertEqual(len(orphans_with_unity), 0, "GUID-referenced image should not be orphaned")

        temp_dir.cleanup()

    def test_truly_orphaned_unity_asset(self):
        """Test that Unity assets with no references are still detected as orphans."""
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        assets = root / "Assets"
        assets.mkdir()

        # Create an orphaned image with .meta but no references
        orphan_path = assets / "orphan.png"
        orphan_path.touch()
        (assets / "orphan.png.meta").write_text("guid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n")

        # Create database
        conn = self._create_test_db(images=["Assets/orphan.png"])

        # Should be orphaned even with Unity root
        orphans, total = orphan_assets(conn, [".png"], unity_root=str(root))
        self.assertEqual(len(orphans), 1)
        self.assertIn("Assets/orphan.png", orphans)

        temp_dir.cleanup()

    def test_fallback_when_no_meta_files(self):
        """Test graceful fallback when Unity root has no .meta files."""
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)

        # Create directory but no Unity project structure
        (root / "images").mkdir()

        # Create database
        conn = self._create_test_db(images=["images/test.png"])

        # Should fall back to path-based checking (everything orphaned)
        orphans, total = orphan_assets(conn, [".png"], unity_root=str(root))
        self.assertEqual(len(orphans), 1)
        self.assertIn("images/test.png", orphans)

        temp_dir.cleanup()

    def test_mixed_references(self):
        """Test assets with both markdown and GUID references."""
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        assets = root / "Assets"
        assets.mkdir()

        # Image with both markdown ref and GUID ref
        img1 = assets / "both.png"
        img1.touch()
        (assets / "both.png.meta").write_text("guid: cccccccccccccccccccccccccccccccc\n")
        prefab = assets / "Test.prefab"
        prefab.write_text("sprite: {guid: cccccccccccccccccccccccccccccccc}")

        # Image with only markdown ref
        img2 = assets / "markdown_only.png"
        img2.touch()
        (assets / "markdown_only.png.meta").write_text("guid: dddddddddddddddddddddddddddddddd\n")

        # Image with only GUID ref
        img3 = assets / "guid_only.png"
        img3.touch()
        (assets / "guid_only.png.meta").write_text("guid: eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee\n")
        (assets / "Another.prefab").write_text("sprite: {guid: eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee}")

        # Create database with markdown edge for img1 and img2
        conn = self._create_test_db(
            images=["Assets/both.png", "Assets/markdown_only.png", "Assets/guid_only.png"],
            edges=[
                ("docs/readme.md", "both.png", "Assets/both.png", 5),
                ("docs/readme.md", "markdown_only.png", "Assets/markdown_only.png", 10),
            ]
        )

        # All three should be non-orphaned
        orphans, total = orphan_assets(conn, [".png"], unity_root=str(root))
        self.assertEqual(total, 3)
        self.assertEqual(len(orphans), 0, "All images have at least one reference")

        temp_dir.cleanup()

    def test_nonexistent_unity_root(self):
        """Test that nonexistent Unity root falls back gracefully."""
        conn = self._create_test_db(images=["Assets/test.png"])

        # Should not crash, just fall back to path-based checking
        orphans, total = orphan_assets(conn, [".png"], unity_root="/nonexistent/path")
        self.assertEqual(len(orphans), 1)
        self.assertIn("Assets/test.png", orphans)


def run_tests():
    """Run all tests and return exit code."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
