import requests
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def query_llm(prompt: list, model="llama3-8b-8192"):
    url = "https://api.groq.com/openai/v1/chat/completions" # Esta URL es CORRECTA
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

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Esto lanzará un error para códigos de estado HTTP 4xx/5xx
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP: {http_err}")
        print(f"Respuesta del servidor: {response.text}")
        return f"Error en la solicitud a la API: {response.text}"
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Error de conexión: {conn_err}")
        return "Error de conexión a la API de Groq. Verifica tu internet."
    except requests.exceptions.Timeout as timeout_err:
        print(f"Tiempo de espera agotado: {timeout_err}")
        return "La solicitud a la API de Groq excedió el tiempo de espera."
    except requests.exceptions.RequestException as req_err:
        print(f"Otro error de solicitud: {req_err}")
        return "Ocurrió un error inesperado al comunicarse con la API de Groq."
    except KeyError:
        print(f"Error: La respuesta de la API no contiene el formato esperado. Respuesta completa: {response.json()}")
        return "Error: Formato de respuesta inesperado de la API."
