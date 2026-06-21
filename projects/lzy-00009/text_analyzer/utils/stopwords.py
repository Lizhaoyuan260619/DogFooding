"""
停用词管理模块 - 加载和管理中英文停用词
"""
import os
from typing import Set, List, Optional

from text_analyzer.config import DEFAULT_CHINESE_STOPWORDS, DEFAULT_ENGLISH_STOPWORDS


class StopwordsManager:
    """停用词管理器"""

    def __init__(self):
        self._chinese_stopwords: Set[str] = set()
        self._english_stopwords: Set[str] = set()
        self._custom_stopwords: Set[str] = set()
        self._load_default_stopwords()

    def _load_default_stopwords(self):
        """加载默认停用词"""
        if os.path.exists(DEFAULT_CHINESE_STOPWORDS):
            self._chinese_stopwords = self._load_stopwords_file(DEFAULT_CHINESE_STOPWORDS)

        if os.path.exists(DEFAULT_ENGLISH_STOPWORDS):
            self._english_stopwords = self._load_stopwords_file(DEFAULT_ENGLISH_STOPWORDS)

    @staticmethod
    def _load_stopwords_file(file_path: str) -> Set[str]:
        """
        从文件加载停用词

        Args:
            file_path: 停用词文件路径

        Returns:
            停用词集合
        """
        stopwords = set()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        stopwords.add(word)
        except Exception as e:
            print(f"警告: 加载停用词文件 {file_path} 失败: {e}")
        return stopwords

    def load_custom_stopwords(self, file_path: str):
        """
        加载自定义停用词文件

        Args:
            file_path: 自定义停用词文件路径
        """
        custom_words = self._load_stopwords_file(file_path)
        self._custom_stopwords.update(custom_words)

    def add_stopword(self, word: str, language: str = "auto"):
        """
        添加单个停用词

        Args:
            word: 停用词
            language: 语言类型 (chinese/english/auto)
        """
        if language == "auto":
            language = self._detect_word_language(word)

        if language == "chinese":
            self._chinese_stopwords.add(word)
        else:
            self._english_stopwords.add(word)

    def add_stopwords(self, words: List[str], language: str = "auto"):
        """
        批量添加停用词

        Args:
            words: 停用词列表
            language: 语言类型
        """
        for word in words:
            self.add_stopword(word, language)

    def get_chinese_stopwords(self) -> Set[str]:
        """获取中文停用词集合"""
        return self._chinese_stopwords.copy()

    def get_english_stopwords(self) -> Set[str]:
        """获取英文停用词集合"""
        return self._english_stopwords.copy()

    def get_all_stopwords(self) -> Set[str]:
        """获取所有停用词（中文 + 英文 + 自定义）"""
        all_stopwords = set()
        all_stopwords.update(self._chinese_stopwords)
        all_stopwords.update(self._english_stopwords)
        all_stopwords.update(self._custom_stopwords)
        return all_stopwords

    def is_stopword(self, word: str, language: str = "auto") -> bool:
        """
        判断一个词是否是停用词

        Args:
            word: 待判断的词
            language: 语言类型

        Returns:
            是否是停用词
        """
        word = word.strip().lower()
        if not word:
            return True

        if word in self._custom_stopwords:
            return True

        if language == "auto":
            language = self._detect_word_language(word)

        if language == "chinese":
            return word in self._chinese_stopwords
        else:
            return word.lower() in self._english_stopwords

    @staticmethod
    def _detect_word_language(word: str) -> str:
        """
        检测词语语言

        Args:
            word: 词语

        Returns:
            'chinese' 或 'english'
        """
        for c in word:
            if '\u4e00' <= c <= '\u9fff':
                return "chinese"
        return "english"

    def filter_stopwords(self, words: List[str], language: str = "auto") -> List[str]:
        """
        过滤停用词

        Args:
            words: 词语列表
            language: 语言类型

        Returns:
            过滤后的词语列表
        """
        return [word for word in words if not self.is_stopword(word, language)]

    def count_stopwords(self, words: List[str], language: str = "auto") -> int:
        """
        统计停用词数量

        Args:
            words: 词语列表
            language: 语言类型

        Returns:
            停用词数量
        """
        return sum(1 for word in words if self.is_stopword(word, language))


stopwords_manager = StopwordsManager()
