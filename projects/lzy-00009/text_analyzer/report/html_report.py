"""
HTML报告生成模块 - 将分析结果整合为HTML报告
"""
import os
import base64
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from text_analyzer.config import OUTPUT_DIR


class HTMLReportGenerator:
    """HTML报告生成器"""

    def __init__(self, title: str = "文本分析报告"):
        self.title = title
        self._sections: List[Tuple[str, str]] = []

    @staticmethod
    def _get_css() -> str:
        """获取CSS样式"""
        return """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
                background-color: #f5f7fa;
                color: #333;
                line-height: 1.6;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
                padding: 40px;
            }
            .report-header {
                text-align: center;
                padding-bottom: 30px;
                border-bottom: 2px solid #e4e7ed;
                margin-bottom: 30px;
            }
            .report-header h1 {
                color: #303133;
                font-size: 28px;
                margin-bottom: 10px;
            }
            .report-header .time {
                color: #909399;
                font-size: 14px;
            }
            .section {
                margin-bottom: 40px;
            }
            .section-title {
                font-size: 20px;
                color: #303133;
                border-left: 4px solid #409eff;
                padding-left: 12px;
                margin-bottom: 20px;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                background-color: #fff;
            }
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ebeef5;
            }
            th {
                background-color: #f5f7fa;
                color: #606266;
                font-weight: 600;
            }
            tr:hover {
                background-color: #f5f7fa;
            }
            .wordcloud-img {
                max-width: 100%;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                margin: 10px 0;
            }
            .similarity-matrix {
                overflow-x: auto;
            }
            .similarity-matrix table {
                font-size: 14px;
            }
            .similarity-matrix td {
                text-align: center;
            }
            .high-similarity {
                color: #67c23a;
                font-weight: bold;
            }
            .medium-similarity {
                color: #e6a23c;
            }
            .low-similarity {
                color: #f56c6c;
            }
            .info-card {
                background-color: #ecf5ff;
                border: 1px solid #d9ecff;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 20px;
            }
            .info-card p {
                color: #409eff;
                margin: 5px 0;
            }
            .keyword-tag {
                display: inline-block;
                background-color: #ecf5ff;
                color: #409eff;
                padding: 4px 12px;
                border-radius: 20px;
                margin: 4px;
                font-size: 14px;
            }
            .wordcloud-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
            }
            .wordcloud-item {
                text-align: center;
            }
            .wordcloud-item h4 {
                margin-bottom: 10px;
                color: #606266;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                padding: 20px;
                color: #fff;
            }
            .stat-card .value {
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-card .label {
                font-size: 14px;
                opacity: 0.9;
            }
            .report-footer {
                text-align: center;
                padding-top: 20px;
                border-top: 1px solid #e4e7ed;
                color: #909399;
                font-size: 12px;
                margin-top: 40px;
            }
        </style>
        """

    def add_section(self, title: str, content: str):
        """
        添加报告章节

        Args:
            title: 章节标题
            content: 章节HTML内容
        """
        self._sections.append((title, content))

    def add_word_frequency_table(self, word_freq: List[Tuple[str, int]],
                                  title: str = "词频统计"):
        """
        添加词频统计表格

        Args:
            word_freq: 词频列表 [(词语, 词频)]
            title: 章节标题
        """
        if not word_freq:
            content = '<p style="color: #909399;">暂无数据</p>'
        else:
            total = sum(freq for _, freq in word_freq)
            rows = ""
            for i, (word, freq) in enumerate(word_freq, 1):
                percentage = (freq / total * 100) if total > 0 else 0
                rows += f"""
                <tr>
                    <td>{i}</td>
                    <td>{word}</td>
                    <td>{freq}</td>
                    <td>{percentage:.2f}%</td>
                </tr>
                """

            content = f"""
            <div class="info-card">
                <p><strong>总词数：</strong>{total} 个</p>
                <p><strong>唯一项数：</strong>{len(word_freq)} 个</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th width="80">排名</th>
                        <th>词语</th>
                        <th width="100">词频</th>
                        <th width="120">占比</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            """
        self.add_section(title, content)

    def add_tfidf_keywords_table(self, keywords: List[Tuple[str, float]],
                                  title: str = "TF-IDF关键词"):
        """
        添加TF-IDF关键词表格

        Args:
            keywords: 关键词列表 [(词语, TF-IDF值)]
            title: 章节标题
        """
        if not keywords:
            content = '<p style="color: #909399;">暂无数据</p>'
        else:
            max_value = max(v for _, v in keywords) if keywords else 1

            keyword_tags = ""
            for word, value in keywords:
                weight = value / max_value if max_value > 0 else 0
                size = int(12 + weight * 8)
                keyword_tags += f'<span class="keyword-tag" style="font-size: {size}px;">{word}</span>'

            rows = ""
            for i, (word, value) in enumerate(keywords, 1):
                rows += f"""
                <tr>
                    <td>{i}</td>
                    <td>{word}</td>
                    <td>{value:.6f}</td>
                </tr>
                """

            content = f"""
            <div style="margin-bottom: 20px;">
                {keyword_tags}
            </div>
            <table>
                <thead>
                    <tr>
                        <th width="80">排名</th>
                        <th>关键词</th>
                        <th width="150">TF-IDF值</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            """
        self.add_section(title, content)

    def add_similarity_matrix(self, doc_names: List[str],
                              similarity_matrix: List[List[float]],
                              title: str = "文档相似度矩阵"):
        """
        添加文档相似度矩阵

        Args:
            doc_names: 文档名称列表
            similarity_matrix: 相似度矩阵
            title: 章节标题
        """
        if not similarity_matrix or not doc_names:
            content = '<p style="color: #909399;">暂无数据</p>'
        else:
            header_cells = "".join(f"<th>{name}</th>" for name in doc_names)

            rows = ""
            for i, row in enumerate(similarity_matrix):
                cells = ""
                for j, value in enumerate(row):
                    percentage = value * 100
                    if i == j:
                        cell_class = ""
                        cell_value = "100.00%"
                    elif percentage >= 70:
                        cell_class = "high-similarity"
                        cell_value = f"{percentage:.2f}%"
                    elif percentage >= 40:
                        cell_class = "medium-similarity"
                        cell_value = f"{percentage:.2f}%"
                    else:
                        cell_class = "low-similarity"
                        cell_value = f"{percentage:.2f}%"
                    cells += f'<td class="{cell_class}">{cell_value}</td>'

                rows += f"""
                <tr>
                    <th>{doc_names[i]}</th>
                    {cells}
                </tr>
                """

            content = f"""
            <div class="similarity-matrix">
                <table>
                    <thead>
                        <tr>
                            <th></th>
                            {header_cells}
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            <div style="margin-top: 15px; font-size: 13px; color: #909399;">
                <span class="high-similarity">● 高相似度 (≥70%)</span>
                <span class="medium-similarity" style="margin-left: 15px;">● 中相似度 (40%-70%)</span>
                <span class="low-similarity" style="margin-left: 15px;">● 低相似度 (<40%)</span>
            </div>
            """
        self.add_section(title, content)

    def add_wordcloud_image(self, image_path: str, title: str = "词云图",
                            description: str = ""):
        """
        添加词云图片

        Args:
            image_path: 图片路径
            title: 章节标题
            description: 图片描述
        """
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode("utf-8")

            img_html = f'<img src="data:image/png;base64,{img_base64}" class="wordcloud-img" alt="{title}">'
        else:
            img_html = f'<p style="color: #f56c6c;">图片不存在: {image_path}</p>'

        desc_html = f'<p style="color: #909399; margin-bottom: 10px;">{description}</p>' if description else ""

        content = f"{desc_html}{img_html}"
        self.add_section(title, content)

    def add_wordcloud_grid(self, wordcloud_items: List[Tuple[str, str]],
                            title: str = "词云图"):
        """
        添加网格布局的词云图

        Args:
            wordcloud_items: [(标题, 图片路径)] 列表
            title: 章节标题
        """
        items_html = ""
        for name, img_path in wordcloud_items:
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                img_html = f'<img src="data:image/png;base64,{img_base64}" class="wordcloud-img" alt="{name}">'
            else:
                img_html = f'<p style="color: #f56c6c;">图片不存在</p>'

            items_html += f"""
            <div class="wordcloud-item">
                <h4>{name}</h4>
                {img_html}
            </div>
            """

        content = f'<div class="wordcloud-grid">{items_html}</div>'
        self.add_section(title, content)

    def add_statistics(self, stats: Dict[str, str], title: str = "统计信息"):
        """
        添加统计信息卡片

        Args:
            stats: 统计信息字典 {标签: 值}
            title: 章节标题
        """
        cards_html = ""
        for label, value in stats.items():
            cards_html += f"""
            <div class="stat-card">
                <div class="value">{value}</div>
                <div class="label">{label}</div>
            </div>
            """

        content = f'<div class="stats-grid">{cards_html}</div>'
        self.add_section(title, content)

    def add_text_content(self, text: str, title: str = "文本内容"):
        """
        添加文本内容

        Args:
            text: 文本内容
            title: 章节标题
        """
        preview = text[:500] + "..." if len(text) > 500 else text
        content = f"""
        <div style="background-color: #f5f7fa; padding: 20px; border-radius: 4px; 
                    max-height: 300px; overflow-y: auto; font-size: 14px; line-height: 1.8;">
            {preview}
        </div>
        """
        self.add_section(title, content)

    def generate(self, output_path: Optional[str] = None) -> str:
        """
        生成HTML报告

        Args:
            output_path: 输出文件路径

        Returns:
            生成的报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(OUTPUT_DIR, f"report_{timestamp}.html")

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        sections_html = ""
        for title, content in self._sections:
            sections_html += f"""
            <div class="section">
                <h2 class="section-title">{title}</h2>
                <div class="section-content">
                    {content}
                </div>
            </div>
            """

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    {self._get_css()}
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>{self.title}</h1>
            <p class="time">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        {sections_html}
        <div class="report-footer">
            <p>由 Text Analyzer 自动生成 | 报告仅供参考</p>
        </div>
    </div>
</body>
</html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def reset(self):
        """重置报告内容"""
        self._sections = []
