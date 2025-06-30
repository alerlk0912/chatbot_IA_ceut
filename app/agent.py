import os
import json
from dotenv import load_dotenv
from groq import Groq
from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from sentence_transformers import SentenceTransformer

load_dotenv()

class Agent:
    def __init__(self, rag_system=None, tools: Optional[object] = None, memory=None):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("Falta GROQ_API_KEY en .env")

        self.client = Groq(api_key=self.groq_api_key)
        self.model = "llama-3.3-70b-versatile"
        self.rag_system = rag_system
        self.tools = tools or []

        self.temperature = 0.3
        self.max_tokens = 1000
        self.system_prompt = (
            "Eres un asistente del Centro de Estudiantes de la UTN Santa Fe. "
            "Responde de forma directa y concisa usando la información disponible. "
            "Si usas documentos o herramientas, menciona brevemente la fuente pero mantén la respuesta clara y al punto."
        )

        self.memory = memory

    def process_query(self, query: str, context: str = "", history: Optional[List[dict]] = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history is None and self.memory:
            history = self.memory.get_history()
        if history:
            messages.extend(history)

        user_message = f"{context}\n\nPregunta: {query}" if context else query
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            respuesta_text = response.choices[0].message.content

            if self.memory:
                self.memory.add_message("user", user_message)
                self.memory.add_message("assistant", respuesta_text)

            return respuesta_text

        except Exception as e:
            return f"Error: {e}"

    def generate_response(self, query: str, history: Optional[List[dict]] = None) -> dict:
        reasoning_steps = []
        context = ""

        if self.rag_system:
            doc_context = self.rag_system.get_context(query)
            if doc_context:
                context += f"\n\n[Contexto RAG]:\n{doc_context}"
                reasoning_steps.append("Se usó contexto de RAG.")

        tool_outputs = []
        used_tools = []

        if self.tools and self._needs_tools(query):
            tools_list = self.tools.list_all_tools() if hasattr(self.tools, 'list_all_tools') else self.tools

            for tool in tools_list:
                if self._tool_matches_query(tool.name, query):
                    try:
                        output = tool.invoke({"query": query})
                        tool_outputs.append(f"{tool.name} → {output}")
                        used_tools.append(tool.name)
                    except Exception as e:
                        tool_outputs.append(f"{tool.name} falló: {e}")

            if tool_outputs:
                context += "\n\n[Resultados de herramientas]:\n" + "\n".join(tool_outputs)
                reasoning_steps.append("Se invocaron herramientas: " + ", ".join(used_tools))

        response = self.process_query(query, context=context, history=history)

        return {
            "response": response,
            "reasoning_steps": reasoning_steps,
            "context_used": bool(context),
            "tools_used": used_tools
        }

    def _needs_tools(self, query: str) -> bool:
        keywords = [
            "calcular", "operación", "hora", "fecha", "buscar", "web", "api",
            "temperatura", "formatear", "pdf", "clima", "validar", "email"
        ]
        return any(k in query.lower() for k in keywords)

    def _tool_matches_query(self, tool_name: str, query: str) -> bool:
        return tool_name.lower() in query.lower()

    def parse_json_response(self, query: str, schema: Optional[dict] = None) -> dict:
        prompt = (
            query + "\n\nDevuelve el resultado en formato JSON."
            if not schema else query + f"\n\nDevuelve un JSON que cumpla con este schema:\n{json.dumps(schema, indent=2)}"
        )

        try:
            response = self.process_query(prompt)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            return {"error": "No se encontró JSON válido", "output": response}
        except Exception as e:
            return {"error": str(e)}

    def update_config(self, temperature=None, max_tokens=None, system_prompt=None):
        if temperature is not None:
            self.temperature = max(0.0, min(2.0, temperature))
        if max_tokens is not None:
            self.max_tokens = max(50, min(4000, max_tokens))
        if system_prompt:
            self.system_prompt = system_prompt

    def get_config(self):
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "has_rag": self.rag_system is not None,
            "tools_loaded": [tool.name for tool in self.tools]
        }

# 🧠 Integración para llama-index
def configure_llm():
    from llama_index.llms.groq import Groq as LlamaGroq
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings

    llm = LlamaGroq(model="llama3-8b-8192", api_key=os.getenv("GROQ_API_KEY"))
    Settings.llm = llm
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
