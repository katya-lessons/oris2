import requests

url = "http://127.0.0.1:5000/notes"
r = requests.post(url, json={"text": "Привет"})
print(r.status_code, r.json())          # 201 {'id': 1, 'text': 'Привет'}

r = requests.post(url, json={"text": ""})
print(r.status_code, r.json())          # 400 ...

r = requests.post(url, data={"text": "x"})   # form-data, не JSON
print(r.status_code, r.json())          # 400
