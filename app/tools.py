import os
import re
import pdfplumber
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import Counter
from langchain.tools import tool
from llama_index.core import Document
from duckduckgo_search import DDGS

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# --- MODELO DE CHUNK ---
@dataclass
class Chunk:
    content: str
    chunk_type: str  # 'table', 'text', 'heading', 'section'
    metadata: Dict[str, Any]
    source: str
    page: int = 0
    confidence: float = 1.0

COMMON_CARRERAS = {
    'sistemas': ['sistemas', 'informática', 'informacion'],
    'industrial': ['industrial'],
    'civil': ['civil'],
    'mecanica': ['mecánica', 'mecanico'],
    'electrica': ['eléctrica'],
}

import logging

logging.basicConfig(
    filename="logs/pdf_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# --- DETECTOR DE PATRONES ACADÉMICOS ---
class AcademicPatternDetector:
    def __init__(self):
        self.year_patterns = [
            (re.compile(r'\b(1°|PRIMER)\s+AÑO\b', re.IGNORECASE), 1),
            (re.compile(r'\b(2°|SEGUNDO)\s+AÑO\b', re.IGNORECASE), 2),
            (re.compile(r'\bTERCER\s+AÑO\b', re.IGNORECASE), 3),
            (re.compile(r'\bCUARTO\s+AÑO\b', re.IGNORECASE), 4),
            (re.compile(r'\bQUINTO\s+AÑO\b', re.IGNORECASE), 5),
        ]
        self.section_patterns = {
            'correlativas': re.compile(r'\bCORRELATIVAS\b', re.IGNORECASE),
            'materias': re.compile(r'MATERIAS\s+(OBLIGATORIAS|ELECTIVAS)?', re.IGNORECASE),
            'plan_estudios': re.compile(r'\bPLAN DE ESTUDIOS\b', re.IGNORECASE),
        }

    def enrich_chunk_metadata(self, chunk: Chunk) -> Chunk:
        text = chunk.content.upper()
        for pattern, año in self.year_patterns:
            if pattern.search(text):
                chunk.metadata['año'] = año
                chunk.metadata['seccion_padre'] = pattern.pattern
        for tipo, pattern in self.section_patterns.items():
            if pattern.search(text):
                chunk.metadata['tipo_contenido'] = tipo
        return chunk

# --- PROCESADOR DE PDF ---
class GenericPDFProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks: List[Chunk] = []
        self.document_patterns: Dict[str, Any] = {}

    def process_folder(self, folder_path: str = "data") -> List[Chunk]:
        if not os.path.exists(folder_path):
            logging.warning(f"Carpeta no existe: {folder_path}")
            return []
        pdfs = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        if not pdfs:
            logging.warning(f"No se encontraron PDFs en: {folder_path}")
            return []
        all_chunks = []
        for f in pdfs:
            path = os.path.join(folder_path, f)
            logging.info(f"Procesando PDF: {path}")
            c = self.process_pdf(path)
            logging.info(f"Se extrajeron {len(c)} chunks del PDF {f}")
            all_chunks.extend(c)
        self._analyze_document_patterns(all_chunks)
        self.chunks = all_chunks
        return all_chunks

    def process_pdf(self, path: str) -> List[Chunk]:
        chunks = []
        detector = AcademicPatternDetector()
        try:
            with pdfplumber.open(path) as pdf:
                carrera = self.detect_carrera(''.join([p.extract_text() or '' for p in pdf.pages[:3]]))
                logging.info(f"Detectada carrera: {carrera} en archivo {os.path.basename(path)}")
                for i, page in enumerate(pdf.pages):
                    logging.info(f"Procesando página {i+1} de {os.path.basename(path)}")
                    chunks += self._extract_tables(page, path, i+1, carrera)
                    text = page.extract_text()
                    if text:
                        for c in self._process_text(text, path, i+1):
                            if carrera:
                                c.metadata['carrera'] = carrera
                            chunks.append(detector.enrich_chunk_metadata(c))
            logging.info(f"Chunks totales extraídos: {len(chunks)} del archivo {os.path.basename(path)}")
        except Exception as e:
            logging.error(f"Error en {path}: {e}")
        return chunks

    def _extract_tables(self, page, src: str, num: int, carrera=None) -> List[Chunk]:
        chunks = []
        try:
            for i, t in enumerate(page.extract_tables()):
                if not t or len(t) < 2: continue
                txt = self._table_to_text(t)
                meta = {
                    'table_id': f"t_{num}_{i}",
                    'rows': len(t), 'cols': len(t[0]) if t[0] else 0,
                    'has_headers': self._detect_table_headers(t)
                }
                if carrera: meta['carrera'] = carrera
                chunks.append(Chunk(txt, 'table', meta, src, num))
        except Exception as e:
            print(f"⚠️ Tabla pág {num}: {e}")
        return chunks

    def _table_to_text(self, table: List[List]) -> str:
        if not table: return ""
        has_headers = self._detect_table_headers(table)
        headers = table[0] if has_headers else []
        txt = "TABLE:\n"
        if headers:
            txt += " | ".join(map(str, headers)) + "\n" + ("-" * 40) + "\n"
        for row in (table[1:] if headers else table):
            if any(row):
                txt += " | ".join(map(str, row)) + "\n"
        return txt

    def _detect_table_headers(self, table: List[List]) -> bool:
        if len(table) < 2: return False
        return sum(1 for c in table[0] if isinstance(c, str) and not c.replace('.', '').isdigit()) > len(table[0]) * 0.7

    def _process_text(self, text: str, src: str, num: int) -> List[Chunk]:
        secciones = self._auto_detect_sections(text)
        if not secciones:
            return self._smart_split_text(text, src, num)
        chunks = []
        for h, cont in secciones:
            if not cont.strip(): continue
            if len(cont) > self.chunk_size * 2:
                sub_chunks = self._smart_split_text(cont, src, num)
                for c in sub_chunks:
                    c.metadata['section_heading'] = h
                    chunks.append(c)
            else:
                chunks.append(Chunk(f"{h}\n\n{cont}", 'section', {
                    'heading': h,
                    'heading_level': self._detect_heading_level(h)
                }, src, num))
        return chunks

    def _auto_detect_sections(self, text: str) -> List[Tuple[str, str]]:
        pats = [
            r'^\s*(\d+\.[\d\.]*\s+[^\n]+)\n',
            r'^\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,})\s*\n',
            r'^\s*([^:\n]{5,}:)\s*\n',
            r'^([^\n]+)\n[-=]{3,}\n',
        ]
        for p in pats:
            m = list(re.finditer(p, text, re.MULTILINE))
            if len(m) < 2: continue
            return [(m[i].group(1).strip(), text[m[i].end():m[i+1].start()].strip() if i+1 < len(m) else text[m[i].end():].strip()) for i in range(len(m))]
        return []

    def _smart_split_text(self, text: str, src: str, num: int) -> List[Chunk]:
        chunks = []
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        current = ""
        for p in paragraphs:
            if len(current) + len(p) > self.chunk_size and current:
                chunks.append(Chunk(current.strip(), 'text', {'paragraph_count': current.count('\n\n')+1}, src, num))
                words = current.split()
                current = ' '.join(words[-self.chunk_overlap:]) + '\n\n' + p
            else:
                current += '\n\n' + p if current else p
        if current.strip():
            chunks.append(Chunk(current.strip(), 'text', {'paragraph_count': current.count('\n\n')+1}, src, num))
        return chunks

    def _analyze_document_patterns(self, chunks: List[Chunk]) -> None:
        all_text = ' '.join(c.content for c in chunks)
        words = re.findall(r'\b[a-záéíóúñü]{3,}\b', all_text.lower())
        self.document_patterns = {
            'frequent_terms': Counter(words).most_common(20),
            'avg_chunk_size': sum(len(c.content) for c in chunks) / len(chunks),
            'table_percentage': sum(1 for c in chunks if c.chunk_type == 'table') / len(chunks)
        }

    def _detect_heading_level(self, heading: str) -> int:
        return heading.count('.') if re.match(r'^\d+\.', heading) else 1

    @staticmethod
    def detect_carrera(text: str) -> Optional[str]:
        text = text.lower()
        for carrera, keywords in COMMON_CARRERAS.items():
            if any(k in text for k in keywords): return carrera
        return None

# --- WRAPPER DE HERRAMIENTAS ---
class Tools:
    def __init__(self, tavily_api_key: Optional[str] = None):
        self.pdf_processor = GenericPDFProcessor(chunk_size=800, chunk_overlap=100)
        self.tavily_client = TavilyClient(api_key=tavily_api_key) if TAVILY_AVAILABLE and tavily_api_key else None

    @tool
    def load_pdfs_from_folder(self, folder_path: str = "data") -> List[Document]:
        """Carga todos los archivos PDF desde una carpeta 
        y los convierte en objetos Document para RAG."""
        chunks = self.pdf_processor.process_folder(folder_path)
        return [Document(text=c.content, metadata=c.metadata) for c in chunks]

    @tool
    def search_web(self, query: str, max_results: int = 3, prefer_tavily: bool = True) -> dict:
        """Realiza una búsqueda web utilizando Tavily o DuckDuckGo y devuelve los resultados relevantes."""
        strategies = []
        if prefer_tavily and self.tavily_client:
            strategies = [('tavily', self.search_web_tavily), ('duckduckgo', self.search_web_duckduckgo)]
        else:
            strategies = [('duckduckgo', self.search_web_duckduckgo)]
            if self.tavily_client:
                strategies.append(('tavily', self.search_web_tavily))
        for _, func in strategies:
            result = func(query, max_results)
            if result and result.get("results"):
                return result
        return {'query': query, 'results': [], 'error': 'No resultados', 'source': 'Ninguno'}

    def search_web_tavily(self, query: str, max_results: int) -> dict:
        try:
            response = self.tavily_client.search(
                query=query, 
                max_results=max_results, 
                search_depth="advanced", 
                include_domains=['frsf.utn.edu.ar', 'ceut-frsf.com.ar']
            )
            return {
                'query': query,
                'results': [{'title': r.get('title', ''), 'url': r.get('url', ''), 'snippet': r.get('content', ''), 'score': r.get('score', 0)} for r in response.get('results', [])],
                'source': 'Tavily AI',
                'total_results': len(response.get('results', []))
            }
        except Exception as e:
            return {'error': f'Error Tavily: {e}'}

    def search_web_duckduckgo(self, query: str, max_results: int) -> dict:
        try:
            with DDGS() as ddgs:
                search_query = f"{query} (site:frsf.utn.edu.ar OR site:ceut-frsf.com.ar)"
                results = ddgs.text(
                    search_query, 
                    max_results=max_results, 
                    region='ar-es', 
                    safesearch='moderate'
                )
                return {
                    'query': query,
                    'results': [{'title': r.get('title', ''), 'url': r.get('href', ''), 'snippet': r.get('body', ''), 'score': 1.0} for r in results],
                    'source': 'DuckDuckGo',
                    'total_results': len(results)
                }
        except Exception as e:
            return {'error': f'Error DuckDuckGo: {e}'}

    def list_all_tools(self) -> List[Any]:
        from langchain.tools import Tool
        return [Tool.from_function(func=getattr(self, attr)) for attr in dir(self) if callable(getattr(self, attr)) and hasattr(getattr(self, attr), "_tool")]
