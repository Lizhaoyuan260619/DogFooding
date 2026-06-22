import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import logging

from .scanner import ScanResult, FileNode

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    id: str
    type: str
    title: str
    description: str
    severity: str = "info"
    category: str = "general"
    actions: List[Dict[str, Any]] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    rationale: str = ""
    best_practice: str = ""


@dataclass
class StructureDiff:
    source: str
    target: str
    action: str


@dataclass
class RecommendedStructure:
    directories: List[str] = field(default_factory=list)
    file_mappings: List[StructureDiff] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationResult:
    recommendations: List[Recommendation] = field(default_factory=list)
    recommended_structure: Optional[RecommendedStructure] = None
    naming_convention: Dict[str, Any] = field(default_factory=dict)
    module_boundaries: List[Dict[str, Any]] = field(default_factory=list)
    generated_rules: List[Dict[str, Any]] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendations": [
                {
                    "id": r.id,
                    "type": r.type,
                    "title": r.title,
                    "description": r.description,
                    "severity": r.severity,
                    "category": r.category,
                    "actions": r.actions,
                    "affected_files": r.affected_files,
                    "rationale": r.rationale,
                    "best_practice": r.best_practice,
                }
                for r in self.recommendations
            ],
            "recommended_structure": {
                "directories": self.recommended_structure.directories if self.recommended_structure else [],
                "file_mappings": [
                    {"source": m.source, "target": m.target, "action": m.action}
                    for m in (self.recommended_structure.file_mappings if self.recommended_structure else [])
                ],
                "summary": self.recommended_structure.summary if self.recommended_structure else {},
            },
            "naming_convention": self.naming_convention,
            "module_boundaries": self.module_boundaries,
            "generated_rules": self.generated_rules,
            "statistics": self.statistics,
        }


CATEGORY_DIR_MAP = {
    "image": "images",
    "document": "documents",
    "audio": "audio",
    "video": "videos",
    "archive": "archives",
    "code": "src",
    "config": "config",
    "other": "misc",
}

EXT_LANGUAGE_MAP = {
    "py": "Python",
    "js": "JavaScript",
    "ts": "TypeScript",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "cs": "C#",
    "go": "Go",
    "rb": "Ruby",
    "php": "PHP",
    "rs": "Rust",
    "swift": "Swift",
    "kt": "Kotlin",
    "scala": "Scala",
    "r": "R",
    "lua": "Lua",
    "dart": "Dart",
    "vue": "Vue",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "sh": "Shell",
    "bat": "Batch",
}

LANGUAGE_NAMING = {
    "Python": {"preferred": "snake_case", "classes": "PascalCase", "constants": "UPPER_SNAKE_CASE"},
    "JavaScript": {"preferred": "camelCase", "classes": "PascalCase", "constants": "UPPER_SNAKE_CASE", "files": "kebab-case or camelCase"},
    "TypeScript": {"preferred": "camelCase", "classes": "PascalCase", "constants": "UPPER_SNAKE_CASE", "files": "kebab-case or camelCase"},
    "Java": {"preferred": "camelCase", "classes": "PascalCase", "constants": "UPPER_SNAKE_CASE", "files": "PascalCase"},
    "C": {"preferred": "snake_case", "files": "snake_case"},
    "C++": {"preferred": "snake_case", "classes": "PascalCase", "files": "snake_case"},
    "C#": {"preferred": "PascalCase", "files": "PascalCase"},
    "Go": {"preferred": "camelCase", "files": "snake_case"},
    "Ruby": {"preferred": "snake_case", "classes": "PascalCase", "files": "snake_case"},
    "PHP": {"preferred": "snake_case", "classes": "PascalCase", "files": "snake_case"},
    "Rust": {"preferred": "snake_case", "files": "snake_case"},
    "Swift": {"preferred": "camelCase", "classes": "PascalCase", "files": "PascalCase"},
    "Kotlin": {"preferred": "camelCase", "classes": "PascalCase", "files": "PascalCase"},
    "Vue": {"preferred": "PascalCase", "files": "PascalCase"},
    "CSS": {"preferred": "kebab-case", "files": "kebab-case"},
    "HTML": {"preferred": "kebab-case", "files": "kebab-case"},
    "Shell": {"preferred": "snake_case", "files": "snake_case"},
    "SQL": {"preferred": "snake_case", "files": "snake_case"},
}


