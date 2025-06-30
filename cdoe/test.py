import requests
import json

response = requests.post('http://localhost:8080/run_code', json={
    'code': '''
print("Hello world")
print(2323 + 2346347)
''',
    'language': 'python',
})

print(json.dumps(response.json(), indent=2))