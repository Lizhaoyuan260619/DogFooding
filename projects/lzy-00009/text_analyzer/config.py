"""
配置模块 - 管理全局配置和常量
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DB_PATH = os.path.join(DATA_DIR, "text_analyzer.db")
STOPWORDS_DIR = os.path.join(DATA_DIR, "stopwords")

DEFAULT_CHINESE_STOPWORDS = os.path.join(STOPWORDS_DIR, "chinese_stopwords.txt")
DEFAULT_ENGLISH_STOPWORDS = os.path.join(STOPWORDS_DIR, "english_stopwords.txt")

DEFAULT_WORDCLOUD_WIDTH = 800
DEFAULT_WORDCLOUD_HEIGHT = 600
DEFAULT_WORDCLOUD_BG_COLOR = "white"
DEFAULT_WORDCLOUD_FONT = None

DEFAULT_TOP_N = 20
DEFAULT_TFIDF_TOP_N = 10

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STOPWORDS_DIR, exist_ok=True)
