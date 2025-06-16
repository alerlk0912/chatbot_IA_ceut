from llama_index.core import VectorStoreIndex
from tools import load_pdfs_from_folder

def create_index(documents):
    return VectorStoreIndex.from_documents(documents)

def create_chat_engine(index, verbose=False):
    return index.as_chat_engine(chat_mode="context", verbose=verbose)
