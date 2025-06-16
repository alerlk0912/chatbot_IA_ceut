import os
from dotenv import load_dotenv
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

def configure_llm():
    load_dotenv()
    llm = Groq(model="llama3-8b-8192", api_key=os.getenv("GROQ_API_KEY"))
    Settings.llm = llm
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
