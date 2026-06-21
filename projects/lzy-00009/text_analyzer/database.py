"""
数据库模块 - 使用SQLite存储分析历史记录
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

from text_analyzer.config import DB_PATH


class DatabaseManager:
    """数据库管理器，负责所有数据库操作"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_time TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                file_path TEXT,
                file_name TEXT,
                parameters TEXT,
                results TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                content TEXT,
                language TEXT,
                word_count INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_analysis_type 
            ON analysis_history(analysis_type)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_analysis_time 
            ON analysis_history(analysis_time)
        ''')

        conn.commit()
        conn.close()

    def add_analysis_record(self, analysis_type: str, file_path: Optional[str] = None,
                            file_name: Optional[str] = None,
                            parameters: Optional[Dict[str, Any]] = None,
                            results: Optional[Dict[str, Any]] = None) -> int:
        """
        添加分析历史记录

        Args:
            analysis_type: 分析类型（word_frequency, tfidf, similarity等）
            file_path: 文件路径
            file_name: 文件名
            parameters: 分析参数
            results: 分析结果

        Returns:
            记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        params_json = json.dumps(parameters, ensure_ascii=False) if parameters else None
        results_json = json.dumps(results, ensure_ascii=False) if results else None

        cursor.execute('''
            INSERT INTO analysis_history 
            (analysis_time, analysis_type, file_path, file_name, parameters, results)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (analysis_time, analysis_type, file_path, file_name, params_json, results_json))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def get_analysis_history(self, analysis_type: Optional[str] = None,
                             limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        查询分析历史记录

        Args:
            analysis_type: 分析类型过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            历史记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if analysis_type:
            cursor.execute('''
                SELECT * FROM analysis_history 
                WHERE analysis_type = ? 
                ORDER BY analysis_time DESC 
                LIMIT ? OFFSET ?
            ''', (analysis_type, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM analysis_history 
                ORDER BY analysis_time DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            record = dict(row)
            if record['parameters']:
                record['parameters'] = json.loads(record['parameters'])
            if record['results']:
                record['results'] = json.loads(record['results'])
            results.append(record)

        return results

    def get_analysis_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取分析记录

        Args:
            record_id: 记录ID

        Returns:
            记录详情
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM analysis_history WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            record = dict(row)
            if record['parameters']:
                record['parameters'] = json.loads(record['parameters'])
            if record['results']:
                record['results'] = json.loads(record['results'])
            return record

        return None

    def add_document(self, file_path: str, file_name: str, content: str,
                     language: str = "auto", word_count: int = 0) -> int:
        """
        添加或更新文档记录

        Args:
            file_path: 文件路径
            file_name: 文件名
            content: 文件内容
            language: 语言类型
            word_count: 词数

        Returns:
            文档ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (file_path, file_name, content, language, word_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_path, file_name, content, language, word_count))

        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return doc_id

    def get_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取文档列表

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            文档列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, file_path, file_name, language, word_count, created_at 
            FROM documents 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档

        Args:
            doc_id: 文档ID

        Returns:
            文档详情
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)

        return None

    def search_documents(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索文档

        Args:
            keyword: 关键词

        Returns:
            匹配的文档列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, file_path, file_name, language, word_count, created_at 
            FROM documents 
            WHERE file_name LIKE ? OR file_path LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%'))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def delete_analysis_record(self, record_id: int) -> bool:
        """
        删除分析记录

        Args:
            record_id: 记录ID

        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM analysis_history WHERE id = ?', (record_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            统计信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM analysis_history')
        total_analyses = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM documents')
        total_docs = cursor.fetchone()['count']

        cursor.execute('''
            SELECT analysis_type, COUNT(*) as count 
            FROM analysis_history 
            GROUP BY analysis_type
        ''')
        type_counts = {row['analysis_type']: row['count'] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_analyses': total_analyses,
            'total_documents': total_docs,
            'analysis_by_type': type_counts
        }


db_manager = DatabaseManager()
