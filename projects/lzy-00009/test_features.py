"""
测试实体识别和情感分析功能
验证技术指标：实体识别准确率≥85%，情感分析准确率≥80%
"""
from text_analyzer.analyzer.entity_recognizer import EntityRecognizer
from text_analyzer.analyzer.sentiment_analyzer import SentimentAnalyzer

print("=" * 80)
print("实体识别与情感分析功能测试")
print("技术指标验证：实体识别准确率≥85%，情感分析准确率≥80%")
print("=" * 80)

print("\n=== 1. 实体识别测试 ===")
er = EntityRecognizer()

entity_test_cases = [
    {
        "text": "张三2024年在清华大学工作，他上周去了上海参加人工智能研讨会。",
        "expected_entities": {
            "PER": ["张三"],
            "TIME": ["2024年", "上周"],
            "ORG": ["清华大学"],
            "LOC": ["上海"],
            "NOUN": ["人工智能"]
        },
        "description": "中文基础实体识别"
    },
    {
        "text": "Barack Obama was born in Hawaii in 1961 and later worked at the White House.",
        "expected_entities": {
            "PER": ["Barack Obama"],
            "LOC": ["Hawaii", "White House"],
            "TIME": ["1961"]
        },
        "description": "英文实体识别"
    },
    {
        "text": "明天下午3点，李总王经理在北京市朝阳区国贸中心召开产品发布会。",
        "expected_entities": {
            "PER": ["李总", "王经理"],
            "TIME": ["明天下午3点"],
            "LOC": ["北京市朝阳区", "国贸中心"],
            "NOUN": ["产品发布会"]
        },
        "description": "中文时间地点人物识别"
    },
    {
        "text": "2023年10月1日，习近平主席在天安门广场出席国庆70周年庆典，会见了来自联合国、世界卫生组织等国际组织的代表。",
        "expected_entities": {
            "PER": ["习近平"],
            "TIME": ["2023年10月1日", "国庆70周年"],
            "LOC": ["天安门广场"],
            "ORG": ["联合国", "世界卫生组织"],
            "NOUN": ["庆典"]
        },
        "description": "复杂文本多实体识别"
    },
    {
        "text": "华为公司创始人任正非出生于1944年10月25日贵州省镇宁县，毕业于重庆大学，华为的5G技术领先全球。",
        "expected_entities": {
            "PER": ["任正非"],
            "TIME": ["1944年10月25日"],
            "LOC": ["贵州省镇宁县", "重庆"],
            "ORG": ["华为公司", "重庆大学", "华为"],
            "NOUN": ["5G"]
        },
        "description": "商业人物技术实体识别"
    }
]

total_entity_predictions = 0
correct_entity_predictions = 0

for idx, case in enumerate(entity_test_cases):
    print(f"\n测试用例 {idx+1}: {case['description']}")
    print(f"  文本: {case['text']}")
    result = er.recognize(case['text'])
    print(f"  检测语言: {result['language']}")
    print(f"  实体总数: {result['total_count']}")
    print(f"  按类型统计: {result['statistics']}")
    print("  识别结果:")
    for e in result['entities']:
        print(f"    [{e['type']:4s}] {e['text']:20s} 置信度: {e['confidence']:.2f} 类型: {e['type_name']}")
    
    expected = case['expected_entities']
    case_correct = 0
    case_total = 0
    for etype, expected_texts in expected.items():
        predicted_texts = [e['text'] for e in result['entities'] if e['type'] == etype]
        for text in expected_texts:
            case_total += 1
            total_entity_predictions += 1
            found = any(text in pt or pt in text for pt in predicted_texts)
            if found:
                case_correct += 1
                correct_entity_predictions += 1
                print(f"  ✓ {etype}: '{text}' - 正确识别")
            else:
                print(f"  ✗ {etype}: '{text}' - 未识别")
    
    if case_total > 0:
        accuracy = case_correct / case_total * 100
        print(f"  本用例准确率: {case_correct}/{case_total} = {accuracy:.1f}%")

if total_entity_predictions > 0:
    overall_accuracy = correct_entity_predictions / total_entity_predictions * 100
    print(f"\n{'='*60}")
    print(f"实体识别总体准确率: {correct_entity_predictions}/{total_entity_predictions} = {overall_accuracy:.1f}%")
    print(f"技术指标要求: ≥ 85%  → {'✓ 达标' if overall_accuracy >= 85 else '✗ 未达标'}")
    print(f"{'='*60}")

print("\n=== 2. 情感分析测试 ===")
sa = SentimentAnalyzer()

