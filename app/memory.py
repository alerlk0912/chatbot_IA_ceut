import json
import os
from typing import List, Dict, Optional

class ConversationMemory:
    def __init__(self, session_file: str = "./data/sessions.json", user_id: Optional[str] = None):
        self.session_file = session_file
        self.user_id = user_id or "default_user"
        self.sessions = self.load_from_file()

        # Asegurar que la sesión del usuario exista
        if self.user_id not in self.sessions:
            self.sessions[self.user_id] = []

    def add_message(self, role: str, content: str):
        """Agrega un mensaje al historial y guarda automáticamente"""
        self.sessions[self.user_id].append({
            "role": role,
            "content": content
        })
        self.auto_save()

    def get_history(self) -> List[Dict[str, str]]:
        """Devuelve el historial de mensajes para el usuario"""
        return self.sessions.get(self.user_id, [])

    def save_to_file(self):
        """Guarda todas las sesiones en JSON"""
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(self.sessions, f, indent=2, ensure_ascii=False)

    def load_from_file(self) -> Dict[str, List[Dict[str, str]]]:
        """Carga sesiones desde archivo JSON si existe, sino retorna dict vacío"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        else:
            return {}

    def auto_save(self):
        """Guarda automáticamente después de cada mensaje agregado"""
        self.save_to_file()

    def clear_history(self):
        """Borra el historial del usuario y guarda"""
        self.sessions[self.user_id] = []
        self.auto_save()
