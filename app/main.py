import streamlit as st
from rag import cargar_documento, buscar_contexto
from agent import query_llm
from tools import generar_texto_links

# Configuración inicial de la app
st.set_page_config(page_title="🤖 Chatbot UTN FRSF", layout="wide")
st.title("🤖 Chatbot del Centro de Estudiantes - UTN FRSF")

# Cargar documentos PDF una vez
@st.cache_resource
def cargar_datos():
    return cargar_documento("data/faqs.pdf")

documentos = cargar_datos()

# Inicializar estado de historial
if "historial" not in st.session_state:
    st.session_state.historial = []

# Input del usuario
with st.container():
    st.subheader("📩 Realizá tu consulta")
    input_usuario = st.text_input("¿En qué podemos ayudarte?", key="input", placeholder="Ej: ¿Cómo me inscribo a una materia?")

# Botón para limpiar historial
st.sidebar.button("🧹 Limpiar historial", on_click=lambda: st.session_state.historial.clear())

# Procesamiento de la consulta
if st.button("Enviar") and input_usuario:
    with st.spinner("🔎 Buscando información relevante..."):
        try:
            contexto_rag = buscar_contexto(input_usuario, documentos)
            links_utiles = generar_texto_links()

            MAX_CONTEXT_CHARS = 3000
            contexto_recortado = contexto_rag[:MAX_CONTEXT_CHARS]

            # Mostrar contexto
            with st.expander("🔍 Ver contexto utilizado"):
                st.text_area("Contexto (RAG)", value=contexto_recortado, height=200)

            # Preparar prompt
            prompt = [
                {"role": "system", "content": "Sos un chatbot del centro de estudiantes de UTN FRSF. Respondé de forma clara y breve usando el contexto proporcionado."},
                {"role": "user", "content": f"{input_usuario}\n\nContexto:\n{contexto_recortado}\n\nLinks:\n{links_utiles}"}
            ]

            # Obtener respuesta
            respuesta = query_llm(prompt)

            # Guardar en historial
            st.session_state.historial.append((input_usuario, respuesta))

        except Exception as e:
            st.error(f"⚠️ Ocurrió un error: {e}")

# Mostrar historial (últimas consultas primero)
if st.session_state.historial:
    st.subheader("📜 Historial de conversación")

    for entrada, salida in reversed(st.session_state.historial):
        with st.container():
            st.markdown(f"**🧑 Usuario:** {entrada}")
            st.markdown(f"**🤖 Chatbot:** {salida}")
            st.markdown("---")