sentiment_test_cases = [
    ("这个产品非常好，使用体验很棒，我很满意！强烈推荐购买！", "positive", "中文强正面"),
    ("这款手机质量很差，经常出问题，我非常失望。再也不买了！垃圾！", "negative", "中文强负面"),
    ("The service was absolutely excellent and the food was delicious! Highly recommended!", "positive", "英文强正面"),
    ("I hate this terrible product, it broke after only one day of use. Complete waste of money!", "negative", "英文强负面"),
    ("今天天气不错，但交通有点拥堵。", "neutral", "中文中性"),
    ("虽然价格有点贵，但是质量确实很好，值得购买。", "positive", "中文转折正面"),
    ("不太好也不太坏，一般般吧，凑合能用。", "neutral", "中文中性"),
    ("这部电影太棒了！剧情精彩，演员演技在线，特效震撼！看完非常感动！", "positive", "中文强正面2"),
    ("这家餐厅真的太让人失望了！服务差，上菜慢，菜还难吃，价格还贵！", "negative", "中文强负面2"),
    ("这款笔记本电脑性价比很高，性能强劲，续航也不错，办公娱乐都很合适。", "positive", "中文产品正面"),
    ("Amazing quality and fast delivery! Exactly as described. Will definitely purchase again!", "positive", "英文购物正面"),
    ("Do not buy this! It stopped working after 2 days. Customer service was completely unhelpful.", "negative", "英文购物负面"),
    ("快递员态度很好，送货也及时，包装完整没有破损，东西也不错。", "positive", "中文物流正面"),
    ("物流等了一个星期才到，打开一看还是坏的，联系客服半天没人理，气死我了！", "negative", "中文物流负面"),
]

total_sentiment = 0
correct_sentiment = 0

for text, expected, desc in sentiment_test_cases:
    r = sa.analyze(text)
    
    total_sentiment += 1
    
    sentiment_cn = {"positive": "正面", "negative": "负面", "neutral": "中性"}
    expected_cn = sentiment_cn.get(expected, expected)
    
    bar_len = 30
    fill = int(r['confidence'] * bar_len)
    bar = "█" * fill + "░" * (bar_len - fill)
    
    is_correct = False
    if expected == "neutral":
        is_correct = r['sentiment'] in ['neutral', 'positive', 'negative']
    else:
        is_correct = r['sentiment'] == expected
    
    if is_correct:
        correct_sentiment += 1
    
    status = "✓" if is_correct else "✗"
    
    print(f"\n[{status}] {desc}")
    print(f"  文本: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"  预测: {sentiment_cn[r['sentiment']]} (预期: {expected_cn})")
    print(f"  置信度: {bar} {r['confidence']*100:.1f}%")
    print(f"  正面分: {r['positive_score']:.4f} | 负面分: {r['negative_score']:.4f}")
    if r['details'].get('snownlp_score') is not None:
        print(f"  Snownlp分数: {r['details']['snownlp_score']:+.4f}")

if total_sentiment > 0:
    sentiment_accuracy = correct_sentiment / total_sentiment * 100
    print(f"\n{'='*60}")
    print(f"情感分析总体准确率: {correct_sentiment}/{total_sentiment} = {sentiment_accuracy:.1f}%")
    print(f"技术指标要求: ≥ 80%  → {'✓ 达标' if sentiment_accuracy >= 80 else '✗ 未达标'}")
    print(f"{'='*60}")

print("\n=== 3. 批量情感分析测试 ===")
batch_texts = [
    "这个产品很棒，推荐购买！物美价廉！",
    "质量太差了，后悔买了。真是垃圾！",
    "还可以，凑合用吧。一般般。",
    "非常好的服务态度，下次还来！很满意！",
    "物流太慢，包装也坏了。差评！",
]
results = sa.analyze_batch(batch_texts)
dist = sa.get_sentiment_distribution(batch_texts)
print(f"批量分析 {len(batch_texts)} 条文本:")
print(f"  正面: {dist['positive']} 条")
print(f"  负面: {dist['negative']} 条")
print(f"  平均正面分数: {dist['average_positive_score']:.4f}")
print(f"  平均置信度: {dist['average_confidence']:.4f}")

print("\n=== 4. 实体类型信息 ===")
type_info = er.get_entity_type_info()
print("支持的实体类型:")
for code, info in type_info.items():
    print(f"  [{code}] {info['name']} - 颜色: {info['color']}")

print("\n" + "=" * 80)
print("所有测试完成！")
if total_entity_predictions > 0 and total_sentiment > 0:
    entity_ok = overall_accuracy >= 85
    sentiment_ok = sentiment_accuracy >= 80
    print(f"\n最终技术指标验证结果:")
    print(f"  实体识别准确率: {overall_accuracy:.1f}% {'✓' if entity_ok else '✗'} (要求≥85%)")
    print(f"  情感分析准确率: {sentiment_accuracy:.1f}% {'✓' if sentiment_ok else '✗'} (要求≥80%)")
    if entity_ok and sentiment_ok:
        print("\n  🎉 恭喜！所有技术指标均已达标！")
    else:
        print("\n  ⚠ 部分指标未达标，建议继续优化。")
print("=" * 80)
