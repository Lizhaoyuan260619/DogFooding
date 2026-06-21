import os
import shutil
import zipfile
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class ActionType:
    MOVE = "move"
    RENAME = "rename"
    COPY = "copy"
    ZIP = "zip"
    DELETE = "delete"
    BACKUP = "backup"


class FileOperationException(Exception):
    pass


class FileOperation:
    def __init__(self, operation_type: str, source_path: str, target_path: str = None,
                 metadata: Dict = None):
        self.operation_type = operation_type
        self.source_path = source_path
        self.target_path = target_path
        self.metadata = metadata or {}
        self.status = "pending"
        self.error_message = None


class FileOperator:
    def __init__(self, dry_run: bool = False, on_progress: Callable = None):
        self.dry_run = dry_run
        self.on_progress = on_progress
        self.operations: List[FileOperation] = []

    def _report_progress(self, operation: FileOperation):
        if self.on_progress:
            self.on_progress(operation)

    def _get_unique_path(self, target_path: str) -> str:
        if not os.path.exists(target_path):
            return target_path

        directory = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        name, ext = os.path.splitext(filename)

        counter = 1
        while True:
            new_name = f"{name}({counter}){ext}"
            new_path = os.path.join(directory, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def move(self, source_path: str, target_dir: str, new_name: str = None) -> FileOperation:
        source_path = os.path.abspath(source_path)
        target_dir = os.path.abspath(target_dir)

        if not os.path.exists(source_path):
            op = FileOperation(ActionType.MOVE, source_path, None, {"error": "Source not found"})
            op.status = "failed"
            op.error_message = f"Source file not found: {source_path}"
            self.operations.append(op)
            self._report_progress(op)
            return op

        if new_name:
            target_filename = new_name
        else:
            target_filename = os.path.basename(source_path)

        target_path = os.path.join(target_dir, target_filename)
        target_path = self._get_unique_path(target_path)

        op = FileOperation(ActionType.MOVE, source_path, target_path)

        if self.dry_run:
            op.status = "dry_run"
            self.operations.append(op)
            self._report_progress(op)
            return op

        try:
            os.makedirs(target_dir, exist_ok=True)
            shutil.move(source_path, target_path)
            op.status = "success"
            op.metadata["original_size"] = os.path.getsize(target_path)
        except Exception as e:
            op.status = "failed"
            op.error_message = str(e)
            logger.error(f"Failed to move {source_path} to {target_path}: {e}")

        self.operations.append(op)
        self._report_progress(op)
        return op

    def rename(self, source_path: str, new_name: str) -> FileOperation:
        source_path = os.path.abspath(source_path)

        if not os.path.exists(source_path):
            op = FileOperation(ActionType.RENAME, source_path, None, {"error": "Source not found"})
            op.status = "failed"
            op.error_message = f"Source file not found: {source_path}"
            self.operations.append(op)
            self._report_progress(op)
            return op

        directory = os.path.dirname(source_path)
        target_path = os.path.join(directory, new_name)
        target_path = self._get_unique_path(target_path)

        op = FileOperation(ActionType.RENAME, source_path, target_path)

        if self.dry_run:
            op.status = "dry_run"
            self.operations.append(op)
            self._report_progress(op)
            return op

        try:
            os.rename(source_path, target_path)
            op.status = "success"
        except Exception as e:
            op.status = "failed"
            op.error_message = str(e)
            logger.error(f"Failed to rename {source_path} to {target_path}: {e}")

        self.operations.append(op)
        self._report_progress(op)
        return op

    def copy(self, source_path: str, target_dir: str, new_name: str = None) -> FileOperation:
        source_path = os.path.abspath(source_path)
        target_dir = os.path.abspath(target_dir)

        if not os.path.exists(source_path):
            op = FileOperation(ActionType.COPY, source_path, None, {"error": "Source not found"})
            op.status = "failed"
            op.error_message = f"Source file not found: {source_path}"
            self.operations.append(op)
            self._report_progress(op)
            return op

        if new_name:
            target_filename = new_name
        else:
            target_filename = os.path.basename(source_path)

        target_path = os.path.join(target_dir, target_filename)
        target_path = self._get_unique_path(target_path)

        op = FileOperation(ActionType.COPY, source_path, target_path)

        if self.dry_run:
            op.status = "dry_run"
            self.operations.append(op)
            self._report_progress(op)
            return op

        try:
            os.makedirs(target_dir, exist_ok=True)
            if os.path.isdir(source_path):
                shutil.copytree(source_path, target_path)
            else:
                shutil.copy2(source_path, target_path)
            op.status = "success"
        except Exception as e:
            op.status = "failed"
            op.error_message = str(e)
            logger.error(f"Failed to copy {source_path} to {target_path}: {e}")

        self.operations.append(op)
        self._report_progress(op)
        return op

    def backup(self, source_path: str, backup_dir: str = None) -> FileOperation:
        source_path = os.path.abspath(source_path)

        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(source_path), ".fo_backup")

        backup_dir = os.path.abspath(backup_dir)

        if not os.path.exists(source_path):
            op = FileOperation(ActionType.BACKUP, source_path, None, {"error": "Source not found"})
            op.status = "failed"
            op.error_message = f"Source file not found: {source_path}"
            self.operations.append(op)
            self._report_progress(op)
            return op

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_basename = os.path.basename(source_path)
        backup_name = f"{timestamp}_{source_basename}"
        target_path = os.path.join(backup_dir, backup_name)

        op = FileOperation(ActionType.BACKUP, source_path, target_path,
                          {"backup_dir": backup_dir, "timestamp": timestamp})

        if self.dry_run:
            op.status = "dry_run"
            self.operations.append(op)
            self._report_progress(op)
            return op

        try:
            os.makedirs(backup_dir, exist_ok=True)
            if os.path.isdir(source_path):
                shutil.copytree(source_path, target_path)
            else:
                shutil.copy2(source_path, target_path)
            op.status = "success"
        except Exception as e:
            op.status = "failed"
            op.error_message = str(e)
            logger.error(f"Failed to backup {source_path} to {target_path}: {e}")

        self.operations.append(op)
        self._report_progress(op)
        return op

    def zip(self, source_path: str, target_dir: str = None, zip_name: str = None,
            delete_original: bool = False) -> FileOperation:
        source_path = os.path.abspath(source_path)

        if target_dir is None:
            target_dir = os.path.dirname(source_path)
        target_dir = os.path.abspath(target_dir)

        if not os.path.exists(source_path):
            op = FileOperation(ActionType.ZIP, source_path, None, {"error": "Source not found"})
            op.status = "failed"
            op.error_message = f"Source file not found: {source_path}"
            self.operations.append(op)
            self._report_progress(op)
            return op

        if zip_name is None:
            source_basename = os.path.basename(source_path)
            if os.path.isfile(source_path):
                zip_name = os.path.splitext(source_basename)[0] + ".zip"
            else:
                zip_name = source_basename + ".zip"

        target_path = os.path.join(target_dir, zip_name)
        target_path = self._get_unique_path(target_path)

        op = FileOperation(ActionType.ZIP, source_path, target_path,
                          {"delete_original": delete_original})

        if self.dry_run:
            op.status = "dry_run"
            self.operations.append(op)
            self._report_progress(op)
            return op

        try:
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                            zipf.write(file_path, arcname)

            if delete_original:
                if os.path.isdir(source_path):
                    shutil.rmtree(source_path)
                else:
                    os.remove(source_path)

            op.status = "success"
        except Exception as e:
            op.status = "failed"
            op.error_message = str(e)
            logger.error(f"Failed to zip {source_path} to {target_path}: {e}")

        self.operations.append(op)
        self._report_progress(op)
        return op

    def unzip(self, zip_path: str, target_dir: str = None) -> FileOperation:
        zip_path = os.path.abspath(zip_path)

        if target_dir is None:
            target_dir = os.path.dirname(zip_path)
        target_dir = os.path.abspath(target_dir)

        if not os.path.exists(zip_path):
            op = FileOperation(ActionType.ZIP, zip_path, None, {"error": "Zip file not found"})
            op.status = "failed"
            op.error_message = f"Zip file not found: {zip_path}"
            self.operations.append(op)
            self._report_progress(op)
            return op

        op = FileOperation(ActionType.ZIP, zip_path, target_dir, {"unzip": True})

        if self.dry_run:
            op.status = "dry_run"
            self.operations.append(op)
            self._report_progress(op)
            return op

        try:
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(target_dir)
            op.status = "success"
            op.metadata["extracted"] = True
        except Exception as e:
            op.status = "failed"
            op.error_message = str(e)
            logger.error(f"Failed to unzip {zip_path} to {target_dir}: {e}")

        self.operations.append(op)
        self._report_progress(op)
        return op

    def execute_action(self, action: Dict[str, Any], source_path: str,
                       context: Dict[str, Any] = None) -> FileOperation:
        action_type = action.get("action_type", "")
        params = action.get("action_params", {}) or {}
        context = context or {}

        if action_type == ActionType.MOVE:
            target_dir = self._resolve_template(params.get("target_dir", ""), context)
            new_name = self._resolve_template(params.get("new_name", ""), context) or None
            return self.move(source_path, target_dir, new_name)

        elif action_type == ActionType.RENAME:
            new_name = self._resolve_template(params.get("new_name", ""), context)
            return self.rename(source_path, new_name)

        elif action_type == ActionType.COPY:
            target_dir = self._resolve_template(params.get("target_dir", ""), context)
            new_name = self._resolve_template(params.get("new_name", ""), context) or None
            return self.copy(source_path, target_dir, new_name)

        elif action_type == ActionType.BACKUP:
            backup_dir = params.get("backup_dir")
            if backup_dir:
                backup_dir = self._resolve_template(backup_dir, context)
            return self.backup(source_path, backup_dir)

        elif action_type == ActionType.ZIP:
            target_dir = params.get("target_dir")
            if target_dir:
                target_dir = self._resolve_template(target_dir, context)
            zip_name = params.get("zip_name")
            if zip_name:
                zip_name = self._resolve_template(zip_name, context)
            delete_original = params.get("delete_original", False)
            return self.zip(source_path, target_dir, zip_name, delete_original)

        else:
            op = FileOperation(action_type, source_path)
            op.status = "failed"
            op.error_message = f"Unknown action type: {action_type}"
            self.operations.append(op)
            self._report_progress(op)
            return op

    def _resolve_template(self, template: str, context: Dict[str, Any]) -> str:
        if not template:
            return template

        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        return result
