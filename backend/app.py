import os
import uuid
import time
import shutil
import traceback
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

VECTOR_DIR = os.path.join(os.path.dirname(__file__), "vector_db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(VECTOR_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI Video Assistance Backend")

# CORS Setup - Open for production reliability to stop 'Failed to process' bugs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS = {}

class ChatRequest(BaseModel):
    session_id: str
    question: str

class ClearRequest(BaseModel):
    session_id: Optional[str] = None


def _serialize_session(session_id: str) -> dict:
    s = SESSIONS[session_id]
    return {
        "session_id": session_id,
        "title": s["title"],
        "transcript": s["transcript"],
        "summary": s["summary"],
        "action_items": s["action_items"],
        "key_decisions": s["key_decisions"],
        "questions": s["questions"],
        "created_at": s["created_at"],
    }


def _safe_rmtree(path, retries=5, delay=0.3):
    for attempt in range(retries):
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            return True
        except Exception as e:
            if attempt == retries - 1:
                print(f"Could not delete {path} after {retries} tries: {e}")
                return False
            time.sleep(delay)
    return False


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process_source(
    source: Optional[str] = Form(None),
    translate: Optional[str] = Form("false"),
    file: Optional[UploadFile] = File(None),
    request: Request = None
):
    try:
        is_translate = False
        uploaded_path = None
        final_source = ""

        # Check for multipart file upload
        if file is not None and file.filename != "":
            is_translate = translate.strip().lower() in ("true", "1", "yes", "y")
            
            # Safe filename extraction
            base_filename = os.path.basename(file.filename)
            save_path = os.path.join(UPLOAD_DIR, base_filename)
            
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            final_source = save_path
            uploaded_path = save_path
        else:
            # Handle standard JSON body text fallback
            try:
                body = await request.json()
                final_source = (body.get("source") or "").strip()
                is_translate = bool(body.get("translate", False))
            except Exception:
                # If content was form data but without a file
                if source:
                    final_source = source.strip()
                    is_translate = translate.strip().lower() in ("true", "1", "yes", "y")

        if not final_source:
            raise HTTPException(status_code=400, detail="'source' or file upload is required")

        # ── LAZY IMPORTS HERE ──
        from utils.audio_processor import process_input
        from CORE.transcriber import transcribe_all
        from CORE.summarize import summarize, generate_title
        from CORE.extractor import extract_actionable_items, extract_key_decisions, extract_questions
        from CORE.rag_engine import build_rag_chain

        chunks = process_input(final_source)
        transcript = transcribe_all(chunks, is_translate)

        title = generate_title(transcript)
        summary = summarize(transcript)
        action_items = extract_actionable_items(transcript)
        key_decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)
        session_id = str(uuid.uuid4())

        rag_chain, vector_store = build_rag_chain(transcript, session_id=session_id)

        SESSIONS[session_id] = {
            "rag_chain": rag_chain,
            "vector_store": vector_store,
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": key_decisions,
            "questions": questions,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "uploaded_path": uploaded_path,
        }

        return _serialize_session(session_id)

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return _serialize_session(session_id)


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    try:
        session_id = payload.session_id
        question = payload.question.strip()

        if session_id not in SESSIONS:
            raise HTTPException(status_code=400, detail="Invalid or expired session_id")
        if not question:
            raise HTTPException(status_code=400, detail="'question' is required")

        # ── LAZY IMPORT FOR CHAT ──
        from CORE.rag_engine import ask_question

        rag_chain = SESSIONS[session_id]["rag_chain"]
        answer = ask_question(rag_chain, question)

        return {
            "answer": answer,
            "question": question,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear")
async def clear_session(payload: ClearRequest):
    try:
        session_id = payload.session_id

        if session_id and session_id in SESSIONS:
            session_data = SESSIONS.pop(session_id)
            vector_store = session_data.get("vector_store")

            if vector_store:
                try:
                    vector_store.delete_collection()
                except Exception as inner_e:
                    print(f"Could not delete collection: {inner_e}")
 
            # ── LAZY IMPORT FOR CLEAR ──
            from CORE.vector_store import release_vector_store
            release_vector_store(vector_store)

        if os.path.exists(UPLOAD_DIR):
            for f in os.listdir(UPLOAD_DIR):
                _safe_rmtree(os.path.join(UPLOAD_DIR, f))

        if os.path.exists(VECTOR_DIR):
            for f in os.listdir(VECTOR_DIR):
                _safe_rmtree(os.path.join(VECTOR_DIR, f))

        return {"message": "Session cleared", "session_id": session_id}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)