import requests

url = "http://localhost:63450/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer token-abc123"
}

def send_requests(data: dict) -> str:
    response = requests.post(url, headers=headers, json=data, timeout=3600)
    completion = response.json()

    return completion['choices']