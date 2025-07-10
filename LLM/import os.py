import os
import requests

model_url = "https://gpt4all.io/models/mistral-7b.Q4_K_M.gguf"
model_path = os.path.expanduser("C:/Users/massimiliano.catapan/.cache/gpt4all/mistral-7b.Q4_K_M.gguf")

if not os.path.exists(model_path):
    print("Downloading Mistral 7B model...")
    response = requests.get(model_url, stream=True)
    with open(model_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download completed!")
else:
    print("Model already exists.")