class SmartRecommender:
    def __init__(self, scan_result: ScanResult):
        self.scan = scan_result
        self.recs: List[Recommendation] = []
        self._rec_counter = 0

    def _next_id(self, prefix: str) -> str:
        self._rec_counter += 1
        return f"{prefix}_{self._rec_counter:03d}"

    def generate_all(self) -> RecommendationResult:
        self.recs = []

        self._analyze_directory_structure()
        self._analyze_file_categorization()
        self._analyze_naming_conventions()
        self._analyze_module_boundaries()
        self._analyze_code_organization()
        self._add_anomaly_recommendations()

        recommended_structure = self._build_recommended_structure()
        naming_convention = self._build_naming_convention()
        module_boundaries = self._build_module_boundaries()
        generated_rules = self._generate_organizer_rules()

        stats = self._build_statistics()

        return RecommendationResult(
            recommendations=sorted(self.recs, key=lambda r: self._severity_order(r.severity)),
            recommended_structure=recommended_structure,
            naming_convention=naming_convention,
            module_boundaries=module_boundaries,
            generated_rules=generated_rules,
            statistics=stats,
        )

    def _severity_order(self, severity: str) -> int:
        order = {"critical": 0, "high": 1, "warning": 2, "info": 3, "suggestion": 4}
        return order.get(severity, 5)

    def _analyze_directory_structure(self):
        stats = self.scan.stats

        if stats.avg_files_per_dir > 30:
            flat_dirs = self._find_flat_directories()
            if flat_dirs:
                affected = [d for d, _ in flat_dirs]
                self.recs.append(Recommendation(
                    id=self._next_id("STRUCT"),
                    type="directory_structure",
                    title="目录文件过多，建议拆分",
                    description=f"发现 {len(flat_dirs)} 个目录包含过多文件，建议按功能或类型进一步划分子目录",
                    severity="warning",
                    category="structure",
                    affected_files=affected,
                    rationale="单个目录文件过多会降低查找效率，增加维护成本",
                    best_practice="每个目录建议包含 10-30 个条目，超过时应考虑创建子目录进行分组",
                ))

        if stats.max_depth > 8:
            self.recs.append(Recommendation(
                id=self._next_id("STRUCT"),
                type="deep_nesting",
                title="目录嵌套过深",
                description=f"当前最大目录深度为 {stats.max_depth} 层，超过建议的 8 层",
                severity="warning",
                category="structure",
                rationale="过深的目录层级会增加路径复杂度，影响可读性和维护性",
                best_practice="建议目录层级控制在 3-6 层，最深不超过 8 层",
            ))

    def _find_flat_directories(self, threshold: int = 30) -> List[Tuple[str, int]]:
        result = []
        if not self.scan.tree:
            return result

        def traverse(node: FileNode):
            if node.is_dir:
                direct_files = sum(1 for c in node.children if not c.is_dir)
                if direct_files > threshold:
                    result.append((node.path, direct_files))
                for child in node.children:
                    if child.is_dir:
                        traverse(child)

        traverse(self.scan.tree)
        return result

    def _analyze_file_categorization(self):
        stats = self.scan.stats
        categories = stats.category_distribution
        if not categories:
            return

        total = sum(categories.values())
        root_files = [f for f in self.scan.all_files if f.depth == 1]

        uncategorized_in_root = []
        for f in root_files:
            if f.category in {"code", "document", "image", "audio", "video"}:
                uncategorized_in_root.append(f.path)

        if len(uncategorized_in_root) > 5:
            self.recs.append(Recommendation(
                id=self._next_id("CAT"),
                type="file_categorization",
                title="根目录存在大量未分类文件",
                description=f"在根目录发现 {len(uncategorized_in_root)} 个可分类文件，建议按类型归档到子目录",
                severity="warning",
                category="organization",
                affected_files=uncategorized_in_root,
                rationale="根目录文件杂乱会影响项目可读性，难以快速定位资源",
                best_practice="按照文件类型或功能模块将文件组织到专用子目录中",
                actions=[
                    {"action": "move_by_category", "description": "按文件类型自动移动到对应子目录"}
                ],
            ))

        code_count = categories.get("code", 0)
        doc_count = categories.get("document", 0)
        img_count = categories.get("image", 0)

        if code_count > 0:
            code_flat = [f for f in self.scan.all_files if f.category == "code" and f.depth <= 1]
            if len(code_flat) > 10:
                self.recs.append(Recommendation(
                    id=self._next_id("CAT"),
                    type="code_organization",
                    title="源代码文件分散，建议模块化组织",
                    description=f"在根目录附近发现 {len(code_flat)} 个代码文件，建议按模块划分到 src/ 目录下的子文件夹",
                    severity="warning",
                    category="organization",
                    affected_files=[f.path for f in code_flat],
                    rationale="源代码平铺在根目录不利于模块化管理和团队协作",
                    best_practice="遵循标准项目结构：src/ 放置源码，按模块/功能创建子目录，tests/ 放置测试",
                ))

        if doc_count > 0:
            docs_flat = [f for f in self.scan.all_files if f.category == "document" and f.depth <= 1]
            non_project_docs = [f for f in docs_flat if f.naming_pattern != "project_doc"]
            if len(non_project_docs) > 3:
                self.recs.append(Recommendation(
                    id=self._next_id("CAT"),
                    type="document_organization",
                    title="文档文件建议归档到 docs/ 目录",
                    description=f"发现 {len(non_project_docs)} 个文档文件散落在根目录，建议移动到 docs/ 目录",
                    severity="info",
                    category="organization",
                    affected_files=[f.path for f in non_project_docs],
                    rationale="将文档集中管理便于查找和维护项目文档",
                    best_practice="在项目根目录创建 docs/ 文件夹，按主题进一步划分子目录",
                ))

        if img_count > 0:
            images_flat = [f for f in self.scan.all_files if f.category == "image" and f.depth <= 1]
            if len(images_flat) > 3:
                self.recs.append(Recommendation(
                    id=self._next_id("CAT"),
                    type="asset_organization",
                    title="图片资源建议归档",
                    description=f"发现 {len(images_flat)} 张图片散落在根目录，建议移动到 images/ 或 assets/ 目录",
                    severity="info",
                    category="organization",
                    affected_files=[f.path for f in images_flat],
                    rationale="图片等资源文件与代码混放影响项目整洁度",
                    best_practice="创建 assets/ 或 images/ 目录存放图片，可按用途进一步细分",
                ))

    def _analyze_naming_conventions(self):
        naming = self.scan.naming_analysis
        code_files = [f for f in self.scan.all_files if f.category == "code"]

        if not code_files:
            return

        consistency = naming.get("consistency_score", 0)
        dominant = naming.get("dominant_pattern")

        if consistency < 0.5:
            rec = Recommendation(
                id=self._next_id("NAME"),
                type="naming_inconsistency",
                title="文件命名风格不统一",
                description=f"代码文件命名一致性评分仅为 {consistency:.0%}，存在多种命名风格混用",
                severity="warning",
                category="naming",
            )

            languages = self._detect_languages()
            if languages:
                primary_lang = languages.most_common(1)[0][0]
                lang_naming = LANGUAGE_NAMING.get(primary_lang, {})
                preferred = lang_naming.get("preferred", "")
                if preferred:
                    rec.description += f"\n{primary_lang} 项目推荐使用 {preferred} 风格"
                    rec.rationale = f"统一的命名规范是代码可读性的基础，{primary_lang} 社区普遍采用 {preferred}"
                    rec.best_practice = f"遵循 {primary_lang} 社区约定：{preferred} 用于变量/函数，" + \
                                        f"{lang_naming.get('classes', 'PascalCase')} 用于类名，" + \
                                        f"{lang_naming.get('constants', 'UPPER_SNAKE_CASE')} 用于常量"

            anomaly_files = naming.get("anomalies", [])
            if anomaly_files:
                rec.affected_files = anomaly_files[:20]

            self.recs.append(rec)

        pattern_details = naming.get("pattern_details", {})
        if len(pattern_details) > 3:
            self.recs.append(Recommendation(
                id=self._next_id("NAME"),
                type="multiple_naming_styles",
                title="命名风格过多",
                description=f"项目中同时使用了 {len(pattern_details)} 种命名风格：{', '.join(pattern_details.keys())}",
                severity="info",
                category="naming",
                rationale="多种命名风格并存会增加团队成员的认知负担",
                best_practice="选定一种主要命名风格并在项目中统一使用",
            ))

    def _detect_languages(self) -> Counter:
        langs = Counter()
        for f in self.scan.all_files:
            if f.category == "code" and f.extension:
                lang = EXT_LANGUAGE_MAP.get(f.extension)
                if lang:
                    langs[lang] += 1
        return langs

    def _analyze_module_boundaries(self):
        clusters = self.scan.module_clusters
        dep_graph = self.scan.dependency_graph

        if not clusters:
            return

        self.recs.append(Recommendation(
            id=self._next_id("MOD"),
            type="module_detection",
            title=f"检测到 {len(clusters)} 个潜在模块",
            description="根据文件依赖关系分析，识别出紧密耦合的文件集群，可考虑明确模块边界",
            severity="info",
            category="architecture",
            rationale="清晰的模块边界有助于代码维护、测试和团队协作",
            best_practice="将高内聚的文件组织到同一模块目录下，并通过公共接口暴露功能",
        ))

        if dep_graph:
            reverse_deps = defaultdict(list)
            for src, deps in dep_graph.items():
                for dep in deps:
                    reverse_deps[dep].append(src)

            hotspots = [(f, len(deps)) for f, deps in reverse_deps.items() if len(deps) >= 3]
            hotspots.sort(key=lambda x: -x[1])

            if hotspots:
                top_hotspots = hotspots[:5]
                self.recs.append(Recommendation(
                    id=self._next_id("MOD"),
                    type="dependency_hotspots",
                    title="存在高依赖集中文件",
                    description=f"发现 {len(hotspots)} 个文件被多个模块依赖，可能是潜在的耦合点",
                    severity="info",
                    category="architecture",
                    affected_files=[f for f, _ in top_hotspots],
                    rationale="过度集中的依赖会导致修改风险放大，一处改动影响多个模块",
                    best_practice="考虑拆分核心依赖文件，引入抽象层或接口隔离",
                ))

    def _analyze_code_organization(self):
        code_files = [f for f in self.scan.all_files if f.category == "code"]
        if not code_files:
            return

        test_files = [f for f in code_files if f.naming_pattern == "test_file"]
        src_files = [f for f in code_files if f.naming_pattern != "test_file"]

        has_tests_dir = any("test" in os.path.basename(f.parent).lower() or
                           "tests" in os.path.basename(f.parent).lower()
                           for f in test_files)

        if test_files and not has_tests_dir:
            misplaced_tests = [f.path for f in test_files if f.depth <= 2]
            if misplaced_tests:
                self.recs.append(Recommendation(
                    id=self._next_id("CODE"),
                    type="test_organization",
                    title="测试文件建议集中存放",
                    description=f"发现 {len(misplaced_tests)} 个测试文件散落在源码目录中，建议统一存放在 tests/ 目录",
                    severity="info",
                    category="organization",
                    affected_files=misplaced_tests,
                    rationale="测试文件集中管理便于运行测试、统计覆盖率和维护测试代码",
                    best_practice="创建 tests/ 目录，按与源码对应的结构组织测试文件",
                ))

    def _add_anomaly_recommendations(self):
        for anomaly in self.scan.anomalies:
            atype = anomaly.get("type")
            severity = anomaly.get("severity", "info")
            message = anomaly.get("message", "")

            rec_type = "anomaly_" + atype
            category_map = {
                "too_many_files_per_dir": "structure",
                "deep_nesting": "structure",
                "large_file": "performance",
                "empty_or_single_file_dir": "structure",
                "flat_code_structure": "organization",
            }

            self.recs.append(Recommendation(
                id=self._next_id("ANOM"),
                type=rec_type,
                title=f"异常检测: {atype}",
                description=message,
                severity=severity,
                category=category_map.get(atype, "general"),
                affected_files=[anomaly.get("path")] if anomaly.get("path") else [],
            ))

    def _build_recommended_structure(self) -> RecommendedStructure:
        root = self.scan.root_path
        directories = []
        mappings = []
        stats = self.scan.stats
        cats = stats.category_distribution

        code_count = cats.get("code", 0)
        doc_count = cats.get("document", 0)
        img_count = cats.get("image", 0)
        audio_count = cats.get("audio", 0)
        video_count = cats.get("video", 0)
        archive_count = cats.get("archive", 0)

        if code_count > 0:
            directories.append("src")
            directories.append("tests")
        if doc_count > 0:
            directories.append("docs")
        if img_count > 0:
            directories.append("assets/images")
        if audio_count > 0:
            directories.append("assets/audio")
        if video_count > 0:
            directories.append("assets/video")
        if archive_count > 0:
            directories.append("archives")

        for f in self.scan.all_files:
            if f.depth != 1 and f.category not in {"directory"}:
                continue

            target_dir = CATEGORY_DIR_MAP.get(f.category)
            if not target_dir:
                continue

            if f.category == "code":
                if f.naming_pattern == "test_file":
                    target_dir = "tests"
                else:
                    target_dir = "src"
            elif f.category == "document":
                if f.naming_pattern == "project_doc":
                    continue
            elif f.category in {"image", "audio", "video"}:
                target_dir = f"assets/{CATEGORY_DIR_MAP[f.category]}"

            source = f.path
            target = os.path.join(root, target_dir, f.name)

            if os.path.normpath(source) != os.path.normpath(target):
                mappings.append(StructureDiff(source=source, target=target, action="move"))

        summary = {
            "total_files_to_move": len(mappings),
            "new_directories": directories,
            "category_breakdown": dict(cats),
        }

        return RecommendedStructure(directories=directories, file_mappings=mappings, summary=summary)

    def _build_naming_convention(self) -> Dict[str, Any]:
        naming = self.scan.naming_analysis
        languages = self._detect_languages()

        result = {
            "current_state": {
                "dominant_pattern": naming.get("dominant_pattern"),
                "consistency_score": naming.get("consistency_score"),
                "pattern_distribution": naming.get("pattern_details", {}),
            },
            "recommendations": {},
        }

        for lang, count in languages.most_common(3):
            lang_naming = LANGUAGE_NAMING.get(lang, {})
            if lang_naming:
                result["recommendations"][lang] = lang_naming

        if naming.get("dominant_pattern"):
            result["recommendations"]["_project"] = {
                "enforce": naming["dominant_pattern"],
                "exceptions": ["classes: PascalCase", "constants: UPPER_SNAKE_CASE"],
            }

        return result

    def _build_module_boundaries(self) -> List[Dict[str, Any]]:
        boundaries = []
        clusters = self.scan.module_clusters
        dep_graph = self.scan.dependency_graph

        for i, cluster in enumerate(clusters, 1):
            module_files = sorted(cluster)
            common_parent = os.path.commonpath(module_files) if len(module_files) > 1 else os.path.dirname(module_files[0])

            internal_deps = 0
            external_deps = 0
            for fp in module_files:
                for dep in dep_graph.get(fp, []):
                    if dep in module_files:
                        internal_deps += 1
                    else:
                        external_deps += 1

            boundaries.append({
                "id": f"module_{i}",
                "name": os.path.basename(common_parent) or f"module_{i}",
                "root_directory": common_parent,
                "files": module_files,
                "file_count": len(module_files),
                "internal_dependencies": internal_deps,
                "external_dependencies": external_deps,
                "cohesion_score": round(internal_deps / max(internal_deps + external_deps, 1), 2),
            })

        return sorted(boundaries, key=lambda b: -b["cohesion_score"])

    def _generate_organizer_rules(self) -> List[Dict[str, Any]]:
        rules = []
        root = self.scan.root_path
        cats = self.scan.stats.category_distribution

        category_configs = [
            ("image", "jpg,jpeg,png,gif,bmp,webp,svg,ico", "Images", "图片文件"),
            ("document", "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,rtf,md", "Documents", "文档文件"),
            ("audio", "mp3,wav,flac,aac,ogg,wma,m4a", "Audio", "音频文件"),
            ("video", "mp4,avi,mkv,mov,wmv,flv,webm", "Videos", "视频文件"),
            ("archive", "zip,rar,7z,tar,gz,bz2,xz", "Archives", "压缩包"),
        ]

        for cat, exts, folder, desc in category_configs:
            if cats.get(cat, 0) > 0:
                rules.append({
                    "name": f"智能推荐 - {desc}归类",
                    "description": f"将{desc}移动到 {folder}/ 文件夹",
                    "priority": 50,
                    "enabled": True,
                    "logic_operator": "AND",
                    "conditions": [
                        {
                            "condition_type": "extension",
                            "condition_value": exts,
                            "negate": False,
                            "sort_order": 0,
                        }
                    ],
                    "actions": [
                        {
                            "action_type": "move",
                            "action_params": {"target_dir": folder, "new_name": ""},
                            "sort_order": 0,
                        }
                    ],
                })

        test_count = sum(1 for f in self.scan.all_files if f.naming_pattern == "test_file")
        if test_count > 0:
            rules.append({
                "name": "智能推荐 - 测试文件归集",
                "description": "将测试文件移动到 tests/ 目录",
                "priority": 45,
                "enabled": True,
                "logic_operator": "AND",
                "conditions": [
                    {
                        "condition_type": "filename_keyword",
                        "condition_value": "test,spec,__tests__,unittest",
                        "negate": False,
                        "sort_order": 0,
                    }
                ],
                "actions": [
                    {
                        "action_type": "move",
                        "action_params": {"target_dir": "tests", "new_name": ""},
                        "sort_order": 0,
                    }
                ],
            })

        return rules

    def _build_statistics(self) -> Dict[str, Any]:
        stats = self.scan.stats
        return {
            "total_scanned": {
                "files": stats.total_files,
                "directories": stats.total_dirs,
                "total_size_bytes": stats.total_size,
                "max_depth": stats.max_depth,
                "avg_files_per_dir": round(stats.avg_files_per_dir, 1),
            },
            "distribution": {
                "by_category": dict(stats.category_distribution),
                "by_extension": dict(stats.ext_distribution.most_common(20)),
                "by_size_bucket": stats.size_distribution,
                "by_depth": dict(stats.depth_distribution),
            },
            "naming": {
                "patterns": dict(stats.naming_patterns),
                "consistency": self.scan.naming_analysis.get("consistency_score", 0),
                "dominant": self.scan.naming_analysis.get("dominant_pattern"),
            },
            "recommendations": {
                "total": len(self.recs),
                "by_severity": dict(Counter(r.severity for r in self.recs)),
                "by_category": dict(Counter(r.category for r in self.recs)),
            },
            "modules_detected": len(self.scan.module_clusters),
            "anomalies": len(self.scan.anomalies),
        }
