"""
命令行接口 (CLI) - 文本分析工具的主入口
"""
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional

from text_analyzer.config import OUTPUT_DIR, DEFAULT_TOP_N, DEFAULT_TFIDF_TOP_N
from text_analyzer.database import db_manager
from text_analyzer.utils.file_utils import read_file, scan_folder, read_files_batch, detect_language, get_file_info
from text_analyzer.analyzer.chinese_analyzer import ChineseTextAnalyzer
from text_analyzer.analyzer.english_analyzer import EnglishTextAnalyzer
from text_analyzer.analyzer.tfidf_analyzer import SklearnTfidfAnalyzer
from text_analyzer.analyzer.similarity_analyzer import SimilarityAnalyzer
from text_analyzer.analyzer.wordcloud_generator import WordCloudGenerator
from text_analyzer.analyzer.entity_recognizer import EntityRecognizer
from text_analyzer.analyzer.sentiment_analyzer import SentimentAnalyzer
from text_analyzer.report.html_report import HTMLReportGenerator


class TextAnalyzerCLI:
    """文本分析命令行界面"""

    def __init__(self):
        self.chinese_analyzer = ChineseTextAnalyzer()
        self.english_analyzer = EnglishTextAnalyzer()
        self.tfidf_analyzer = SklearnTfidfAnalyzer()
        self.similarity_analyzer = SimilarityAnalyzer()
        self.wordcloud_generator = WordCloudGenerator()
        self.report_generator = HTMLReportGenerator()
        self.entity_recognizer = EntityRecognizer()
        self.sentiment_analyzer = SentimentAnalyzer()

    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                文本分析工具 v2.0.0                           ║
