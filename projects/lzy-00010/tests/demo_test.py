#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能验证测试脚本 - 使用隔离沙箱确保测试独立

每个测试功能模块都使用独立的 TestEnvironmentSandbox，
确保测试之间不会相互干扰。
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import TestEnvironmentSandbox
from file_organizer.templates import TemplateManager


class TestRunner:
    """测试运行器 - 管理测试执行与结果统计"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.results = []

    def run_test(self, name: str, test_func) -> bool:
        """运行单个测试"""
        print(f"\n{'=' * 60}")
        print(f"【{name}】")
        print("=" * 60)

        try:
            test_func()
            self.passed += 1
            self.results.append((name, "PASS", ""))
            print(f"\n✅ {name} - 通过")
            return True
        except AssertionError as e:
            self.failed += 1
            self.results.append((name, "FAIL", str(e)))
            print(f"\n❌ {name} - 失败: {e}")
            return False
        except Exception as e:
            self.errors += 1
            self.results.append((name, "ERROR", str(e)))
            print(f"\n💥 {name} - 错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def summary(self):
        print("\n" + "=" * 60)
        print("测试汇总")
        print("=" * 60)
        print(f"总测试数: {len(self.results)}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"错误: {self.errors}")
        print()

        if self.failed > 0 or self.errors > 0:
            print("失败/错误的测试:")
            for name, status, msg in self.results:
                if status != "PASS":
                    print(f"  [{status}] {name}: {msg}")

        return self.failed == 0 and self.errors == 0


def _setup_source_dir(sandbox, files: list) -> str:
    """在沙箱中创建源目录和测试文件，避开_db目录"""
    src_dir = os.path.join(sandbox.temp_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    for f in files:
        sandbox.create_file(f"src/{f}", f"content of {f}")
    return src_dir


def test_dry_run_mode():
    """测试1: 干跑模式验证"""
    with TestEnvironmentSandbox("dry_run_test") as sandbox:
        test_files = [
            'photo1.jpg', 'photo2.png', 'image3.gif',
            'report.pdf', 'essay.docx', 'notes.txt',
            'movie.mp4', 'clip.avi',
            'song.mp3', 'music.wav',
            'backup.zip', 'data.rar',
        ]
        src_dir = _setup_source_dir(sandbox, test_files)
        total_files = len(test_files)

        db = sandbox.get_db()
        TemplateManager.apply_template(db, 'downloads_organize', {'categories': 'simple'})

        engine = sandbox.get_engine()
        result = engine.organize([src_dir], dry_run=True)

        assert result["success"], "整理应该成功"
        assert result["dry_run"] == True, "应该是干跑模式"
        assert result["total_files"] == total_files, f"应该扫描 {total_files} 个文件，实际 {result['total_files']} 个"
        assert result["matched_files"] == total_files, f"应该匹配 {total_files} 个文件"
        assert result["operations_count"] == total_files, f"应该有 {total_files} 个操作"

        files_after = [f for f in os.listdir(src_dir)
                      if os.path.isfile(os.path.join(src_dir, f))]
        assert len(files_after) == total_files, "干跑模式不应该移动任何文件"

        print(f"扫描文件: {result['total_files']}")
        print(f"匹配文件: {result['matched_files']}")
        print(f"拟执行操作: {result['operations_count']} 个")
        print("干跑后文件数:", len(files_after), "(应该不变)")


def test_execute_organize():
    """测试2: 执行文件整理"""
    with TestEnvironmentSandbox("execute_test") as sandbox:
        test_files = [
            'photo1.jpg', 'photo2.png', 'image3.gif',
            'report.pdf', 'essay.docx', 'notes.txt',
        ]
        src_dir = _setup_source_dir(sandbox, test_files)

        db = sandbox.get_db()
        TemplateManager.apply_template(db, 'downloads_organize', {'categories': 'simple'})

        engine = sandbox.get_engine()
        result = engine.organize([src_dir], dry_run=False)

        assert result["success"], "整理应该成功"
        assert result["success_count"] > 0, "应该有成功的操作"

        images_dir = os.path.join(src_dir, '图片')
        docs_dir = os.path.join(src_dir, '文档')

        assert os.path.isdir(images_dir), "图片文件夹应该存在"
        assert os.path.isdir(docs_dir), "文档文件夹应该存在"

        image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png', '.gif'))]
        doc_files = [f for f in os.listdir(docs_dir) if f.endswith(('.pdf', '.docx', '.txt'))]

        assert len(image_files) == 3, f"图片文件夹应该有3个文件，实际有{len(image_files)}个"
        assert len(doc_files) == 3, f"文档文件夹应该有3个文件，实际有{len(doc_files)}个"

        print(f"成功操作: {result['success_count']}")
        print(f"图片文件夹: {len(image_files)} 个文件")
        print(f"文档文件夹: {len(doc_files)} 个文件")


def test_undo_operation():
    """测试3: 撤销功能（独立环境）"""
    with TestEnvironmentSandbox("undo_test") as sandbox:
        test_files = ['a.jpg', 'b.png', 'c.txt', 'd.docx']
        src_dir = _setup_source_dir(sandbox, test_files)
        total_files = len(test_files)

        db = sandbox.get_db()
        target_dir = os.path.join(sandbox.temp_dir, "Images")
        rule_data = {
            "name": "图片规则",
            "priority": 10,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [{"condition_type": "file_type", "condition_value": "image"}],
            "actions": [{"action_type": "move", "action_params": {"target_dir": target_dir}}]
        }
        db.save_rule_complete(rule_data)

        engine = sandbox.get_engine()
        organize_result = engine.organize([src_dir], dry_run=False)

        assert organize_result["success_count"] == 2, f"应该移动2个图片文件，实际 {organize_result['success_count']} 个"

        assert os.path.isdir(target_dir), "图片目录应该存在"

        undo_result = engine.undo(organize_result["batch_id"])

        assert undo_result["success"], "撤销应该成功"
        assert undo_result["success_count"] == 2, f"应该成功撤销2个操作，实际 {undo_result['success_count']} 个"

        root_files = [f for f in os.listdir(src_dir)
                     if os.path.isfile(os.path.join(src_dir, f))]
        assert len(root_files) == total_files, f"撤销后源目录应该有{total_files}个文件，实际有{len(root_files)}个"

        print(f"整理操作: {organize_result['success_count']} 个成功")
        print(f"撤销操作: {undo_result['success_count']} 个成功")
        print(f"撤销后源目录文件数: {len(root_files)} (应该等于原始文件数)")


def test_unique_filename_handling():
    """测试4: 同名文件安全处理（独立环境）"""
    with TestEnvironmentSandbox("unique_test") as sandbox:
        sandbox.create_file('source/test.txt', 'original content')
        sandbox.create_file('target/test.txt', 'existing file')

        source = os.path.join(sandbox.temp_dir, 'source', 'test.txt')
        target = os.path.join(sandbox.temp_dir, 'target')

        from file_organizer.file_operator import FileOperator
        operator = FileOperator(dry_run=False)
        op = operator.move(source, target)

        assert op.status == "success", "移动应该成功"
        assert "(1)" in os.path.basename(op.target_path), "目标文件名应该包含(1)"

        original_exists = os.path.exists(os.path.join(target, 'test.txt'))
        new_exists = os.path.exists(os.path.join(target, 'test(1).txt'))

        assert original_exists, "原始文件应该仍然存在"
        assert new_exists, "带序号的新文件应该存在"

        print(f"移动结果: {op.status}")
        print(f"目标文件名: {os.path.basename(op.target_path)}")
        print(f"原始文件仍在: {original_exists}")
        print(f"新文件存在: {new_exists}")


def test_operation_logs():
    """测试5: 操作日志记录（独立环境）"""
    with TestEnvironmentSandbox("logs_test") as sandbox:
        src_dir = _setup_source_dir(sandbox, ['file1.jpg', 'file2.txt'])

        db = sandbox.get_db()
        target_dir = os.path.join(sandbox.temp_dir, "Images")
        rule_data = {
            "name": "测试规则",
            "priority": 10,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [{"condition_type": "extension", "condition_value": "jpg"}],
            "actions": [{"action_type": "move", "action_params": {"target_dir": target_dir}}]
        }
        db.save_rule_complete(rule_data)

        engine = sandbox.get_engine()
        result = engine.organize([src_dir], dry_run=False)

        batch_id = result["batch_id"]
        logs = db.get_operations_by_batch(batch_id)

        assert len(logs) >= 1, "应该至少有1条日志记录"

        success_logs = [log for log in logs if log["status"] == "success"]
        assert len(success_logs) >= 1, "应该有成功的操作记录"

        all_logs = db.get_operation_logs(limit=10)
        assert len(all_logs) >= 1, "应该能查询到操作日志"

        print(f"批次ID: {batch_id}")
        print(f"该批次日志数: {len(logs)}")
        print(f"成功操作数: {len(success_logs)}")
        print(f"最近日志数: {len(all_logs)}")


def test_rule_crud():
    """测试6: 规则管理（独立环境）"""
    with TestEnvironmentSandbox("rule_test") as sandbox:
        db = sandbox.get_db()

        rule_data = {
            "name": "测试规则",
            "description": "用于测试的规则",
            "priority": 5,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg", "negate": False}
            ],
            "actions": [
                {"action_type": "move", "action_params": {"target_dir": "Images"}}
            ]
        }

        rule_id = db.save_rule_complete(rule_data)
        assert rule_id > 0, "规则ID应该大于0"

        rule = db.get_rule(rule_id)
        assert rule is not None, "应该能查询到规则"
        assert rule["name"] == "测试规则", "规则名称应该正确"
        assert len(rule["conditions"]) == 1, "应该有1个条件"
        assert len(rule["actions"]) == 1, "应该有1个动作"

        db.update_rule(rule_id, enabled=False)
        rule = db.get_rule(rule_id)
        assert not rule["enabled"], "规则应该被禁用"

        all_rules = db.get_all_rules()
        assert len(all_rules) == 1, "应该有1条规则"

        db.delete_rule(rule_id)
        rule = db.get_rule(rule_id)
        assert rule is None, "规则应该被删除"

        print(f"创建规则: ID={rule_id}")
        print(f"条件数: 1, 操作数: 1")
        print(f"禁用后状态: 禁用")
        print(f"删除后: 不存在")


def test_multiple_templates_independent():
    """测试7: 多模板应用互不干扰"""
    with TestEnvironmentSandbox("templates_test") as sandbox:
        db = sandbox.get_db()

        rule_ids1 = TemplateManager.apply_template(db, "extension_sort", {"target_dir": ""})
        count1 = len(db.get_all_rules())

        rule_ids2 = TemplateManager.apply_template(db, "temp_cleanup", {"action": "zip"})
        count2 = len(db.get_all_rules())

        assert count2 == count1 + len(rule_ids2), "两次应用模板应该累加"

        print(f"第一次模板应用: {len(rule_ids1)} 条规则")
        print(f"第二次模板应用: {len(rule_ids2)} 条规则")
        print(f"总规则数: {count2}")


def test_undo_with_multiple_operations():
    """测试8: 多次操作后撤销特定批次"""
    with TestEnvironmentSandbox("multi_undo_test") as sandbox:
        test_files = ['a.jpg', 'b.jpg', 'c.txt', 'd.txt']
        src_dir = _setup_source_dir(sandbox, test_files)

        db = sandbox.get_db()
        images_dir = os.path.join(sandbox.temp_dir, "Images")
        docs_dir = os.path.join(sandbox.temp_dir, "Docs")

        rule_data = {
            "name": "图片分类",
            "priority": 10,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [{"condition_type": "file_type", "condition_value": "image"}],
            "actions": [{"action_type": "move", "action_params": {"target_dir": images_dir}}]
        }
        db.save_rule_complete(rule_data)

        rule_data2 = {
            "name": "文档分类",
            "priority": 5,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [{"condition_type": "file_type", "condition_value": "document"}],
            "actions": [{"action_type": "move", "action_params": {"target_dir": docs_dir}}]
        }
        db.save_rule_complete(rule_data2)

        engine = sandbox.get_engine()

        result1 = engine.organize([src_dir], dry_run=False)
        batch1_count = result1["success_count"]
        print(f"第一次整理: {batch1_count} 个操作")

        extra_doc = os.path.join(src_dir, "extra.txt")
        with open(extra_doc, 'w') as f:
            f.write("extra doc")

        result2 = engine.organize([src_dir], dry_run=False)
        batch2_count = result2["success_count"]
        print(f"第二次整理: {batch2_count} 个操作")

        undo_result = engine.undo(result1["batch_id"])
        print(f"撤销第一次: {undo_result['success_count']} 个成功")

        assert undo_result["success_count"] > 0, "撤销第一次应该有成功的操作"

        remaining_docs = len([f for f in os.listdir(docs_dir)
                             if os.path.isfile(os.path.join(docs_dir, f))])
        assert remaining_docs >= 1, "撤销第一次后，文档目录应该还有文件"

        print(f"撤销后文档目录剩余文件: {remaining_docs} 个")


def main():
    print("=" * 60)
    print("文件自动整理工具 - 功能验证测试（隔离版）")
    print("=" * 60)
    print("\n每个测试使用独立沙箱环境，确保测试间互不干扰")

    runner = TestRunner()

    tests = [
        ("测试1: 干跑模式", test_dry_run_mode),
        ("测试2: 执行文件整理", test_execute_organize),
        ("测试3: 撤销功能", test_undo_operation),
        ("测试4: 同名文件安全处理", test_unique_filename_handling),
        ("测试5: 操作日志记录", test_operation_logs),
        ("测试6: 规则管理", test_rule_crud),
        ("测试7: 多模板应用", test_multiple_templates_independent),
        ("测试8: 多批次撤销", test_undo_with_multiple_operations),
    ]

    for name, func in tests:
        runner.run_test(name, func)

    all_passed = runner.summary()

    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
