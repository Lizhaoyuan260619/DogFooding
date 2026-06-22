import requests
text = "On June 22, 2024, Dr. John Smith attended the International AI Conference at Stanford. This conference was absolutely amazing! Highly recommend!"
r = requests.post('http://localhost:5000/api/analyze', json={'text': text})
print(r.text)
