


import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document




CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcripts"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"



def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})

def build_vector_store(transcript : str)->Chroma:
    
    splitter = RecursiveCharacterTextSplitter(chunk_size = 500 , chunk_overlap = 50)
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={"chunck": i})
        for i, chunk in enumerate(chunks)
    ]

    emebddings = get_embeddings()
    vector_store = Chroma.from_documents(
        docs,
        embedding=emebddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )
    return vector_store

def load_vector_store()->Chroma: # for data retrieval
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    return vector_store

def get_retriver(vector_store : Chroma,k :int = 4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
        )