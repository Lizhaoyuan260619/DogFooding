"""
文件处理工具 - 文件读取、批量处理等功能
"""
import os
from typing import List, Tuple, Dict, Optional


def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    读取文本文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        文件内容字符串

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件读取错误
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"路径不是文件: {file_path}")

    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                content = f.read()
            return content
        except Exception as e:
            raise IOError(f"无法读取文件 {file_path}: {e}")
    except Exception as e:
        raise IOError(f"读取文件时发生错误 {file_path}: {e}")


def read_files_batch(file_paths: List[str]) -> List[Tuple[str, str, Optional[str]]]:
    """
    批量读取文件

    Args:
        file_paths: 文件路径列表

    Returns:
        [(文件路径, 文件名, 文件内容)] 列表，读取失败的文件内容为None
    """
    results = []
    for file_path in file_paths:
        try:
            content = read_file(file_path)
            file_name = os.path.basename(file_path)
            results.append((file_path, file_name, content))
        except Exception as e:
            print(f"警告: 读取文件 {file_path} 失败: {e}")
            file_name = os.path.basename(file_path) if os.path.exists(file_path) else file_path
            results.append((file_path, file_name, None))
    return results


def scan_folder(folder_path: str, extension: str = ".txt") -> List[str]:
    """
    扫描文件夹，获取指定扩展名的文件列表

    Args:
        folder_path: 文件夹路径
        extension: 文件扩展名（如 .txt）

    Returns:
        文件路径列表

    Raises:
        FileNotFoundError: 文件夹不存在
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    if not os.path.isdir(folder_path):
        raise ValueError(f"路径不是文件夹: {folder_path}")

    file_paths = []
    extension = extension.lower()

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(extension):
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    return sorted(file_paths)


def get_file_info(file_path: str) -> Dict:
    """
    获取文件信息

    Args:
        file_path: 文件路径

    Returns:
        文件信息字典
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    stat = os.stat(file_path)
    return {
        "path": os.path.abspath(file_path),
        "name": os.path.basename(file_path),
        "size": stat.st_size,
        "size_human": format_file_size(stat.st_size),
        "modified": stat.st_mtime,
    }


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def detect_language(text: str) -> str:
    """
    简单检测文本语言

    Args:
        text: 文本内容

    Returns:
        'chinese' 或 'english' 或 'mixed'
    """
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    english_chars = sum(1 for c in text if c.isascii() and c.isalpha())

    total = chinese_chars + english_chars
    if total == 0:
        return "unknown"

    chinese_ratio = chinese_chars / total

    if chinese_ratio > 0.7:
        return "chinese"
    elif chinese_ratio < 0.3:
        return "english"
    else:
        return "mixed"
