# app.py
import os
import tempfile
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import run_pipeline  # <-- ONLY import from backend/main

app = FastAPI(title="AI Video Assistant API")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id -> pipeline result dict
SESSIONS: dict[str, dict] = {}


class ClearRequest(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    question: str


def _serialize_session(session_id: str, result: dict) -> dict:
    return {
        "session_id": session_id,
        "title": result.get("title"),
        "transcript": result.get("transcript"),
        "summary": result.get("summary"),
        "action_items": result.get("action_items"),
        "key_decisions": result.get("key_decisions"),
        "questions": result.get("questions"),
    }


def _ask(rag_chain, question: str) -> str:
    """
    Matches CORE/rag_engine.ask_question(rag_chain, question) exactly:
        answer = rag_chain.invoke(question)
    No dict wrapping — the chain's RunnablePassthrough expects the raw
    question string directly.
    """
    if rag_chain is None:
        raise HTTPException(status_code=400, detail="RAG chain not available for this session")
    return rag_chain.invoke(question)


@app.post("/api/process")
async def process_source(request: Request):
    """
    Single endpoint that handles BOTH:
    - multipart/form-data (file upload)         -> form fields: file, translate
    - application/json    ({ source, translate })
    matching the frontend's single POST /process call.
    """
    content_type = request.headers.get("content-type", "")
    tmp_path = None

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()
            upload = form.get("file")
            translate_flag = form.get("translate") == "true"

            if upload is None:
                raise HTTPException(status_code=422, detail="No file provided")

            suffix = os.path.splitext(upload.filename or "")[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await upload.read())
                tmp_path = tmp.name

            result = run_pipeline(tmp_path, translate_flag)

        elif "application/json" in content_type:
            body = await request.json()
            source = body.get("source")
            translate_flag = bool(body.get("translate", False))

            if not source:
                raise HTTPException(status_code=422, detail="Missing 'source' field")

            result = run_pipeline(source, translate_flag)

        else:
            raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}")

        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = result
        return _serialize_session(session_id, result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/clear")
async def clear_session(body: ClearRequest):
    session = SESSIONS.pop(body.session_id, None)
    if session and session.get("vector_store") is not None:
        try:
            from CORE.vector_store import release_vector_store
            release_vector_store(session["vector_store"])
        except Exception as e:
            print(f"[clear_session] cleanup failed: {e}")
    return {"status": "cleared"}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    session = SESSIONS.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rag_chain = session.get("rag_chain")
    answer = _ask(rag_chain, body.question)

    return {
        "answer": answer,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, reload=True)