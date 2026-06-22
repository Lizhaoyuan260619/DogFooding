#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件自动整理工具 - 单元测试（使用隔离测试基类）
"""

import os
import sys
import tempfile
import shutil
import unittest
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import IsolatedTestCase, run_tests_random_order
from file_organizer.database import Database
from file_organizer.rule_engine import RuleEngine, RuleMatcher, FileInfo
from file_organizer.file_operator import FileOperator, FileOperation, ActionType
from file_organizer.organizer import OrganizerEngine
from file_organizer.templates import TemplateManager


class TestDatabase(IsolatedTestCase):
    """数据库层测试"""

    def setUp_test(self):
        self.db = self.get_db()

    def test_add_and_get_rule(self):
        rule_id = self.db.add_rule("测试规则", "这是一个测试规则", priority=10)
        self.assertGreater(rule_id, 0)

        rule = self.db.get_rule(rule_id)
        self.assertIsNotNone(rule)
        self.assertEqual(rule["name"], "测试规则")
        self.assertEqual(rule["description"], "这是一个测试规则")
        self.assertEqual(rule["priority"], 10)
        self.assertTrue(rule["enabled"])

    def test_update_rule(self):
        rule_id = self.db.add_rule("原名称", "", priority=5)
        self.db.update_rule(rule_id, name="新名称", priority=20, enabled=False)

        rule = self.db.get_rule(rule_id)
        self.assertEqual(rule["name"], "新名称")
        self.assertEqual(rule["priority"], 20)
        self.assertFalse(rule["enabled"])

    def test_delete_rule(self):
        rule_id = self.db.add_rule("要删除的规则")
        self.assertIsNotNone(self.db.get_rule(rule_id))

        self.db.delete_rule(rule_id)
        self.assertIsNone(self.db.get_rule(rule_id))

    def test_add_condition(self):
        rule_id = self.db.add_rule("条件测试规则")
        cond_id = self.db.add_condition(rule_id, "extension", "jpg,png", negate=False, sort_order=0)
        self.assertGreater(cond_id, 0)

        rule = self.db.get_rule(rule_id)
        self.assertEqual(len(rule["conditions"]), 1)
        self.assertEqual(rule["conditions"][0]["condition_type"], "extension")
        self.assertEqual(rule["conditions"][0]["condition_value"], "jpg,png")

    def test_add_action(self):
        rule_id = self.db.add_rule("动作测试规则")
        action_id = self.db.add_action(rule_id, "move",
                                       {"target_dir": "/test/dir", "new_name": ""},
                                       sort_order=0)
        self.assertGreater(action_id, 0)

        rule = self.db.get_rule(rule_id)
        self.assertEqual(len(rule["actions"]), 1)
        self.assertEqual(rule["actions"][0]["action_type"], "move")
        self.assertEqual(rule["actions"][0]["action_params"]["target_dir"], "/test/dir")

    def test_operation_logs(self):
        batch_id = "test_batch_001"
        log_id = self.db.log_operation(
            batch_id=batch_id,
            operation_type="move",
            source_path="/source/file.txt",
            target_path="/target/file.txt",
            status="success",
            error_message=None,
            metadata={"size": 1024}
        )
        self.assertGreater(log_id, 0)

        logs = self.db.get_operations_by_batch(batch_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["operation_type"], "move")
        self.assertEqual(logs[0]["status"], "success")

    def test_get_last_batch_id(self):
        batch_id = self.db.get_last_batch_id()
        self.assertIsNone(batch_id)

        self.db.log_operation("batch1", "move", "/a", "/b", "success")
        self.db.log_operation("batch2", "move", "/c", "/d", "success")

        last_batch = self.db.get_last_batch_id()
        self.assertEqual(last_batch, "batch2")

    def test_save_rule_complete(self):
        rule_data = {
            "name": "完整规则",
            "description": "测试完整保存",
            "priority": 15,
            "enabled": True,
            "logic_operator": "OR",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg", "negate": False},
                {"condition_type": "file_size_min", "condition_value": "1MB", "negate": False}
            ],
            "actions": [
                {"action_type": "move", "action_params": {"target_dir": "Images"}, "sort_order": 0}
            ]
        }

        rule_id = self.db.save_rule_complete(rule_data)
        rule = self.db.get_rule(rule_id)

        self.assertEqual(rule["name"], "完整规则")
        self.assertEqual(rule["logic_operator"], "OR")
        self.assertEqual(len(rule["conditions"]), 2)
        self.assertEqual(len(rule["actions"]), 1)


class TestRuleEngine(IsolatedTestCase):
    """规则引擎测试"""

    def setUp_test(self):
        self._create_test_files()

    def _create_test_files(self):
        self.test_file_jpg = self.create_test_file("test.jpg", "x" * 1024)
        self.test_file_txt = self.create_test_file("document.txt", "x" * 500)
        self.test_file_pdf = self.create_test_file("report.pdf", "x" * 3000)

        old_date = datetime.now() - timedelta(days=60)
        old_time = old_date.timestamp()
        os.utime(self.test_file_txt, (old_time, old_time))

    def test_file_info(self):
        file_info = FileInfo(self.test_file_jpg)
        self.assertEqual(file_info.filename, "test.jpg")
        self.assertEqual(file_info.name, "test")
        self.assertEqual(file_info.extension, ".jpg")
        self.assertEqual(file_info.size, 1024)
        self.assertTrue(file_info.is_file)

    def test_extension_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg,png"}
            ]
        }
        matcher = RuleMatcher(rule)

        file_info = FileInfo(self.test_file_jpg)
        self.assertTrue(matcher.match(file_info))

        file_info_txt = FileInfo(self.test_file_txt)
        self.assertFalse(matcher.match(file_info_txt))

    def test_filename_keyword_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "filename_keyword", "condition_value": "test,report"}
            ]
        }
        matcher = RuleMatcher(rule)

        file_info = FileInfo(self.test_file_jpg)
        self.assertTrue(matcher.match(file_info))

        file_info_pdf = FileInfo(self.test_file_pdf)
        self.assertTrue(matcher.match(file_info_pdf))

    def test_file_size_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "file_size_min", "condition_value": "1KB"},
                {"condition_type": "file_size_max", "condition_value": "2KB"}
            ]
        }
        matcher = RuleMatcher(rule)

        file_info = FileInfo(self.test_file_jpg)
        self.assertTrue(matcher.match(file_info))

        file_info_pdf = FileInfo(self.test_file_pdf)
        self.assertFalse(matcher.match(file_info_pdf))

    def test_date_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "date_modified_to", "condition_value": "30d"}
            ]
        }
        matcher = RuleMatcher(rule)

        file_info = FileInfo(self.test_file_txt)
        self.assertTrue(matcher.match(file_info))

        file_info_jpg = FileInfo(self.test_file_jpg)
        self.assertFalse(matcher.match(file_info_jpg))

    def test_regex_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "regex", "condition_value": "^test\\."}
            ]
        }
        matcher = RuleMatcher(rule)

        file_info = FileInfo(self.test_file_jpg)
        self.assertTrue(matcher.match(file_info))

        file_info_pdf = FileInfo(self.test_file_pdf)
        self.assertFalse(matcher.match(file_info_pdf))

    def test_file_type_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "file_type", "condition_value": "image"}
            ]
        }
        matcher = RuleMatcher(rule)

        file_info = FileInfo(self.test_file_jpg)
        self.assertTrue(matcher.match(file_info))

        file_info_txt = FileInfo(self.test_file_txt)
        self.assertFalse(matcher.match(file_info_txt))

    def test_and_logic(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg"},
                {"condition_type": "file_size_min", "condition_value": "500B"}
            ]
        }
        matcher = RuleMatcher(rule)
        file_info = FileInfo(self.test_file_jpg)
        self.assertTrue(matcher.match(file_info))

    def test_or_logic(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "OR",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg"},
                {"condition_type": "extension", "condition_value": "txt"}
            ]
        }
        matcher = RuleMatcher(rule)
        file_info_jpg = FileInfo(self.test_file_jpg)
        file_info_txt = FileInfo(self.test_file_txt)
        self.assertTrue(matcher.match(file_info_jpg))
        self.assertTrue(matcher.match(file_info_txt))

    def test_not_logic(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "NOT",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg"}
            ]
        }
        matcher = RuleMatcher(rule)
        file_info_jpg = FileInfo(self.test_file_jpg)
        file_info_txt = FileInfo(self.test_file_txt)
        self.assertFalse(matcher.match(file_info_jpg))
        self.assertTrue(matcher.match(file_info_txt))

    def test_negate_condition(self):
        rule = {
            "name": "测试",
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "extension", "condition_value": "jpg", "negate": True}
            ]
        }
        matcher = RuleMatcher(rule)
        file_info_jpg = FileInfo(self.test_file_jpg)
        file_info_txt = FileInfo(self.test_file_txt)
        self.assertFalse(matcher.match(file_info_jpg))
        self.assertTrue(matcher.match(file_info_txt))

    def test_rule_engine_priority(self):
        rules = [
            {"id": 1, "name": "低优先级", "priority": 1, "enabled": True,
             "logic_operator": "AND", "conditions": [{"condition_type": "extension", "condition_value": "jpg"}],
             "actions": []},
            {"id": 2, "name": "高优先级", "priority": 10, "enabled": True,
             "logic_operator": "AND", "conditions": [{"condition_type": "extension", "condition_value": "jpg"}],
             "actions": []}
        ]
        engine = RuleEngine(rules)
        result = engine.match_first(self.test_file_jpg)
        self.assertIsNotNone(result)
        rule, info = result
        self.assertEqual(rule["name"], "高优先级")

    def test_scan_directory(self):
        rules = [
            {"id": 1, "name": "图片规则", "priority": 1, "enabled": True,
             "logic_operator": "AND", "conditions": [{"condition_type": "file_type", "condition_value": "image"}],
             "actions": []}
        ]
        engine = RuleEngine(rules)
        results = engine.scan_directory(self.temp_dir, recursive=True)
        self.assertGreater(len(results), 0)


class TestFileOperator(IsolatedTestCase):
    """文件操作引擎测试"""

    def setUp_test(self):
        self.source_dir = self.create_subdir("source")
        self.target_dir = os.path.join(self.temp_dir, "target")
        self.test_file = self.create_test_file("source/test.txt", "Hello World")

    def test_move_file(self):
        operator = FileOperator(dry_run=False)
        op = operator.move(self.test_file, self.target_dir)

        self.assertEqual(op.status, "success")
        self.assertEqual(op.operation_type, ActionType.MOVE)
        self.assertFalse(os.path.exists(self.test_file))
        self.assertTrue(os.path.exists(op.target_path))

    def test_move_dry_run(self):
        operator = FileOperator(dry_run=True)
        op = operator.move(self.test_file, self.target_dir)

        self.assertEqual(op.status, "dry_run")
        self.assertTrue(os.path.exists(self.test_file))

    def test_rename_file(self):
        operator = FileOperator(dry_run=False)
        op = operator.rename(self.test_file, "newname.txt")

        self.assertEqual(op.status, "success")
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "newname.txt")))

    def test_copy_file(self):
        operator = FileOperator(dry_run=False)
        op = operator.copy(self.test_file, self.target_dir)

        self.assertEqual(op.status, "success")
        self.assertTrue(os.path.exists(self.test_file))
        self.assertTrue(os.path.exists(op.target_path))

    def test_backup_file(self):
        operator = FileOperator(dry_run=False)
        op = operator.backup(self.test_file)

        self.assertEqual(op.status, "success")
        self.assertTrue(os.path.exists(op.target_path))

    def test_zip_file(self):
        operator = FileOperator(dry_run=False)
        op = operator.zip(self.test_file, self.target_dir)

        self.assertEqual(op.status, "success")
        self.assertTrue(op.target_path.endswith(".zip"))
        self.assertTrue(os.path.exists(op.target_path))

    def test_unique_path(self):
        os.makedirs(self.target_dir, exist_ok=True)
        existing_file = os.path.join(self.target_dir, "test.txt")
        with open(existing_file, 'w') as f:
            f.write("existing")

        operator = FileOperator(dry_run=False)
        op = operator.move(self.test_file, self.target_dir)

        self.assertEqual(op.status, "success")
        self.assertTrue("(1)" in os.path.basename(op.target_path))

    def test_unzip_file(self):
        operator = FileOperator(dry_run=False)
        zip_op = operator.zip(self.test_file, self.target_dir, "archive.zip")

        extract_dir = os.path.join(self.target_dir, "extracted")
        unzip_op = operator.unzip(zip_op.target_path, extract_dir)

        self.assertEqual(unzip_op.status, "success")
        extracted_file = os.path.join(extract_dir, "test.txt")
        self.assertTrue(os.path.exists(extracted_file))


class TestOrganizerEngine(IsolatedTestCase):
    """整理引擎测试（含撤销功能）"""

    def setUp_test(self):
        self.source_dir = self.create_subdir("source")
        self._create_test_files()
        self._create_test_rules()
        self.db = self.get_db()
        self.engine = OrganizerEngine(db=self.db)

    def _create_test_files(self):
        for i in range(3):
            self.create_test_file(f"source/image{i}.jpg", "x" * 1024)

        for i in range(2):
            self.create_test_file(f"source/doc{i}.txt", "document content")

    def _create_test_rules(self):
        db = self.get_db()
        images_dir = os.path.join(self.temp_dir, "Images")
        rule_data = {
            "name": "图片分类",
            "description": "将图片移动到Images文件夹",
            "priority": 10,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "file_type", "condition_value": "image"}
            ],
            "actions": [
                {
                    "action_type": "move",
                    "action_params": {
                        "target_dir": images_dir,
                        "new_name": ""
                    },
                    "sort_order": 0
                }
            ]
        }
        db.save_rule_complete(rule_data)

    def test_organize_dry_run(self):
        result = self.engine.organize([self.source_dir], dry_run=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["dry_run"], True)
        self.assertGreater(result["matched_files"], 0)

        for f in os.listdir(self.source_dir):
            if os.path.isfile(os.path.join(self.source_dir, f)):
                self.assertTrue(f.endswith('.jpg') or f.endswith('.txt'))

    def test_organize_execute(self):
        result = self.engine.organize([self.source_dir], dry_run=False)

        self.assertTrue(result["success"])
        self.assertGreater(result["success_count"], 0)

        images_dir = os.path.join(self.temp_dir, "Images")
        self.assertTrue(os.path.isdir(images_dir))

        image_files = [f for f in os.listdir(images_dir) if f.endswith('.jpg')]
        self.assertEqual(len(image_files), 3)

    def test_undo_operation(self):
        organize_result = self.engine.organize([self.source_dir], dry_run=False)
        self.assertTrue(organize_result["success"])

        images_dir = os.path.join(self.temp_dir, "Images")
        self.assertTrue(os.path.isdir(images_dir))

        undo_result = self.engine.undo(organize_result["batch_id"])
        self.assertTrue(undo_result["success"])
        self.assertGreater(undo_result["success_count"], 0)

        source_files = [f for f in os.listdir(self.source_dir)
                       if os.path.isfile(os.path.join(self.source_dir, f))]
        jpg_files = [f for f in source_files if f.endswith('.jpg')]
        self.assertEqual(len(jpg_files), 3)

    def test_undo_with_intermediate_operations(self):
        db = self.get_db()
        docs_dir = os.path.join(self.temp_dir, "Docs")
        doc_rule = {
            "name": "文档分类",
            "priority": 5,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "file_type", "condition_value": "document"}
            ],
            "actions": [
                {"action_type": "move", "action_params": {"target_dir": docs_dir}}
            ]
        }
        db.save_rule_complete(doc_rule)
        self.engine = OrganizerEngine(db=db)

        result1 = self.engine.organize([self.source_dir], dry_run=False)
        self.assertTrue(result1["success"])
        self.assertGreater(result1["success_count"], 0)

        images_dir = os.path.join(self.temp_dir, "Images")
        self.assertTrue(os.path.isdir(images_dir))
        self.assertTrue(os.path.isdir(docs_dir))

        extra_doc = os.path.join(self.source_dir, "extra_doc.txt")
        with open(extra_doc, 'w') as f:
            f.write("extra document")

        result2 = self.engine.organize([self.source_dir], dry_run=False)
        self.assertTrue(result2["success"])

        undo_result = self.engine.undo(result1["batch_id"])
        self.assertTrue(undo_result["success"])
        self.assertGreater(undo_result["success_count"], 0)

        self.assertTrue(os.path.isdir(docs_dir))
        doc_files = [f for f in os.listdir(docs_dir)
                    if os.path.isfile(os.path.join(docs_dir, f))]
        self.assertGreater(len(doc_files), 0)

        source_files = [f for f in os.listdir(self.source_dir)
                       if os.path.isfile(os.path.join(self.source_dir, f))]
        jpg_files = [f for f in source_files if f.endswith('.jpg')]
        self.assertEqual(len(jpg_files), 3)

    def test_test_rule(self):
        rule = self.db.get_all_rules()[0]

        test_files = [
            os.path.join(self.source_dir, "image0.jpg"),
            os.path.join(self.source_dir, "doc0.txt")
        ]

        results = self.engine.test_rule(rule, test_files)
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["matched"])
        self.assertFalse(results[1]["matched"])


class TestTemplates(IsolatedTestCase):
    """模板功能测试"""

    def setUp_test(self):
        self.db = self.get_db()

    def test_get_all_templates(self):
        templates = TemplateManager.get_all_templates()
        self.assertEqual(len(templates), 5)

    def test_extension_template(self):
        template = TemplateManager.get_template("extension_sort")
        self.assertIsNotNone(template)
        self.assertEqual(template["id"], "extension_sort")
        self.assertIn("generate_rules", template)

        rules = template["generate_rules"]()
        self.assertGreater(len(rules), 0)

    def test_photo_archive_template(self):
        template = TemplateManager.get_template("photo_archive")
        self.assertIsNotNone(template)

        rules = template["generate_rules"]({"date_source": "modified", "structure": "year_month"})
        self.assertEqual(len(rules), 1)
        self.assertIn("modified_year", rules[0]["actions"][0]["action_params"]["target_dir"])

    def test_temp_cleanup_template(self):
        template = TemplateManager.get_template("temp_cleanup")
        self.assertIsNotNone(template)

        rules = template["generate_rules"]({"action": "zip", "older_than": "30d"})
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["actions"][0]["action_type"], "zip")

    def test_downloads_template(self):
        template = TemplateManager.get_template("downloads_organize")
        self.assertIsNotNone(template)

        rules = template["generate_rules"]({"categories": "simple"})
        self.assertGreater(len(rules), 3)

    def test_music_template(self):
        template = TemplateManager.get_template("music_organize")
        self.assertIsNotNone(template)

        rules = template["generate_rules"]({"structure": "artist/album"})
        self.assertEqual(len(rules), 1)

    def test_apply_template_to_db(self):
        rule_ids = TemplateManager.apply_template(self.db, "extension_sort", {"target_dir": ""})
        self.assertGreater(len(rule_ids), 0)

        rules = self.db.get_all_rules()
        self.assertEqual(len(rules), len(rule_ids))


class TestIsolationVerification(unittest.TestCase):
    """测试隔离性验证 - 确保测试之间不会相互干扰"""

    def test_organize_undo_isolation_1(self):
        """第一轮整理-撤销测试"""
        from tests.test_utils import TestEnvironmentSandbox

        with TestEnvironmentSandbox("iso_test1") as sandbox:
            src_dir = os.path.join(sandbox.temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            sandbox.create_file("src/a.jpg", "aaa")
            sandbox.create_file("src/b.txt", "bbb")
            sandbox.create_file("src/c.png", "ccc")

            db = sandbox.get_db()
            images_dir = os.path.join(sandbox.temp_dir, "Images")
            rule_data = {
                "name": "图片规则",
                "priority": 10,
                "enabled": True,
                "logic_operator": "AND",
                "conditions": [{"condition_type": "file_type", "condition_value": "image"}],
                "actions": [{"action_type": "move", "action_params": {"target_dir": images_dir}}]
            }
            db.save_rule_complete(rule_data)

            engine = sandbox.get_engine()
            result = engine.organize([src_dir], dry_run=False)
            self.assertEqual(result["success_count"], 2)

            undo_result = engine.undo(result["batch_id"])
            self.assertEqual(undo_result["success_count"], 2)

            files = [f for f in os.listdir(src_dir)
                    if os.path.isfile(os.path.join(src_dir, f))]
            self.assertEqual(len(files), 3)

    def test_organize_undo_isolation_2(self):
        """第二轮整理-撤销测试 - 验证与第一轮独立"""
        from tests.test_utils import TestEnvironmentSandbox

        with TestEnvironmentSandbox("iso_test2") as sandbox:
            src_dir = os.path.join(sandbox.temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            sandbox.create_file("src/x.jpg", "xxx")
            sandbox.create_file("src/y.docx", "yyy")
            sandbox.create_file("src/z.mp3", "zzz")

            db = sandbox.get_db()
            pics_dir = os.path.join(sandbox.temp_dir, "Pics")
            rule_data = {
                "name": "图片规则",
                "priority": 10,
                "enabled": True,
                "logic_operator": "AND",
                "conditions": [{"condition_type": "file_type", "condition_value": "image"}],
                "actions": [{"action_type": "move", "action_params": {"target_dir": pics_dir}}]
            }
            db.save_rule_complete(rule_data)

            engine = sandbox.get_engine()
            result = engine.organize([src_dir], dry_run=False)
            self.assertEqual(result["success_count"], 1)

            undo_result = engine.undo(result["batch_id"])
            self.assertEqual(undo_result["success_count"], 1)

            files = [f for f in os.listdir(src_dir)
                    if os.path.isfile(os.path.join(src_dir, f))]
            self.assertEqual(len(files), 3)

    def test_unique_path_isolation(self):
        """同名文件处理测试 - 独立环境验证"""
        from tests.test_utils import TestEnvironmentSandbox

        with TestEnvironmentSandbox("iso_unique") as sandbox:
            sandbox.create_file("source/test.txt", "original")
            sandbox.create_file("target/test.txt", "existing")

            source = os.path.join(sandbox.temp_dir, "source", "test.txt")
            target = os.path.join(sandbox.temp_dir, "target")

            operator = FileOperator(dry_run=False)
            op = operator.move(source, target)

            self.assertEqual(op.status, "success")
            self.assertTrue("(1)" in os.path.basename(op.target_path))
            self.assertTrue(os.path.exists(os.path.join(target, "test.txt")))
            self.assertTrue(os.path.exists(os.path.join(target, "test(1).txt")))


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestRuleEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperator))
    suite.addTests(loader.loadTestsFromTestCase(TestOrganizerEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplates))
    suite.addTests(loader.loadTestsFromTestCase(TestIsolationVerification))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print(f"测试完成: 运行 {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    return result.wasSuccessful()


def run_isolation_verification():
    """运行隔离性验证"""
    print("=" * 60)
    print("测试隔离性验证 - 多轮随机顺序测试")
    print("=" * 60)

    test_cases = [
        TestDatabase,
        TestRuleEngine,
        TestFileOperator,
        TestOrganizerEngine,
        TestTemplates,
        TestIsolationVerification,
    ]

    return run_tests_random_order(test_cases, iterations=5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--isolation":
        success = run_isolation_verification()
    else:
        success = run_tests()
    sys.exit(0 if success else 1)
