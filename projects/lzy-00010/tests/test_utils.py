#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具模块 - 提供测试环境隔离与状态管理
"""

import os
import sys
import tempfile
import shutil
import unittest
import random
import string
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_organizer.database import Database
from file_organizer.organizer import OrganizerEngine
from file_organizer.file_operator import FileOperator


class IsolatedTestCase(unittest.TestCase):
    """
    隔离测试基类 - 确保每个测试用例在完全独立的环境中运行
    
    特性：
    1. 自动创建独立的临时目录
    2. 自动创建独立的数据库文件
    3. setUp 前验证环境干净
    4. tearDown 后强制清理所有资源
    5. 提供便捷的测试文件创建方法
    """

    def setUp(self):
        self._test_passed = False
        self._cleanup_called = False

        self._test_id = self._generate_test_id()
        self.temp_dir = tempfile.mkdtemp(prefix=f'fo_test_{self._test_id}_')
        self.db_dir = os.path.join(self.temp_dir, "_db")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "test.db")

        self._files_created = []
        self._dirs_created = [self.temp_dir, self.db_dir]

        self._verify_environment_clean()
        self.setUp_test()

    def setUp_test(self):
        pass

    def tearDown(self):
        try:
            self.tearDown_test()
        finally:
            self._force_cleanup()
            self._cleanup_called = True

    def tearDown_test(self):
        pass

    def _generate_test_id(self) -> str:
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        test_name = self.__class__.__name__ + "_" + self._testMethodName
        return f"{test_name}_{random_str}"

    def _verify_environment_clean(self):
        assert os.path.isdir(self.temp_dir), f"临时目录不存在: {self.temp_dir}"
        assert os.path.isdir(self.db_dir), f"数据库目录不存在: {self.db_dir}"

        db_exists = os.path.exists(self.db_path)
        assert not db_exists, f"测试前数据库已存在，环境不干净: {self.db_path}"

        temp_files = os.listdir(self.temp_dir)
        db_only = len(temp_files) == 1 and temp_files[0] == "_db"
        assert db_only, f"测试前临时目录有多余文件: {temp_files}"

    def _force_cleanup(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"警告: 清理临时目录失败 {self.temp_dir}: {e}")

    def create_test_file(self, relative_path: str, content: str = None) -> str:
        if content is None:
            content = f"test content for {relative_path}"

        full_path = os.path.join(self.temp_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)

        self._files_created.append(full_path)
        return full_path

    def create_test_files(self, file_list: List[str]) -> List[str]:
        paths = []
        for filepath in file_list:
            paths.append(self.create_test_file(filepath))
        return paths

    def create_subdir(self, relative_path: str) -> str:
        full_path = os.path.join(self.temp_dir, relative_path)
        os.makedirs(full_path, exist_ok=True)
        self._dirs_created.append(full_path)
        return full_path

    def get_db(self) -> Database:
        return Database(self.db_path)

    def get_engine(self) -> OrganizerEngine:
        return OrganizerEngine(db_path=self.db_path)

    def assertFileExists(self, path: str, msg: str = None):
        full_path = os.path.join(self.temp_dir, path) if not os.path.isabs(path) else path
        self.assertTrue(os.path.exists(full_path),
                       msg or f"文件应该存在: {full_path}")

    def assertFileNotExists(self, path: str, msg: str = None):
        full_path = os.path.join(self.temp_dir, path) if not os.path.isabs(path) else path
        self.assertFalse(os.path.exists(full_path),
                        msg or f"文件不应该存在: {full_path}")

    def assertFileCount(self, directory: str, expected_count: int, pattern: str = None):
        full_dir = os.path.join(self.temp_dir, directory) if not os.path.isabs(directory) else directory
        if not os.path.isdir(full_dir):
            self.fail(f"目录不存在: {full_dir}")

        files = os.listdir(full_dir)
        if pattern:
            import fnmatch
            files = [f for f in files if fnmatch.fnmatch(f, pattern)]

        self.assertEqual(len(files), expected_count,
                        f"目录 {directory} 中文件数量不符: 预期{expected_count}, 实际{len(files)}")

    def assertDirHasFiles(self, directory: str, expected_files: List[str]):
        full_dir = os.path.join(self.temp_dir, directory) if not os.path.isabs(directory) else directory
        if not os.path.isdir(full_dir):
            self.fail(f"目录不存在: {full_dir}")

        actual_files = sorted(os.listdir(full_dir))
        expected_files_sorted = sorted(expected_files)
        self.assertEqual(actual_files, expected_files_sorted,
                        f"目录 {directory} 中的文件列表不符")


class TestEnvironmentSandbox:
    """
    测试沙箱 - 用于在功能测试中创建完全隔离的环境
    
    使用示例:
        with TestEnvironmentSandbox() as sandbox:
            sandbox.create_files(...)
            engine = sandbox.get_engine()
            ...
    """

    def __init__(self, name: str = "sandbox"):
        self.name = name
        self._temp_dir = None
        self._db_path = None
        self._db = None
        self._engine = None
        self._file_operator = None

    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp(prefix=f'fo_sandbox_{self.name}_')

        db_dir = os.path.join(self._temp_dir, "_db")
        os.makedirs(db_dir, exist_ok=True)
        self._db_path = os.path.join(db_dir, "test.db")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        return False

    @property
    def temp_dir(self):
        if not self._temp_dir:
            raise RuntimeError("沙箱尚未初始化")
        return self._temp_dir

    @property
    def db_path(self):
        return self._db_path

    def get_db(self) -> Database:
        if not self._db:
            self._db = Database(self._db_path)
        return self._db

    def get_engine(self) -> OrganizerEngine:
        if not self._engine:
            self._engine = OrganizerEngine(db=self.get_db())
        return self._engine

    def get_file_operator(self, dry_run: bool = False) -> FileOperator:
        return FileOperator(dry_run=dry_run)

    def create_file(self, relative_path: str, content: str = None) -> str:
        if content is None:
            content = f"content of {relative_path}"

        full_path = os.path.join(self._temp_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)

        return full_path

    def create_files(self, files: List[str]) -> List[str]:
        return [self.create_file(f) for f in files]

    def list_files(self, directory: str = None) -> List[str]:
        target = directory or self._temp_dir
        if not os.path.isabs(target):
            target = os.path.join(self._temp_dir, target)

        result = []
        for root, dirs, files in os.walk(target):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self._temp_dir)
                result.append(rel_path)
        return sorted(result)

    def count_files(self, directory: str = None) -> int:
        return len(self.list_files(directory))

    def snapshot_state(self) -> Dict[str, Any]:
        return {
            "files": self.list_files(),
            "file_count": self.count_files(),
            "db_path": self._db_path,
            "db_exists": os.path.exists(self._db_path)
        }


def run_tests_random_order(test_cases, iterations: int = 5):
    """
    随机顺序运行测试，验证测试隔离性
    
    Args:
        test_cases: 测试用例类列表
        iterations: 迭代次数
    """
    import random

    print(f"随机顺序测试 ({iterations} 轮)...")

    all_tests = []
    for test_class in test_cases:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        for test in suite:
            all_tests.append(test)

    for i in range(iterations):
        print(f"\n第 {i+1} 轮...")
        random.shuffle(all_tests)

        suite = unittest.TestSuite()
        for test in all_tests:
            suite.addTest(test)

        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)

        if not result.wasSuccessful():
            print(f"第 {i+1} 轮失败!")
            if result.failures:
                print("失败的测试:")
                for test, trace in result.failures:
                    print(f"  - {test}")
            if result.errors:
                print("错误的测试:")
                for test, trace in result.errors:
                    print(f"  - {test}")
            return False

    print(f"\n✅ 所有 {iterations} 轮随机顺序测试通过!")
    return True
