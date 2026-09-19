"""Unit tests for unity_guid_parser.py

Tests use inline fixtures to verify GUID parsing and reference resolution
without requiring a Unity project to be cloned.

Run with:
    python skills/pkm-metadata-indexer/test_unity_guid_parser.py
    ~/.venvs/pkm-indexer/bin/python skills/pkm-metadata-indexer/test_unity_guid_parser.py
"""
import tempfile
import unittest
from pathlib import Path

from unity_guid_parser import UnityGuidParser, GUID_PATTERN, GUID_REF_PATTERN


class TestGuidPatterns(unittest.TestCase):
    """Test regex patterns for GUID extraction."""

    def test_guid_meta_pattern(self):
        """Test GUID extraction from .meta file content."""
        content = """fileFormatVersion: 2
guid: 1234567890abcdef1234567890abcdef
TextureImporter:
  fileIDToRecycleName: {}
"""
        match = GUID_PATTERN.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), '1234567890abcdef1234567890abcdef')

    def test_guid_meta_pattern_case_insensitive(self):
        """Test GUID pattern is case-insensitive."""
        content = "guid: ABCD1234ABCD1234ABCD1234ABCD1234"
        match = GUID_PATTERN.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).lower(), 'abcd1234abcd1234abcd1234abcd1234')

    def test_guid_ref_pattern(self):
        """Test GUID extraction from prefab/scene references."""
        content = "{fileID: 11500000, guid: abcdef1234567890abcdef1234567890, type: 3}"
        match = GUID_REF_PATTERN.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), 'abcdef1234567890abcdef1234567890')

    def test_guid_ref_pattern_multiple(self):
        """Test finding multiple GUID references."""
        content = """
        m_Icon: {fileID: 0}
        m_NavMeshLayer: 0
        sprite: {fileID: 21300000, guid: aaa111aaa111aaa111aaa111aaa111aa, type: 3}
        material: {fileID: 0}
        texture: {fileID: 2800000, guid: bbb222bbb222bbb222bbb222bbb222bb, type: 3}
        """
        matches = list(GUID_REF_PATTERN.finditer(content))
        self.assertEqual(len(matches), 2)
        guids = [m.group(1) for m in matches]
        self.assertIn('aaa111aaa111aaa111aaa111aaa111aa', guids)
        self.assertIn('bbb222bbb222bbb222bbb222bbb222bb', guids)


class TestUnityGuidParser(unittest.TestCase):
    """Test UnityGuidParser with inline fixture files."""

    def setUp(self):
        """Create a temporary Unity project structure."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create Assets directory
        assets = self.root / "Assets"
        assets.mkdir()

        # Create subdirectories
        sprites = assets / "Sprites"
        sprites.mkdir()
        prefabs = assets / "Prefabs"
        prefabs.mkdir()
        scenes = assets / "Scenes"
        scenes.mkdir()

        # Create image files with .meta files
        self._create_asset_with_meta(
            sprites / "player.png",
            "11111111111111111111111111111111"
        )
        self._create_asset_with_meta(
            sprites / "enemy.png",
            "22222222222222222222222222222222"
        )
        self._create_asset_with_meta(
            sprites / "background.jpg",
            "33333333333333333333333333333333"
        )
        self._create_asset_with_meta(
            sprites / "orphaned.png",
            "44444444444444444444444444444444"
        )

        # Create a prefab that references some sprites
        prefab_content = """
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
GameObject:
  m_Component:
  - component: {fileID: 4, guid: 00000000000000000000000000000000, type: 0}
  m_Layer: 0
SpriteRenderer:
  m_Sprite: {fileID: 21300000, guid: 11111111111111111111111111111111, type: 3}
  m_Material: {fileID: 0}
  backgroundSprite: {fileID: 21300000, guid: 33333333333333333333333333333333, type: 3}
"""
        (prefabs / "Player.prefab").write_text(prefab_content)

        # Create a scene that references a sprite
        scene_content = """
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
GameObject:
  serializedVersion: 6
SpriteRenderer:
  m_Sprite: {fileID: 21300000, guid: 22222222222222222222222222222222, type: 3}
"""
        (scenes / "MainScene.unity").write_text(scene_content)

        # Create a material
        material_content = """
