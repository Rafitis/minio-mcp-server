import requests
import json

url = "http://localhost:11434/api/generate"

data = {
    "model": "llama3.2:latest",
    "prompt": "Can you explain what transformers are in the context of machine learning?",
    "system": "You are a knowledgeable and precise AI assistant with expertise in machine learning and NLP. Provide clear, technical explanations suitable for a developer audience."
}

response = requests.post(
    url, json=data, stream=True
)  # remove the stream=True to get the full response

# check the response status
if response.status_code == 200:
    print("Generated Text:", end=" ", flush=True)
    # Iterate over the streaming response
    for line in response.iter_lines():
        if line:
            # Decode the line and parse the JSON
            decoded_line = line.decode("utf-8")
            result = json.loads(decoded_line)
            # Get the text from the response
            generated_text = result.get("response", "")
            print(generated_text, end="", flush=True)
else:
    print("Error:", response.status_code, response.text)