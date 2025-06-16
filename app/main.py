import streamlit as st
import base64
from rag import cargar_documento, buscar_contexto
from agent import query_llm
from tools import generar_texto_links

# Configuración inicial de la app
st.set_page_config(
    page_title="🤖 Asistente Virtual CEUT",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para cargar CSS y forzar estilos personalizados
def load_css():
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Función para convertir imagen a base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Cargar documentos PDF una vez
@st.cache_resource
def cargar_datos():
    return cargar_documento("data/faqs.pdf")

# Función para mostrar el header con logo
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

# Función para mostrar preguntas rápidas (versión original corregida)
def render_quick_questions():
    st.markdown('<div class="quick-questions-title">Preguntas Frecuentes</div>', unsafe_allow_html=True)
    
    quick_questions = [
        {"text": "¿Qué becas están disponibles?", "category": "Becas", "icon": "🎓", "color": "blue"},
        {"text": "¿Cuándo es el próximo evento?", "category": "Eventos", "icon": "📅", "color": "green"},
        {"text": "¿Cómo me contacto con el centro?", "category": "Contacto", "icon": "💬", "color": "orange"},
        {"text": "¿Qué actividades deportivas hay?", "category": "Deportes", "icon": "👥", "color": "purple"},
        {"text": "¿Cuáles son los horarios de atención?", "category": "Horarios", "icon": "🕐", "color": "gray"},
        {"text": "¿Qué dice el reglamento de becas?", "category": "Documentos", "icon": "📄", "color": "red"}
    ]
    
    for i, question in enumerate(quick_questions):
        if st.button(
            f"{question['icon']} {question['text']}", 
            key=f"quick_{i}",
            use_container_width=True
        ):
            st.session_state.input_usuario = question['text']
            st.session_state.send_message = True
            st.rerun()

# Función para mostrar información de contacto
def render_contact_info():
    st.markdown("""
    <div class="info-card info-horarios">
        <h4 style="margin: 0 0 8px 0; display: flex; align-items: center; gap: 8px;">
            🕐 Horarios de Atención
        </h4>
        <p style="margin: 0; color: #1e40af;">Lunes a Viernes: 9:00 - 18:00</p>
    </div>
    
    <div class="info-card info-contacto">
        <h4 style="margin: 0 0 8px 0; display: flex; align-items: center; gap: 8px;">
            💬 Contacto
        </h4>
        <p style="margin: 0; color: #166534; font-size: 14px;">centro@frsf.utn.edu.ar</p>
        <p style="margin: 0; color: #166534; font-size: 14px;">(0342) 460-1579</p>
    </div>
        
    <div class="info-card info-ubicacion">
        <h4 style="margin: 0 0 8px 0; display: flex; align-items: center; gap: 8px;">
            📍 Ubicación
        </h4>
        <p style="margin: 0; color: #9a3412; font-size: 14px;">Lavaise 610, Santa Fe, Argentina</p>
    </div>
    """, unsafe_allow_html=True)

# Función para mostrar mensajes del chat
def render_chat_messages():
    if st.session_state.historial:
        for i, (entrada, salida) in enumerate(st.session_state.historial):
            # Mensaje del usuario (solo si no está vacío)
            if entrada.strip():
                st.markdown(f"""
                <div class="message-container user-message">
                    <div class="message-content user">
                        <div class="avatar user-avatar">👤</div>
                        <div class="message-text">{entrada}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Mensaje del bot
            st.markdown(f"""
            <div class="message-container bot-message">
                <div class="message-content bot">
                    <div class="avatar bot-avatar">🤖</div>
                    <div class="message-text">{salida}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Función para limpiar historial
def limpiar_historial():
    st.session_state.historial = []
    # Agregar mensaje de bienvenida nuevamente
    st.session_state.historial.append((
        "",
        "¡Hola! 👋 Soy el asistente virtual del Centro de Estudiantes UTN FRSF. Estoy aquí para ayudarte con información sobre becas, eventos, trámites y todo lo que necesites saber sobre la vida universitaria. ¿En qué puedo ayudarte hoy?"
    ))

# Función principal
def main():
    # Cargar CSS con forzado de estilos
    load_css()
    
    # Inicializar estados
    if "historial" not in st.session_state:
        st.session_state.historial = []
        # Mensaje de bienvenida
        st.session_state.historial.append((
            "",
            "¡Hola! 👋 Soy el asistente virtual del Centro de Estudiantes UTN FRSF. Estoy aquí para ayudarte con información sobre becas, eventos, trámites y todo lo que necesites saber sobre la vida universitaria. ¿En qué puedo ayudarte hoy?"
        ))
    
    if "input_usuario" not in st.session_state:
        st.session_state.input_usuario = ""
    
    if "send_message" not in st.session_state:
        st.session_state.send_message = False
    
    # Cargar documentos
    documentos = cargar_datos()
    
    # Renderizar header
    render_header()
    
    # Layout principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown("""
        <div class="chat-header">
            <h2>🤖 Asistente Virtual CEUT</h2>
            <span class="powered-badge">Powered by Groq</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Área de mensajes
        with st.container():
            render_chat_messages()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input del usuario con funcionalidad Enter
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        # Crear formulario para habilitar Enter
        with st.form(key="chat_form", clear_on_submit=True):
            col_input, col_send, col_clear = st.columns([3, 1, 1])
            
            with col_input:
                input_usuario = st.text_input(
                    "Mensaje",  # <- Agregar un label apropiado
                    value=st.session_state.input_usuario,
                    placeholder="Escribe tu pregunta aquí...",
                    key="chat_input_form",
                    label_visibility="collapsed"  # Esto lo mantiene oculto visualmente
                )
            
            with col_send:
                #st.html('<button class="gradient-button send-button" onclick="submitForm()">▶️ Enviar</button>')
                send_button = st.form_submit_button("Enviar", use_container_width=True)

            with col_clear:
                #st.html('<button class="gradient-button clear-button" onclick="submitForm()">🧹 Limpiar</button>')
                clear_button = st.form_submit_button("🧹 Limpiar", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Sidebar con pestañas (solo Preguntas e Información)
        tab1, tab2 = st.tabs(["Preguntas", "Información"])
        
        with tab1:
            render_quick_questions()
        
        with tab2:
            render_contact_info()

    # Procesamiento del botón limpiar
    if clear_button:
        limpiar_historial()
        st.rerun()
    
    # Procesamiento de la consulta (Enter o botón Enviar)
    if (send_button and input_usuario) or st.session_state.send_message:
        if st.session_state.send_message:
            input_usuario = st.session_state.input_usuario
            st.session_state.send_message = False
            st.session_state.input_usuario = ""
        
        with st.spinner("🔎 Buscando información relevante..."):
            try:
                contexto_rag = buscar_contexto(input_usuario, documentos)
                links_utiles = generar_texto_links()
                
                MAX_CONTEXT_CHARS = 3000
                contexto_recortado = contexto_rag[:MAX_CONTEXT_CHARS]
                
                # Preparar prompt
                prompt = [
                    {"role": "system", "content": "Sos un chatbot del centro de estudiantes de UTN FRSF que ayuda a los estudiantes con sus dudas. Proporciona respuestas claras y concisas basadas en la información proporcionada."},
                    {"role": "user", "content": f"{input_usuario}\n\nContexto:\n{contexto_recortado}\n\nLinks:\n{links_utiles}"}
                ]
                
                # Obtener respuesta
                respuesta = query_llm(prompt)
                
                # Guardar en historial
                st.session_state.historial.append((input_usuario, respuesta))
                st.rerun()
                
            except Exception as e:
                st.error(f"⚠️ Ocurrió un error: {e}")

if __name__ == "__main__":
    main()