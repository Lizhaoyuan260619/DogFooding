import os
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging

from .scanner import FileScanner, ScanResult
from .recommender import SmartRecommender, RecommendationResult
from .incremental import IncrementalAnalyzer, IncrementalDiff
from .exporter import RuleExporter, ExportOptions
from .database import Database

logger = logging.getLogger(__name__)


@dataclass
class SmartAnalyzeResult:
    scan_result: ScanResult
    recommendation_result: RecommendationResult
    incremental_diff: Optional[IncrementalDiff] = None
    is_incremental: bool = False


class SmartRecommenderEngine:
    def __init__(self, db: Database = None, db_path: str = None):
        if db:
            self.db = db
        else:
            self.db = Database(db_path)
        self.scanner = FileScanner()
        self.incremental = IncrementalAnalyzer()
        self._last_result: Optional[SmartAnalyzeResult] = None

    def analyze(
        self,
        target_dir: str,
        use_incremental: bool = True,
        on_progress: Callable[[str], None] = None,
    ) -> SmartAnalyzeResult:
        target_dir = os.path.abspath(target_dir)
        if not os.path.isdir(target_dir):
            raise ValueError(f"Not a directory: {target_dir}")

        if on_progress:
            on_progress("正在扫描目录结构...")

        old_snapshot = None
        if use_incremental and self.incremental.has_snapshot(target_dir):
            old_snapshot = self.incremental.load_snapshot(target_dir)

        scan_result = self.scanner.scan(target_dir)

        diff = None
        is_incremental = False
        if old_snapshot:
            diff = self.incremental.diff(old_snapshot, scan_result)
            is_incremental = diff.has_changes()

        if on_progress:
            on_progress(f"扫描完成，共 {scan_result.stats.total_files} 个文件")
            on_progress("正在生成智能推荐...")

        recommender = SmartRecommender(scan_result)
        rec_result = recommender.generate_all()

        if on_progress:
            on_progress(f"生成 {len(rec_result.recommendations)} 条推荐建议")
            on_progress("保存分析快照...")

        self.incremental.save_snapshot(scan_result)

        result = SmartAnalyzeResult(
            scan_result=scan_result,
            recommendation_result=rec_result,
            incremental_diff=diff,
            is_incremental=is_incremental,
        )
        self._last_result = result
        return result

    def analyze_incremental(
        self,
        target_dir: str,
        on_progress: Callable[[str], None] = None,
    ) -> Dict[str, Any]:
        target_dir = os.path.abspath(target_dir)
        if not self.incremental.has_snapshot(target_dir):
            result = self.analyze(target_dir, use_incremental=True, on_progress=on_progress)
            return {
                "is_first_scan": True,
                "result": result,
                "update_info": None,
            }

        result = self.analyze(target_dir, use_incremental=True, on_progress=on_progress)
        update_info = self.incremental.update_recommendations(
            result.incremental_diff,
            result.scan_result,
        )

        return {
            "is_first_scan": False,
            "result": result,
            "update_info": update_info,
        }

    def get_last_result(self) -> Optional[SmartAnalyzeResult]:
        return self._last_result

    def export(
        self,
        result: RecommendationResult,
        output_path: str,
        options: ExportOptions = None,
    ) -> str:
        exporter = RuleExporter(result)
        return exporter.export(output_path, options)

    def apply_generated_rules(self, result: RecommendationResult) -> List[int]:
        rule_ids = []
        for rule_data in result.generated_rules:
            rule_id = self.db.save_rule_complete(rule_data)
            rule_ids.append(rule_id)
        return rule_ids

    def get_structure_comparison(
        self, result: SmartAnalyzeResult
    ) -> Dict[str, Any]:
        scan = result.scan_result
        rec = result.recommendation_result
        struct = rec.recommended_structure

        current_tree = self._build_tree_display(scan.tree)
        recommended_dirs = struct.directories if struct else []
        file_mappings = []
        if struct:
            for m in struct.file_mappings:
                file_mappings.append({
                    "source": m.source,
                    "target": m.target,
                    "action": m.action,
                    "source_display": os.path.relpath(m.source, scan.root_path),
                    "target_display": os.path.relpath(m.target, scan.root_path),
                })

        return {
            "root_path": scan.root_path,
            "current_tree": current_tree,
            "recommended_directories": recommended_dirs,
            "file_mappings": file_mappings,
            "summary": struct.summary if struct else {},
            "stats": {
                "total_files": scan.stats.total_files,
                "total_dirs": scan.stats.total_dirs,
                "total_size": scan.stats.total_size,
            },
        }

    def _build_tree_display(self, node, max_depth: int = 4) -> Dict[str, Any]:
        if not node:
            return {}
        if node.depth > max_depth:
            return {
                "name": node.name,
                "is_dir": node.is_dir,
                "truncated": True,
            }

        children = []
        for child in node.children[:50]:
            children.append(self._build_tree_display(child, max_depth))

        return {
            "name": node.name,
            "path": node.path,
            "is_dir": node.is_dir,
            "size": node.size,
            "depth": node.depth,
            "category": node.category,
            "children": children,
            "truncated_children": max(0, len(node.children) - 50),
        }
