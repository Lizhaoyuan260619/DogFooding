"""
英文文本分析模块 - 分词、词干提取、词频统计、停用词过滤
"""
import re
from typing import List, Dict, Tuple, Optional
from collections import Counter

from text_analyzer.utils.stopwords import stopwords_manager


class EnglishTextAnalyzer:
    """英文文本分析器"""

    _nltk_data_ensured = False

    def __init__(self, stemmer_type: str = "porter"):
        self._stopwords = stopwords_manager.get_english_stopwords()
        self._custom_stopwords = set()
        self._stemmer_type = stemmer_type
        self._stemmer = None
        self._nltk_available = False
        self._init_nltk()

    @classmethod
    def _ensure_nltk_data(cls):
        """
        确保NLTK必要数据已下载，首次运行时自动下载

        下载的数据包括:
        - punkt: 句子分割器
        - punkt_tab: 新版句子分割器 (NLTK 3.9+)
        - stopwords: 停用词表
        """
        if cls._nltk_data_ensured:
            return

        try:
            import nltk

            required_resources = [
                ('tokenizers/punkt', 'punkt'),
                ('tokenizers/punkt_tab', 'punkt_tab'),
                ('corpora/stopwords', 'stopwords'),
            ]

            for resource_path, resource_name in required_resources:
                try:
                    nltk.data.find(resource_path)
                except LookupError:
                    try:
                        nltk.download(resource_name, quiet=True)
                    except Exception:
                        pass

            cls._nltk_data_ensured = True

        except ImportError:
            pass

    def _init_nltk(self):
        """初始化NLTK相关组件"""
        try:
            import nltk
            self._ensure_nltk_data()
            self._stemmer = self._get_stemmer(self._stemmer_type)
            self._nltk_available = True
        except ImportError:
            self._nltk_available = False
            self._stemmer = None

    @staticmethod
    def _get_stemmer(stemmer_type: str):
        """
        获取词干提取器

        Args:
            stemmer_type: 词干提取器类型 (porter, lancaster, snowball)

        Returns:
            词干提取器实例
        """
        try:
            from nltk.stem import PorterStemmer, LancasterStemmer, SnowballStemmer

            if stemmer_type == "porter":
                return PorterStemmer()
            elif stemmer_type == "lancaster":
                return LancasterStemmer()
            elif stemmer_type == "snowball":
                return SnowballStemmer("english")
            else:
                return PorterStemmer()
        except ImportError:
            print("警告: nltk 未安装，词干提取功能将不可用")
            return None

    def add_stopwords(self, words: List[str]):
        """
        添加自定义停用词

        Args:
            words: 停用词列表
        """
        self._custom_stopwords.update([w.lower() for w in words])

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
                    word = line.strip().lower()
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

    def tokenize(self, text: str, use_stopwords: bool = True,
                 to_lower: bool = True) -> List[str]:
        """
        英文分词

        Args:
            text: 输入文本
            use_stopwords: 是否过滤停用词
            to_lower: 是否转换为小写

        Returns:
            分词结果列表
        """
        if to_lower:
            text = text.lower()

        words = self._do_tokenize(text)
        words = [word for word in words if re.match(r'^[a-zA-Z]+$', word)]

        if use_stopwords:
            stopwords = self._get_all_stopwords()
            words = [word for word in words if word not in stopwords]

        return words

    def _do_tokenize(self, text: str) -> List[str]:
        """
        执行分词，优先使用NLTK，失败时降级到正则表达式

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        if self._nltk_available:
            try:
                import nltk
                self._ensure_nltk_data()
                return nltk.word_tokenize(text)
            except Exception:
                pass

        return re.findall(r'\b[a-zA-Z]+\b', text)

    def stem(self, words: List[str]) -> List[str]:
        """
        词干提取

        Args:
            words: 词语列表

        Returns:
            词干列表
        """
        if self._stemmer is None:
            return words

        return [self._stemmer.stem(word) for word in words]

    def word_frequency(self, text: str, top_n: Optional[int] = None,
                       use_stopwords: bool = True,
                       use_stemming: bool = True,
                       min_length: int = 2) -> List[Tuple[str, int]]:
        """
        词频统计

        Args:
            text: 输入文本
            top_n: 返回前N个高频词，None表示返回全部
            use_stopwords: 是否过滤停用词
            use_stemming: 是否使用词干提取
            min_length: 词语最小长度

        Returns:
            [(词语, 词频)] 按词频降序排列
        """
        words = self.tokenize(text, use_stopwords=use_stopwords)

        if use_stemming:
            words = self.stem(words)

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
        all_words = self.tokenize(text, use_stopwords=False)
        total_chars = len(text.replace("\n", "").replace(" ", ""))
        total_words = len(all_words)

        sentences = self._count_sentences(text)
        paragraphs = self._count_paragraphs(text)

        if use_stopwords:
            filtered_words = self.tokenize(text, use_stopwords=True)
            stopwords_count = total_words - len(filtered_words)
            valid_words = len(filtered_words)
            unique_words = len(set(filtered_words))
        else:
            stopwords_count = 0
            valid_words = total_words
            unique_words = len(set(all_words))

        avg_word_length = total_chars / total_words if total_words > 0 else 0
        avg_sentence_length = total_words / sentences if sentences > 0 else 0

        return {
            "total_chars": total_chars,
            "total_words": total_words,
            "valid_words": valid_words,
            "unique_words": unique_words,
            "stopwords_count": stopwords_count,
            "sentences": sentences,
            "paragraphs": paragraphs,
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
        }

    @staticmethod
    def _count_sentences(text: str) -> int:
        """统计句子数量"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    @staticmethod
    def _count_paragraphs(text: str) -> int:
        """统计段落数量"""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return len(paragraphs)

    def extract_keywords(self, text: str, top_n: int = 10,
                         use_stopwords: bool = True,
                         use_stemming: bool = True,
                         min_length: int = 3) -> List[Tuple[str, float]]:
        """
        基于词频提取关键词

        Args:
            text: 输入文本
            top_n: 关键词数量
            use_stopwords: 是否过滤停用词
            use_stemming: 是否使用词干提取
            min_length: 词语最小长度

        Returns:
            [(关键词, 权重)] 列表
        """
        word_freq = self.word_frequency(text, top_n=None,
                                        use_stopwords=use_stopwords,
                                        use_stemming=use_stemming,
                                        min_length=min_length)

        if not word_freq:
            return []

        max_freq = word_freq[0][1] if word_freq else 1

        keywords = []
        for word, freq in word_freq[:top_n]:
            weight = freq / max_freq if max_freq > 0 else 0
            keywords.append((word, weight))

        return keywords

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本，去除特殊字符

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        text = re.sub(r'[^a-zA-Z0-9\s.,!?\'"-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
