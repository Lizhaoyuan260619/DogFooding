import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.expanduser("~"), ".file_organizer", "file_organizer.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                logic_operator TEXT DEFAULT 'AND',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value TEXT,
                negate INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_params TEXT,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                target_path TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                metadata TEXT,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conditions_rule_id ON conditions(rule_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_actions_rule_id ON actions(rule_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_batch_id ON operation_logs(batch_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_executed_at ON operation_logs(executed_at)
        ''')

        conn.commit()
        conn.close()

    def add_rule(self, name: str, description: str = "", priority: int = 0,
                 logic_operator: str = "AND") -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rules (name, description, priority, logic_operator) VALUES (?, ?, ?, ?)",
            (name, description, priority, logic_operator)
        )
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rule_id

    def update_rule(self, rule_id: int, name: str = None, description: str = None,
                    priority: int = None, enabled: bool = None, logic_operator: str = None):
        conn = self._get_conn()
        cursor = conn.cursor()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if logic_operator is not None:
            updates.append("logic_operator = ?")
            params.append(logic_operator)
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(rule_id)
            cursor.execute(f"UPDATE rules SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def delete_rule(self, rule_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        cursor.execute("DELETE FROM conditions WHERE rule_id = ?", (rule_id,))
        cursor.execute("DELETE FROM actions WHERE rule_id = ?", (rule_id,))
        conn.commit()
        conn.close()

    def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        rule = dict(row)
        rule["conditions"] = self._get_conditions(cursor, rule_id)
        rule["actions"] = self._get_actions(cursor, rule_id)
        conn.close()
        return rule

    def get_all_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        query = "SELECT * FROM rules"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY priority DESC, id ASC"
        cursor.execute(query)
        rows = cursor.fetchall()
        rules = []
        for row in rows:
            rule = dict(row)
            rule["conditions"] = self._get_conditions(cursor, rule["id"])
            rule["actions"] = self._get_actions(cursor, rule["id"])
            rules.append(rule)
        conn.close()
        return rules

    def _get_conditions(self, cursor, rule_id: int) -> List[Dict[str, Any]]:
        cursor.execute(
            "SELECT * FROM conditions WHERE rule_id = ? ORDER BY sort_order, id",
            (rule_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_actions(self, cursor, rule_id: int) -> List[Dict[str, Any]]:
        cursor.execute(
            "SELECT * FROM actions WHERE rule_id = ? ORDER BY sort_order, id",
            (rule_id,)
        )
        actions = []
        for row in cursor.fetchall():
            action = dict(row)
            if action["action_params"]:
                action["action_params"] = json.loads(action["action_params"])
            else:
                action["action_params"] = {}
            actions.append(action)
        return actions

    def add_condition(self, rule_id: int, condition_type: str, condition_value: str = None,
                      negate: bool = False, sort_order: int = 0) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conditions (rule_id, condition_type, condition_value, negate, sort_order) VALUES (?, ?, ?, ?, ?)",
            (rule_id, condition_type, condition_value, 1 if negate else 0, sort_order)
        )
        condition_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return condition_id

    def update_condition(self, condition_id: int, condition_type: str = None,
                         condition_value: str = None, negate: bool = None, sort_order: int = None):
        conn = self._get_conn()
        cursor = conn.cursor()
        updates = []
        params = []
        if condition_type is not None:
            updates.append("condition_type = ?")
            params.append(condition_type)
        if condition_value is not None:
            updates.append("condition_value = ?")
            params.append(condition_value)
        if negate is not None:
            updates.append("negate = ?")
            params.append(1 if negate else 0)
        if sort_order is not None:
            updates.append("sort_order = ?")
            params.append(sort_order)
        if updates:
            params.append(condition_id)
            cursor.execute(f"UPDATE conditions SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def delete_condition(self, condition_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conditions WHERE id = ?", (condition_id,))
        conn.commit()
        conn.close()

    def add_action(self, rule_id: int, action_type: str, action_params: Dict = None,
                   sort_order: int = 0) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        params_json = json.dumps(action_params) if action_params else None
        cursor.execute(
            "INSERT INTO actions (rule_id, action_type, action_params, sort_order) VALUES (?, ?, ?, ?)",
            (rule_id, action_type, params_json, sort_order)
        )
        action_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return action_id

    def update_action(self, action_id: int, action_type: str = None,
                      action_params: Dict = None, sort_order: int = None):
        conn = self._get_conn()
        cursor = conn.cursor()
        updates = []
        params = []
        if action_type is not None:
            updates.append("action_type = ?")
            params.append(action_type)
        if action_params is not None:
            updates.append("action_params = ?")
            params.append(json.dumps(action_params))
        if sort_order is not None:
            updates.append("sort_order = ?")
            params.append(sort_order)
        if updates:
            params.append(action_id)
            cursor.execute(f"UPDATE actions SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def delete_action(self, action_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM actions WHERE id = ?", (action_id,))
        conn.commit()
        conn.close()

    def log_operation(self, batch_id: str, operation_type: str, source_path: str,
                      target_path: str = None, status: str = "success",
                      error_message: str = None, metadata: Dict = None) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT INTO operation_logs (batch_id, operation_type, source_path, target_path, status, error_message, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (batch_id, operation_type, source_path, target_path, status, error_message, metadata_json)
        )
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id

    def get_last_batch_id(self) -> Optional[str]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT batch_id FROM operation_logs ORDER BY executed_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return row["batch_id"] if row else None

    def get_operations_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM operation_logs WHERE batch_id = ? ORDER BY id DESC",
            (batch_id,)
        )
        operations = []
        for row in cursor.fetchall():
            op = dict(row)
            if op["metadata"]:
                op["metadata"] = json.loads(op["metadata"])
            operations.append(op)
        conn.close()
        return operations

    def get_operation_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM operation_logs ORDER BY executed_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        logs = []
        for row in cursor.fetchall():
            log = dict(row)
            if log["metadata"]:
                log["metadata"] = json.loads(log["metadata"])
            logs.append(log)
        conn.close()
        return logs

    def save_rule_complete(self, rule_data: Dict[str, Any]) -> int:
        rule_id = rule_data.get("id")
        if rule_id and self.get_rule(rule_id):
            self.update_rule(
                rule_id,
                name=rule_data.get("name"),
                description=rule_data.get("description"),
                priority=rule_data.get("priority"),
                enabled=rule_data.get("enabled"),
                logic_operator=rule_data.get("logic_operator")
            )
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conditions WHERE rule_id = ?", (rule_id,))
            cursor.execute("DELETE FROM actions WHERE rule_id = ?", (rule_id,))
            conn.commit()
            conn.close()
        else:
            rule_id = self.add_rule(
                name=rule_data.get("name", "Untitled Rule"),
                description=rule_data.get("description", ""),
                priority=rule_data.get("priority", 0),
                logic_operator=rule_data.get("logic_operator", "AND")
            )

        for i, cond in enumerate(rule_data.get("conditions", [])):
            self.add_condition(
                rule_id,
                condition_type=cond["condition_type"],
                condition_value=cond.get("condition_value"),
                negate=cond.get("negate", False),
                sort_order=cond.get("sort_order", i)
            )

        for i, action in enumerate(rule_data.get("actions", [])):
            self.add_action(
                rule_id,
                action_type=action["action_type"],
                action_params=action.get("action_params", {}),
                sort_order=action.get("sort_order", i)
            )

        return rule_id
