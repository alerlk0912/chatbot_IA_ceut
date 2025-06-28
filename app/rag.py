import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from sklearn.decomposition import PCA
import plotly.express as px

from tools import Tools
from llama_index.core import VectorStoreIndex

class RAG:
    def __init__(self, persist_directory="./data/chroma_db", tools=None, tavily_api_key=None):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)

        try:
            self.collection = self.client.get_collection(name="documents")
        except:
            self.collection = self.client.create_collection(name="documents")

        self.embeddings_cache = {}
        self.tools = tools if tools else Tools(tavily_api_key=tavily_api_key)

    def load_documents(self, text):
        return [s.strip() for s in re.split(r'\.\s*', text) if len(s.strip()) > 10]

    def index_documents(self, documents, document_name="default"):
        if isinstance(documents, str):
            documents = self.load_documents(documents)
        if not documents:
            return False

        try:
            embeddings = self.model.encode(documents)
            ids = [f"{document_name}_{i}" for i in range(len(documents))]
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                ids=ids,
                metadatas=[{"source": document_name, "sentence_id": i} for i in range(len(documents))]
            )
            self.embeddings_cache[document_name] = {
                'embeddings': embeddings,
                'documents': documents
            }
            return True
        except Exception as e:
            print(f"Error indexando documentos: {e}")
            return False

    def search(self, query, top_k=3):
        if not query.strip():
            return []

        try:
            query_embedding = self.model.encode([query])
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k
            )

            return [
                {
                    'document': doc,
                    'similarity': 1 - dist,
                    'source': meta.get('source', 'local'),
                    'distance': dist
                }
                for doc, dist, meta in zip(
                    results['documents'][0],
                    results['distances'][0],
                    results['metadatas'][0]
                )
            ]
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []

    def get_rag_results(self, query, top_k=3, include_web=True):
        """
        Devuelve los resultados relevantes (locales y web) para un query.
        """
        results = {
            "documents": [],
            "web_results": [],
            "combined_context": "",
            "sources": [],
            "confidence": 0.0
        }

        doc_results = self.search(query, top_k=top_k)
        if include_web:
            if self.tools.tavily_client:
                web_results = self.tools.search_web_tavily(query, max_results=top_k)
            else:
                web_results = self.tools.search_web_duckduckgo(query, max_results=top_k)
        else:
            web_results = None

        context_parts = []
        similarities = []

        for res in doc_results:
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
                results["web_results"].append({
                    'title': title,
                    'snippet': snippet,
                    'url': url
                })
                results["sources"].append(url)

        results["combined_context"] = "\n\n".join(context_parts)
        results["confidence"] = float(np.mean(similarities)) if similarities else 0.0
        return results

    def get_context(self, query, max_context_length=1000, include_web=True):
        """
        Devuelve solo el contexto en texto plano, para usar en prompts.
        """
        rag_info = self.get_rag_results(query, include_web=include_web)
        context = rag_info["combined_context"]
        return context[:max_context_length]

    def get_collection_stats(self):
        try:
            return {
                'total_documents': self.collection.count(),
                'collection_name': self.collection.name
            }
        except:
            return {'total_documents': 0, 'collection_name': 'documents'}

    def clear_collection(self):
        try:
            self.client.delete_collection(name="documents")
            self.collection = self.client.create_collection(name="documents")
            self.embeddings_cache.clear()
            return True
        except Exception as e:
            print(f"Error limpiando colección: {e}")
            return False

    def visualize_embeddings(self, document_name=None):
        if not self.embeddings_cache:
            return None
        try:
            if document_name and document_name in self.embeddings_cache:
                data = self.embeddings_cache[document_name]
                embeddings = data['embeddings']
                documents = data['documents']
                sources = [document_name] * len(documents)
            else:
                embeddings_list, documents_list, sources_list = [], [], []
                for name, data in self.embeddings_cache.items():
                    embeddings_list.append(data['embeddings'])
                    documents_list.extend(data['documents'])
                    sources_list.extend([name] * len(data['documents']))
                embeddings = np.vstack(embeddings_list)
                documents = documents_list
                sources = sources_list

            pca = PCA(n_components=2)
            pca_embeddings = pca.fit_transform(embeddings)
            df = pd.DataFrame(pca_embeddings, columns=['PCA1', 'PCA2'])
            df['text'] = documents
            df['source'] = sources
            fig = px.scatter(df, x='PCA1', y='PCA2', color='source', hover_data=['text'],
                             title='Visualización de Embeddings')
            fig.update_layout(hovermode='closest')
            return fig
        except Exception as e:
            print(f"Error en visualización: {e}")
            return None

    def chat(self, query):
        context = self.get_context(query)
        return context if context else "No encontré información relevante en documentos ni en la web."

# Compatibilidad con LlamaIndex
def create_index(documents):
    return VectorStoreIndex.from_documents(documents)

def create_chat_engine(index, verbose=False):
    return index.as_chat_engine(chat_mode="context", verbose=verbose)
