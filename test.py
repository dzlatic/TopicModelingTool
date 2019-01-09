import requests
res = requests.post('http://localhost:8000/model/1/inference', json={"text":"lalala"})
if res.ok:
    print(res.json())