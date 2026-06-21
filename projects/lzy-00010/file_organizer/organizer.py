import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from .database import Database
from .rule_engine import RuleEngine, FileInfo
from .file_operator import FileOperator, ActionType, FileOperation

logger = logging.getLogger(__name__)


class OrganizerEngine:
    def __init__(self, db: Database = None, db_path: str = None):
        if db:
            self.db = db
        else:
            self.db = Database(db_path)
        self.dry_run = False
        self.batch_id = None
        self.operations: List[FileOperation] = []
        self.on_progress: Optional[Callable] = None

    def organize(self, target_dirs: List[str], dry_run: bool = False,
                 recursive: bool = True, on_progress: Callable = None) -> Dict[str, Any]:
        self.dry_run = dry_run
        self.batch_id = str(uuid.uuid4())
        self.operations = []
        self.on_progress = on_progress

        rules = self.db.get_all_rules(enabled_only=True)
        if not rules:
            return {
                "success": False,
                "message": "No enabled rules found",
                "batch_id": self.batch_id,
                "operations": []
            }

        rule_engine = RuleEngine(rules)
        file_operator = FileOperator(dry_run=dry_run, on_progress=self._on_file_operation)

        total_files = 0
        matched_files = 0
        processed_files = 0

        all_files = []
        for target_dir in target_dirs:
            if not os.path.isdir(target_dir):
                logger.warning(f"Directory not found: {target_dir}")
                continue
            for root, dirs, files in os.walk(target_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    all_files.append(file_path)
                if not recursive:
                    break

        total_files = len(all_files)

        for file_path in all_files:
            try:
                result = rule_engine.match_first(file_path)
                if result:
                    matched_files += 1
                    rule, file_info = result
                    self._execute_rule_actions(rule, file_info, file_operator)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                if self.on_progress:
                    op = FileOperation("error", file_path)
                    op.status = "failed"
                    op.error_message = str(e)
                    self.on_progress(op)
            processed_files += 1

        self._log_operations()

        success_count = sum(1 for op in self.operations if op.status == "success")
        failed_count = sum(1 for op in self.operations if op.status == "failed")

        return {
            "success": True,
            "batch_id": self.batch_id,
            "total_files": total_files,
            "matched_files": matched_files,
            "operations_count": len(self.operations),
            "success_count": success_count,
            "failed_count": failed_count,
            "dry_run": dry_run,
            "operations": self.operations
        }

    def _execute_rule_actions(self, rule: Dict[str, Any], file_info: FileInfo,
                              file_operator: FileOperator):
        actions = rule.get("actions", [])
        if not actions:
            return

        context = {
            "filename": file_info.filename,
            "name": file_info.name,
            "ext": file_info.extension.lstrip("."),
            "extension": file_info.extension.lstrip("."),
            "size": file_info.size,
            "modified": file_info.modified_time.strftime("%Y%m%d"),
            "modified_year": file_info.modified_time.strftime("%Y"),
            "modified_month": file_info.modified_time.strftime("%m"),
            "modified_day": file_info.modified_time.strftime("%d"),
            "created": file_info.created_time.strftime("%Y%m%d"),
            "created_year": file_info.created_time.strftime("%Y"),
            "created_month": file_info.created_time.strftime("%m"),
            "created_day": file_info.created_time.strftime("%d"),
        }

        current_path = file_info.path
        source_dir = os.path.dirname(current_path)

        for action in actions:
            try:
                action_copy = self._resolve_action_paths(action, source_dir, context)
                op = file_operator.execute_action(action_copy, current_path, context)
                self.operations.append(op)

                if op.status == "success" and op.target_path:
                    action_type = action.get("action_type", "")
                    if action_type in [ActionType.MOVE, ActionType.RENAME]:
                        current_path = op.target_path
            except Exception as e:
                logger.error(f"Error executing action {action}: {e}")

    def _on_file_operation(self, operation: FileOperation):
        if self.on_progress:
            self.on_progress(operation)

    def _log_operations(self):
        for op in self.operations:
            self.db.log_operation(
                batch_id=self.batch_id,
                operation_type=op.operation_type,
                source_path=op.source_path,
                target_path=op.target_path,
                status=op.status,
                error_message=op.error_message,
                metadata=op.metadata
            )

    def _resolve_action_paths(self, action: Dict[str, Any], source_dir: str,
                             context: Dict[str, Any]) -> Dict[str, Any]:
        import copy
        action_copy = copy.deepcopy(action)
        params = action_copy.get("action_params", {}) or {}

        path_params = ["target_dir", "backup_dir"]
        for param_name in path_params:
            if param_name in params and params[param_name]:
                path = params[param_name]
                resolved = path
                for key, value in context.items():
                    placeholder = "{" + key + "}"
                    if placeholder in resolved:
                        resolved = resolved.replace(placeholder, str(value))

                if not os.path.isabs(resolved):
                    resolved = os.path.join(source_dir, resolved)
                params[param_name] = resolved

        action_copy["action_params"] = params
        return action_copy

    def undo(self, batch_id: str = None) -> Dict[str, Any]:
        if batch_id is None:
            batch_id = self.db.get_last_batch_id()
            if batch_id is None:
                return {
                    "success": False,
                    "message": "No operations to undo"
                }

        operations = self.db.get_operations_by_batch(batch_id)
        if not operations:
            return {
                "success": False,
                "message": f"No operations found for batch {batch_id}"
            }

        undo_batch_id = str(uuid.uuid4())
        undo_results = []
        file_operator = FileOperator(dry_run=False)

        for op in operations:
            if op["status"] != "success":
                continue

            try:
                undo_op = self._undo_operation(op, file_operator)
                undo_results.append(undo_op)

                self.db.log_operation(
                    batch_id=undo_batch_id,
                    operation_type=f"undo_{op['operation_type']}",
                    source_path=op["target_path"],
                    target_path=op["source_path"],
                    status=undo_op.status,
                    error_message=undo_op.error_message,
                    metadata={"original_batch_id": batch_id, "original_operation_id": op["id"]}
                )
            except Exception as e:
                logger.error(f"Error undoing operation {op['id']}: {e}")

        success_count = sum(1 for op in undo_results if op.status == "success")
        failed_count = sum(1 for op in undo_results if op.status == "failed")

        return {
            "success": True,
            "original_batch_id": batch_id,
            "undo_batch_id": undo_batch_id,
            "total_operations": len(undo_results),
            "success_count": success_count,
            "failed_count": failed_count,
            "operations": undo_results
        }

    def _undo_operation(self, op: Dict[str, Any], file_operator: FileOperator) -> FileOperation:
        op_type = op["operation_type"]
        source = op["target_path"]
        target = op["source_path"]
        metadata = op.get("metadata", {}) or {}

        if op_type == ActionType.MOVE:
            target_dir = os.path.dirname(target)
            new_name = os.path.basename(target)
            return file_operator.move(source, target_dir, new_name)

        elif op_type == ActionType.RENAME:
            new_name = os.path.basename(target)
            return file_operator.rename(source, new_name)

        elif op_type == ActionType.COPY:
            if os.path.exists(source):
                try:
                    if os.path.isdir(source):
                        import shutil
                        shutil.rmtree(source)
                    else:
                        os.remove(source)
                    result = FileOperation("undo_copy", source, target)
                    result.status = "success"
                    return result
                except Exception as e:
                    result = FileOperation("undo_copy", source, target)
                    result.status = "failed"
                    result.error_message = str(e)
                    return result
            else:
                result = FileOperation("undo_copy", source, target)
                result.status = "success"
                result.error_message = "Copy target already removed"
                return result

        elif op_type == ActionType.BACKUP:
            if os.path.exists(source):
                try:
                    if os.path.isdir(source):
                        import shutil
                        shutil.rmtree(source)
                    else:
                        os.remove(source)
                    result = FileOperation("undo_backup", source, target)
                    result.status = "success"
                    return result
                except Exception as e:
                    result = FileOperation("undo_backup", source, target)
                    result.status = "failed"
                    result.error_message = str(e)
                    return result
            else:
                result = FileOperation("undo_backup", source, target)
                result.status = "failed"
                result.error_message = "Backup file not found"
                return result

        elif op_type == ActionType.ZIP:
            if metadata.get("unzip"):
                result = FileOperation("undo_zip", source, target)
                result.status = "skipped"
                return result
            else:
                if os.path.exists(source):
                    target_dir = os.path.dirname(target)
                    return file_operator.unzip(source, target_dir)
                else:
                    result = FileOperation("undo_zip", source, target)
                    result.status = "failed"
                    result.error_message = "Zip file not found"
                    return result

        else:
            result = FileOperation(f"undo_{op_type}", source, target)
            result.status = "skipped"
            result.error_message = f"Undo not supported for {op_type}"
            return result

    def test_rule(self, rule: Dict[str, Any], test_paths: List[str]) -> List[Dict[str, Any]]:
        matcher = RuleEngine([rule]).matchers[0] if rule.get("enabled", True) else None
        if matcher is None:
            return []

        results = []
        for path in test_paths:
            try:
                file_info = FileInfo(path)
                matched = matcher.match(file_info)
                results.append({
                    "path": path,
                    "matched": matched,
                    "filename": file_info.filename,
                    "size": file_info.size,
                    "modified": file_info.modified_time
                })
            except Exception as e:
                results.append({
                    "path": path,
                    "matched": False,
                    "error": str(e)
                })

        return results
