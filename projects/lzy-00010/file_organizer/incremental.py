import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

from .scanner import ScanResult, FileScanner

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    path: str
    change_type: str
    old_sig: str = ""
    new_sig: str = ""
    old_size: int = 0
    new_size: int = 0


@dataclass
class IncrementalDiff:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    changes: List[FileChange] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return len(self.added) > 0 or len(self.removed) > 0 or len(self.modified) > 0


@dataclass
class ScanSnapshot:
    root_path: str
    scan_time: str
    file_signatures: Dict[str, str]
    file_metadata: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_path": self.root_path,
            "scan_time": self.scan_time,
            "file_signatures": self.file_signatures,
            "file_metadata": self.file_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanSnapshot":
        return cls(
            root_path=data["root_path"],
            scan_time=data["scan_time"],
            file_signatures=data.get("file_signatures", {}),
            file_metadata=data.get("file_metadata", {}),
        )

    @classmethod
    def from_scan_result(cls, result: ScanResult) -> "ScanSnapshot":
        metadata = {}
        for f in result.all_files:
            metadata[f.path] = {
                "size": f.size,
                "category": f.category,
                "extension": f.extension,
                "depth": f.depth,
                "naming_pattern": f.naming_pattern,
                "modified_time": f.modified_time.isoformat(),
            }
        return cls(
            root_path=result.root_path,
            scan_time=result.scan_time.isoformat(),
            file_signatures=dict(result.file_signatures),
            file_metadata=metadata,
        )


class IncrementalAnalyzer:
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".file_organizer", "snapshots")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _snapshot_path(self, root_path: str) -> str:
        path_hash = hashlib.md5(os.path.abspath(root_path).encode()).hexdigest()
        return os.path.join(self.cache_dir, f"snapshot_{path_hash}.json")

    def save_snapshot(self, result: ScanResult) -> str:
        snapshot = ScanSnapshot.from_scan_result(result)
        path = self._snapshot_path(result.root_path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)
        return path

    def load_snapshot(self, root_path: str) -> Optional[ScanSnapshot]:
        path = self._snapshot_path(root_path)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ScanSnapshot.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load snapshot for {root_path}: {e}")
            return None

    def has_snapshot(self, root_path: str) -> bool:
        return os.path.exists(self._snapshot_path(root_path))

    def diff(self, old_snapshot: ScanSnapshot, new_result: ScanResult) -> IncrementalDiff:
        old_sigs = old_snapshot.file_signatures
        new_sigs = new_result.file_signatures
        old_meta = old_snapshot.file_metadata

        diff = IncrementalDiff()

        old_paths = set(old_sigs.keys())
        new_paths = set(new_sigs.keys())

        added_paths = new_paths - old_paths
        removed_paths = old_paths - new_paths
        common_paths = old_paths & new_paths

        diff.added = sorted(added_paths)
        diff.removed = sorted(removed_paths)

        for p in added_paths:
            meta = None
            for f in new_result.all_files:
                if f.path == p:
                    meta = {"size": f.size, "category": f.category}
                    break
            diff.changes.append(FileChange(
                path=p,
                change_type="added",
                new_sig=new_sigs[p],
                new_size=meta["size"] if meta else 0,
            ))

        for p in removed_paths:
            old_meta = old_meta.get(p, {})
            diff.changes.append(FileChange(
                path=p,
                change_type="removed",
                old_sig=old_sigs.get(p, ""),
                old_size=old_meta.get("size", 0),
            ))

        for p in common_paths:
            if old_sigs[p] != new_sigs[p]:
                diff.modified.append(p)
                old_meta_entry = old_meta.get(p, {})
                new_meta_entry = None
                for f in new_result.all_files:
                    if f.path == p:
                        new_meta_entry = {"size": f.size, "category": f.category}
                        break
                diff.changes.append(FileChange(
                    path=p,
                    change_type="modified",
                    old_sig=old_sigs[p],
                    new_sig=new_sigs[p],
                    old_size=old_meta_entry.get("size", 0),
                    new_size=new_meta_entry["size"] if new_meta_entry else 0,
                ))
            else:
                diff.unchanged.append(p)

        diff.summary = {
            "added": len(diff.added),
            "removed": len(diff.removed),
            "modified": len(diff.modified),
            "unchanged": len(diff.unchanged),
            "total_changes": len(diff.added) + len(diff.removed) + len(diff.modified),
        }

        return diff

    def update_recommendations(
        self,
        old_diff: IncrementalDiff,
        new_result: ScanResult,
        previous_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        changes = []
        for change in old_diff.changes:
            changes.append({
                "path": change.path,
                "type": change.change_type,
                "size_delta": change.new_size - change.old_size,
            })

        affected_categories = set()
        for f in new_result.all_files:
            if f.path in old_diff.added or f.path in old_diff.modified:
                affected_categories.add(f.category)

        return {
            "needs_full_rescan": len(old_diff.removed) > 0 or len(old_diff.added) > 10,
            "changes": changes,
            "change_count": old_diff.summary,
            "affected_categories": sorted(affected_categories),
            "incremental_hints": self._generate_incremental_hints(old_diff, new_result),
        }

    def _generate_incremental_hints(
        self, diff: IncrementalDiff, new_result: ScanResult
    ) -> List[Dict[str, Any]]:
        hints = []

        if diff.added:
            added_cats = {}
            for f in new_result.all_files:
                if f.path in diff.added:
                    added_cats[f.category] = added_cats.get(f.category, 0) + 1

            for cat, count in added_cats.items():
                if count >= 3:
                    hints.append({
                        "type": "bulk_add",
                        "category": cat,
                        "count": count,
                        "suggestion": f"新增了 {count} 个{cat}类文件，建议检查是否需要更新归类规则",
                    })

        if diff.modified:
            large_mods = [c for c in diff.changes
                          if c.change_type == "modified" and abs(c.new_size - c.old_size) > 1024 * 1024]
            if large_mods:
                hints.append({
                    "type": "large_modifications",
                    "count": len(large_mods),
                    "suggestion": f"{len(large_mods)} 个文件发生较大变更，建议评估是否影响模块边界",
                })

        if diff.removed:
            hints.append({
                "type": "files_removed",
                "count": len(diff.removed),
                "suggestion": f"{len(diff.removed)} 个文件被移除，建议检查相关引用和模块完整性",
            })

        return hints
