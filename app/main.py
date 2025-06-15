import streamlit as st
import time
# from rag import cargar_documento, buscar_contexto
# from agent import query_llm
# from tools import generar_texto_links

# Configuración inicial de la app
st.set_page_config(
    page_title="🤖 Chatbot UTN FRSF", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para estilo moderno
st.markdown("""
<style>
    /* Gradiente de fondo */
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 50%, #e8f5e8 100%);
    }
    
    /* Header con logo */
    .header-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid rgba(229, 231, 235, 0.8);
        text-align: center;
        position: relative;
    }
    
    /* Badge IA Asistente */
    .ai-badge {
        display: inline-block;
        background: linear-gradient(45deg, #3b82f6, #10b981);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        margin-top: 10px;
        animation: pulse 2s infinite;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Contenedor principal del chat */
    .chat-container {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        min-height: 500px;
    }
    
    /* Header del chat */
    .chat-header {
        background: linear-gradient(135deg, #3b82f6, #10b981);
        color: white;
        padding: 15px 20px;
        border-radius: 10px 10px 0 0;
        margin: -20px -20px 20px -20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Mensajes del chat */
    .chat-message {
        margin: 15px 0;
        display: flex;
        gap: 12px;
        animation: fadeIn 0.5s ease-in;
    }
    
    .chat-message.user {
        justify-content: flex-end;
    }
    
    .chat-message.assistant {
        justify-content: flex-start;
    }
    
    .message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }
    
    .avatar-user {
        background: linear-gradient(135deg, #6b7280, #9ca3af);
        color: white;
    }
    
    .avatar-bot {
        background: linear-gradient(135deg, #3b82f6, #10b981);
        color: white;
    }
    
    .message-content {
        max-width: 80%;
        padding: 12px 16px;
        border-radius: 18px;
        line-height: 1.5;
    }
    
    .message-user {
        background: linear-gradient(135deg, #3b82f6, #1e40af);
        color: white;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .message-assistant {
        background: #f9fafb;
        color: #374151;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Botones de preguntas frecuentes */
    .quick-question-btn {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 8px;
        text-align: left;
    }
    
    .quick-question-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    /* Categorías de colores */
    .category-becas { background: linear-gradient(135deg, #dbeafe, #bfdbfe); color: #1e40af; }
    .category-eventos { background: linear-gradient(135deg, #dcfce7, #bbf7d0); color: #166534; }
    .category-contacto { background: linear-gradient(135deg, #fed7aa, #fdba74); color: #9a3412; }
    .category-deportes { background: linear-gradient(135deg, #e9d5ff, #d8b4fe); color: #7c2d12; }
    .category-horarios { background: linear-gradient(135deg, #f3f4f6, #d1d5db); color: #374151; }
    .category-documentos { background: linear-gradient(135deg, #fecaca, #fca5a5); color: #991b1b; }
    
    /* Sidebar */
    .sidebar-content {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .info-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .info-horarios { border-left-color: #3b82f6; background: linear-gradient(135deg, #dbeafe, #f0f9ff); }
    .info-contacto { border-left-color: #10b981; background: linear-gradient(135deg, #dcfce7, #f0fdf4); }
    .info-ubicacion { border-left-color: #f59e0b; background: linear-gradient(135deg, #fed7aa, #fffbeb); }
    
    /* Input del chat */
    .chat-input-container {
        background: rgba(249, 250, 251, 0.8);
        padding: 16px;
        border-radius: 0 0 15px 15px;
        margin: 20px -20px -20px -20px;
        border-top: 1px solid #e5e7eb;
    }
    
    /* Indicador de escritura */
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #3b82f6;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
    
    /* Tabs estilizadas */
    .custom-tab {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 8px 16px;
        margin: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .custom-tab.active {
        background: linear-gradient(135deg, #3b82f6, #10b981);
        color: white;
        border-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Header con logo
st.image("data/ceut-logo.png", use_column_width=True)
st.markdown(
    '<div style="text-align:center; margin-top:-10px;">'
    '</div>', unsafe_allow_html=True
)

# Layout principal
col_chat, col_sidebar = st.columns([2, 1])

with col_chat:
    # Contenedor del chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Header del chat
    st.markdown("""
    <div class="chat-header">
        <span style="font-size: 20px;">🤖</span>
        <div>
            <strong>Asistente Virtual CEUT</strong>
            <div style="font-size: 12px; opacity: 0.9;">Powered by Groq</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar historial si no existe
    if "historial" not in st.session_state:
        st.session_state.historial = [
            ("assistant", "¡Hola! 👋 Soy el asistente virtual del Centro de Estudiantes UTN FRSF. Estoy aquí para ayudarte con información sobre becas, eventos, trámites y todo lo que necesites saber sobre la vida universitaria. ¿En qué puedo ayudarte hoy?")
        ]
    
    # Mostrar historial de mensajes
    chat_container = st.container()
    with chat_container:
        for role, mensaje in st.session_state.historial:
            if role == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="message-content message-user">{mensaje}</div>
                    <div class="message-avatar avatar-user">👤</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div class="message-avatar avatar-bot">🤖</div>
                    <div class="message-content message-assistant">{mensaje}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Input del usuario
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_button = st.columns([4, 1])
        with col_input:
            input_usuario = st.text_input(
                "Escribe tu pregunta aquí...", 
                placeholder="Ej: ¿Cómo me inscribo a una materia?",
                label_visibility="collapsed"
            )
        with col_button:
            enviar = st.form_submit_button("Enviar 📤", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_sidebar:
    # Pestañas de la sidebar
    tab1, tab2, tab3 = st.tabs(["❓ Preguntas", "📄 Documentos", "ℹ️ Información"])
    
    with tab1:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown("**💡 Preguntas Frecuentes**")
        
        # Preguntas rápidas con estilo
        preguntas = [
            {"texto": "¿Qué becas están disponibles?", "categoria": "becas", "icono": "🎓"},
            {"texto": "¿Cuándo es el próximo evento?", "categoria": "eventos", "icono": "📅"},
            {"texto": "¿Cómo me contacto con el centro?", "categoria": "contacto", "icono": "💬"},
            {"texto": "¿Qué actividades deportivas hay?", "categoria": "deportes", "icono": "⚽"},
            {"texto": "¿Cuáles son los horarios de atención?", "categoria": "horarios", "icono": "🕐"},
            {"texto": "¿Qué dice el reglamento de becas?", "categoria": "documentos", "icono": "📋"}
        ]
        
        for i, pregunta in enumerate(preguntas):
            if st.button(
                f"{pregunta['icono']} {pregunta['texto']}", 
                key=f"pregunta_{i}",
                use_container_width=True
            ):
                # Agregar pregunta al historial
                st.session_state.historial.append(("user", pregunta['texto']))
                # Simular respuesta (aquí irá la lógica real)
                st.session_state.historial.append(("assistant", f"Respuesta simulada para: {pregunta['texto']} (LLM deshabilitado)"))
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown("**📄 Gestión de Documentos**")
        st.info("🔧 Próximamente: gestor de documentos.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown("**🏛️ Centro de Estudiantes**")
        
        # Información con cards estilizadas
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
        
        st.markdown('</div>', unsafe_allow_html=True)

# Procesamiento de la consulta
if enviar and input_usuario:
    # Agregar mensaje del usuario al historial
    st.session_state.historial.append(("user", input_usuario))
    
    with st.spinner("🔎 Buscando información relevante..."):
        try:
            # Simular tiempo de procesamiento
            time.sleep(1)
            
            # contexto_rag = buscar_contexto(input_usuario, documentos)
            # links_utiles = generar_texto_links()
            # MAX_CONTEXT_CHARS = 3000
            # contexto_recortado = contexto_rag[:MAX_CONTEXT_CHARS]
            
            # Mostrar contexto en expander (comentado para futuro uso)
            # with st.expander("🔍 Ver contexto utilizado"):
            #     st.text_area("Contexto (RAG)", value=contexto_recortado, height=200)
            
            # prompt = [
            #     {"role": "system", "content": "Sos un chatbot del centro de estudiantes de UTN FRSF. Respondé de forma clara y breve usando el contexto proporcionado."},
            #     {"role": "user", "content": f"{input_usuario}\n\nContexto:\n{contexto_recortado}\n\nLinks:\n{links_utiles}"}
            # ]
            
            # respuesta = query_llm(prompt)
            
            # Por ahora, respuesta simulada
            respuesta = f"Respuesta simulada para: '{input_usuario}' (LLM deshabilitado)"
            
            # Agregar respuesta al historial
            st.session_state.historial.append(("assistant", respuesta))
            
        except Exception as e:
            st.error(f"⚠️ Ocurrió un error: {e}")
    
    # Recargar para mostrar nuevos mensajes
    st.rerun()

# Botón para limpiar historial en la sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🧹 Limpiar historial", use_container_width=True):
    st.session_state.historial = [
        ("assistant", "¡Hola! 👋 Soy el asistente virtual del Centro de Estudiantes UTN FRSF. Estoy aquí para ayudarte con información sobre becas, eventos, trámites y todo lo que necesites saber sobre la vida universitaria. ¿En qué puedo ayudarte hoy?")
    ]
    st.rerun()

# JavaScript para auto-scroll (opcional)
st.markdown("""
<script>
    function scrollToBottom() {
        window.scrollTo(0, document.body.scrollHeight);
    }
    setTimeout(scrollToBottom, 100);
</script>
""", unsafe_allow_html=True)