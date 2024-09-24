import requests
import json

# Provide the endpoint and the api key
endpoint_url = ""
api_key = ""

# Define the headers
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

payload = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Azure?"}
    ],
    "max_tokens": 100,
    "temperature": 0.7,
    "top_p": 1.0,
    "n": 1,
    "stop": None
}

# Send the request
response = requests.post(endpoint_url, headers=headers, data=json.dumps(payload))

# Check the response
if response.status_code == 200:
    result = response.json()
    print("Response:", result["choices"][0]["message"]["content"].strip())
else:
    print("Error:", response.status_code, response.text)