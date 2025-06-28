import os
import re
import datetime
import math
import requests
import pdfplumber
from typing import Dict, Any, Optional, List
from langchain.tools import tool
from llama_index.core import Document
from duckduckgo_search import DDGS

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

class Tools:
    def __init__(self, tavily_api_key: Optional[str] = None):
        self.tavily_api_key = tavily_api_key
        self.tavily_client = None

        if TAVILY_AVAILABLE and tavily_api_key:
            try:
                self.tavily_client = TavilyClient(api_key=tavily_api_key)
            except Exception as e:
                print(f"Error inicializando Tavily: {e}")

    # --- BÚSQUEDA WEB ---

    def search_web_tavily(self, query: str, max_results: int = 3):
        if not self.tavily_client:
            return None
        try:
            response = self.tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_domains=['frsf.utn.edu.ar']
            )
            return {
                'query': query,
                'results': [
                    {
                        'title': r.get('title', ''),
                        'url': r.get('url', ''),
                        'snippet': r.get('content', ''),
                        'score': r.get('score', 0)
                    }
                    for r in response.get('results', [])
                ],
                'source': 'Tavily AI',
                'total_results': len(response.get('results', []))
            }
        except Exception as e:
            return {'error': f'Error Tavily: {e}'}

    def search_web_duckduckgo(self, query: str, max_results: int = 3):
        try:
            results = []
            with DDGS() as ddgs:
                search = ddgs.text(
                    f"{query} site:frsf.utn.edu.ar",
                    max_results=max_results,
                    region='ar-es',
                    safesearch='moderate'
                )
                for r in search:
                    results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', ''),
                        'score': 1.0
                    })
            return {
                'query': query,
                'results': results,
                'source': 'DuckDuckGo',
                'total_results': len(results)
            }
        except Exception as e:
            return {'error': f'Error DuckDuckGo: {e}'}

    @tool
    def search_web(self, query: str, max_results: int = 3, prefer_tavily: bool = True) -> dict:
        """
        Busca en la web usando Tavily o DuckDuckGo con fallback automático.
        """
        strategies = []
        if prefer_tavily and self.tavily_client:
            strategies = [('tavily', self.search_web_tavily), ('duckduckgo', self.search_web_duckduckgo)]
        else:
            strategies = [('duckduckgo', self.search_web_duckduckgo)]
            if self.tavily_client:
                strategies.append(('tavily', self.search_web_tavily))

        for name, func in strategies:
            result = func(query, max_results)
            if result and result.get("results"):
                return result

        return {
            'query': query,
            'results': [],
            'error': 'No se pudo obtener resultados',
            'source': 'Ninguno'
        }

    # --- PDF LOADER ---

    @tool
    def load_pdfs_from_folder(self, folder_path: str = "data") -> List[Document]:
        """
        Carga documentos PDF desde una carpeta.
        """
        documents = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                with pdfplumber.open(os.path.join(folder_path, filename)) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if not text:
                            continue
                        blocks = [t.strip() for t in re.split(r'\n{2,}', text) if len(t.strip()) > 5]
                        for block in blocks:
                            documents.append(Document(
                                text=block,
                                metadata={"page": i + 1, "source": filename}
                            ))
        return documents

    # --- HERRAMIENTAS GENÉRICAS ---

    @tool
    def calculate(self, expression: str) -> str:
        """
        Evalúa una expresión matemática segura.
        """
        try:
            safe_expression = re.sub(r'[^0-9+\-*/.() ]', '', expression)
            result = eval(safe_expression, {"__builtins__": {}}, {k: v for k, v in math.__dict__.items() if not k.startswith("__")})
            return f"{safe_expression} = {result}"
        except ZeroDivisionError:
            return "Error: División por cero"
        except Exception as e:
            return f"Error: {e}"

    @tool
    def get_current_time(self) -> str:
        """
        Devuelve la fecha y hora actual.
        """
        now = datetime.datetime.now()
        return now.strftime("%A, %d de %B de %Y - %H:%M:%S")

    @tool
    def call_api(self, url: str, method: str = "GET") -> dict:
        """
        Realiza una llamada simple a API externa.
        """
        try:
            response = requests.request(method.upper(), url, timeout=10)
            return {
                'status_code': response.status_code,
                'data': response.text[:500]
            }
        except Exception as e:
            return {"error": str(e)}

    @tool
    def validate_email(self, email: str) -> bool:
        """
        Valida el formato de un email.
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @tool
    def format_text(self, text: str, format_type: str = "uppercase") -> str:
        """
        Formatea texto en diferentes estilos.
        """
        formats = {
            'uppercase': text.upper(),
            'lowercase': text.lower(),
            'title': text.title(),
            'capitalize': text.capitalize(),
            'reverse': text[::-1]
        }
        return formats.get(format_type, text)

    @tool
    def get_weather(self, location: str) -> dict:
        """
        Simula una respuesta de clima.
        """
        return {
            'location': location,
            'temperature': '22°C',
            'condition': 'Soleado',
            'note': 'Datos simulados'
        }

    # --- REGISTRO ---

    def list_all_tools(self) -> List[Any]:
        """
        Devuelve todas las herramientas disponibles como LangChain tools.
        """
        from langchain.tools import Tool
        return [
            Tool.from_function(func=getattr(self, attr))
            for attr in dir(self)
            if callable(getattr(self, attr)) and hasattr(getattr(self, attr), "_tool")
        ]
