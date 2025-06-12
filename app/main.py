import streamlit as st
from rag import cargar_documento, buscar_contexto
from agent import query_llm
from tools import generar_texto_links

# Cargamos el documento completo
documentos = cargar_documento("data/faqs.pdf")

st.set_page_config(page_title="Chatbot UTN FRSF", layout="wide")
st.title("🤖 Chatbot del Centro de Estudiantes")

if "historial" not in st.session_state:
    st.session_state.historial = []

input_usuario = st.text_input("¿En qué podemos ayudarte?", key="input")

if st.button("Enviar") and input_usuario:
    with st.spinner("Buscando información..."):
        contexto_rag = buscar_contexto(input_usuario, documentos)
        links_utiles = generar_texto_links()
        
        MAX_CONTEXT_CHARS = 3000  # Puedes ajustar este valor según pruebas
        contexto_recortado = contexto_rag[:MAX_CONTEXT_CHARS]
        
        with st.expander("🔍 Ver contexto utilizado"):
            st.text(contexto_recortado)

        prompt = [
        {"role": "system", "content": "Sos un chatbot del centro de estudiantes de UTN FRSF que ayuda a los estudiantes con sus dudas. Proporciona respuestas claras y concisas basadas en la información proporcionada."},
        {"role": "user", "content": f"{input_usuario}\n\nContexto:\n{contexto_recortado}\n\nLinks:\n{links_utiles}"}
        ]

        respuesta = query_llm(prompt)

    st.session_state.historial.append((input_usuario, respuesta))


# Mostrar historial
for entrada, salida in reversed(st.session_state.historial):
    st.markdown(f"**🧑 Usuario:** {entrada}")
    st.markdown(f"**🤖 Chatbot:** {salida}")
    st.markdown("---")
