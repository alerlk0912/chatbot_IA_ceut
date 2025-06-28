from typing import TypedDict, List, Optional, Dict
from langchain.memory import ConversationBufferMemory


class RAGResult(TypedDict, total=False):
    content: str
    score: float
    source: str


class UTNBotState(TypedDict, total=False):
    # 🔹 Input del usuario
    user_query: str
    user_id: str

    # 🔹 Resultados RAG
    rag_results: List[RAGResult]
    rag_confidence: float
    rag_sources: List[str]

    # 🔹 Web search y extracción
    web_urls: List[str]
    extracted_content: str
    extraction_success: bool

    # 🔹 Generación de respuesta
    final_response: str
    response_sources: List[str]

    # 🔹 Memoria conversacional
    conversation_memory: ConversationBufferMemory
    context_summary: str

    # 🔹 Métricas y debugging
    timestamp: str
    processing_time: float
    confidence_scores: Dict[str, float]  # Ej: {"rag": 0.82, "web_content": 0.76}

    # 🔹 Extra (debug y trazabilidad opcional)
    fallback_used: Optional[str]  # "web_search", "rag_only", etc.
    decision_path: Optional[List[str]]  # ["rag_search", "web_search", "web_fetch", ...]
