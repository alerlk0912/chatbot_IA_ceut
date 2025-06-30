import os
import json
from dotenv import load_dotenv
from typing import List, Optional
from langchain_core.tools import Tool
import google.generativeai as genai

load_dotenv()

class Agent:
    def __init__(self, rag_system=None, tools: Optional[object] = None, memory=None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Falta GEMINI_API_KEY en .env")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        self.rag_system = rag_system
        self.tools = tools or []
        self.temperature = 0.3
        self.max_tokens = 2048
        self.system_prompt = (
            "Sos un asistente virtual del Centro de Estudiantes de la UTN Santa Fe. "
            "Respondé de forma clara, concisa y amigable a preguntas sobre materias, planes de estudio, becas, autoridades, inscripción y vida universitaria. "
            "Si usás documentos o enlaces, incluí al final una sección titulada '📎 Enlaces útiles', en donde muestres los links en formato Markdown clickeable: "
            "[Nombre del documento o recurso](https://link.com). "
            "Usá viñetas o listas cuando sea apropiado. No inventes información: si no tenés datos suficientes, indicá que deben consultar los documentos o sitios correspondientes."
        )

        self.memory = memory

    def process_query(self, query: str, context: str = "", history: Optional[List[dict]] = None) -> str:
        try:
            prompt = f"{self.system_prompt}\n\n{context}\n\nUsuario: {query}" if context else f"{self.system_prompt}\n\nUsuario: {query}"
            response = self.model.generate_content(prompt)
            response_text = response.text

            if self.memory:
                self.memory.add_message("user", query)
                self.memory.add_message("assistant", response_text)

            return response_text
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