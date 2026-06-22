import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from .recommender import RecommendationResult

logger = logging.getLogger(__name__)


@dataclass
class ExportOptions:
    include_rules: bool = True
    include_recommendations: bool = True
    include_structure: bool = True
    include_naming: bool = True
    include_modules: bool = True
    include_statistics: bool = True
    pretty_print: bool = True


class RuleExporter:
    def __init__(self, result: RecommendationResult):
        self.result = result

    def to_dict(self, options: ExportOptions = None) -> Dict[str, Any]:
        options = options or ExportOptions()
        output = {}

        if options.include_recommendations:
            output["recommendations"] = [
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
                for r in self.result.recommendations
            ]

        if options.include_structure and self.result.recommended_structure:
            output["recommended_structure"] = {
                "directories": self.result.recommended_structure.directories,
                "file_mappings": [
                    {
                        "source": m.source,
                        "target": m.target,
                        "action": m.action,
                    }
                    for m in self.result.recommended_structure.file_mappings
                ],
                "summary": self.result.recommended_structure.summary,
            }

        if options.include_naming:
            output["naming_convention"] = self.result.naming_convention

        if options.include_modules:
            output["module_boundaries"] = self.result.module_boundaries

        if options.include_rules:
            output["generated_rules"] = self.result.generated_rules

        if options.include_statistics:
            output["statistics"] = self.result.statistics

        return output

    def to_json(self, options: ExportOptions = None) -> str:
        options = options or ExportOptions()
        data = self.to_dict(options)
        if options.pretty_print:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def to_yaml(self, options: ExportOptions = None) -> str:
        options = options or ExportOptions()
        data = self.to_dict(options)
        try:
            import yaml
            if options.pretty_print:
                return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
            return yaml.dump(data, allow_unicode=True, sort_keys=False)
        except ImportError:
            logger.warning("PyYAML not installed, falling back to JSON format")
            return self.to_json(options)

    def to_markdown(self, options: ExportOptions = None) -> str:
        options = options or ExportOptions()
        lines = []

        lines.append("# 智能文件组织推荐报告")
        lines.append("")
        lines.append(f"_生成时间: {self._current_time()}_")
        lines.append("")

        stats = self.result.statistics
        if options.include_statistics and stats:
            lines.append("## 📊 项目统计概览")
            lines.append("")
            scanned = stats.get("total_scanned", {})
            lines.append(f"- 总文件数: **{scanned.get('files', 0)}**")
            lines.append(f"- 总目录数: **{scanned.get('directories', 0)}**")
            lines.append(f"- 最大嵌套深度: **{scanned.get('max_depth', 0)}**")
            lines.append(f"- 平均每目录文件数: **{scanned.get('avg_files_per_dir', 0)}**")
            lines.append("")

            dist = stats.get("distribution", {})
            cats = dist.get("by_category", {})
            if cats:
                lines.append("### 文件类型分布")
                lines.append("")
                lines.append("| 类型 | 文件数 |")
                lines.append("|------|--------|")
                for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                    lines.append(f"| {cat} | {count} |")
                lines.append("")

        rec_stats = stats.get("recommendations", {})
        if options.include_recommendations and self.result.recommendations:
            lines.append("## 💡 推荐建议")
            lines.append("")
            lines.append(
                f"共 **{len(self.result.recommendations)}** 条建议 "
                f"(高优先级: {rec_stats.get('by_severity', {}).get('high', 0) + rec_stats.get('by_severity', {}).get('critical', 0)}, "
                f"警告: {rec_stats.get('by_severity', {}).get('warning', 0)}, "
                f"提示: {rec_stats.get('by_severity', {}).get('info', 0)})"
            )
            lines.append("")

            severity_icons = {"critical": "🔴", "high": "🟠", "warning": "🟡", "info": "🔵", "suggestion": "⚪"}
            for rec in self.result.recommendations:
                icon = severity_icons.get(rec.severity, "•")
                lines.append(f"### {icon} {rec.title}")
                lines.append("")
                lines.append(f"- **类型**: {rec.type}")
                lines.append(f"- **严重程度**: {rec.severity}")
                lines.append(f"- **分类**: {rec.category}")
                lines.append("")
                lines.append(rec.description)
                lines.append("")
                if rec.rationale:
                    lines.append(f"**理由**: {rec.rationale}")
                    lines.append("")
                if rec.best_practice:
                    lines.append(f"**最佳实践**: {rec.best_practice}")
                    lines.append("")
                if rec.affected_files:
                    lines.append(f"**受影响文件** ({len(rec.affected_files)} 个):")
                    lines.append("")
                    for f in rec.affected_files[:10]:
                        lines.append(f"- `{f}`")
                    if len(rec.affected_files) > 10:
                        lines.append(f"- ... 等 {len(rec.affected_files)} 个文件")
                    lines.append("")

        if options.include_structure and self.result.recommended_structure:
            struct = self.result.recommended_structure
            lines.append("## 📁 推荐目录结构")
            lines.append("")
            if struct.directories:
                lines.append("建议创建以下目录:")
                lines.append("")
                for d in struct.directories:
                    lines.append(f"- `{d}/`")
                lines.append("")
            if struct.file_mappings:
                lines.append(f"**需要移动的文件**: {len(struct.file_mappings)} 个")
                lines.append("")
                lines.append("| 源路径 | 目标路径 |")
                lines.append("|--------|----------|")
                for m in struct.file_mappings[:20]:
                    lines.append(f"| `{os.path.basename(m.source)}` | `{m.target}` |")
                if len(struct.file_mappings) > 20:
                    lines.append(f"| ... | 等 {len(struct.file_mappings)} 个映射 |")
                lines.append("")

        if options.include_naming and self.result.naming_convention:
            nc = self.result.naming_convention
            lines.append("## 🏷️ 命名规范建议")
            lines.append("")
            current = nc.get("current_state", {})
            lines.append("### 当前状态")
            lines.append("")
            lines.append(f"- 主流命名风格: **{current.get('dominant_pattern', 'N/A')}**")
            lines.append(f"- 一致性评分: **{current.get('consistency_score', 0):.0%}**")
            lines.append("")
            patterns = current.get("pattern_distribution", {})
            if patterns:
                lines.append("### 风格分布")
                lines.append("")
                lines.append("| 命名风格 | 文件数 |")
                lines.append("|----------|--------|")
                for pat, count in sorted(patterns.items(), key=lambda x: -x[1]):
                    lines.append(f"| {pat} | {count} |")
                lines.append("")

            recs = nc.get("recommendations", {})
            if recs:
                lines.append("### 各语言推荐规范")
                lines.append("")
                for lang, rules in recs.items():
                    if lang.startswith("_"):
                        continue
                    lines.append(f"#### {lang}")
                    lines.append("")
                    for k, v in rules.items():
                        lines.append(f"- {k}: `{v}`")
                    lines.append("")

        if options.include_modules and self.result.module_boundaries:
            lines.append("## 🧩 模块边界分析")
            lines.append("")
            lines.append(f"检测到 **{len(self.result.module_boundaries)}** 个潜在模块")
            lines.append("")
            for i, mod in enumerate(self.result.module_boundaries, 1):
                lines.append(f"### 模块 {i}: {mod.get('name', 'Unknown')}")
                lines.append("")
                lines.append(f"- 根目录: `{mod.get('root_directory', '')}`")
                lines.append(f"- 文件数: **{mod.get('file_count', 0)}**")
                lines.append(f"- 内部依赖: {mod.get('internal_dependencies', 0)}")
                lines.append(f"- 外部依赖: {mod.get('external_dependencies', 0)}")
                lines.append(f"- 内聚度: **{mod.get('cohesion_score', 0):.0%}**")
                lines.append("")

        if options.include_rules and self.result.generated_rules:
            lines.append("## 📋 可应用的整理规则")
            lines.append("")
            lines.append(f"可生成 **{len(self.result.generated_rules)}** 条规则")
            lines.append("")
            for i, rule in enumerate(self.result.generated_rules, 1):
                lines.append(f"### {i}. {rule.get('name', 'Untitled')}")
                lines.append("")
                lines.append(f"- 描述: {rule.get('description', '')}")
                lines.append(f"- 优先级: {rule.get('priority', 0)}")
                lines.append("")

        lines.append("---")
        lines.append("*由 file-organizer 智能推荐模块自动生成*")

        return "\n".join(lines)

    def export(self, file_path: str, options: ExportOptions = None) -> str:
        options = options or ExportOptions()
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            content = self.to_json(options)
        elif ext in (".yaml", ".yml"):
            content = self.to_yaml(options)
        elif ext in (".md", ".markdown"):
            content = self.to_markdown(options)
        else:
            content = self.to_json(options)

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    @staticmethod
    def _current_time() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
