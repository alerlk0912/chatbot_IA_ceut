import sys
import asyncio
if sys.platform.startswith("win") and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import base64
from rag import RAG
from tools import Tools
import os

import nest_asyncio
nest_asyncio.apply()
import warnings

warnings.filterwarnings("ignore", message="`resume_download` is deprecated")
warnings.filterwarnings("ignore", message="Could get FontBBox from font descriptor")
warnings.filterwarnings("ignore", message="Cannot set gray stroke color")
warnings.filterwarnings("ignore", message="Cannot set gray non-stroke color")

st.set_page_config(
    page_title="🤖 Asistente Virtual CEUT",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

from agent import Agent

from memory import ConversationMemory  # IMPORTA tu clase memory

import logging

logging.basicConfig(
    filename="logs/main.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

@st.cache_resource
def cargar_chat_engine():
    logging.info("📦 Iniciando carga del motor de chat...")
    tools = Tools(tavily_api_key=os.getenv("TAVILY_API_KEY"))
    logging.info(f"🔧 Tools instanciado correctamente: {type(tools)}")
    
    # Paso 1: Cargar e indexar documentos si es necesario
    persist_path = "./data/chroma_db"
    needs_indexing = True

    rag = RAG(persist_directory=persist_path, tools=tools)
    
    stats = rag.get_collection_stats()
    logging.info(f"📊 DOCUMENTOS EN BASE: {stats['total_documents']}")
    
    if needs_indexing:
        logging.info("📂 No hay base persistente o está vacía. Se cargarán documentos desde carpeta 'data/'.")
        documents = tools.load_pdfs_from_folder("data")
        for doc in documents:
            logging.info(f"📝 Documento: {doc.metadata.get('source', 'desconocido')}")
        
        success = rag.index_documents(documents, document_name="ceut")
        stats = rag.get_collection_stats()
        
        if success:
            logging.info(f"✅ Indexación exitosa. Total documentos indexados: {stats['total_documents']}")
        else:
            logging.warning("⚠️ Falló la indexación de documentos.")
    else:
        stats = rag.get_collection_stats()
        logging.info(f"📚 Sistema RAG inicializado. Documentos ya indexados: {stats['total_documents']}")

    # Paso 3: Inicializar memoria y agente
    memory = ConversationMemory(session_file="./data/sessions.json", user_id="default_user")
    logging.info("🧠 Memoria de conversación inicializada.")

    return Agent(rag_system=rag, tools=tools, memory=memory)


def render_header():
    logo_base64 = get_base64_image("ceut-logo.png")
    if logo_base64:
        st.markdown(f"""
        <div class="header-container">
            <div class="logo-container">
                <img src="data:image/png;base64,{logo_base64}" alt="CEUT Santa Fe" class="logo-image">
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="header-container">
            <div class="logo-container">
                <h1 style="color: #2563eb; text-align: center; margin: 0;">🎓 CEUT SANTA FE</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_quick_questions():
    st.markdown('<div class="quick-questions-title">Preguntas Frecuentes</div>', unsafe_allow_html=True)
    quick_questions = [
        {"text": "¿Qué becas están disponibles?", "category": "Becas", "icon": "🎓"},
        {"text": "¿Qué actividades deportivas hay?", "category": "Deportes", "icon": "👥"},
        {"text": "¿Teléfonos Útiles de la UTN Santa Fe?", "category": "Contacto", "icon": "💬"},
        {"text": "¿Cuándo es el próximo evento?", "category": "Eventos", "icon": "📅"}
    ]
    for i, question in enumerate(quick_questions):
        if st.button(f"{question['icon']} {question['text']}", key=f"quick_{i}", use_container_width=True):
            st.session_state.input_usuario = question['text']
            st.session_state.send_message = True
            st.rerun()

def render_contact_info():
    st.markdown("""
    <div class="info-card info-horarios">
        <h4>🕐 Horarios de Atención</h4>
        <p>Lunes a Viernes: 08:00 - 21:00</p>
    </div>
    <div class="info-card info-contacto">
        <h4>💬 Contacto</h4>
        <p>Ig: <a href="https://www.instagram.com/ceut.frsf/" target="_blank">ceut.frsf</a></p>
    </div>
    <div class="info-card info-ubicacion">
        <h4>📍 Ubicación</h4>
        <p>Aula 0, UTN Santa Fe</p>
    </div>
    """, unsafe_allow_html=True)

def render_chat_messages():
    if st.session_state.historial:
        for entrada, salida in st.session_state.historial:
            if entrada.strip():
                st.markdown(f"""
                <div class="message-container user-message">
                    <div class="message-content user">
                        <div class="avatar user-avatar">👤</div>
                        <div class="message-text">{entrada}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="message-container bot-message">
                <div class="message-content bot">
                    <div class="avatar bot-avatar">🤖</div>
                    <div class="message-text">{salida}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def limpiar_historial():
    st.session_state.historial = [("", "¡Hola! 👋 Soy el asistente virtual del Centro de Estudiantes UTN FRSF. Estoy aquí para ayudarte.")]

def main():
    load_css()

    if "historial" not in st.session_state:
        limpiar_historial()
    if "input_usuario" not in st.session_state:
        st.session_state.input_usuario = ""
    if "send_message" not in st.session_state:
        st.session_state.send_message = False

    agent = cargar_chat_engine()  # 🟢 Renombrado por claridad
    render_header()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown("""
        <div class="chat-header">
            <h2>🤖 Asistente Virtual CEUT</h2>
            <span class="powered-badge">Powered by Groq</span>
        </div>
        """, unsafe_allow_html=True)

        render_chat_messages()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        with st.form(key="chat_form", clear_on_submit=True):
            col_input, col_send, col_clear = st.columns([3, 1, 1])
            with col_input:
                input_usuario = st.text_input("Mensaje", value=st.session_state.input_usuario, placeholder="Escribe tu pregunta aquí...", key="chat_input_form", label_visibility="collapsed")
            with col_send:
                send_button = st.form_submit_button("Enviar", use_container_width=True)
            with col_clear:
                clear_button = st.form_submit_button("🧹 Limpiar", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        tab1, tab2 = st.tabs(["Preguntas", "Información"])
        with tab1:
            render_quick_questions()
        with tab2:
            render_contact_info()

    if clear_button:
        limpiar_historial()
        st.rerun()

    if (send_button and input_usuario) or st.session_state.send_message:
        if st.session_state.send_message:
            input_usuario = st.session_state.input_usuario
            st.session_state.send_message = False
            st.session_state.input_usuario = ""

        with st.spinner("🤖 Pensando..."):
            try:
                resultado = agent.generate_response(input_usuario)  # 🟢 Llamamos a agent, no rag
                respuesta = resultado['response']

                # 🟢 Podés mostrar qué sistemas se usaron, si querés:
                sistemas = []
                if resultado.get("context_used"):
                    sistemas.append("📄 RAG")
                if resultado.get("tools_used"):
                    sistemas.append("🛠️ Tools")

                if sistemas:
                    respuesta += f"\n\n_Respuesta generada usando: {' + '.join(sistemas)}_"

                st.session_state.historial.append((input_usuario, respuesta))
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