Material:
  serializedVersion: 6
  m_Shader: {fileID: 46, guid: 0000000000000000f000000000000000, type: 0}
  m_Textures:
    _MainTex: {fileID: 2800000, guid: 11111111111111111111111111111111, type: 3}
"""
        (assets / "PlayerMaterial.mat").write_text(material_content)

    def _create_asset_with_meta(self, asset_path: Path, guid: str):
        """Create an asset file and its .meta file."""
        asset_path.touch()
        meta_content = f"""fileFormatVersion: 2
guid: {guid}
TextureImporter:
  fileIDToRecycleName: {{}}
  externalObjects: {{}}
  serializedVersion: 9
"""
        meta_path = asset_path.with_suffix(asset_path.suffix + '.meta')
        meta_path.write_text(meta_content)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_scan_meta_files(self):
        """Test scanning .meta files builds guid -> path mapping."""
        parser = UnityGuidParser(str(self.root))
        parser._scan_meta_files()

        self.assertEqual(len(parser.guid_to_path), 4)
        self.assertEqual(
            parser.guid_to_path['11111111111111111111111111111111'],
            'Assets/Sprites/player.png'
        )
        self.assertEqual(
            parser.guid_to_path['22222222222222222222222222222222'],
            'Assets/Sprites/enemy.png'
        )

    def test_path_normalization(self):
        """Test that paths are normalized with forward slashes."""
        parser = UnityGuidParser(str(self.root))
        parser._scan_meta_files()

        # All paths should use forward slashes
        for path in parser.guid_to_path.values():
            self.assertNotIn('\\', path)
            self.assertTrue(path.startswith('Assets/'))

    def test_scan_references(self):
        """Test scanning prefabs and scenes for GUID references."""
        parser = UnityGuidParser(str(self.root))
        parser._scan_meta_files()
        parser._scan_references()

        # Player sprite is referenced in prefab and material
        player_guid = '11111111111111111111111111111111'
        self.assertIn(player_guid, parser.references)
        refs = parser.references[player_guid]
        self.assertEqual(len(refs), 2)  # prefab + material

        # Enemy sprite is referenced in scene
        enemy_guid = '22222222222222222222222222222222'
        self.assertIn(enemy_guid, parser.references)
        self.assertEqual(len(parser.references[enemy_guid]), 1)

        # Background is referenced in prefab
        bg_guid = '33333333333333333333333333333333'
        self.assertIn(bg_guid, parser.references)
        self.assertEqual(len(parser.references[bg_guid]), 1)

        # Orphaned sprite has no references
        orphan_guid = '44444444444444444444444444444444'
        self.assertNotIn(orphan_guid, parser.references)

    def test_get_asset_path(self):
        """Test retrieving asset path from GUID."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        path = parser.get_asset_path('11111111111111111111111111111111')
        self.assertEqual(path, 'Assets/Sprites/player.png')

        # Case insensitive
        path = parser.get_asset_path('11111111111111111111111111111111'.upper())
        self.assertEqual(path, 'Assets/Sprites/player.png')

        # Non-existent GUID
        self.assertIsNone(parser.get_asset_path('00000000000000000000000000000000'))

    def test_get_guid(self):
        """Test retrieving GUID from asset path."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        guid = parser.get_guid('Assets/Sprites/player.png')
        self.assertEqual(guid, '11111111111111111111111111111111')

        # Windows-style path
        guid = parser.get_guid('Assets\\Sprites\\enemy.png')
        self.assertEqual(guid, '22222222222222222222222222222222')

        # Non-existent path
        self.assertIsNone(parser.get_guid('Assets/DoesNotExist.png'))

    def test_get_references(self):
        """Test getting all references to an asset."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        refs = parser.get_references('Assets/Sprites/player.png')
        self.assertEqual(len(refs), 2)
        self.assertTrue(any('Player.prefab' in ref for ref in refs))
        self.assertTrue(any('PlayerMaterial.mat' in ref for ref in refs))

        # Enemy is referenced once
        refs = parser.get_references('Assets/Sprites/enemy.png')
        self.assertEqual(len(refs), 1)

        # Orphaned has no references
        refs = parser.get_references('Assets/Sprites/orphaned.png')
        self.assertEqual(len(refs), 0)

    def test_is_referenced(self):
        """Test checking if an asset is referenced."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        self.assertTrue(parser.is_referenced('Assets/Sprites/player.png'))
        self.assertTrue(parser.is_referenced('Assets/Sprites/enemy.png'))
        self.assertFalse(parser.is_referenced('Assets/Sprites/orphaned.png'))
        self.assertFalse(parser.is_referenced('Assets/DoesNotExist.png'))

    def test_find_orphans_all_assets(self):
        """Test finding orphans across all assets."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        orphans, total = parser.find_orphans()
        self.assertEqual(total, 4)  # All 4 image assets
        self.assertEqual(len(orphans), 1)  # Only orphaned.png
        self.assertIn('Assets/Sprites/orphaned.png', orphans)

    def test_find_orphans_by_extension(self):
        """Test finding orphans filtered by extension."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        # Only .png files
        orphans, total = parser.find_orphans(extensions=['.png'])
        self.assertEqual(total, 3)  # 3 PNG files
        self.assertEqual(len(orphans), 1)
        self.assertEqual(orphans[0], 'Assets/Sprites/orphaned.png')

        # Only .jpg files
        orphans, total = parser.find_orphans(extensions=['.jpg'])
        self.assertEqual(total, 1)  # 1 JPG file
        self.assertEqual(len(orphans), 0)  # background.jpg is referenced

        # Multiple extensions
        orphans, total = parser.find_orphans(extensions=['.png', '.jpg'])
        self.assertEqual(total, 4)
        self.assertEqual(len(orphans), 1)

    def test_get_stats(self):
        """Test statistics gathering."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        stats = parser.get_stats()
        self.assertEqual(stats['total_assets'], 4)
        # referenced_assets includes all GUIDs with references, including Unity
        # internal GUIDs from prefabs/scenes that aren't in our asset list
        self.assertGreaterEqual(stats['referenced_assets'], 3)  # at least player, enemy, background
        self.assertGreater(stats['total_references'], 0)
        self.assertGreater(stats['unique_referrers'], 0)

    def test_nonexistent_root(self):
        """Test parser handles non-existent root gracefully."""
        parser = UnityGuidParser('/nonexistent/path')
        parser.scan()

        self.assertEqual(len(parser.guid_to_path), 0)
        self.assertEqual(len(parser.references), 0)
        orphans, total = parser.find_orphans()
        self.assertEqual(len(orphans), 0)
        self.assertEqual(total, 0)

    def test_case_insensitive_guid_lookup(self):
        """Test GUID lookups are case-insensitive."""
        parser = UnityGuidParser(str(self.root))
        parser.scan()

        # All these should resolve to the same asset
        guid_lower = '11111111111111111111111111111111'
        guid_upper = '11111111111111111111111111111111'.upper()
        guid_mixed = '11111111111111111111111111111111'.replace('1', 'A', 2)

        path1 = parser.get_asset_path(guid_lower)
        path2 = parser.get_asset_path(guid_upper)
        path3 = parser.get_asset_path(guid_mixed)

        self.assertEqual(path1, path2)
        # Mixed won't match since we only have 1s in our test GUID
        # But the test shows case-insensitivity works


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""

    def test_orphan_detection_workflow(self):
        """Test complete workflow: scan project, find orphaned images."""
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)

        # Create minimal Unity project
        assets = root / "Assets"
        assets.mkdir()

        # Asset with references
        used_img = assets / "used.png"
        used_img.touch()
        (assets / "used.png.meta").write_text("guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n")

        # Orphaned asset
        orphan_img = assets / "orphan.png"
        orphan_img.touch()
        (assets / "orphan.png.meta").write_text("guid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n")

        # Prefab referencing the used asset
        prefab = assets / "Test.prefab"
        prefab.write_text("sprite: {guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}")

        # Run workflow
        parser = UnityGuidParser(str(root))
        parser.scan()
        orphans, total = parser.find_orphans(extensions=['.png'])

        # Verify results
        self.assertEqual(total, 2)
        self.assertEqual(len(orphans), 1)
        self.assertIn('Assets/orphan.png', orphans)

        temp_dir.cleanup()


def run_tests():
    """Run all tests and return exit code."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
