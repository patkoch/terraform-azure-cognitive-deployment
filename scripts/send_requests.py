import requests
import json

# Provide the endpoint and the api key
endpoint_url = "<enter the endpoint url here"
api_key = "<enter the api key here>"

# Define the headers
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

# Define the payload with instructions and context
# Define the payload with instructions and context
payload = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Which AI model are you?"}
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