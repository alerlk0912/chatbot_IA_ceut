from langchain_community.document_loaders import PyPDFLoader
from tools import scrape_secciones_utn

def cargar_documento(pdf_path="data/faqs.pdf"):
    loader = PyPDFLoader(pdf_path)
    documentos_pdf = loader.load()

    documentos_web = scrape_secciones_utn()

    return documentos_pdf + documentos_web

# Cargar contexto desde documentos en texto plano
def buscar_contexto(pregunta, documentos):
    pregunta = pregunta.lower()
    palabras = pregunta.split()
    contexto = []

    for doc in documentos:
        contenido = doc.page_content.lower()
        if any(palabra in contenido for palabra in palabras):
            contexto.append(doc.page_content)

    if not contexto:
        contexto = [documentos[0].page_content]

    return "\n".join(contexto[:3])


