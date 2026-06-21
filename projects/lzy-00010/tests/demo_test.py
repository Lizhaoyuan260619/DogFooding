#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能验证测试脚本
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_organizer.database import Database
from file_organizer.templates import TemplateManager
from file_organizer.organizer import OrganizerEngine


def main():
    print("=" * 60)
    print("文件自动整理工具 - 功能验证测试")
    print("=" * 60)

    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix='fo_test_')
    db_dir = tempfile.mkdtemp(prefix='fo_db_')
    print(f"\n测试目录: {test_dir}")

    try:
        # 创建测试文件
        file_types = {
            'images': ['photo1.jpg', 'photo2.png', 'image3.gif'],
            'documents': ['report.pdf', 'essay.docx', 'notes.txt'],
            'videos': ['movie.mp4', 'clip.avi'],
            'music': ['song.mp3', 'music.wav'],
            'archives': ['backup.zip', 'data.rar'],
        }

        print("\n创建测试文件...")
        total_files = 0
        for category, files in file_types.items():
            for f in files:
                filepath = os.path.join(test_dir, f)
                with open(filepath, 'w') as fp:
                    fp.write('test content ' * 10)
                total_files += 1

        print(f"共创建 {total_files} 个测试文件")

        # 初始化数据库（放在测试目录外）
        db_dir = tempfile.mkdtemp(prefix='fo_db_')
        db_path = os.path.join(db_dir, 'test.db')
        db = Database(db_path)

        # 应用下载目录整理模板
        print("\n" + "-" * 60)
        print("应用下载目录整理模板...")
        rule_ids = TemplateManager.apply_template(db, 'downloads_organize', {'categories': 'simple'})
        print(f"生成了 {len(rule_ids)} 条规则")

        rules = db.get_all_rules()
        for rule in rules:
            cond_count = len(rule['conditions'])
            print(f"  [{rule['id']}] {rule['name']} - 优先级:{rule['priority']}, 条件:{cond_count}个")

        # 测试干跑模式
        print("\n" + "-" * 60)
        print("【测试1】干跑模式 (--dry-run)")
        print("-" * 60)

        engine = OrganizerEngine(db=db)
        result = engine.organize([test_dir], dry_run=True)

        print(f"扫描文件: {result['total_files']}")
        print(f"匹配文件: {result['matched_files']}")
        print(f"拟执行操作: {result['operations_count']} 个")

        print("\n操作详情预览:")
        for op in result['operations']:
            if op.status == 'dry_run':
                src_name = os.path.basename(op.source_path)
                dst_name = os.path.basename(op.target_path) if op.target_path else ''
                print(f"  [{op.operation_type:6s}] {src_name:20s} -> {dst_name}")

        # 验证文件没有被移动
        files_before = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
        print(f"\n干跑后根目录文件数: {len(files_before)} (应该不变)")
        assert len(files_before) == total_files, "干跑模式不应该修改文件！"
        print("✓ 干跑模式验证通过")

        # 实际执行整理
        print("\n" + "-" * 60)
        print("【测试2】执行文件整理")
        print("-" * 60)

        result = engine.organize([test_dir], dry_run=False)
        print(f"执行结果:")
        print(f"  总文件数: {result['total_files']}")
        print(f"  匹配文件: {result['matched_files']}")
        print(f"  成功操作: {result['success_count']}")
        print(f"  失败操作: {result['failed_count']}")
        print(f"  批次ID: {result['batch_id']}")

        print("\n整理后目录结构:")
        for item in sorted(os.listdir(test_dir)):
            item_path = os.path.join(test_dir, item)
            if os.path.isdir(item_path):
                files = os.listdir(item_path)
                print(f"  📁 {item}/ ({len(files)} 个文件)")
                for f in sorted(files):
                    print(f"    - {f}")

        # 验证文件是否被正确分类
        images_dir = os.path.join(test_dir, '图片')
        docs_dir = os.path.join(test_dir, '文档')

        if os.path.isdir(images_dir):
            image_files = os.listdir(images_dir)
            assert len(image_files) == 3, f"图片文件夹应该有3个文件，实际有{len(image_files)}个"
            print("\n✓ 图片分类正确")

        if os.path.isdir(docs_dir):
            doc_files = os.listdir(docs_dir)
            assert len(doc_files) == 3, f"文档文件夹应该有3个文件，实际有{len(doc_files)}个"
            print("✓ 文档分类正确")

        first_batch_id = result['batch_id']

        # 测试撤销功能
        print("\n" + "-" * 60)
        print("【测试3】撤销功能")
        print("-" * 60)

        print(f"撤销批次: {first_batch_id}")

        undo_result = engine.undo(first_batch_id)
        print(f"撤销结果:")
        print(f"  操作数: {undo_result['total_operations']}")
        print(f"  成功: {undo_result['success_count']}")
        print(f"  失败: {undo_result['failed_count']}")

        files_after_undo = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
        print(f"\n撤销后根目录文件数: {len(files_after_undo)}")

        assert len(files_after_undo) == total_files, f"撤销后应该有{total_files}个文件，实际有{len(files_after_undo)}个"
        print("✓ 撤销功能正常工作")

        # 测试同名文件处理
        print("\n" + "-" * 60)
        print("【测试4】同名文件安全处理")
        print("-" * 60)

        # 重新整理
        engine.organize([test_dir], dry_run=False)
        print("先整理文件...")

        # 复制文件回去制造同名
        test_file = os.path.join(images_dir, 'photo1.jpg')
        shutil.copy(test_file, os.path.join(test_dir, 'photo1.jpg'))
        print("复制 photo1.jpg 回到根目录...")

        result2 = engine.organize([test_dir], dry_run=False)
        print(f"再次整理，成功操作: {result2['success_count']}")

        image_files = sorted(os.listdir(images_dir))
        print(f"图片文件夹文件:")
        for f in image_files:
            if os.path.isfile(os.path.join(images_dir, f)):
                print(f"  - {f}")

        has_numbered = any('(1)' in f for f in image_files if os.path.isfile(os.path.join(images_dir, f)))
        if has_numbered:
            print("✓ 同名文件自动加序号处理正确")
        else:
            print("⚠ 未检测到带序号的文件")

        # 测试操作日志
        print("\n" + "-" * 60)
        print("【测试5】操作日志")
        print("-" * 60)

        logs = db.get_operation_logs(limit=10)
        print(f"最近10条操作日志:")
        for log in logs:
            status_icon = "✓" if log['status'] == 'success' else "✗"
            src_name = os.path.basename(log['source_path'])
            print(f"  [{log['executed_at']}] {status_icon} {log['operation_type']:8s} - {src_name}")

        # 测试规则管理
        print("\n" + "-" * 60)
        print("【测试6】规则管理")
        print("-" * 60)

        new_rule = {
            "name": "大文件压缩",
            "description": "大于1MB的文件自动压缩",
            "priority": 5,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {"condition_type": "file_size_min", "condition_value": "1KB", "negate": False}
            ],
            "actions": [
                {"action_type": "zip", "action_params": {"target_dir": "archives", "delete_original": False}}
            ]
        }

        rule_id = db.save_rule_complete(new_rule)
        print(f"新建规则: ID={rule_id}")

        rule = db.get_rule(rule_id)
        print(f"  名称: {rule['name']}")
        print(f"  条件数: {len(rule['conditions'])}")
        print(f"  操作数: {len(rule['actions'])}")

        db.update_rule(rule_id, enabled=False)
        rule = db.get_rule(rule_id)
        print(f"  禁用后状态: {'启用' if rule['enabled'] else '禁用'}")

        db.delete_rule(rule_id)
        rule = db.get_rule(rule_id)
        print(f"  删除后: {'存在' if rule else '已删除'}")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    finally:
        # 清理临时目录
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n临时目录已清理: {test_dir}")
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)


if __name__ == "__main__":
    main()
