import requests
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def query_llm(prompt: list, model="llama3-8b-8192"):
    # Convertimos la lista de mensajes al formato esperado por Groq
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": prompt,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

