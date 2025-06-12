import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

def obtener_links_utiles():
    return [
        {"titulo": "Página del CEUT", "url": "https://www.ceut-frsf.com.ar/home"},
        {"titulo": "Calendario académico", "url": "https://www.ceut-frsf.com.ar/home"},
        {"titulo": "Sysacad", "url": "https://sysacad.frsf.utn.edu.ar/"},
        {"titulo": "Horarios de cursado", "url": "https://www.frsf.utn.edu.ar/alumnado/cursado"},
        {"titulo": "Instagram del CEUT", "url": "https://www.instagram.com/ceut.frsf/"},
        {"titulo": "Pasantías", "url": "https://www.frsf.utn.edu.ar/extension/pasantias"},
        {"titulo": "Carreras", "url": "https://www.frsf.utn.edu.ar/carreras"},
        {"titulo": "Busquedas Laborales", "url": "https://www.frsf.utn.edu.ar/graduados/busquedas-laborales"},
        {"titulo": "Campus Virtual", "url": "https://campusvirtual.frsf.utn.edu.ar/"}
    ]

def generar_texto_links():
    links = obtener_links_utiles()
    return "\n".join([f"{l['titulo']}: {l['url']}" for l in links])

def scrape_secciones_utn():
    urls = [
        "https://www.frsf.utn.edu.ar/carreras/ingenierias",
        "https://ingreso.frsf.utn.edu.ar/",
        "https://www.frsf.utn.edu.ar/extension/pasantias"
    ]
    docs = []
    for url in urls:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        texto = soup.get_text(separator="\n", strip=True)
        docs.append(Document(page_content=texto, metadata={"source": url}))
    return docs
