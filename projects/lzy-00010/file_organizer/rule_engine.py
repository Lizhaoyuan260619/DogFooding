import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RuleCondition:
    EXTENSION = "extension"
    FILENAME_KEYWORD = "filename_keyword"
    FILE_SIZE_MIN = "file_size_min"
    FILE_SIZE_MAX = "file_size_max"
    DATE_MODIFIED_FROM = "date_modified_from"
    DATE_MODIFIED_TO = "date_modified_to"
    DATE_CREATED_FROM = "date_created_from"
    DATE_CREATED_TO = "date_created_to"
    REGEX = "regex"
    FILE_TYPE = "file_type"
    CONTAINS_TEXT = "contains_text"


class FileInfo:
    def __init__(self, file_path: str):
        self.path = os.path.abspath(file_path)
        self.filename = os.path.basename(file_path)
        self.name, self.extension = os.path.splitext(self.filename)
        self.extension = self.extension.lower()
        self.size = os.path.getsize(file_path)
        stat = os.stat(file_path)
        self.modified_time = datetime.fromtimestamp(stat.st_mtime)
        self.created_time = datetime.fromtimestamp(stat.st_ctime)
        self.is_file = os.path.isfile(file_path)
        self.is_dir = os.path.isdir(file_path)


class RuleMatcher:
    def __init__(self, rule: Dict[str, Any]):
        self.rule = rule
        self.conditions = rule.get("conditions", [])
        self.logic_operator = rule.get("logic_operator", "AND").upper()

    def match(self, file_info: FileInfo) -> bool:
        if not self.conditions:
            return True

        results = []
        for condition in self.conditions:
            result = self._match_condition(file_info, condition)
            if condition.get("negate"):
                result = not result
            results.append(result)

        if self.logic_operator == "AND":
            return all(results)
        elif self.logic_operator == "OR":
            return any(results)
        elif self.logic_operator == "NOT":
            return not all(results)
        else:
            return all(results)

    def _match_condition(self, file_info: FileInfo, condition: Dict[str, Any]) -> bool:
        cond_type = condition.get("condition_type", "")
        cond_value = condition.get("condition_value", "")

        try:
            if cond_type == RuleCondition.EXTENSION:
                return self._match_extension(file_info, cond_value)
            elif cond_type == RuleCondition.FILENAME_KEYWORD:
                return self._match_filename_keyword(file_info, cond_value)
            elif cond_type == RuleCondition.FILE_SIZE_MIN:
                return self._match_file_size_min(file_info, cond_value)
            elif cond_type == RuleCondition.FILE_SIZE_MAX:
                return self._match_file_size_max(file_info, cond_value)
            elif cond_type == RuleCondition.DATE_MODIFIED_FROM:
                return self._match_date_modified_from(file_info, cond_value)
            elif cond_type == RuleCondition.DATE_MODIFIED_TO:
                return self._match_date_modified_to(file_info, cond_value)
            elif cond_type == RuleCondition.DATE_CREATED_FROM:
                return self._match_date_created_from(file_info, cond_value)
            elif cond_type == RuleCondition.DATE_CREATED_TO:
                return self._match_date_created_to(file_info, cond_value)
            elif cond_type == RuleCondition.REGEX:
                return self._match_regex(file_info, cond_value)
            elif cond_type == RuleCondition.FILE_TYPE:
                return self._match_file_type(file_info, cond_value)
            else:
                logger.warning(f"Unknown condition type: {cond_type}")
                return False
        except Exception as e:
            logger.error(f"Error matching condition {cond_type}: {e}")
            return False

    def _match_extension(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        extensions = [ext.strip().lower() for ext in value.split(",")]
        if not extensions:
            return False
        ext = file_info.extension.lstrip(".")
        return ext in extensions

    def _match_filename_keyword(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        keywords = [kw.strip().lower() for kw in value.split(",")]
        filename_lower = file_info.filename.lower()
        return any(kw in filename_lower for kw in keywords)

    def _match_file_size_min(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            min_size = self._parse_size(value)
            return file_info.size >= min_size
        except ValueError:
            return False

    def _match_file_size_max(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            max_size = self._parse_size(value)
            return file_info.size <= max_size
        except ValueError:
            return False

    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.strip().upper()
        units = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 * 1024,
            "GB": 1024 * 1024 * 1024,
        }
        for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
            if size_str.endswith(unit):
                num = float(size_str[:-len(unit)].strip())
                return int(num * multiplier)
        return int(float(size_str))

    def _parse_date(self, date_str: str) -> datetime:
        date_str = date_str.strip()
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        if date_str.lower().endswith("d"):
            days = int(date_str[:-1])
            return datetime.now() - timedelta(days=days)
        raise ValueError(f"Cannot parse date: {date_str}")

    def _match_date_modified_from(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            from_date = self._parse_date(value)
            return file_info.modified_time >= from_date
        except ValueError:
            return False

    def _match_date_modified_to(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            to_date = self._parse_date(value)
            return file_info.modified_time <= to_date
        except ValueError:
            return False

    def _match_date_created_from(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            from_date = self._parse_date(value)
            return file_info.created_time >= from_date
        except ValueError:
            return False

    def _match_date_created_to(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            to_date = self._parse_date(value)
            return file_info.created_time <= to_date
        except ValueError:
            return False

    def _match_regex(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        try:
            pattern = re.compile(value, re.IGNORECASE)
            return bool(pattern.search(file_info.filename))
        except re.error:
            return False

    def _match_file_type(self, file_info: FileInfo, value: str) -> bool:
        if not value:
            return False
        file_type = value.strip().lower()
        ext = file_info.extension.lstrip(".")

        image_exts = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tiff", "tif"}
        document_exts = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "odt", "ods", "odp", "md"}
        audio_exts = {"mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "aiff"}
        video_exts = {"mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"}
        archive_exts = {"zip", "rar", "7z", "tar", "gz", "bz2", "xz"}
        code_exts = {"py", "js", "ts", "java", "c", "cpp", "h", "hpp", "cs", "go", "rb", "php", "html", "css", "json", "xml", "yaml", "yml", "sql", "sh", "bat"}

        type_map = {
            "image": image_exts,
            "photo": image_exts,
            "picture": image_exts,
            "document": document_exts,
            "doc": document_exts,
            "audio": audio_exts,
            "music": audio_exts,
            "video": video_exts,
            "movie": video_exts,
            "archive": archive_exts,
            "compressed": archive_exts,
            "code": code_exts,
            "programming": code_exts,
        }

        if file_type in type_map:
            return ext in type_map[file_type]
        return False


class RuleEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = sorted(rules, key=lambda r: (-r.get("priority", 0), r.get("id", 0)))
        self.matchers = [RuleMatcher(rule) for rule in self.rules if rule.get("enabled", True)]

    def match_first(self, file_path: str) -> Optional[Tuple[Dict[str, Any], FileInfo]]:
        file_info = FileInfo(file_path)
        for rule, matcher in zip(self.rules, self.matchers):
            if matcher.match(file_info):
                return rule, file_info
        return None

    def match_all(self, file_path: str) -> List[Tuple[Dict[str, Any], FileInfo]]:
        file_info = FileInfo(file_path)
        matches = []
        for rule, matcher in zip(self.rules, self.matchers):
            if matcher.match(file_info):
                matches.append((rule, file_info))
        return matches

    def scan_directory(self, directory: str, recursive: bool = True) -> List[Tuple[str, List[Dict[str, Any]]]]:
        results = []
        if not os.path.isdir(directory):
            return results

        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                matches = []
                try:
                    file_info = FileInfo(file_path)
                    for rule, matcher in zip(self.rules, self.matchers):
                        if matcher.match(file_info):
                            matches.append(rule)
                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {e}")
                if matches:
                    results.append((file_path, matches))
            if not recursive:
                break

        return results
