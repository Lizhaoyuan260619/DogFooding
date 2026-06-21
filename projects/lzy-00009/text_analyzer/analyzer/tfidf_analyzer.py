"""
TF-IDF 关键词提取模块 - 支持多文档处理
"""
import math
from typing import List, Dict, Tuple, Optional
from collections import Counter

from text_analyzer.analyzer.chinese_analyzer import ChineseTextAnalyzer
from text_analyzer.analyzer.english_analyzer import EnglishTextAnalyzer


class TfidfAnalyzer:
    """TF-IDF 分析器"""

    def __init__(self, language: str = "auto", use_stopwords: bool = True):
        self.language = language
        self.use_stopwords = use_stopwords
        self.chinese_analyzer = ChineseTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()
        self._idf_cache: Dict[str, float] = {}
        self._doc_count: int = 0

    def _tokenize(self, text: str, language: str = "auto") -> List[str]:
        """
        对文本进行分词

        Args:
            text: 输入文本
            language: 语言类型

        Returns:
            分词结果列表
        """
        if language == "auto":
            language = self._detect_language(text)

        if language == "chinese":
            return self.chinese_analyzer.segment(text, use_stopwords=self.use_stopwords)
        else:
            words = self.english_analyzer.tokenize(text, use_stopwords=self.use_stopwords)
            return self.english_analyzer.stem(words)

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        检测文本语言

        Args:
            text: 输入文本

        Returns:
            'chinese' 或 'english'
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())

        total = chinese_chars + english_chars
        if total == 0:
            return "english"

        chinese_ratio = chinese_chars / total
        return "chinese" if chinese_ratio > 0.3 else "english"

    def compute_tf(self, words: List[str]) -> Dict[str, float]:
        """
        计算词频 (Term Frequency)

        TF = 某个词在文档中出现的次数 / 文档中总词数

        Args:
            words: 词语列表

        Returns:
            {词语: TF值} 字典
        """
        if not words:
            return {}

        word_counts = Counter(words)
        total_words = len(words)

        tf = {}
        for word, count in word_counts.items():
            tf[word] = count / total_words

        return tf

    def compute_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """
        计算逆文档频率 (Inverse Document Frequency)

        IDF = log(总文档数 / (包含该词的文档数 + 1))

        Args:
            documents: 文档列表，每个文档是词语列表

        Returns:
            {词语: IDF值} 字典
        """
        total_docs = len(documents)
        if total_docs == 0:
            return {}

        idf = {}
        doc_freq = Counter()

        for words in documents:
            unique_words = set(words)
            for word in unique_words:
                doc_freq[word] += 1

        for word, freq in doc_freq.items():
            idf[word] = math.log(total_docs / (freq + 1)) + 1

        self._idf_cache = idf
        self._doc_count = total_docs

        return idf

    def compute_tfidf(self, documents: List[str],
                      doc_names: Optional[List[str]] = None) -> List[Dict[str, float]]:
        """
        计算多篇文档的TF-IDF值

        Args:
            documents: 文档内容列表
            doc_names: 文档名称列表

        Returns:
            每篇文档的TF-IDF字典列表
        """
        if doc_names is None:
            doc_names = [f"doc_{i}" for i in range(len(documents))]

        tokenized_docs = []
        for doc in documents:
            lang = self.language if self.language != "auto" else self._detect_language(doc)
            words = self._tokenize(doc, language=lang)
            tokenized_docs.append(words)

        idf = self.compute_idf(tokenized_docs)

        tfidf_results = []
        for words in tokenized_docs:
            tf = self.compute_tf(words)
            tfidf = {}
            for word, tf_value in tf.items():
                idf_value = idf.get(word, 0)
                tfidf[word] = tf_value * idf_value
            tfidf_results.append(tfidf)

        return tfidf_results

    def extract_keywords(self, documents: List[str],
                         doc_names: Optional[List[str]] = None,
                         top_n: int = 10) -> List[List[Tuple[str, float]]]:
        """
        提取每篇文档的关键词

        Args:
            documents: 文档内容列表
            doc_names: 文档名称列表
            top_n: 每个文档提取的关键词数量

        Returns:
            每篇文档的关键词列表 [(词语, TF-IDF值)]
        """
        tfidf_results = self.compute_tfidf(documents, doc_names)

        keywords_list = []
        for tfidf in tfidf_results:
            sorted_items = sorted(tfidf.items(), key=lambda x: x[1], reverse=True)
            keywords_list.append(sorted_items[:top_n])

        return keywords_list

    def get_keywords_dict(self, documents: List[str],
                          doc_names: Optional[List[str]] = None,
                          top_n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """
        获取以文档名为键的关键词字典

        Args:
            documents: 文档内容列表
            doc_names: 文档名称列表
            top_n: 每个文档提取的关键词数量

        Returns:
            {文档名: [(词语, TF-IDF值)]} 字典
        """
        if doc_names is None:
            doc_names = [f"doc_{i}" for i in range(len(documents))]

        keywords_list = self.extract_keywords(documents, doc_names, top_n)

        result = {}
        for name, keywords in zip(doc_names, keywords_list):
            result[name] = keywords

        return result


class SklearnTfidfAnalyzer:
    """基于 scikit-learn 的 TF-IDF 分析器（性能更好）"""

    def __init__(self, language: str = "auto", use_stopwords: bool = True,
                 max_features: int = 1000):
        self.language = language
        self.use_stopwords = use_stopwords
        self.max_features = max_features
        self.chinese_analyzer = ChineseTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()

    def _preprocess_chinese(self, text: str) -> str:
        """中文文本预处理，分词后用空格连接"""
        words = self.chinese_analyzer.segment(text, use_stopwords=self.use_stopwords)
        return " ".join(words)

    def _preprocess_english(self, text: str) -> str:
        """英文文本预处理"""
        words = self.english_analyzer.tokenize(text, use_stopwords=self.use_stopwords)
        words = self.english_analyzer.stem(words)
        return " ".join(words)

    def _preprocess(self, documents: List[str]) -> List[str]:
        """文本预处理"""
        processed = []
        for doc in documents:
            if self.language == "auto":
                lang = self._detect_language(doc)
            else:
                lang = self.language

            if lang == "chinese":
                processed.append(self._preprocess_chinese(doc))
            else:
                processed.append(self._preprocess_english(doc))
        return processed

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

    def extract_keywords(self, documents: List[str],
                         doc_names: Optional[List[str]] = None,
                         top_n: int = 10) -> List[List[Tuple[str, float]]]:
        """
        使用 scikit-learn 提取关键词

        Args:
            documents: 文档内容列表
            doc_names: 文档名称列表
            top_n: 每个文档提取的关键词数量

        Returns:
            每篇文档的关键词列表 [(词语, TF-IDF值)]
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            print("警告: scikit-learn 未安装，使用纯Python实现")
            analyzer = TfidfAnalyzer(self.language, self.use_stopwords)
            return analyzer.extract_keywords(documents, doc_names, top_n)

        if doc_names is None:
            doc_names = [f"doc_{i}" for i in range(len(documents))]

        processed_docs = self._preprocess(documents)

        vectorizer = TfidfVectorizer(max_features=self.max_features)
        tfidf_matrix = vectorizer.fit_transform(processed_docs)
        feature_names = vectorizer.get_feature_names_out()

        results = []
        for i in range(len(documents)):
            row = tfidf_matrix.getrow(i).toarray()[0]
            tfidf_dict = {}
            for j, value in enumerate(row):
                if value > 0:
                    tfidf_dict[feature_names[j]] = value

            sorted_items = sorted(tfidf_dict.items(), key=lambda x: x[1], reverse=True)
            results.append(sorted_items[:top_n])

        return results

    def compute_similarity_matrix(self, documents: List[str]) -> List[List[float]]:
        """
        计算文档间的余弦相似度矩阵

        Args:
            documents: 文档内容列表

        Returns:
            相似度矩阵
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            print("警告: scikit-learn 未安装")
            return []

        processed_docs = self._preprocess(documents)

        vectorizer = TfidfVectorizer(max_features=self.max_features)
        tfidf_matrix = vectorizer.fit_transform(processed_docs)

        similarity_matrix = cosine_similarity(tfidf_matrix)

        return similarity_matrix.tolist()
