import argparse
import sys
import os
import json
from typing import List, Dict, Any

from .database import Database
from .organizer import OrganizerEngine
from .templates import TemplateManager
from .file_operator import FileOperation


class CLI:
    def __init__(self):
        self.db = Database()
        self.engine = OrganizerEngine(db=self.db)

    def run(self, args=None):
        parser = self._create_parser()
        if args is None:
            args = sys.argv[1:]
        parsed_args = parser.parse_args(args)

        if hasattr(parsed_args, 'func'):
            return parsed_args.func(parsed_args)
        else:
            parser.print_help()
            return 0

    def _create_parser(self):
        parser = argparse.ArgumentParser(
            prog="file-organizer",
            description="文件自动整理工具 - 智能分类、整理和管理您的文件",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  file-organizer organize ~/Downloads
  file-organizer organize --dry-run ~/Downloads
  file-organizer organize --rule "按后缀分类" ~/Downloads
  file-organizer undo
  file-organizer rules list
  file-organizer templates list
  file-organizer templates apply extension_sort
            """
        )

        parser.add_argument("--db", help="数据库文件路径", default=None)
        parser.add_argument("--version", action="version", version="file-organizer 1.0.0")

        subparsers = parser.add_subparsers(dest="command", help="可用命令")

        self._add_organize_parser(subparsers)
        self._add_undo_parser(subparsers)
        self._add_rules_parser(subparsers)
        self._add_templates_parser(subparsers)
        self._add_logs_parser(subparsers)
        self._add_test_parser(subparsers)

        return parser

    def _add_organize_parser(self, subparsers):
        parser = subparsers.add_parser("organize", help="整理文件")
        parser.add_argument("directories", nargs="+", help="要整理的目录路径")
        parser.add_argument("--dry-run", "-n", action="store_true",
                           help="干跑模式，仅显示拟执行的操作而不实际执行")
        parser.add_argument("--no-recursive", action="store_true",
                           help="不递归子目录")
        parser.add_argument("--rule", "-r", action="append",
                           help="仅使用指定的规则（可多次指定）")
        parser.add_argument("--quiet", "-q", action="store_true",
                           help="安静模式，减少输出")
        parser.set_defaults(func=self._cmd_organize)

    def _add_undo_parser(self, subparsers):
        parser = subparsers.add_parser("undo", help="撤销最近一次操作")
        parser.add_argument("--batch-id", "-b", help="指定要撤销的批次ID")
        parser.add_argument("--quiet", "-q", action="store_true",
                           help="安静模式")
        parser.set_defaults(func=self._cmd_undo)

    def _add_rules_parser(self, subparsers):
        parser = subparsers.add_parser("rules", help="规则管理")
        rules_sub = parser.add_subparsers(dest="rules_command")

        list_parser = rules_sub.add_parser("list", help="列出所有规则")
        list_parser.add_argument("--all", "-a", action="store_true",
                                help="显示所有规则（包括禁用的）")
        list_parser.set_defaults(func=self._cmd_rules_list)

        add_parser = rules_sub.add_parser("add", help="添加规则（从JSON文件）")
        add_parser.add_argument("file", help="规则JSON文件路径")
        add_parser.set_defaults(func=self._cmd_rules_add)

        delete_parser = rules_sub.add_parser("delete", help="删除规则")
        delete_parser.add_argument("rule_id", type=int, help="规则ID")
        delete_parser.set_defaults(func=self._cmd_rules_delete)

        show_parser = rules_sub.add_parser("show", help="显示规则详情")
        show_parser.add_argument("rule_id", type=int, help="规则ID")
        show_parser.set_defaults(func=self._cmd_rules_show)

        enable_parser = rules_sub.add_parser("enable", help="启用规则")
        enable_parser.add_argument("rule_id", type=int, help="规则ID")
        enable_parser.set_defaults(func=self._cmd_rules_enable)

        disable_parser = rules_sub.add_parser("disable", help="禁用规则")
        disable_parser.add_argument("rule_id", type=int, help="规则ID")
        disable_parser.set_defaults(func=self._cmd_rules_disable)

    def _add_templates_parser(self, subparsers):
        parser = subparsers.add_parser("templates", help="模板管理")
        templates_sub = parser.add_subparsers(dest="templates_command")

        list_parser = templates_sub.add_parser("list", help="列出所有可用模板")
        list_parser.set_defaults(func=self._cmd_templates_list)

        apply_parser = templates_sub.add_parser("apply", help="应用模板")
        apply_parser.add_argument("template_id", help="模板ID")
        apply_parser.add_argument("--param", "-p", action="append",
                                 help="模板参数，格式: key=value，可多次指定")
        apply_parser.set_defaults(func=self._cmd_templates_apply)

        show_parser = templates_sub.add_parser("show", help="显示模板详情")
        show_parser.add_argument("template_id", help="模板ID")
        show_parser.set_defaults(func=self._cmd_templates_show)

    def _add_logs_parser(self, subparsers):
        parser = subparsers.add_parser("logs", help="查看操作日志")
        parser.add_argument("--limit", "-n", type=int, default=20,
                           help="显示的日志条数（默认20）")
        parser.add_argument("--batch", "-b", help="显示指定批次的日志")
        parser.set_defaults(func=self._cmd_logs)

    def _add_test_parser(self, subparsers):
        parser = subparsers.add_parser("test", help="测试规则匹配")
        parser.add_argument("rule_id", type=int, help="规则ID")
        parser.add_argument("files", nargs="+", help="要测试的文件路径")
        parser.set_defaults(func=self._cmd_test)

    def _cmd_organize(self, args):
        if not args.quiet:
            mode = "干跑模式" if args.dry_run else "执行模式"
            print(f"文件整理工具 - {mode}")
            print(f"目标目录: {', '.join(args.directories)}")
            print("-" * 50)

        def on_progress(op: FileOperation):
            if args.quiet:
                return
            status_icon = {
                "success": "✓",
                "failed": "✗",
                "dry_run": "⊙",
                "pending": "…"
            }.get(op.status, "?")

            type_names = {
                "move": "移动",
                "rename": "重命名",
                "copy": "复制",
                "zip": "压缩",
                "backup": "备份",
                "delete": "删除"
            }
            type_name = type_names.get(op.operation_type, op.operation_type)

            if op.status == "dry_run":
                print(f"  {status_icon} [{type_name}] {op.source_path}")
                print(f"         → {op.target_path}")
            elif op.status == "success":
                print(f"  {status_icon} [{type_name}] {os.path.basename(op.source_path)} → {os.path.basename(op.target_path) if op.target_path else ''}")
            elif op.status == "failed":
                print(f"  {status_icon} [{type_name}] {os.path.basename(op.source_path)} 失败: {op.error_message}")

        result = self.engine.organize(
            target_dirs=args.directories,
            dry_run=args.dry_run,
            recursive=not args.no_recursive,
            on_progress=on_progress
        )

        if not args.quiet:
            print("-" * 50)
            if result["success"]:
                print(f"完成! 扫描文件: {result['total_files']} 个")
                print(f"匹配文件: {result['matched_files']} 个")
                print(f"执行操作: {result['operations_count']} 个")
                print(f"成功: {result['success_count']} 个, 失败: {result['failed_count']} 个")
                print(f"批次ID: {result['batch_id']}")
            else:
                print(f"错误: {result['message']}")

        return 0 if result["success"] else 1

    def _cmd_undo(self, args):
        if not args.quiet:
            if args.batch_id:
                print(f"撤销操作 - 批次: {args.batch_id}")
            else:
                print("撤销操作 - 最近一次操作")
            print("-" * 50)

        result = self.engine.undo(batch_id=args.batch_id)

        if not args.quiet:
            print("-" * 50)
            if result["success"]:
                print(f"撤销完成!")
                print(f"操作数: {result['total_operations']}")
                print(f"成功: {result['success_count']} 个, 失败: {result['failed_count']} 个")
            else:
                print(f"错误: {result['message']}")

        return 0 if result["success"] else 1

    def _cmd_rules_list(self, args):
        rules = self.db.get_all_rules(enabled_only=not args.all)

        print(f"规则列表 (共 {len(rules)} 条):")
        print("-" * 70)
        print(f"{'ID':<5} {'名称':<30} {'优先级':<6} {'状态':<8} {'条件':<6} {'操作':<6}")
        print("-" * 70)

        for rule in rules:
            status = "启用" if rule["enabled"] else "禁用"
            print(f"{rule['id']:<5} {rule['name']:<30} {rule['priority']:<6} "
                  f"{status:<8} {len(rule['conditions']):<6} {len(rule['actions']):<6}")

        return 0

    def _cmd_rules_add(self, args):
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                rule_data = json.load(f)

            rule_id = self.db.save_rule_complete(rule_data)
            print(f"规则添加成功! ID: {rule_id}")
            return 0
        except Exception as e:
            print(f"添加规则失败: {e}")
            return 1

    def _cmd_rules_delete(self, args):
        rule = self.db.get_rule(args.rule_id)
        if not rule:
            print(f"规则 {args.rule_id} 不存在")
            return 1

        self.db.delete_rule(args.rule_id)
        print(f"规则 {args.rule_id} 已删除")
        return 0

    def _cmd_rules_show(self, args):
        rule = self.db.get_rule(args.rule_id)
        if not rule:
            print(f"规则 {args.rule_id} 不存在")
            return 1

        print(f"规则详情 - {rule['name']}")
        print("-" * 50)
        print(f"ID: {rule['id']}")
        print(f"名称: {rule['name']}")
        print(f"描述: {rule['description']}")
        print(f"优先级: {rule['priority']}")
        print(f"状态: {'启用' if rule['enabled'] else '禁用'}")
        print(f"逻辑运算: {rule['logic_operator']}")

        print(f"\n条件 ({len(rule['conditions'])} 个):")
        for i, cond in enumerate(rule['conditions'], 1):
            negate_str = "NOT " if cond['negate'] else ""
            print(f"  {i}. {negate_str}{cond['condition_type']}: {cond['condition_value']}")

        print(f"\n操作 ({len(rule['actions'])} 个):")
        for i, action in enumerate(rule['actions'], 1):
            params_str = json.dumps(action['action_params'], ensure_ascii=False) if action['action_params'] else ""
            print(f"  {i}. {action['action_type']}: {params_str}")

        return 0

    def _cmd_rules_enable(self, args):
        rule = self.db.get_rule(args.rule_id)
        if not rule:
            print(f"规则 {args.rule_id} 不存在")
            return 1

        self.db.update_rule(args.rule_id, enabled=True)
        print(f"规则 {args.rule_id} 已启用")
        return 0

    def _cmd_rules_disable(self, args):
        rule = self.db.get_rule(args.rule_id)
        if not rule:
            print(f"规则 {args.rule_id} 不存在")
            return 1

        self.db.update_rule(args.rule_id, enabled=False)
        print(f"规则 {args.rule_id} 已禁用")
        return 0

    def _cmd_templates_list(self, args):
        templates = TemplateManager.get_all_templates()

        print(f"可用模板 (共 {len(templates)} 个):")
        print("-" * 60)
        print(f"{'ID':<25} {'名称':<20} {'分类':<15}")
        print("-" * 60)

        for template in templates:
            print(f"{template['id']:<25} {template['name']:<20} {template['category']:<15}")
            print(f"  {template['description']}")
            print()

        return 0

    def _cmd_templates_apply(self, args):
        params = {}
        if args.param:
            for p in args.param:
                if "=" in p:
                    key, value = p.split("=", 1)
                    params[key] = value

        template = TemplateManager.get_template(args.template_id)
        if not template:
            print(f"模板 {args.template_id} 不存在")
            return 1

        rule_ids = TemplateManager.apply_template(self.db, args.template_id, params)

        print(f"模板 \"{template['name']}\" 已应用")
        print(f"生成了 {len(rule_ids)} 条规则:")
        for rule_id in rule_ids:
            rule = self.db.get_rule(rule_id)
            if rule:
                print(f"  - [{rule_id}] {rule['name']}")

        return 0

    def _cmd_templates_show(self, args):
        template = TemplateManager.get_template(args.template_id)
        if not template:
            print(f"模板 {args.template_id} 不存在")
            return 1

        print(f"模板详情 - {template['name']}")
        print("-" * 50)
        print(f"ID: {template['id']}")
        print(f"名称: {template['name']}")
        print(f"分类: {template['category']}")
        print(f"描述: {template['description']}")

        if template.get("params"):
            print(f"\n可配置参数:")
            for param in template["params"]:
                print(f"  - {param['name']}: {param['label']}")
                print(f"    默认值: {param['default']}")
                print(f"    说明: {param['description']}")

        return 0

    def _cmd_logs(self, args):
        if args.batch:
            logs = self.db.get_operations_by_batch(args.batch)
            print(f"批次 {args.batch} 的操作日志 (共 {len(logs)} 条):")
        else:
            logs = self.db.get_operation_logs(limit=args.limit)
            print(f"最近操作日志 (前 {len(logs)} 条):")

        print("-" * 80)
        print(f"{'时间':<20} {'类型':<10} {'状态':<8} {'文件'}")
        print("-" * 80)

        for log in logs:
            status_icon = "✓" if log["status"] == "success" else "✗"
            filename = os.path.basename(log["source_path"])
            print(f"{log['executed_at']:<20} {log['operation_type']:<10} "
                  f"{status_icon} {log['status']:<6} {filename}")

        return 0

    def _cmd_test(self, args):
        rule = self.db.get_rule(args.rule_id)
        if not rule:
            print(f"规则 {args.rule_id} 不存在")
            return 1

        print(f"测试规则: {rule['name']}")
        print("-" * 50)

        results = self.engine.test_rule(rule, args.files)

        for result in results:
            if result.get("error"):
                print(f"✗ {result['path']} - 错误: {result['error']}")
            elif result["matched"]:
                print(f"✓ {result['path']} - 匹配")
            else:
                print(f"✗ {result['path']} - 不匹配")

        matched = sum(1 for r in results if r.get("matched"))
        print("-" * 50)
        print(f"匹配: {matched}/{len(results)} 个文件")

        return 0


def main():
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
