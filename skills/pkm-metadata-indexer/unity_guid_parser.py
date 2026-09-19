"""Unity GUID parser for asset reference resolution.

Maps Unity asset GUIDs to file paths and resolves references in prefabs, scenes,
and materials, so an image is only considered orphaned when no GUID reference exists.

Unity stores a GUID in each `.meta` file:
    guid: 1234567890abcdef1234567890abcdef

Prefabs, scenes, and materials reference assets by GUID:
    {fileID: 11500000, guid: 1234567890abcdef1234567890abcdef, type: 3}

This parser builds a guid -> asset_path mapping and finds all GUID references,
enabling orphan detection for Unity projects where prose-based link detection
only reaches a tiny fraction of actual references.

Usage:
    from scripts.unity_guid_parser import UnityGuidParser

    parser = UnityGuidParser('/path/to/unity/project')
    parser.scan()

    # Get asset path from GUID
    asset_path = parser.guid_to_path('1234567890abcdef1234567890abcdef')

    # Get all references to an asset
    refs = parser.get_references('Assets/Sprites/player.png')

    # Find orphaned assets (no GUID references)
    orphans = parser.find_orphans(extensions=['.png', '.jpg'])
"""
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


GUID_PATTERN = re.compile(r'^guid:\s*([0-9a-f]{32})\s*$', re.MULTILINE | re.IGNORECASE)
GUID_REF_PATTERN = re.compile(r'\bguid:\s*([0-9a-f]{32})\b', re.IGNORECASE)


class UnityGuidParser:
    """Parse Unity .meta files and asset references by GUID."""

    def __init__(self, root_path: str):
        """Initialize parser for a Unity project.

        Args:
            root_path: Path to Unity project root (contains Assets/ folder)
        """
        self.root = Path(root_path)
        self.guid_to_path: Dict[str, str] = {}
        self.path_to_guid: Dict[str, str] = {}
        self.references: Dict[str, Set[str]] = {}  # guid -> set of referrer paths

    def scan(self) -> None:
        """Scan the project to build GUID mappings and find all references."""
        self._scan_meta_files()
        self._scan_references()

    def _scan_meta_files(self) -> None:
        """Build guid -> path mapping from all .meta files."""
        if not self.root.exists():
            return

        for meta_file in self.root.rglob('*.meta'):
            if '.claude' in meta_file.parts:
                continue
            try:
                content = meta_file.read_text(encoding='utf-8', errors='ignore')
                match = GUID_PATTERN.search(content)
                if match:
                    guid = match.group(1).lower()
                    # The .meta file corresponds to the file without .meta extension
                    asset_path = str(meta_file.with_suffix('').relative_to(self.root))
                    asset_path = asset_path.replace('\\', '/')
                    self.guid_to_path[guid] = asset_path
                    self.path_to_guid[asset_path] = guid
            except (OSError, UnicodeDecodeError):
                # Skip files we can't read
                continue

    def _scan_references(self) -> None:
        """Find all GUID references in prefabs, scenes, materials, etc."""
        if not self.root.exists():
            return

        # Unity file types that contain GUID references
        extensions = {'.prefab', '.unity', '.mat', '.asset', '.controller', '.anim'}

        for file_path in self.root.rglob('*'):
            if file_path.suffix.lower() not in extensions:
                continue
            if '.claude' in file_path.parts:
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                referrer_path = str(file_path.relative_to(self.root)).replace('\\', '/')

                for match in GUID_REF_PATTERN.finditer(content):
                    guid = match.group(1).lower()
                    if guid not in self.references:
                        self.references[guid] = set()
                    self.references[guid].add(referrer_path)
            except (OSError, UnicodeDecodeError):
                continue

    def get_asset_path(self, guid: str) -> Optional[str]:
        """Get the asset path for a GUID.

        Args:
            guid: Unity GUID (32 hex chars, case-insensitive)

        Returns:
            Asset path relative to project root, or None if not found
        """
        return self.guid_to_path.get(guid.lower())

    def get_guid(self, asset_path: str) -> Optional[str]:
        """Get the GUID for an asset path.

        Args:
            asset_path: Asset path relative to project root

        Returns:
            GUID string, or None if not found
        """
        normalized = asset_path.replace('\\', '/')
        return self.path_to_guid.get(normalized)

    def get_references(self, asset_path: str) -> List[str]:
        """Get all files that reference an asset.

        Args:
            asset_path: Asset path relative to project root

        Returns:
            List of referrer paths that reference this asset
        """
        guid = self.get_guid(asset_path)
        if not guid:
            return []
        return sorted(self.references.get(guid, set()))

    def is_referenced(self, asset_path: str) -> bool:
        """Check if an asset has any GUID references.

        Args:
            asset_path: Asset path relative to project root

        Returns:
            True if the asset is referenced by at least one file
        """
        guid = self.get_guid(asset_path)
        if not guid:
            return False
        return guid in self.references and len(self.references[guid]) > 0

    def find_orphans(self, extensions: Optional[List[str]] = None) -> Tuple[List[str], int]:
        """Find assets with no GUID references.

        Args:
            extensions: List of file extensions to check (e.g., ['.png', '.jpg'])
                       If None, checks all indexed assets

        Returns:
            Tuple of (orphaned_paths, total_matching_assets)
        """
        matching_assets = []

        for asset_path in self.path_to_guid.keys():
            if extensions:
                path_obj = Path(asset_path)
                if path_obj.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue
            matching_assets.append(asset_path)

        orphans = [
            path for path in matching_assets
            if not self.is_referenced(path)
        ]

        return sorted(orphans), len(matching_assets)

    def get_stats(self) -> Dict[str, int]:
        """Get parser statistics.

        Returns:
            Dictionary with counts of assets, GUIDs, and references
        """
        return {
            'total_assets': len(self.guid_to_path),
            'total_references': sum(len(refs) for refs in self.references.values()),
            'referenced_assets': len(self.references),
            'unique_referrers': len(set(
                ref for refs in self.references.values() for ref in refs
            ))
        }