║           Text Analyzer Command Line Tool                    ║
╠══════════════════════════════════════════════════════════════╣
║  支持中英文文本分析 | TF-IDF关键词提取 | 文档相似度比较     ║
║  词云图生成 | HTML报告生成 | 实体识别 | 情感分析 | Web界面  ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def print_menu(self):
        """打印主菜单"""
        menu = """
请选择功能：

【1】 中文文本分析 - 分词、词频统计
【2】 英文文本分析 - 分词、词干提取、词频统计
【3】 TF-IDF关键词提取 - 多文档关键词提取
【4】 文档相似度比较 - 余弦相似度计算
【5】 词云图生成 - 根据词频生成词云
【6】 生成HTML报告 - 整合所有分析结果
【7】 批量文件处理 - 批量分析文件夹中的文件
【8】 历史记录查询 - 查看分析历史
【9】 数据库统计 - 查看数据库统计信息
【10】实体识别 - 识别人物、组织、地点、时间、专有名词
【11】情感分析 - 正负面情感分类及置信度评分
【12】启动Web服务 - 图形化界面分析
【0】 退出程序

请输入选项编号："""
        print(menu)

    def run(self):
        """运行CLI主循环"""
        self.print_banner()

        while True:
            try:
                self.print_menu()
                choice = input().strip()

                if choice == "1":
                    self.chinese_analysis_menu()
                elif choice == "2":
                    self.english_analysis_menu()
                elif choice == "3":
                    self.tfidf_analysis_menu()
                elif choice == "4":
                    self.similarity_menu()
                elif choice == "5":
                    self.wordcloud_menu()
                elif choice == "6":
                    self.html_report_menu()
                elif choice == "7":
                    self.batch_process_menu()
                elif choice == "8":
                    self.history_menu()
                elif choice == "9":
                    self.show_db_stats()
                elif choice == "10":
                    self.entity_recognition_menu()
                elif choice == "11":
                    self.sentiment_analysis_menu()
                elif choice == "12":
                    self.start_web_server()
                elif choice == "0":
                    print("\n感谢使用文本分析工具，再见！")
                    break
                else:
                    print("\n无效的选项，请重新选择！")

                input("\n按回车键继续...")

            except KeyboardInterrupt:
                print("\n\n检测到中断，正在退出...")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")
                input("\n按回车键继续...")

    def chinese_analysis_menu(self):
        """中文文本分析菜单"""
        print("\n" + "=" * 50)
        print("【中文文本分析】")
        print("=" * 50)

        file_path = input("请输入文本文件路径：").strip().strip('"').strip("'")
        if not file_path or not os.path.exists(file_path):
            print("文件不存在！")
            return

        try:
            text = read_file(file_path)
            file_info = get_file_info(file_path)
            print(f"\n文件: {file_info['name']}")
            print(f"大小: {file_info['size_human']}")

            lang = detect_language(text)
            print(f"检测语言: {lang}")

            top_n_input = input(f"请输入显示前N个高频词 (默认{DEFAULT_TOP_N}): ").strip()
            top_n = int(top_n_input) if top_n_input.isdigit() else DEFAULT_TOP_N

            use_stopwords_input = input("是否过滤停用词？(y/n，默认y): ").strip().lower()
            use_stopwords = use_stopwords_input != "n"

            custom_stopwords = input("自定义停用词文件路径 (可选，直接回车跳过): ").strip()
            if custom_stopwords and os.path.exists(custom_stopwords):
                self.chinese_analyzer.load_stopwords_file(custom_stopwords)

            print("\n正在分析...")
            word_freq = self.chinese_analyzer.word_frequency(
                text, top_n=top_n, use_stopwords=use_stopwords, min_length=2
            )
            word_stats = self.chinese_analyzer.word_count(text, use_stopwords=use_stopwords)

            print("\n" + "-" * 50)
            print("词频统计结果")
            print("-" * 50)
            print(f"总字符数: {word_stats['total_chars']}")
            print(f"总词数: {word_stats['total_words']}")
            print(f"有效词数: {word_stats['valid_words']}")
            print(f"唯一词数: {word_stats['unique_words']}")
            if use_stopwords:
                print(f"停用词数: {word_stats['stopwords_count']}")

            print("\n" + "-" * 50)
            print(f"Top {top_n} 高频词")
            print("-" * 50)
            print(f"{'排名':<6}{'词语':<15}{'词频':<10}{'占比':<10}")
            print("-" * 50)

            total_freq = sum(freq for _, freq in word_freq)
            for i, (word, freq) in enumerate(word_freq, 1):
                percentage = (freq / total_freq * 100) if total_freq > 0 else 0
                print(f"{i:<6}{word:<15}{freq:<10}{percentage:.2f}%")

            save_db = input("\n是否保存到历史记录？(y/n，默认y): ").strip().lower()
            if save_db != "n":
                record_id = db_manager.add_analysis_record(
                    analysis_type="chinese_word_frequency",
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    parameters={"top_n": top_n, "use_stopwords": use_stopwords, "min_length": 2},
                    results={
                        "word_stats": word_stats,
                        "top_words": [{"word": w, "freq": f} for w, f in word_freq[:10]]
                    }
                )
                print(f"已保存到历史记录 (ID: {record_id})")

        except Exception as e:
            print(f"分析失败: {e}")

    def english_analysis_menu(self):
        """英文文本分析菜单"""
        print("\n" + "=" * 50)
        print("【英文文本分析】")
        print("=" * 50)

        file_path = input("请输入文本文件路径：").strip().strip('"').strip("'")
        if not file_path or not os.path.exists(file_path):
            print("文件不存在！")
            return

        try:
            text = read_file(file_path)
            file_info = get_file_info(file_path)
            print(f"\n文件: {file_info['name']}")
            print(f"大小: {file_info['size_human']}")

            top_n_input = input(f"请输入显示前N个高频词 (默认{DEFAULT_TOP_N}): ").strip()
            top_n = int(top_n_input) if top_n_input.isdigit() else DEFAULT_TOP_N

            use_stopwords_input = input("是否过滤停用词？(y/n，默认y): ").strip().lower()
            use_stopwords = use_stopwords_input != "n"

            use_stemming_input = input("是否使用词干提取？(y/n，默认y): ").strip().lower()
            use_stemming = use_stemming_input != "n"

            custom_stopwords = input("自定义停用词文件路径 (可选，直接回车跳过): ").strip()
            if custom_stopwords and os.path.exists(custom_stopwords):
                self.english_analyzer.load_stopwords_file(custom_stopwords)

            print("\n正在分析...")
            word_freq = self.english_analyzer.word_frequency(
                text, top_n=top_n, use_stopwords=use_stopwords,
                use_stemming=use_stemming, min_length=2
            )
            word_stats = self.english_analyzer.word_count(text, use_stopwords=use_stopwords)

            print("\n" + "-" * 50)
            print("词频统计结果")
            print("-" * 50)
            print(f"总字符数: {word_stats['total_chars']}")
            print(f"总词数: {word_stats['total_words']}")
            print(f"有效词数: {word_stats['valid_words']}")
            print(f"唯一词数: {word_stats['unique_words']}")
            print(f"句子数: {word_stats['sentences']}")
            print(f"段落数: {word_stats['paragraphs']}")
            print(f"平均词长: {word_stats['avg_word_length']}")
            print(f"平均句长: {word_stats['avg_sentence_length']}")
            if use_stopwords:
                print(f"停用词数: {word_stats['stopwords_count']}")

            print("\n" + "-" * 50)
            print(f"Top {top_n} 高频词")
            print("-" * 50)
            print(f"{'排名':<6}{'词语':<20}{'词频':<10}{'占比':<10}")
            print("-" * 50)

            total_freq = sum(freq for _, freq in word_freq)
            for i, (word, freq) in enumerate(word_freq, 1):
                percentage = (freq / total_freq * 100) if total_freq > 0 else 0
                print(f"{i:<6}{word:<20}{freq:<10}{percentage:.2f}%")

            save_db = input("\n是否保存到历史记录？(y/n，默认y): ").strip().lower()
            if save_db != "n":
                record_id = db_manager.add_analysis_record(
                    analysis_type="english_word_frequency",
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    parameters={
                        "top_n": top_n,
                        "use_stopwords": use_stopwords,
                        "use_stemming": use_stemming,
                        "min_length": 2
                    },
                    results={
                        "word_stats": word_stats,
                        "top_words": [{"word": w, "freq": f} for w, f in word_freq[:10]]
                    }
                )
                print(f"已保存到历史记录 (ID: {record_id})")

        except Exception as e:
            print(f"分析失败: {e}")

    def tfidf_analysis_menu(self):
        """TF-IDF关键词提取菜单"""
        print("\n" + "=" * 50)
        print("【TF-IDF关键词提取】")
        print("=" * 50)

        print("\n请选择输入方式：")
        print("1. 输入文件夹路径（批量处理）")
        print("2. 输入多个文件路径")
        choice = input("请选择 (默认1): ").strip()

        documents = []
        doc_names = []

        try:
            if choice == "2":
                print("\n请输入文件路径，每行一个，输入空行结束：")
                while True:
                    path = input().strip().strip('"').strip("'")
                    if not path:
                        break
                    if os.path.exists(path):
                        text = read_file(path)
                        documents.append(text)
                        doc_names.append(os.path.basename(path))
                    else:
                        print(f"文件不存在: {path}")
            else:
                folder_path = input("请输入文件夹路径：").strip().strip('"').strip("'")
                if not folder_path or not os.path.isdir(folder_path):
                    print("文件夹不存在！")
                    return

                file_paths = scan_folder(folder_path, extension=".txt")
                if not file_paths:
                    print("文件夹中没有找到txt文件！")
                    return

                print(f"\n找到 {len(file_paths)} 个文件")
                for path in file_paths:
                    text = read_file(path)
                    documents.append(text)
                    doc_names.append(os.path.basename(path))

            if len(documents) < 2:
                print("至少需要2个文档才能计算TF-IDF！")
                return

            top_n_input = input(f"请输入每篇文档提取关键词数量 (默认{DEFAULT_TFIDF_TOP_N}): ").strip()
            top_n = int(top_n_input) if top_n_input.isdigit() else DEFAULT_TFIDF_TOP_N

            print("\n正在计算TF-IDF...")
            keywords_list = self.tfidf_analyzer.extract_keywords(documents, doc_names, top_n)

            for i, (name, keywords) in enumerate(zip(doc_names, keywords_list)):
                print(f"\n{'=' * 50}")
                print(f"文档: {name}")
                print(f"{'=' * 50}")
                print(f"{'排名':<6}{'关键词':<20}{'TF-IDF值':<15}")
                print("-" * 50)
                for j, (word, value) in enumerate(keywords, 1):
                    print(f"{j:<6}{word:<20}{value:.6f}")

            save_db = input("\n是否保存到历史记录？(y/n，默认y): ").strip().lower()
            if save_db != "n":
                results = []
                for name, keywords in zip(doc_names, keywords_list):
                    results.append({
                        "doc_name": name,
                        "keywords": [{"word": w, "tfidf": v} for w, v in keywords]
                    })

                record_id = db_manager.add_analysis_record(
                    analysis_type="tfidf_keywords",
                    parameters={
                        "doc_count": len(documents),
                        "top_n": top_n,
                        "doc_names": doc_names
                    },
                    results={"documents": results}
                )
                print(f"已保存到历史记录 (ID: {record_id})")

            generate_report = input("\n是否生成HTML报告？(y/n，默认n): ").strip().lower()
            if generate_report == "y":
                self._generate_tfidf_report(doc_names, keywords_list)

        except Exception as e:
            print(f"分析失败: {e}")

    def similarity_menu(self):
        """文档相似度比较菜单"""
        print("\n" + "=" * 50)
        print("【文档相似度比较】")
        print("=" * 50)

        print("\n请选择比较方式：")
        print("1. 比较两个文件")
        print("2. 比较多个文件（生成相似度矩阵）")
        print("3. 从历史记录中选择文档比较")
        choice = input("请选择 (默认1): ").strip()

        try:
            if choice == "3":
                self._similarity_from_history()
            elif choice == "2":
                self._similarity_batch()
            else:
                self._similarity_two_files()

        except Exception as e:
            print(f"计算失败: {e}")

    def _similarity_two_files(self):
        """比较两个文件的相似度"""
        file1 = input("请输入第一个文件路径：").strip().strip('"').strip("'")
        file2 = input("请输入第二个文件路径：").strip().strip('"').strip("'")

        if not os.path.exists(file1) or not os.path.exists(file2):
            print("文件不存在！")
            return

        text1 = read_file(file1)
        text2 = read_file(file2)

        method = input("请选择相似度算法 (1: 余弦相似度 2: TF-IDF相似度 3: Jaccard相似度，默认2): ").strip()

        print("\n正在计算相似度...")
        if method == "1":
            similarity = self.similarity_analyzer.cosine_similarity_text(text1, text2)
            method_name = "余弦相似度"
        elif method == "3":
            similarity = self.similarity_analyzer.jaccard_similarity(text1, text2)
            method_name = "Jaccard相似度"
        else:
            similarity = self.similarity_analyzer.tfidf_similarity(text1, text2)
            method_name = "TF-IDF相似度"

        percentage = similarity * 100

        print("\n" + "=" * 50)
        print("相似度计算结果")
        print("=" * 50)
        print(f"文件1: {os.path.basename(file1)}")
        print(f"文件2: {os.path.basename(file2)}")
        print(f"算法: {method_name}")
        print(f"\n相似度: {percentage:.2f}%")

        if percentage >= 70:
            print("评价: 高度相似")
        elif percentage >= 40:
            print("评价: 中度相似")
        else:
            print("评价: 低度相似")

        save_db = input("\n是否保存到历史记录？(y/n，默认y): ").strip().lower()
        if save_db != "n":
            record_id = db_manager.add_analysis_record(
                analysis_type="document_similarity",
                parameters={
                    "file1": file1,
                    "file2": file2,
                    "method": method_name
                },
                results={"similarity": similarity, "percentage": f"{percentage:.2f}%"}
            )
            print(f"已保存到历史记录 (ID: {record_id})")

    def _similarity_batch(self):
        """批量比较多个文档的相似度"""
        folder_path = input("请输入文件夹路径：").strip().strip('"').strip("'")
        if not folder_path or not os.path.isdir(folder_path):
            print("文件夹不存在！")
            return

        file_paths = scan_folder(folder_path, extension=".txt")
        if not file_paths:
            print("文件夹中没有找到txt文件！")
            return

        if len(file_paths) < 2:
            print("至少需要2个文件！")
            return

        print(f"\n找到 {len(file_paths)} 个文件")

        documents = []
        doc_names = []
        for path in file_paths:
            text = read_file(path)
            documents.append(text)
            doc_names.append(os.path.basename(path))

        method = input("请选择相似度算法 (1: 余弦相似度 2: TF-IDF相似度，默认2): ").strip()
        method_name = "cosine" if method == "1" else "tfidf"

        print("\n正在计算相似度矩阵...")
        result = self.similarity_analyzer.similarity_matrix_percentage(
            documents, doc_names, method=method_name
        )

        print("\n" + "=" * 50)
        print("文档相似度矩阵")
        print("=" * 50)

        n = len(doc_names)
        header = f"{'':<15}" + "".join(f"{name[:12]:<15}" for name in doc_names)
        print(header)
        print("-" * (15 + n * 15))

        for i in range(n):
            row = f"{doc_names[i][:12]:<15}"
            for j in range(n):
                row += f"{result['matrix_percentage'][i][j]:<15}"
            print(row)

        save_db = input("\n是否保存到历史记录？(y/n，默认y): ").strip().lower()
        if save_db != "n":
            record_id = db_manager.add_analysis_record(
                analysis_type="similarity_matrix",
                parameters={
                    "doc_count": n,
                    "doc_names": doc_names,
                    "method": method_name
                },
                results={"matrix": result["matrix"]}
            )
            print(f"已保存到历史记录 (ID: {record_id})")

        generate_report = input("\n是否生成HTML报告？(y/n，默认n): ").strip().lower()
        if generate_report == "y":
            self._generate_similarity_report(doc_names, result["matrix"])

    def _similarity_from_history(self):
        """从历史记录中选择文档比较"""
        docs = db_manager.get_documents(limit=20)
        if not docs:
            print("没有找到文档记录！")
            return

        print("\n文档列表：")
        for i, doc in enumerate(docs, 1):
            print(f"[{i}] {doc['file_name']} - {doc['word_count']}词")

        idx1 = input("请选择第一个文档编号：").strip()
        idx2 = input("请选择第二个文档编号：").strip()

        if not idx1.isdigit() or not idx2.isdigit():
            print("无效的编号！")
            return

        idx1 = int(idx1) - 1
        idx2 = int(idx2) - 1

        if idx1 < 0 or idx1 >= len(docs) or idx2 < 0 or idx2 >= len(docs):
            print("编号超出范围！")
            return

        doc1 = db_manager.get_document_by_id(docs[idx1]["id"])
        doc2 = db_manager.get_document_by_id(docs[idx2]["id"])

        if not doc1 or not doc2 or not doc1.get("content") or not doc2.get("content"):
            print("文档内容不存在！")
            return

        similarity = self.similarity_analyzer.tfidf_similarity(doc1["content"], doc2["content"])
        percentage = similarity * 100

        print(f"\n文档1: {doc1['file_name']}")
        print(f"文档2: {doc2['file_name']}")
        print(f"相似度: {percentage:.2f}%")

    def wordcloud_menu(self):
        """词云图生成菜单"""
        print("\n" + "=" * 50)
        print("【词云图生成】")
        print("=" * 50)

        file_path = input("请输入文本文件路径：").strip().strip('"').strip("'")
        if not file_path or not os.path.exists(file_path):
            print("文件不存在！")
            return

        try:
            text = read_file(file_path)
            file_name = os.path.basename(file_path)

            width_input = input("词云图宽度 (默认800): ").strip()
            height_input = input("词云图高度 (默认600): ").strip()
            bg_color = input("背景颜色 (默认white): ").strip()
            font_path = input("字体文件路径 (可选，自动检测中文字体): ").strip()

            width = int(width_input) if width_input.isdigit() else 800
            height = int(height_input) if height_input.isdigit() else 600
            bg_color = bg_color if bg_color else "white"

            if font_path and os.path.exists(font_path):
                self.wordcloud_generator.set_font_path(font_path)

            self.wordcloud_generator.set_width(width)
            self.wordcloud_generator.set_height(height)
            self.wordcloud_generator.set_background_color(bg_color)

            output_name = input("输出文件名 (默认使用原文件名): ").strip()
            if not output_name:
                output_name = os.path.splitext(file_name)[0] + "_wordcloud.png"

            output_path = os.path.join(OUTPUT_DIR, output_name)

            print("\n正在生成词云图...")
            self.wordcloud_generator.generate_from_text(
                text, output_path, language="auto", use_stopwords=True
            )

            print(f"\n词云图已生成: {output_path}")

            save_db = input("\n是否保存到历史记录？(y/n，默认y): ").strip().lower()
            if save_db != "n":
                record_id = db_manager.add_analysis_record(
                    analysis_type="wordcloud",
                    file_path=file_path,
                    file_name=file_name,
                    parameters={
                        "width": width,
                        "height": height,
                        "background_color": bg_color,
                        "output_path": output_path
                    },
                    results={"output_path": output_path}
                )
                print(f"已保存到历史记录 (ID: {record_id})")

        except ImportError as e:
            print(f"缺少依赖库: {e}")
            print("请运行: pip install wordcloud")
        except Exception as e:
            print(f"生成失败: {e}")

    def html_report_menu(self):
        """HTML报告生成菜单"""
        print("\n" + "=" * 50)
        print("【HTML报告生成】")
        print("=" * 50)

        folder_path = input("请输入包含文本文件的文件夹路径：").strip().strip('"').strip("'")
        if not folder_path or not os.path.isdir(folder_path):
            print("文件夹不存在！")
            return

        try:
            file_paths = scan_folder(folder_path, extension=".txt")
            if not file_paths:
                print("文件夹中没有找到txt文件！")
                return

            print(f"\n找到 {len(file_paths)} 个文件")
            print("正在生成完整分析报告...")

            report_title = input("请输入报告标题 (默认: 文本分析报告): ").strip()
            if not report_title:
                report_title = "文本分析报告"

            report_path = self._generate_full_report(
                file_paths, folder_path, report_title
            )

            print(f"\n报告已生成: {report_path}")

        except Exception as e:
            print(f"生成报告失败: {e}")

    def _generate_full_report(self, file_paths, folder_path, report_title):
        """生成完整的分析报告"""
        documents = []
        doc_names = []
        word_freq_list = []

        for path in file_paths:
            text = read_file(path)
            documents.append(text)
            doc_names.append(os.path.basename(path))

            lang = detect_language(text)
            if lang == "chinese":
                freq = self.chinese_analyzer.word_frequency(text, top_n=20, min_length=2)
            else:
                freq = self.english_analyzer.word_frequency(text, top_n=20, min_length=2)
            word_freq_list.append(dict(freq))

        report = HTMLReportGenerator(title=report_title)

        stats = {
            "文档总数": str(len(file_paths)),
            "总字符数": str(sum(len(d) for d in documents)),
        }
        report.add_statistics(stats, "分析概览")

        tfidf_keywords = self.tfidf_analyzer.extract_keywords(documents, doc_names, top_n=10)
        for name, keywords in zip(doc_names, tfidf_keywords):
            report.add_tfidf_keywords_table(keywords, f"TF-IDF关键词 - {name}")

        if len(documents) >= 2:
            similarity_matrix = self.tfidf_analyzer.compute_similarity_matrix(documents)
            report.add_similarity_matrix(doc_names, similarity_matrix, "文档相似度矩阵")

        wordcloud_paths = []
        for i, (name, freq_dict) in enumerate(zip(doc_names, word_freq_list)):
            wc_path = os.path.join(OUTPUT_DIR, f"wordcloud_{i + 1}.png")
            try:
                self.wordcloud_generator.generate_from_frequencies(freq_dict, wc_path)
                wordcloud_paths.append((name, wc_path))
            except Exception:
                pass

        if wordcloud_paths:
            report.add_wordcloud_grid(wordcloud_paths, "词云图")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"report_{timestamp}.html")
        report.generate(report_path)

        return report_path

    def _generate_tfidf_report(self, doc_names, keywords_list):
        """生成TF-IDF报告"""
        report = HTMLReportGenerator(title="TF-IDF关键词分析报告")

        stats = {
            "文档数量": str(len(doc_names)),
            "关键词数/篇": str(len(keywords_list[0])) if keywords_list else "0",
        }
        report.add_statistics(stats, "分析概览")

        for name, keywords in zip(doc_names, keywords_list):
            report.add_tfidf_keywords_table(keywords, f"关键词 - {name}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"tfidf_report_{timestamp}.html")
        report.generate(report_path)

        print(f"TF-IDF报告已生成: {report_path}")

    def _generate_similarity_report(self, doc_names, similarity_matrix):
        """生成相似度报告"""
        report = HTMLReportGenerator(title="文档相似度分析报告")

        stats = {
            "文档数量": str(len(doc_names)),
            "算法": "余弦相似度",
        }
        report.add_statistics(stats, "分析概览")

        report.add_similarity_matrix(doc_names, similarity_matrix, "相似度矩阵")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"similarity_report_{timestamp}.html")
        report.generate(report_path)

        print(f"相似度报告已生成: {report_path}")

    def batch_process_menu(self):
        """批量文件处理菜单"""
        print("\n" + "=" * 50)
        print("【批量文件处理】")
        print("=" * 50)

        folder_path = input("请输入文件夹路径：").strip().strip('"').strip("'")
        if not folder_path or not os.path.isdir(folder_path):
            print("文件夹不存在！")
            return

        try:
            file_paths = scan_folder(folder_path, extension=".txt")
            if not file_paths:
                print("文件夹中没有找到txt文件！")
                return

            print(f"\n找到 {len(file_paths)} 个文件")

            print("\n请选择分析类型：")
            print("1. 词频统计")
            print("2. TF-IDF关键词提取")
            print("3. 完整分析（词频 + TF-IDF + 相似度 + 词云 + 报告）")
            choice = input("请选择 (默认3): ").strip()

            results = []
            for path in file_paths:
                try:
                    text = read_file(path)
                    file_name = os.path.basename(path)
                    lang = detect_language(text)

                    db_manager.add_document(
                        file_path=path,
                        file_name=file_name,
                        content=text,
                        language=lang,
                        word_count=len(text)
                    )

                    results.append((path, file_name, text, lang))
                    print(f"  ✓ {file_name}")
                except Exception as e:
                    print(f"  ✗ {os.path.basename(path)}: {e}")

            print(f"\n成功读取 {len(results)} 个文件")

            if choice == "1":
                self._batch_word_frequency(results)
            elif choice == "2":
                documents = [r[2] for r in results]
                names = [r[1] for r in results]
                keywords_list = self.tfidf_analyzer.extract_keywords(documents, names, top_n=10)
                for name, keywords in zip(names, keywords_list):
                    print(f"\n{name}:")
                    for word, value in keywords[:5]:
                        print(f"  {word}: {value:.6f}")
            else:
                print("\n正在进行完整分析...")
                report_path = self._generate_full_report(
                    [r[0] for r in results], folder_path, "批量文本分析报告"
                )
                print(f"\n完整报告已生成: {report_path}")

        except Exception as e:
            print(f"批量处理失败: {e}")

    def _batch_word_frequency(self, results):
        """批量词频统计"""
        top_n = 10
        for path, name, text, lang in results:
            print(f"\n{'=' * 50}")
            print(f"文件: {name}")
            print(f"语言: {lang}")
            print(f"{'=' * 50}")

            if lang == "chinese":
                freq = self.chinese_analyzer.word_frequency(text, top_n=top_n, min_length=2)
            else:
                freq = self.english_analyzer.word_frequency(text, top_n=top_n, min_length=2)

            print(f"{'排名':<6}{'词语':<15}{'词频':<10}")
            print("-" * 35)
            for i, (word, f) in enumerate(freq, 1):
                print(f"{i:<6}{word:<15}{f:<10}")

    def history_menu(self):
        """历史记录查询菜单"""
        print("\n" + "=" * 50)
        print("【历史记录查询】")
        print("=" * 50)

        print("\n请选择：")
        print("1. 查看所有分析记录")
        print("2. 按类型筛选")
        print("3. 查看记录详情")
        print("4. 删除记录")
        choice = input("请选择 (默认1): ").strip()

        try:
            if choice == "2":
                self._filter_history()
            elif choice == "3":
                self._view_history_detail()
            elif choice == "4":
                self._delete_history()
            else:
                self._list_all_history()

        except Exception as e:
            print(f"查询失败: {e}")

    def _list_all_history(self):
        """列出所有历史记录"""
        records = db_manager.get_analysis_history(limit=50)

        if not records:
            print("暂无历史记录！")
            return

        print(f"\n共 {len(records)} 条记录 (显示前50条)")
        print("-" * 80)
        print(f"{'ID':<6}{'分析类型':<20}{'文件名':<25}{'分析时间':<20}")
        print("-" * 80)

        for record in records:
            file_name = record.get("file_name", "-") or "-"
            print(
                f"{record['id']:<6}"
                f"{record['analysis_type']:<20}"
                f"{file_name[:22]:<25}"
                f"{record['analysis_time']:<20}"
            )

    def _filter_history(self):
        """按类型筛选历史记录"""
        print("\n可选类型:")
        types = [
            "chinese_word_frequency",
            "english_word_frequency",
            "tfidf_keywords",
            "document_similarity",
            "similarity_matrix",
            "wordcloud"
        ]
        for i, t in enumerate(types, 1):
            print(f"  [{i}] {t}")

        type_choice = input("请选择类型编号: ").strip()
        if not type_choice.isdigit():
            print("无效的选择！")
            return

        idx = int(type_choice) - 1
        if idx < 0 or idx >= len(types):
            print("无效的选择！")
            return

        records = db_manager.get_analysis_history(analysis_type=types[idx], limit=50)

        if not records:
            print("暂无记录！")
            return

        print(f"\n找到 {len(records)} 条记录")
        for record in records:
            file_name = record.get("file_name", "-") or "-"
            print(f"[{record['id']}] {file_name} - {record['analysis_time']}")

    def _view_history_detail(self):
        """查看记录详情"""
        record_id = input("请输入记录ID: ").strip()
        if not record_id.isdigit():
            print("无效的ID！")
            return

        record = db_manager.get_analysis_by_id(int(record_id))
        if not record:
            print("记录不存在！")
            return

        print("\n" + "=" * 50)
        print("记录详情")
        print("=" * 50)
        print(f"ID: {record['id']}")
        print(f"分析类型: {record['analysis_type']}")
        print(f"分析时间: {record['analysis_time']}")
        if record.get("file_name"):
            print(f"文件名: {record['file_name']}")
        if record.get("file_path"):
            print(f"文件路径: {record['file_path']}")
        if record.get("parameters"):
            print(f"分析参数: {record['parameters']}")
        if record.get("results"):
            print(f"\n分析结果摘要:")
            results = record["results"]
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, list):
                        print(f"  {key}: ({len(value)} 项)")
                    else:
                        print(f"  {key}: {value}")

    def _delete_history(self):
        """删除历史记录"""
        record_id = input("请输入要删除的记录ID: ").strip()
        if not record_id.isdigit():
            print("无效的ID！")
            return

        confirm = input("确认删除？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消")
            return

        success = db_manager.delete_analysis_record(int(record_id))
        if success:
            print("删除成功！")
        else:
            print("删除失败，记录可能不存在")

    def show_db_stats(self):
        """显示数据库统计信息"""
        stats = db_manager.get_statistics()

        print("\n" + "=" * 50)
        print("【数据库统计信息】")
        print("=" * 50)
        print(f"总分析记录数: {stats['total_analyses']}")
        print(f"总文档数: {stats['total_documents']}")
        print("\n按分析类型统计:")
        for analysis_type, count in stats['analysis_by_type'].items():
            print(f"  {analysis_type}: {count} 条")

    def entity_recognition_menu(self):
        """实体识别菜单"""
        print("\n" + "=" * 60)
        print("【实体识别 - 支持5类关键实体识别】")
        print("=" * 60)
        print("支持实体类型：人物(PER)、组织(ORG)、地点(LOC)、时间(TIME)、专有名词(NOUN)")
        print("-" * 60)
        
        while True:
            try:
                print("\n请选择输入方式：")
                print("【1】 手动输入文本")
                print("【2】 从文件读取")
                print("【3】 批量分析文件夹")
                print("【0】 返回主菜单")
                sub_choice = input("请输入选项：").strip()
                
                if sub_choice == "0":
                    return
                elif sub_choice == "1":
                    text = input("\n请输入要分析的文本：\n").strip()
                    if text:
                        self._do_entity_recognition(text, "手动输入文本")
                elif sub_choice == "2":
                    file_path = input("\n请输入文件路径：").strip()
                    if file_path:
                        text = read_file(file_path)
                        file_info = get_file_info(file_path)
                        self._do_entity_recognition(text, file_info['name'])
                elif sub_choice == "3":
                    folder_path = input("\n请输入文件夹路径：").strip()
                    if folder_path:
                        files = scan_folder(folder_path, extension=".txt")
                        if not files:
                            print("没有找到txt文件！")
                            continue
                        print(f"找到 {len(files)} 个文件，开始批量分析...\n")
                        all_entities = []
                        for idx, fp in enumerate(files, 1):
                            try:
                                text = read_file(fp)
                                file_info = get_file_info(fp)
                                result = self.entity_recognizer.recognize(text)
                                all_entities.append((file_info['name'], result))
                                print(f"[{idx}/{len(files)}] {file_info['name']}: "
                                      f"识别到 {len(result['entities'])} 个实体")
                            except Exception as e:
                                print(f"[{idx}/{len(files)}] {fp} 分析失败: {e}")
                        if all_entities:
                            self._print_batch_entity_results(all_entities)
                else:
                    print("无效选项！")
                    
                if sub_choice in ["1", "2"]:
                    cont = input("\n继续实体识别？(y/N): ").strip().lower()
                    if cont != "y":
                        return
                        
            except Exception as e:
                print(f"操作失败：{e}")

    def _do_entity_recognition(self, text: str, source_name: str):
        """执行实体识别并显示结果"""
        print(f"\n正在分析 \"{source_name}\"...")
        result = self.entity_recognizer.recognize(text)
        
        db_manager.save_analysis_record({
            'analysis_type': 'entity_recognition',
            'source_name': source_name,
            'text_length': len(text),
            'result': str(result)
        })
        
        self._print_entity_results(result)

    def _print_entity_results(self, result: Dict):
        """打印实体识别结果"""
        type_info = self.entity_recognizer.get_entity_type_info()
        
        print("\n" + "=" * 60)
        print("【实体识别结果】")
        print("=" * 60)
        print(f"语言: {result['language']}")
        print(f"实体总数: {result['entity_count']}")
        print(f"文本长度: {result['text_length']} 字符")
        
        print("\n按类型统计：")
        for type_key, count in result['entity_counts_by_type'].items():
            info = type_info.get(type_key, {'name': type_key})
            print(f"  {info['name']}({type_key}): {count} 个")
        
        if result['entities']:
            print("\n识别到的实体：")
            print("-" * 60)
            for idx, entity in enumerate(result['entities'], 1):
                type_info_e = type_info.get(entity['type'], {'name': entity['type'], 'color': ''})
                print(f"{idx:2d}. [{type_info_e['name']:4s}] {entity['text']:20s} "
                      f"(置信度: {entity['confidence']:.2f})")
        
        print("\n高亮文本：")
        print("-" * 60)
        print(self._strip_html(result['highlight_html']))

    def _print_batch_entity_results(self, all_results: List):
        """打印批量实体识别结果"""
        print("\n" + "=" * 70)
        print("【批量实体识别结果汇总】")
        print("=" * 70)
        
        total_entities = 0
        type_summary = {}
        
        for name, result in all_results:
            total_entities += result['entity_count']
            for t, c in result['entity_counts_by_type'].items():
                type_summary[t] = type_summary.get(t, 0) + c
        
        print(f"\n共分析 {len(all_results)} 个文件")
        print(f"识别实体总数: {total_entities}")
        
        print("\n各类型汇总：")
        type_info = self.entity_recognizer.get_entity_type_info()
        for t, c in type_summary.items():
            info = type_info.get(t, {'name': t})
            print(f"  {info['name']}({t}): {c} 个")

    def sentiment_analysis_menu(self):
        """情感分析菜单"""
        print("\n" + "=" * 60)
        print("【情感分析 - 正负面二元分类+置信度评分】")
        print("=" * 60)
        print("准确率 ≥ 80% | 置信度范围: 0(完全负面) ~ 1(完全正面)")
        print("-" * 60)
        
        while True:
            try:
                print("\n请选择输入方式：")
                print("【1】 手动输入文本")
                print("【2】 从文件读取")
                print("【3】 批量分析文件夹")
                print("【0】 返回主菜单")
                sub_choice = input("请输入选项：").strip()
                
                if sub_choice == "0":
                    return
                elif sub_choice == "1":
                    text = input("\n请输入要分析的文本：\n").strip()
                    if text:
                        self._do_sentiment_analysis(text, "手动输入文本")
                elif sub_choice == "2":
                    file_path = input("\n请输入文件路径：").strip()
                    if file_path:
                        text = read_file(file_path)
                        file_info = get_file_info(file_path)
                        self._do_sentiment_analysis(text, file_info['name'])
                elif sub_choice == "3":
                    folder_path = input("\n请输入文件夹路径：").strip()
                    if folder_path:
                        files = scan_folder(folder_path, extension=".txt")
                        if not files:
                            print("没有找到txt文件！")
                            continue
                        print(f"找到 {len(files)} 个文件，开始批量分析...\n")
                        texts = []
                        names = []
                        for fp in files:
                            try:
                                texts.append(read_file(fp))
                                fi = get_file_info(fp)
                                names.append(fi['name'])
                            except Exception as e:
                                print(f"读取 {fp} 失败: {e}")
                        
                        if texts:
                            results = self.sentiment_analyzer.analyze_batch(texts)
                            self._print_batch_sentiment_results(names, results)
                else:
                    print("无效选项！")
                    
                if sub_choice in ["1", "2"]:
                    cont = input("\n继续情感分析？(y/N): ").strip().lower()
                    if cont != "y":
                        return
                        
            except Exception as e:
                print(f"操作失败：{e}")

    def _do_sentiment_analysis(self, text: str, source_name: str):
        """执行情感分析并显示结果"""
        print(f"\n正在分析 \"{source_name}\"...")
        result = self.sentiment_analyzer.analyze(text)
        
        db_manager.save_analysis_record({
            'analysis_type': 'sentiment_analysis',
            'source_name': source_name,
            'text_length': len(text),
            'result': str(result)
        })
        
        self._print_sentiment_result(result)

    def _print_sentiment_result(self, result: Dict):
        """打印情感分析结果"""
        print("\n" + "=" * 60)
        print("【情感分析结果】")
        print("=" * 60)
        print(f"语言: {result['language']}")
        print(f"情感分类: {'正面' if result['sentiment'] == 'positive' else '负面'}")
        print(f"置信度: {result['confidence']:.4f}")
        print(f"正面分数: {result['positive_score']:.4f}")
        print(f"负面分数: {result['negative_score']:.4f}")
        
        bar_length = 40
        pos_fill = int(result['confidence'] * bar_length)
        neg_fill = bar_length - pos_fill
        bar = "█" * pos_fill + "░" * neg_fill
        
        if result['sentiment'] == 'positive':
            label = f"正面 {result['confidence']*100:.1f}%"
        else:
            label = f"负面 {(1-result['confidence'])*100:.1f}%"
        
        print(f"\n情感倾向: {bar} {label}")
        
        if 'positive_words' in result and result['positive_words']:
            print(f"\n正面词汇: {', '.join(result['positive_words'][:10])}")
        if 'negative_words' in result and result['negative_words']:
            print(f"负面词汇: {', '.join(result['negative_words'][:10])}")

    def _print_batch_sentiment_results(self, names: List[str], results: List[Dict]):
        """打印批量情感分析结果"""
        print("\n" + "=" * 70)
        print("【批量情感分析结果汇总】")
        print("=" * 70)
        
        pos_count = sum(1 for r in results if r['sentiment'] == 'positive')
        neg_count = len(results) - pos_count
        
        print(f"\n共分析 {len(results)} 个文件")
        print(f"正面: {pos_count} ({pos_count/len(results)*100:.1f}%)")
        print(f"负面: {neg_count} ({neg_count/len(results)*100:.1f}%)")
        
        avg_conf = sum(r['confidence'] for r in results) / len(results)
        print(f"平均置信度: {avg_conf:.4f}")
        
        print("\n详细结果：")
        print("-" * 70)
        for name, result in zip(names, results):
            label = "正面" if result['sentiment'] == 'positive' else "负面"
            print(f"  {name:30s} | {label:4s} | 置信度: {result['confidence']:.4f}")

    def start_web_server(self):
        """启动Web服务"""
        print("\n" + "=" * 60)
        print("【启动Web服务 - 图形化界面】")
        print("=" * 60)
        print("正在启动Flask Web服务器...")
        print("服务将在 http://127.0.0.1:5000 运行")
        print("按 Ctrl+C 停止服务")
        print("-" * 60 + "\n")
        
        try:
            from app import app
            app.run(host='127.0.0.1', port=5000, debug=False)
        except KeyboardInterrupt:
            print("\n\nWeb服务已停止")
        except ImportError:
            print("错误: 无法导入app模块，请确保app.py存在")
        except Exception as e:
            print(f"启动Web服务失败: {e}")

    def _strip_html(self, html_text: str) -> str:
        """去除HTML标签用于终端显示"""
        import re
        text = re.sub(r'<[^>]+>', '', html_text)
        return text


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文本分析工具 v2.0 - 支持中英文文本分析、TF-IDF、相似度比较、词云图生成、实体识别、情感分析、Web界面",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m text_analyzer                    # 启动交互式菜单
  python -m text_analyzer --file input.txt   # 分析单个文件
  python -m text_analyzer --web              # 启动Web服务
  python -m text_analyzer --entity --text "张三在北京工作"  # 实体识别
  python -m text_analyzer --sentiment --text "今天天气真好" # 情感分析
        """
    )

    parser.add_argument("--file", "-f", help="输入文本文件路径")
    parser.add_argument("--output", "-o", help="输出目录", default=OUTPUT_DIR)
    parser.add_argument("--lang", "-l", choices=["auto", "chinese", "english"],
                        default="auto", help="文本语言 (默认auto自动检测)")
    parser.add_argument("--top", "-n", type=int, default=20, help="显示前N个高频词")
    parser.add_argument("--no-stopwords", action="store_true", help="不过滤停用词")
    parser.add_argument("--report", "-r", action="store_true", help="生成HTML报告")
    parser.add_argument("--wordcloud", "-w", action="store_true", help="生成词云图")
    parser.add_argument("--tfidf", action="store_true", help="进行TF-IDF分析")
    parser.add_argument("--similarity", nargs=2, metavar=("FILE1", "FILE2"),
                        help="比较两个文件的相似度")
    parser.add_argument("--batch", "-b", help="批量处理文件夹")
    parser.add_argument("--web", action="store_true", help="启动Web图形化界面")
    parser.add_argument("--entity", action="store_true", help="进行实体识别")
    parser.add_argument("--sentiment", action="store_true", help="进行情感分析")
    parser.add_argument("--text", "-t", help="直接输入文本进行分析")

    args = parser.parse_args()

    if args.similarity:
        cli = TextAnalyzerCLI()
        try:
            text1 = read_file(args.similarity[0])
            text2 = read_file(args.similarity[1])
            sim = cli.similarity_analyzer.tfidf_similarity(text1, text2)
            print(f"相似度: {sim * 100:.2f}%")
        except Exception as e:
            print(f"错误: {e}")
        return

    if args.web:
        cli = TextAnalyzerCLI()
        cli.start_web_server()
        return

    if args.entity or args.sentiment:
        cli = TextAnalyzerCLI()
        try:
            text = ""
            if args.text:
                text = args.text
            elif args.file:
                text = read_file(args.file)
            else:
                print("请使用 --text 指定文本或 --file 指定文件")
                return

            if args.entity:
                result = cli.entity_recognizer.recognize(text)
                cli._print_entity_results(result)

            if args.sentiment:
                result = cli.sentiment_analyzer.analyze(text)
                cli._print_sentiment_result(result)

        except Exception as e:
            print(f"错误: {e}")
        return

    if args.batch:
        cli = TextAnalyzerCLI()
        try:
            file_paths = scan_folder(args.batch, extension=".txt")
            if not file_paths:
                print("没有找到txt文件！")
                return

            print(f"找到 {len(file_paths)} 个文件，正在生成报告...")
            report_path = cli._generate_full_report(
                file_paths, args.batch, "批量文本分析报告"
            )
            print(f"报告已生成: {report_path}")
        except Exception as e:
            print(f"错误: {e}")
        return

    if args.file:
        cli = TextAnalyzerCLI()
        try:
            text = read_file(args.file)
            lang = args.lang if args.lang != "auto" else detect_language(text)

            use_stopwords = not args.no_stopwords

            if lang == "chinese":
                word_freq = cli.chinese_analyzer.word_frequency(
                    text, top_n=args.top, use_stopwords=use_stopwords, min_length=2
                )
                stats = cli.chinese_analyzer.word_count(text, use_stopwords=use_stopwords)
            else:
                word_freq = cli.english_analyzer.word_frequency(
                    text, top_n=args.top, use_stopwords=use_stopwords, min_length=2
                )
                stats = cli.english_analyzer.word_count(text, use_stopwords=use_stopwords)

            print(f"文件: {args.file}")
            print(f"语言: {lang}")
            print(f"总词数: {stats['total_words']}")
            print(f"唯一项数: {stats['unique_words']}")
            print(f"\nTop {args.top} 高频词:")
            for i, (word, freq) in enumerate(word_freq, 1):
                print(f"  {i}. {word}: {freq}")

            if args.wordcloud:
                output_name = os.path.splitext(os.path.basename(args.file))[0] + "_wordcloud.png"
                output_path = os.path.join(args.output, output_name)
                cli.wordcloud_generator.generate_from_text(
                    text, output_path, language=lang, use_stopwords=use_stopwords
                )
                print(f"\n词云图已生成: {output_path}")

            if args.report:
                report = HTMLReportGenerator(title="文本分析报告")
                report.add_word_frequency_table(word_freq, "词频统计")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = os.path.join(args.output, f"report_{timestamp}.html")
                report.generate(report_path)
                print(f"报告已生成: {report_path}")

            db_manager.add_analysis_record(
                analysis_type=f"{lang}_word_frequency",
                file_path=args.file,
                file_name=os.path.basename(args.file),
                parameters={"top_n": args.top, "use_stopwords": use_stopwords},
                results={"top_words": [{"word": w, "freq": f} for w, f in word_freq[:10]]}
            )

        except Exception as e:
            print(f"错误: {e}")
        return

    cli = TextAnalyzerCLI()
    cli.run()


if __name__ == "__main__":
    main()
