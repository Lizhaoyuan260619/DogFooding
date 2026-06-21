"""
文档相似度比较模块 - 基于余弦相似度算法
"""
import math
from typing import List, Dict, Tuple, Optional
from collections import Counter

from text_analyzer.analyzer.chinese_analyzer import ChineseTextAnalyzer
from text_analyzer.analyzer.english_analyzer import EnglishTextAnalyzer
from text_analyzer.analyzer.tfidf_analyzer import TfidfAnalyzer


class SimilarityAnalyzer:
    """文档相似度分析器"""

    def __init__(self, language: str = "auto", use_stopwords: bool = True):
        self.language = language
        self.use_stopwords = use_stopwords
        self.chinese_analyzer = ChineseTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()
        self.tfidf_analyzer = TfidfAnalyzer(language, use_stopwords)

    def _tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        lang = self.language if self.language != "auto" else self._detect_language(text)

        if lang == "chinese":
            return self.chinese_analyzer.segment(text, use_stopwords=self.use_stopwords)
        else:
            words = self.english_analyzer.tokenize(text, use_stopwords=self.use_stopwords)
            return self.english_analyzer.stem(words)

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

    @staticmethod
    def _create_word_vector(words1: List[str], words2: List[str]) -> Tuple[List[int], List[int]]:
        """
        创建词向量

        Args:
            words1: 文本1的词语列表
            words2: 文本2的词语列表

        Returns:
            (向量1, 向量2)
        """
        all_words = set(words1) | set(words2)
        word_to_idx = {word: i for i, word in enumerate(all_words)}

        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)

        for word in words1:
            vector1[word_to_idx[word]] += 1

        for word in words2:
            vector2[word_to_idx[word]] += 1

        return vector1, vector2

    @staticmethod
    def _cosine_similarity(vector1: List[int], vector2: List[int]) -> float:
        """
        计算余弦相似度

        Args:
            vector1: 向量1
            vector2: 向量2

        Returns:
            余弦相似度值 (0-1)
        """
        dot_product = sum(a * b for a, b in zip(vector1, vector2))

        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def cosine_similarity_text(self, text1: str, text2: str) -> float:
        """
        计算两段文本的余弦相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度值 (0-1)
        """
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)

        vector1, vector2 = self._create_word_vector(words1, words2)

        return self._cosine_similarity(vector1, vector2)

    def cosine_similarity_percentage(self, text1: str, text2: str) -> str:
        """
        以百分比形式返回相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            百分比形式的相似度字符串
        """
        similarity = self.cosine_similarity_text(text1, text2)
        percentage = similarity * 100
        return f"{percentage:.2f}%"

    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        计算Jaccard相似度

        J(A,B) = |A∩B| / |A∪B|

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            Jaccard相似度值 (0-1)
        """
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))

        if not words1 and not words2:
            return 1.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        基于TF-IDF的余弦相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度值 (0-1)
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            lang = self.language if self.language != "auto" else self._detect_language(text1)

            if lang == "chinese":
                words1 = self.chinese_analyzer.segment(text1, use_stopwords=self.use_stopwords)
                words2 = self.chinese_analyzer.segment(text2, use_stopwords=self.use_stopwords)
                doc1 = " ".join(words1)
                doc2 = " ".join(words2)
            else:
                words1 = self.english_analyzer.tokenize(text1, use_stopwords=self.use_stopwords)
                words1 = self.english_analyzer.stem(words1)
                words2 = self.english_analyzer.tokenize(text2, use_stopwords=self.use_stopwords)
                words2 = self.english_analyzer.stem(words2)
                doc1 = " ".join(words1)
                doc2 = " ".join(words2)

            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([doc1, doc2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return float(similarity)
        except ImportError:
            return self.cosine_similarity_text(text1, text2)

    def similarity_matrix(self, documents: List[str],
                          doc_names: Optional[List[str]] = None,
                          method: str = "tfidf") -> Dict:
        """
        计算多篇文档的相似度矩阵

        Args:
            documents: 文档内容列表
            doc_names: 文档名称列表
            method: 计算方法 (cosine, jaccard, tfidf)

        Returns:
            包含文档名和相似度矩阵的字典
        """
        n = len(documents)
        if doc_names is None:
            doc_names = [f"文档{i + 1}" for i in range(n)]

        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                if method == "jaccard":
                    sim = self.jaccard_similarity(documents[i], documents[j])
                elif method == "cosine":
                    sim = self.cosine_similarity_text(documents[i], documents[j])
                else:
                    sim = self.tfidf_similarity(documents[i], documents[j])

                matrix[i][j] = sim
                matrix[j][i] = sim

        return {
            "doc_names": doc_names,
            "matrix": matrix,
        }

    def similarity_matrix_percentage(self, documents: List[str],
                                     doc_names: Optional[List[str]] = None,
                                     method: str = "tfidf") -> Dict:
        """
        以百分比形式返回相似度矩阵

        Args:
            documents: 文档内容列表
            doc_names: 文档名称列表
            method: 计算方法

        Returns:
            包含文档名和百分比相似度矩阵的字典
        """
        result = self.similarity_matrix(documents, doc_names, method)

        percentage_matrix = []
        for row in result["matrix"]:
            percentage_row = [f"{val * 100:.2f}%" for val in row]
            percentage_matrix.append(percentage_row)

        result["matrix_percentage"] = percentage_matrix
        return result

    def find_similar_documents(self, target_doc: str, documents: List[str],
                               doc_names: Optional[List[str]] = None,
                               top_n: int = 5,
                               method: str = "tfidf") -> List[Tuple[str, float]]:
        """
        查找与目标文档最相似的文档

        Args:
            target_doc: 目标文档
            documents: 待比较的文档列表
            doc_names: 文档名称列表
            top_n: 返回最相似的前N个
            method: 计算方法

        Returns:
            [(文档名, 相似度)] 按相似度降序排列
        """
        if doc_names is None:
            doc_names = [f"文档{i + 1}" for i in range(len(documents))]

        similarities = []
        for i, doc in enumerate(documents):
            if method == "jaccard":
                sim = self.jaccard_similarity(target_doc, doc)
            elif method == "cosine":
                sim = self.cosine_similarity_text(target_doc, doc)
            else:
                sim = self.tfidf_similarity(target_doc, doc)

            similarities.append((doc_names[i], sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
