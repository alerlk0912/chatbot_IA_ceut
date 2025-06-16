import os
import pdfplumber
import re
from llama_index.core import Document

def load_pdfs_from_folder(folder_path="data"):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    blocks = [t.strip() for t in re.split(r'\n{2,}', text) if len(t.strip()) > 30]
                    for block in blocks:
                        documents.append(Document(
                            text=block,
                            metadata={
                                "page": i + 1,
                                "source": filename
                            }
                        ))
    return documents
