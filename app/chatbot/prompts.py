import os
from langchain.document_loaders import PyPDFLoader

def load_all_pdfs():

    pdf_folder = "static/uploads/pdfs"
    documents = []

    for file in os.listdir(pdf_folder):

        if file.endswith(".pdf"):

            path = os.path.join(pdf_folder, file)

            loader = PyPDFLoader(path)

            docs = loader.load()

            documents.extend(docs)

    return documents