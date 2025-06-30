import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import re
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Union
from sentence_transformers import SentenceTransformer
import chromadb
from sklearn.decomposition import PCA
import plotly.express as px

from tools import Tools
from llama_index.core import VectorStoreIndex

import logging
logging.basicConfig(
    filename="logs/pdf_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

import tiktoken
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")  # fallback
    return len(enc.encode(text))

class RAG:
    def __init__(self, persist_directory: str = "./data/chroma_db", tools: Optional[Tools] = None, tavily_api_key: Optional[str] = None):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.persist_directory = persist_directory

        try:
            self.collection = self.client.get_collection(name="documents")
        except chromadb.errors.CollectionNotFoundError:
            self.collection = self.client.create_collection(name="documents")

        self.embeddings_cache = {}
        self.tools = tools or Tools(tavily_api_key=tavily_api_key)

    def load_documents(self, text: str) -> List[str]:
        return [s.strip() for s in re.split(r'\.\s*', text) if len(s.strip()) > 10]

    def index_documents(self, documents: Union[str, List], document_name: str = "default") -> bool:
        try:
            if isinstance(documents, str):
                documents = self.load_documents(documents)
            if not documents:
                return False

            if hasattr(documents[0], 'text') and hasattr(documents[0], 'metadata'):
                raw_texts = [d.text for d in documents]
                metadatas = [d.metadata for d in documents]
            else:
                raw_texts = documents
                metadatas = [{"source": document_name, "sentence_id": i} for i in range(len(documents))]

            embeddings = self.model.encode(raw_texts)
            ids = [f"{document_name}_{i}" for i in range(len(raw_texts))]

            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=raw_texts,
                ids=ids,
                metadatas=metadatas
            )

            self.embeddings_cache[document_name] = {
                'embeddings': embeddings,
                'documents': raw_texts
            }
            return True

        except Exception as e:
            print(f"❌ Error indexando documentos: {e}")
            return False

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if not query.strip():
            return []
        try:
            embedding = self.model.encode([query])
            result = self.collection.query(query_embeddings=embedding.tolist(), n_results=top_k)
            
            documents_info = [
                {
                    'document': doc,
                    'similarity': 1 - dist,
                    'source': meta.get('source', 'local'),
                    'distance': dist
                }
                for doc, dist, meta in zip(result['documents'][0], result['distances'][0], result['metadatas'][0])
            ]

            # Loguear info de los docs recuperados
            logging.info(f"[RAG Search] Query: {query}")
            for info in documents_info:
                logging.info(f"[RAG Search] Doc source: {info['source']}, Similarity: {info['similarity']:.4f}")

            return documents_info
        except Exception as e:
            logging.error(f"❌ Error en búsqueda: {e}")
            return []

    def get_rag_results(self, query: str, top_k: int = 3, include_web: bool = True) -> Dict:
        results = {
            "documents": [],
            "web_results": [],
            "combined_context": "",
            "sources": [],
            "confidence": 0.0
        }

        local_results = self.search(query, top_k=top_k)
        web_results = None
        if include_web:
            if self.tools.tavily_client:
                web_results = self.tools.search_web_tavily(query, max_results=top_k)
            else:
                web_results = self.tools.search_web_duckduckgo(query, max_results=top_k)

        context_parts = []
        similarities = []

        for res in local_results:
            context_parts.append(f"📄 {res['document']}")
            similarities.append(res['similarity'])
            results["documents"].append(res)
            results["sources"].append(res['source'])

        if web_results and web_results.get("results"):
            for item in web_results["results"]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                url = item.get("url", "")
                context_parts.append(f"🌐 {title}: {snippet} ({url})")
                results["web_results"].append({'title': title, 'snippet': snippet, 'url': url})
                results["sources"].append(url)

        results["combined_context"] = "\n\n".join(context_parts)
        results["confidence"] = float(np.mean(similarities)) if similarities else 0.0

        # Log de contexto combinado y fuentes
        logging.info(f"[RAG Results] Query: {query}")
        logging.info(f"[RAG Results] Sources: {results['sources']}")
        logging.info(f"[RAG Results] Confidence: {results['confidence']:.4f}")
        logging.debug(f"[RAG Results] Combined context:\n{results['combined_context'][:1000]}")  # Limitar para no llenar logs

        for i, part in enumerate(context_parts):
            logging.info(f"[RAG Results] Context part {i}: {part[:1000]}")  # Primeros 500 caracteres

        return results

    def get_context(self, query: str, max_context_length: int = 7000, include_web: bool = True) -> str:
        rag_info = self.get_rag_results(query, include_web=include_web)
        return rag_info["combined_context"][:max_context_length]

    def get_collection_stats(self) -> Dict[str, Union[int, str]]:
        try:
            return {
                'total_documents': self.collection.count(),
                'collection_name': self.collection.name
            }
        except Exception:
            return {'total_documents': 0, 'collection_name': 'documents'}

    def clear_collection(self) -> bool:
        try:
            self.client.delete_collection(name="documents")
            self.collection = self.client.create_collection(name="documents")
            self.embeddings_cache.clear()
            return True
        except Exception as e:
            print(f"❌ Error limpiando colección: {e}")
            return False

    def visualize_embeddings(self, document_name: Optional[str] = None):
        if not self.embeddings_cache:
            return None
        try:
            if document_name and document_name in self.embeddings_cache:
                data = self.embeddings_cache[document_name]
                embeddings, documents = data['embeddings'], data['documents']
                sources = [document_name] * len(documents)
            else:
                embeddings, documents, sources = [], [], []
                for name, data in self.embeddings_cache.items():
                    embeddings.append(data['embeddings'])
                    documents.extend(data['documents'])
                    sources.extend([name] * len(data['documents']))
                embeddings = np.vstack(embeddings)

            pca = PCA(n_components=2)
            coords = pca.fit_transform(embeddings)
            df = pd.DataFrame(coords, columns=['PCA1', 'PCA2'])
            df['text'] = documents
            df['source'] = sources
            fig = px.scatter(df, x='PCA1', y='PCA2', color='source', hover_data=['text'],
                             title='Visualización de Embeddings')
            fig.update_layout(hovermode='closest')
            return fig
        except Exception as e:
            print(f"❌ Error en visualización: {e}")
            return None

    def chat(self, query: str) -> str:
        context = self.get_context(query, max_context_length=1500)
        logging.info(f"[Chat] Context length: {len(context)}")
        logging.debug(f"[Chat] Context completo:\n{context}")
        if not context.strip():
            return "No encontré información relevante en documentos ni en la web."
        return context
