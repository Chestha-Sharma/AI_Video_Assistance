import os
import gc
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from chromadb.api.client import SharedSystemClient


CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcripts"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"



def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})

def build_vector_store(transcript: str, session_id: str = None) -> Chroma:
    collection_name = f"meeting_{session_id}" if session_id else COLLECTION_NAME

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={"chunk": i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        docs,
        embedding=embeddings,
        collection_name=collection_name,
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


def release_vector_store(vector_store: Chroma = None):
    """
    Chroma persist_directory ek hi hai (CHROMA_DIR) jo saare sessions
    ke beech share hota hai — sirf collection_name badalta hai.
    Isliye Chroma ka internal SharedSystemClient us directory ke liye
    ek hi sqlite connection cache/reuse karta hai.

    Sirf vector_store.delete_collection() ya vector_store._client = None
    karne se ye underlying sqlite3 connection release NAHI hota, isliye
    disk pe folder locked reh jata hai aur delete fail hota hai.

    Ye function us shared client ko properly stop + cache se clear karta
    hai taaki file handle release ho jaye aur folder delete ho sake.
    """
    if vector_store is not None: 
        try:
            client = getattr(vector_store, "_client", None)
            system = getattr(client, "_system", None)
            if system is not None:
                system.stop()
        except Exception as e:
            print(f"[release_vector_store] Could not stop chroma system: {e}")

    # Global shared-client cache clear karo (path -> client mapping)
    try:
        SharedSystemClient.clear_system_cache()
    except Exception as e:
        print(f"[release_vector_store] Could not clear system cache: {e}")

    gc.collect()