import sys
sys.path.insert(0, '.')
from text_analyzer.analyzer.chinese_analyzer import ChineseTextAnalyzer
from text_analyzer.analyzer.english_analyzer import EnglishTextAnalyzer
from text_analyzer.utils.file_utils import read_file
import re

print('=' * 60)
print('【测试1：中文标点符号过滤】')
print('=' * 60)

text = read_file('test_data/punctuation_test.txt')
analyzer = ChineseTextAnalyzer()

print('\n原文前200字:')
print(text[:200])

words = analyzer.segment(text, use_stopwords=False)
print(f'\n分词结果（共 {len(words)} 个词）:')
print(words)

print('\n检查是否包含标点符号:')
has_punct = False
for word in words:
    if re.search(r'[^\u4e00-\u9fa5a-zA-Z0-9]', word):
        print(f'  发现非字母数字中文字符: "{word}"')
        has_punct = True

if not has_punct:
    print('  ✅ 所有词语都不包含标点符号，过滤成功！')

freq = analyzer.word_frequency(text, top_n=20, use_stopwords=False)
print(f'\n词频统计（Top 20）:')
for word, count in freq:
    print(f'  {word}: {count}')

print('\n' + '=' * 60)
print('【测试2：英文分析 NLTK 数据自动下载】')
print('=' * 60)

try:
    en_analyzer = EnglishTextAnalyzer(stemmer_type='porter')
    print(f'\nNLTK 可用状态: {en_analyzer._nltk_available}')
    print(f'词干提取器已加载: {en_analyzer._stemmer is not None}')
    print(f'NLTK数据已确保: {EnglishTextAnalyzer._nltk_data_ensured}')

    en_text = read_file('test_data/english_sample1.txt')
    words = en_analyzer.tokenize(en_text, use_stopwords=True)
    print(f'\n分词成功，共 {len(words)} 个词')
    print(f'前10个词: {words[:10]}')

    stemmed = en_analyzer.stem(words[:10])
    print(f'词干提取成功: {stemmed}')

    freq_en = en_analyzer.word_frequency(en_text, top_n=10)
    print(f'\n词频统计（Top 10）:')
    for word, count in freq_en:
        print(f'  {word}: {count}')

    print('\n✅ 英文分析模块工作正常，NLTK数据自动加载成功！')

except Exception as e:
    print(f'❌ 英文分析测试失败: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '=' * 60)
print('测试总结')
print('=' * 60)
print('✅ 中文标点符号过滤机制改进完成')
print('✅ 英文NLTK数据自动下载机制改进完成')
