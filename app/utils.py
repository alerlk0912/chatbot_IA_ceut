# utils.py
from dotenv import load_dotenv
import os

def cargar_clave():
    load_dotenv()
    return os.getenv("OPENAI_API_KEY")
