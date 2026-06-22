import os
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tiff", "tif"}
DOCUMENT_EXTS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "odt", "ods", "odp", "md"}
AUDIO_EXTS = {"mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "aiff"}
VIDEO_EXTS = {"mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"}
ARCHIVE_EXTS = {"zip", "rar", "7z", "tar", "gz", "bz2", "xz"}
CODE_EXTS = {
    "py", "js", "ts", "java", "c", "cpp", "h", "hpp", "cs", "go", "rb", "php",
    "html", "css", "json", "xml", "yaml", "yml", "sql", "sh", "bat", "rs", "swift",
    "kt", "scala", "r", "lua", "pl", "pm", "dart", "vue", "jsx", "tsx"
}
CONFIG_EXTS = {"json", "yaml", "yml", "xml", "ini", "cfg", "conf", "toml", "env"}
TEST_INDICATORS = {"test", "tests", "spec", "specs", "__tests__", "unittest"}


@dataclass
class FileNode:
    path: str
    name: str
    extension: str
    size: int
    created_time: datetime
    modified_time: datetime
    is_dir: bool
    parent: str = ""
    depth: int = 0
    category: str = "other"
    children: List["FileNode"] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    naming_pattern: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["created_time"] = self.created_time.isoformat()
        d["modified_time"] = self.modified_time.isoformat()
        d["children"] = [c.to_dict() for c in self.children]
        return d


@dataclass
class DirectoryStats:
    total_files: int = 0
    total_dirs: int = 0
    total_size: int = 0
    ext_distribution: Counter = field(default_factory=Counter)
    category_distribution: Counter = field(default_factory=Counter)
    size_distribution: Dict[str, int] = field(default_factory=dict)
    depth_distribution: Counter = field(default_factory=Counter)
    naming_patterns: Counter = field(default_factory=Counter)
    avg_files_per_dir: float = 0.0
    max_depth: int = 0


@dataclass
class ScanResult:
    root_path: str
    scan_time: datetime
    tree: Optional[FileNode] = None
    all_files: List[FileNode] = field(default_factory=list)
    stats: DirectoryStats = field(default_factory=DirectoryStats)
    naming_analysis: Dict[str, Any] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    module_clusters: List[List[str]] = field(default_factory=list)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    file_signatures: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_path": self.root_path,
            "scan_time": self.scan_time.isoformat(),
            "tree": self.tree.to_dict() if self.tree else None,
            "all_files_count": len(self.all_files),
            "stats": {
                "total_files": self.stats.total_files,
                "total_dirs": self.stats.total_dirs,
                "total_size": self.stats.total_size,
                "ext_distribution": dict(self.stats.ext_distribution),
                "category_distribution": dict(self.stats.category_distribution),
                "size_distribution": self.stats.size_distribution,
                "depth_distribution": dict(self.stats.depth_distribution),
                "naming_patterns": dict(self.stats.naming_patterns),
                "avg_files_per_dir": self.stats.avg_files_per_dir,
                "max_depth": self.stats.max_depth,
            },
            "naming_analysis": self.naming_analysis,
            "dependency_graph": self.dependency_graph,
            "module_clusters": self.module_clusters,
            "anomalies": self.anomalies,
            "file_signatures": self.file_signatures,
        }


