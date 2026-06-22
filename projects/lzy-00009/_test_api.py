import requests
import json

text = "2024年6月22日，张三先生在北京清华大学参加了由教育部组织的人工智能学术研讨会，他表示：这次会议非常精彩，收获满满！"
r = requests.post("http://localhost:5000/api/analyze", json={"text": text})
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
