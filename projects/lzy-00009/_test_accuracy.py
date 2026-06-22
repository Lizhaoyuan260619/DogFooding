import requests, json

samples = [
    ('2024年6月22日，张三先生在北京清华大学参加了由教育部组织的人工智能学术研讨会，他表示：这次会议非常精彩，收获满满！', 'pos'),
    ('昨天在京东买的华为手机，客服态度非常差，屏幕还有划痕，物流也慢得要死。真是太失望了，垃圾服务！', 'neg'),
    ('On June 22, 2024, Dr. John Smith attended the International AI Conference at Stanford. This conference was absolutely amazing! Highly recommend!', 'pos'),
    ('I purchased an iPhone from Amazon last week. The delivery was delayed, and customer service was extremely rude. This is the worst shopping experience ever. Never buying again!', 'neg'),
    ('这部电影非常精彩，演员表演出色，剧情紧凑，值得推荐！', 'pos'),
    ('产品质量太差了，完全不值这个价格，我非常失望。', 'neg'),
]

correct_sentiment = 0
correct_entity_types = 0
total = len(samples)

for text, expected in samples:
    r = requests.post('http://localhost:5000/api/analyze', json={'text': text})
    data = r.json()
    if 'sentiment_analysis' not in data:
        print(f'ERROR for: {text[:60]}...')
        print(json.dumps(data, ensure_ascii=False, indent=2))
        continue
    sa = data['sentiment_analysis']
    er = data['entity_recognition']

    expected_sentiment = 'positive' if expected == 'pos' else 'negative'
    sentiment_ok = sa['sentiment'] == expected_sentiment
    if sentiment_ok:
        correct_sentiment += 1

    # Check entity diversity - counts distinct types
    types_found = [t for t, c in er['statistics'].items() if c > 0]
    entity_ok = len(types_found) >= 3
    if entity_ok:
        correct_entity_types += 1

    print(f'Expected: {expected} | Predicted: {sa["sentiment"]} ({sa["sentiment_name"]}) | Conf: {sa["confidence"]} | Pos: {sa["positive_score"]}')
    print(f'    Entities: {er["total_count"]} | Types: {types_found} | {er["statistics"]}')
    print(f'    Details: {sa["details"]}')
    print(f'    Sentiment OK: {sentiment_ok}, Entity OK: {entity_ok}')
    print()

print(f'Sentiment accuracy: {correct_sentiment}/{total} = {correct_sentiment/total*100:.1f}%')
print(f'Entity diversity (>=3 types): {correct_entity_types}/{total} = {correct_entity_types/total*100:.1f}%')