class FileScanner:
    def __init__(self, ignore_hidden: bool = True, ignore_patterns: List[str] = None):
        self.ignore_hidden = ignore_hidden
        self.ignore_patterns = ignore_patterns or [
            r"\.git", r"node_modules", r"__pycache__", r"\.venv", r"venv",
            r"\.idea", r"\.vscode", r"dist", r"build", r"target", r"\.pyc$"
        ]
        self._compiled_patterns = [re.compile(p) for p in self.ignore_patterns]

    def _should_ignore(self, path: str, name: str) -> bool:
        if self.ignore_hidden and name.startswith("."):
            return True
        for pattern in self._compiled_patterns:
            if pattern.search(path) or pattern.search(name):
                return True
        return False

    def _categorize_file(self, ext: str) -> str:
        ext = ext.lower().lstrip(".")
        if ext in IMAGE_EXTS:
            return "image"
        elif ext in DOCUMENT_EXTS:
            return "document"
        elif ext in AUDIO_EXTS:
            return "audio"
        elif ext in VIDEO_EXTS:
            return "video"
        elif ext in ARCHIVE_EXTS:
            return "archive"
        elif ext in CODE_EXTS:
            return "code"
        elif ext in CONFIG_EXTS:
            return "config"
        return "other"

    def _get_size_bucket(self, size: int) -> str:
        if size < 1024:
            return "<1KB"
        elif size < 1024 * 1024:
            return "1KB-1MB"
        elif size < 10 * 1024 * 1024:
            return "1MB-10MB"
        elif size < 100 * 1024 * 1024:
            return "10MB-100MB"
        else:
            return ">100MB"

    def _analyze_naming_pattern(self, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        name_lower = name.lower()

        if re.match(r"^[a-z]+(_[a-z0-9]+)+$", name):
            return "snake_case"
        elif re.match(r"^[a-z]+(-[a-z0-9]+)+$", name):
            return "kebab-case"
        elif re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
            return "PascalCase"
        elif re.match(r"^[a-z][a-zA-Z0-9]*$", name):
            return "camelCase"
        elif re.match(r"^[A-Z_][A-Z0-9_]*$", name):
            return "UPPER_SNAKE_CASE"
        elif re.match(r"^\d{4}[-_]?\d{2}[-_]?\d{2}", name):
            return "date_prefix"
        elif re.match(r".*[._-]\d+$", name):
            return "numbered_suffix"
        elif re.match(r"^[a-zA-Z0-9]+$", name):
            return "flat"

        for indicator in TEST_INDICATORS:
            if indicator in name_lower:
                return "test_file"

        if name_lower.startswith(("readme", "license", "changelog", "todo", "contributing")):
            return "project_doc"
        if name_lower.startswith(("dockerfile", "makefile", ".env")):
            return "build_config"

        return "mixed"

    def _extract_dependencies(self, file_path: str, ext: str) -> List[str]:
        deps = []
        ext = ext.lower().lstrip(".")

        try:
            if ext in {"py"}:
                deps = self._extract_python_deps(file_path)
            elif ext in {"js", "ts", "jsx", "tsx", "vue"}:
                deps = self._extract_js_deps(file_path)
            elif ext in {"java", "kt"}:
                deps = self._extract_java_deps(file_path)
            elif ext in {"c", "cpp", "h", "hpp"}:
                deps = self._extract_c_deps(file_path)
            elif ext in {"go"}:
                deps = self._extract_go_deps(file_path)
        except Exception as e:
            logger.debug(f"Failed to extract deps from {file_path}: {e}")

        return deps

    def _extract_python_deps(self, file_path: str) -> List[str]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("import ") or line.startswith("from "):
                        match = re.match(r"(?:from\s+)?([\w\.]+)", line)
                        if match:
                            deps.append(match.group(1))
        except Exception:
            pass
        return list(set(deps))

    def _extract_js_deps(self, file_path: str) -> List[str]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for match in re.finditer(r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]", content):
                    deps.append(match.group(1))
        except Exception:
            pass
        return list(set(deps))

    def _extract_java_deps(self, file_path: str) -> List[str]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("import "):
                        match = re.match(r"import\s+([\w\.]+)", line)
                        if match:
                            deps.append(match.group(1))
        except Exception:
            pass
        return list(set(deps))

    def _extract_c_deps(self, file_path: str) -> List[str]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = re.match(r'#include\s+[<"]([^>"]+)[>"]', line.strip())
                    if match:
                        deps.append(match.group(1))
        except Exception:
            pass
        return list(set(deps))

    def _extract_go_deps(self, file_path: str) -> List[str]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for match in re.finditer(r'"([^"]+)"', content):
                    dep = match.group(1)
                    if "/" in dep and "." in dep.split("/")[0]:
                        deps.append(dep)
        except Exception:
            pass
        return list(set(deps))

    def _compute_signature(self, file_path: str) -> str:
        try:
            stat = os.stat(file_path)
            sig_str = f"{file_path}|{stat.st_size}|{stat.st_mtime}"
            return hashlib.md5(sig_str.encode()).hexdigest()
        except Exception:
            return ""

    def _build_tree(self, root_path: str, depth: int = 0, parent: str = "") -> Tuple[Optional[FileNode], List[FileNode]]:
        all_files = []
        try:
            entries = sorted(os.listdir(root_path))
        except PermissionError:
            return None, []

        root_name = os.path.basename(root_path) if parent else root_path
        root_stat = os.stat(root_path)

        root_node = FileNode(
            path=root_path,
            name=root_name,
            extension="",
            size=0,
            created_time=datetime.fromtimestamp(root_stat.st_ctime),
            modified_time=datetime.fromtimestamp(root_stat.st_mtime),
            is_dir=True,
            parent=parent,
            depth=depth,
            category="directory",
        )

        dir_children = []
        file_children = []

        for entry in entries:
            entry_path = os.path.join(root_path, entry)

            if self._should_ignore(entry_path, entry):
                continue

            try:
                if os.path.isdir(entry_path):
                    child_node, child_files = self._build_tree(
                        entry_path, depth + 1, root_path
                    )
                    if child_node:
                        dir_children.append(child_node)
                        all_files.extend(child_files)
                else:
                    stat = os.stat(entry_path)
                    name, ext = os.path.splitext(entry)
                    category = self._categorize_file(ext)
                    pattern = self._analyze_naming_pattern(entry)
                    deps = self._extract_dependencies(entry_path, ext) if category == "code" else []
                    sig = self._compute_signature(entry_path)

                    file_node = FileNode(
                        path=entry_path,
                        name=entry,
                        extension=ext.lower().lstrip("."),
                        size=stat.st_size,
                        created_time=datetime.fromtimestamp(stat.st_ctime),
                        modified_time=datetime.fromtimestamp(stat.st_mtime),
                        is_dir=False,
                        parent=root_path,
                        depth=depth + 1,
                        category=category,
                        naming_pattern=pattern,
                        dependencies=deps,
                    )
                    self.file_signatures[entry_path] = sig
                    file_children.append(file_node)
                    all_files.append(file_node)
            except (PermissionError, OSError) as e:
                logger.debug(f"Skip {entry_path}: {e}")

        root_node.children = dir_children + file_children
        return root_node, all_files

    def _compute_stats(self, tree: FileNode, all_files: List[FileNode]) -> DirectoryStats:
        stats = DirectoryStats()

        code_files = [f for f in all_files if f.category == "code"]
        stats.total_files = len(all_files)
        stats.total_size = sum(f.size for f in all_files)

        def count_dirs(node: FileNode) -> int:
            if not node.is_dir:
                return 0
            return 1 + sum(count_dirs(c) for c in node.children if c.is_dir)

        if tree:
            stats.total_dirs = count_dirs(tree) - 1

        for f in all_files:
            stats.ext_distribution[f.extension] += 1
            stats.category_distribution[f.category] += 1
            stats.size_distribution[self._get_size_bucket(f.size)] = \
                stats.size_distribution.get(self._get_size_bucket(f.size), 0) + 1
            stats.depth_distribution[f.depth] += 1
            if f.naming_pattern:
                stats.naming_patterns[f.naming_pattern] += 1
            if f.depth > stats.max_depth:
                stats.max_depth = f.depth

        stats.avg_files_per_dir = stats.total_files / max(stats.total_dirs, 1)

        return stats

    def _analyze_naming(self, all_files: List[FileNode]) -> Dict[str, Any]:
        result = {
            "overall_pattern": "mixed",
            "consistency_score": 0.0,
            "dominant_pattern": None,
            "pattern_details": {},
            "anomalies": [],
            "recommendations": [],
        }

        code_files = [f for f in all_files if f.category == "code" and f.extension]
        if not code_files:
            return result

        patterns = Counter(f.naming_pattern for f in code_files)
        total = len(code_files)

        result["pattern_details"] = dict(patterns)

        dominant = patterns.most_common(1)
        if dominant:
            result["dominant_pattern"] = dominant[0][0]
            consistency = dominant[0][1] / total
            result["consistency_score"] = round(consistency, 2)

            if consistency >= 0.8:
                result["overall_pattern"] = "consistent"
            elif consistency >= 0.5:
                result["overall_pattern"] = "mostly_consistent"
            else:
                result["overall_pattern"] = "inconsistent"

        ext_patterns = defaultdict(Counter)
        for f in code_files:
            ext_patterns[f.extension][f.naming_pattern] += 1

        for ext, pat_counter in ext_patterns.items():
            if len(pat_counter) > 1:
                for pat, cnt in pat_counter.most_common():
                    if cnt == 1:
                        anomaly_files = [
                            f.path for f in code_files
                            if f.extension == ext and f.naming_pattern == pat
                        ]
                        result["anomalies"].extend(anomaly_files)

        return result

    def _build_dependency_graph(self, all_files: List[FileNode]) -> Dict[str, List[str]]:
        graph = defaultdict(list)
        code_files = {f.path for f in all_files if f.category == "code"}

        for f in all_files:
            if f.category != "code":
                continue
            for dep in f.dependencies:
                dep_normalized = os.path.normpath(os.path.join(os.path.dirname(f.path), dep))
                if dep_normalized in code_files:
                    graph[f.path].append(dep_normalized)

        return dict(graph)

    def _detect_module_clusters(
        self, all_files: List[FileNode], dep_graph: Dict[str, List[str]]
    ) -> List[List[str]]:
        code_files = [f for f in all_files if f.category == "code"]
        if len(code_files) < 3:
            return []

        dir_groups = defaultdict(list)
        for f in code_files:
            parent_dir = os.path.dirname(f.path)
            dir_groups[parent_dir].append(f.path)

        clusters = []
        for dir_path, files in dir_groups.items():
            if len(files) >= 2:
                internal_deps = 0
                for fp in files:
                    for dep in dep_graph.get(fp, []):
                        if dep in files:
                            internal_deps += 1

                if internal_deps >= len(files):
                    clusters.append(files)

        return clusters

    def _detect_anomalies(
        self, tree: FileNode, all_files: List[FileNode], stats: DirectoryStats
    ) -> List[Dict[str, Any]]:
        anomalies = []

        if stats.avg_files_per_dir > 50:
            anomalies.append({
                "type": "too_many_files_per_dir",
                "severity": "warning",
                "message": f"平均每个目录包含 {stats.avg_files_per_dir:.1f} 个文件，建议拆分",
            })

        if stats.max_depth > 10:
            anomalies.append({
                "type": "deep_nesting",
                "severity": "warning",
                "message": f"目录嵌套深度达到 {stats.max_depth} 层，建议简化结构",
            })

        large_files = [f for f in all_files if f.size > 50 * 1024 * 1024]
        for lf in large_files:
            anomalies.append({
                "type": "large_file",
                "severity": "info",
                "message": f"大文件: {lf.path} ({lf.size / 1024 / 1024:.1f}MB)",
                "path": lf.path,
            })

        orphan_dirs = self._find_orphan_dirs(tree)
        for od in orphan_dirs:
            anomalies.append({
                "type": "empty_or_single_file_dir",
                "severity": "info",
                "message": f"目录内容过少，可考虑合并: {od}",
                "path": od,
            })

        if stats.category_distribution.get("code", 0) > 0:
            root_files = [f for f in all_files if f.depth <= 1 and f.category == "code"]
            if len(root_files) > 10:
                anomalies.append({
                    "type": "flat_code_structure",
                    "severity": "warning",
                    "message": "根目录代码文件过多，建议按模块组织",
                })

        return anomalies

    def _find_orphan_dirs(self, node: FileNode) -> List[str]:
        result = []
        if not node.is_dir:
            return result

        file_children = [c for c in node.children if not c.is_dir]
        dir_children = [c for c in node.children if c.is_dir]

        if len(node.children) <= 1 and node.parent:
            if len(file_children) <= 1 and not dir_children:
                result.append(node.path)

        for child in dir_children:
            result.extend(self._find_orphan_dirs(child))

        return result

    def scan(self, root_path: str) -> ScanResult:
        root_path = os.path.abspath(root_path)
        self.file_signatures = {}

        if not os.path.isdir(root_path):
            raise ValueError(f"Not a directory: {root_path}")

        tree, all_files = self._build_tree(root_path)
        stats = self._compute_stats(tree, all_files)
        naming_analysis = self._analyze_naming(all_files)
        dep_graph = self._build_dependency_graph(all_files)
        clusters = self._detect_module_clusters(all_files, dep_graph)
        anomalies = self._detect_anomalies(tree, all_files, stats)

        return ScanResult(
            root_path=root_path,
            scan_time=datetime.now(),
            tree=tree,
            all_files=all_files,
            stats=stats,
            naming_analysis=naming_analysis,
            dependency_graph=dep_graph,
            module_clusters=clusters,
            anomalies=anomalies,
            file_signatures=dict(self.file_signatures),
        )
