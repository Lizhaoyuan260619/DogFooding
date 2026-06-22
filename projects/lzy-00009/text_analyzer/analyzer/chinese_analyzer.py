"""
中文文本分析模块 - 分词、词频统计、停用词过滤
"""
import re
import string
from typing import List, Dict, Tuple, Optional
from collections import Counter

import jieba

from text_analyzer.utils.stopwords import stopwords_manager


class ChineseTextAnalyzer:
    """中文文本分析器"""

    _PUNCTUATION_PATTERN = re.compile(
        r'[' + re.escape(string.punctuation) +
        r'\u3000-\u303f\uff00-\uffef\u2000-\u206f' +
        r'，。！？；：""''（）【】《》〈〉—…·' +
        r']'
    )

    def __init__(self):
        self._stopwords = stopwords_manager.get_chinese_stopwords()
        self._custom_stopwords = set()

    def add_stopwords(self, words: List[str]):
        """
        添加自定义停用词

        Args:
            words: 停用词列表
        """
        self._custom_stopwords.update(words)

    def load_stopwords_file(self, file_path: str):
        """
        从文件加载停用词

        Args:
            file_path: 停用词文件路径
        """
        loaded = set()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        loaded.add(word)
            self._custom_stopwords.update(loaded)
        except Exception as e:
            raise IOError(f"加载停用词文件失败: {e}")

    def _get_all_stopwords(self) -> set:
        """获取所有停用词"""
        all_stopwords = set()
        all_stopwords.update(self._stopwords)
        all_stopwords.update(self._custom_stopwords)
        return all_stopwords

    def segment(self, text: str, use_stopwords: bool = True,
                use_paddle: bool = False) -> List[str]:
        """
        中文分词

        Args:
            text: 输入文本
            use_stopwords: 是否过滤停用词
            use_paddle: 是否使用paddle模式

        Returns:
            分词结果列表
        """
        cleaned_text = self._clean_punctuation(text)

        if use_paddle:
            try:
                jieba.enable_paddle()
                words = jieba.lcut(cleaned_text, use_paddle=True)
            except Exception:
                words = jieba.lcut(cleaned_text)
        else:
            words = jieba.lcut(cleaned_text)

        words = [word.strip() for word in words if word.strip()]

        words = [word for word in words if self._is_valid_word(word)]

        if use_stopwords:
            stopwords = self._get_all_stopwords()
            words = [word for word in words if word not in stopwords]

        return words

    @classmethod
    def _clean_punctuation(cls, text: str) -> str:
        """
        清理文本中的标点符号和特殊字符

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        text = cls._PUNCTUATION_PATTERN.sub(' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def _is_valid_word(word: str) -> bool:
        """
        判断词语是否有效（过滤标点符号、纯数字、空白字符等）

        Args:
            word: 词语

        Returns:
            是否有效
        """
        if not word or not word.strip():
            return False

        word = word.strip()

        if re.match(r'^[\d\s]+$', word):
            return False

        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in word)
        has_english = any(c.isalpha() for c in word)

        if has_chinese or has_english:
            return True

        return False

    def word_frequency(self, text: str, top_n: Optional[int] = None,
                       use_stopwords: bool = True,
                       min_length: int = 1) -> List[Tuple[str, int]]:
        """
        词频统计

        Args:
            text: 输入文本
            top_n: 返回前N个高频词，None表示返回全部
            use_stopwords: 是否过滤停用词
            min_length: 词语最小长度

        Returns:
            [(词语, 词频)] 按词频降序排列
        """
        words = self.segment(text, use_stopwords=use_stopwords)

        if min_length > 1:
            words = [word for word in words if len(word) >= min_length]

        word_counts = Counter(words)

        if top_n:
            return word_counts.most_common(top_n)
        else:
            return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    def word_count(self, text: str, use_stopwords: bool = False) -> Dict:
        """
        统计词语信息

        Args:
            text: 输入文本
            use_stopwords: 是否排除停用词

        Returns:
            统计信息字典
        """
        all_words = self.segment(text, use_stopwords=False)
        total_chars = len(text.replace("\n", "").replace(" ", ""))
        total_words = len(all_words)

        if use_stopwords:
            filtered_words = self.segment(text, use_stopwords=True)
            stopwords_count = total_words - len(filtered_words)
            valid_words = len(filtered_words)
            unique_words = len(set(filtered_words))
        else:
            stopwords_count = 0
            valid_words = total_words
            unique_words = len(set(all_words))

        return {
            "total_chars": total_chars,
            "total_words": total_words,
            "valid_words": valid_words,
            "unique_words": unique_words,
            "stopwords_count": stopwords_count,
        }

    def extract_keywords(self, text: str, top_n: int = 10,
                         use_stopwords: bool = True,
                         min_length: int = 2) -> List[Tuple[str, float]]:
        """
        基于词频提取关键词

        Args:
            text: 输入文本
            top_n: 关键词数量
            use_stopwords: 是否过滤停用词
            min_length: 词语最小长度

        Returns:
            [(关键词, 权重)] 列表
        """
        word_freq = self.word_frequency(text, top_n=None,
                                        use_stopwords=use_stopwords,
                                        min_length=min_length)

        if not word_freq:
            return []

        max_freq = word_freq[0][1] if word_freq else 1

        keywords = []
        for word, freq in word_freq[:top_n]:
            weight = freq / max_freq if max_freq > 0 else 0
            keywords.append((word, weight))

        return keywords

    def add_custom_dictionary(self, dict_path: str):
        """
        添加自定义词典

        Args:
            dict_path: 词典文件路径
        """
        jieba.load_userdict(dict_path)

    def add_word(self, word: str, freq: Optional[int] = None,
                 tag: Optional[str] = None):
        """
        添加单个词语到词典

        Args:
            word: 词语
            freq: 词频
            tag: 词性
        """
        if freq is not None and tag is not None:
            jieba.add_word(word, freq=freq, tag=tag)
        elif freq is not None:
            jieba.add_word(word, freq=freq)
        else:
            jieba.add_word(word)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本，去除特殊字符

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
