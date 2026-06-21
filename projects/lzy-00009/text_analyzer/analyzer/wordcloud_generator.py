"""
词云图生成模块 - 根据词频数据生成PNG格式词云图
"""
import os
from typing import Dict, List, Tuple, Optional
from collections import Counter

from text_analyzer.config import (
    DEFAULT_WORDCLOUD_WIDTH,
    DEFAULT_WORDCLOUD_HEIGHT,
    DEFAULT_WORDCLOUD_BG_COLOR,
    OUTPUT_DIR,
)


class WordCloudGenerator:
    """词云图生成器"""

    def __init__(self, width: int = DEFAULT_WORDCLOUD_WIDTH,
                 height: int = DEFAULT_WORDCLOUD_HEIGHT,
                 background_color: str = DEFAULT_WORDCLOUD_BG_COLOR,
                 font_path: Optional[str] = None,
                 max_words: int = 200):
        self.width = width
        self.height = height
        self.background_color = background_color
        self.font_path = font_path
        self.max_words = max_words

        if font_path is None:
            self.font_path = self._find_chinese_font()

    @staticmethod
    def _find_chinese_font() -> Optional[str]:
        """
        尝试自动查找中文字体

        Returns:
            字体文件路径或None
        """
        common_font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyh.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]

        for font_path in common_font_paths:
            if os.path.exists(font_path):
                return font_path

        return None

    def generate_from_frequencies(self, word_freq: Dict[str, int],
                                  output_path: str) -> str:
        """
        根据词频字典生成词云图

        Args:
            word_freq: 词频字典 {词语: 词频}
            output_path: 输出图片路径

        Returns:
            生成的图片路径
        """
        try:
            from wordcloud import WordCloud
        except ImportError:
            raise ImportError("wordcloud 库未安装，请运行 pip install wordcloud")

        wc = WordCloud(
            width=self.width,
            height=self.height,
            background_color=self.background_color,
            font_path=self.font_path,
            max_words=self.max_words,
            collocations=False,
        )

        wc.generate_from_frequencies(word_freq)

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        wc.to_file(output_path)

        return output_path

    def generate_from_text(self, text: str, output_path: str,
                           language: str = "auto",
                           use_stopwords: bool = True) -> str:
        """
        从文本生成词云图

        Args:
            text: 输入文本
            output_path: 输出图片路径
            language: 语言类型
            use_stopwords: 是否过滤停用词

        Returns:
            生成的图片路径
        """
        word_freq = self._compute_word_frequency(text, language, use_stopwords)
        return self.generate_from_frequencies(word_freq, output_path)

    def generate_from_words(self, words: List[str], output_path: str) -> str:
        """
        从词语列表生成词云图

        Args:
            words: 词语列表
            output_path: 输出图片路径

        Returns:
            生成的图片路径
        """
        word_counts = Counter(words)
        word_freq = dict(word_counts)
        return self.generate_from_frequencies(word_freq, output_path)

    @staticmethod
    def _compute_word_frequency(text: str, language: str = "auto",
                                use_stopwords: bool = True) -> Dict[str, int]:
        """
        计算词频

        Args:
            text: 输入文本
            language: 语言类型
            use_stopwords: 是否过滤停用词

        Returns:
            词频字典
        """
        from text_analyzer.analyzer.chinese_analyzer import ChineseTextAnalyzer
        from text_analyzer.analyzer.english_analyzer import EnglishTextAnalyzer

        if language == "auto":
            language = WordCloudGenerator._detect_language(text)

        if language == "chinese":
            analyzer = ChineseTextAnalyzer()
            words = analyzer.segment(text, use_stopwords=use_stopwords)
        else:
            analyzer = EnglishTextAnalyzer()
            words = analyzer.tokenize(text, use_stopwords=use_stopwords)
            words = analyzer.stem(words)

        word_counts = Counter(words)
        return dict(word_counts)

    @staticmethod
    def _detect_language(text: str) -> str:
        """检测文本语言"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total = chinese_chars + english_chars
        if total == 0:
            return "english"
        chinese_ratio = chinese_chars / total
        return "chinese" if chinese_ratio > 0.3 else "english"

    def generate_batch(self, word_freq_list: List[Dict[str, int]],
                       output_dir: str,
                       file_prefix: str = "wordcloud") -> List[str]:
        """
        批量生成词云图

        Args:
            word_freq_list: 词频字典列表
            output_dir: 输出目录
            file_prefix: 文件名前缀

        Returns:
            生成的图片路径列表
        """
        os.makedirs(output_dir, exist_ok=True)

        output_paths = []
        for i, word_freq in enumerate(word_freq_list):
            output_path = os.path.join(output_dir, f"{file_prefix}_{i + 1}.png")
            path = self.generate_from_frequencies(word_freq, output_path)
            output_paths.append(path)

        return output_paths

    def set_width(self, width: int):
        """设置词云图宽度"""
        self.width = width

    def set_height(self, height: int):
        """设置词云图高度"""
        self.height = height

    def set_background_color(self, color: str):
        """设置背景颜色"""
        self.background_color = color

    def set_font_path(self, font_path: str):
        """设置字体路径"""
        self.font_path = font_path

    def set_max_words(self, max_words: int):
        """设置最大词数"""
        self.max_words = max_words
