import os
import uuid
import time
import traceback
from datetime import datetime
import shutil

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from utils.audio_processor import process_input
from CORE.transcriber import transcribe_all
from CORE.summarize import summarize, generate_title
from CORE.extractor import extract_actionable_items, extract_key_decisions, extract_questions
from CORE.rag_engine import build_rag_chain, ask_question
from CORE.vector_store import release_vector_store

load_dotenv()

VECTOR_DIR = os.path.join(os.path.dirname(__file__), "vector_db")
os.makedirs(VECTOR_DIR, exist_ok=True)

app = Flask(__name__)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
 
SESSIONS = {}


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
    """Windows pe file handle release hone mein thoda delay lagta hai,
    isliye chhoti retry ke saath delete karo."""
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
def health():
    return jsonify({"status": "ok"})


@app.post("/api/process")
def process_source():
    """
    Kicks off the full pipeline (same steps as main.py's run_pipeline):
    transcribe -> title -> summary -> action items -> decisions -> questions -> rag chain

    Accepts EITHER:
      - JSON body: { "source": "<youtube url or path>", "translate": true|false }
      - multipart/form-data: file=<uploaded file>, translate=true|false
    """
    try:
        translate = False
        source = None
        uploaded_path = None  # track so we can delete it later on clear

        if request.content_type and "multipart/form-data" in request.content_type:
            translate = request.form.get("translate", "false").strip().lower() in ("true", "1", "yes", "y")
            uploaded = request.files.get("file")
            if not uploaded or uploaded.filename == "":
                return jsonify({"error": "No file uploaded"}), 400
            filename = secure_filename(uploaded.filename)
            save_path = os.path.join(UPLOAD_DIR, filename)
            uploaded.save(save_path)
            source = save_path
            uploaded_path = save_path
        else:
            data = request.get_json(silent=True) or {}
            source = (data.get("source") or "").strip()
            translate = bool(data.get("translate", False))
            if not source:
                return jsonify({"error": "'source' (YouTube URL or file path) is required"}), 400

        chunks = process_input(source)
        transcript = transcribe_all(chunks, translate)

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

        return jsonify(_serialize_session(session_id))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.get("/api/session/<session_id>")
def get_session(session_id):
    if session_id not in SESSIONS:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(_serialize_session(session_id))


@app.post("/api/chat")
def chat():
    """
    Body: { "session_id": "...", "question": "..." }
    Runs the question through the RAG chain built for that session.
    """
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        question = (data.get("question") or "").strip()

        if not session_id or session_id not in SESSIONS:
            return jsonify({"error": "Invalid or expired session_id"}), 400
        if not question:
            return jsonify({"error": "'question' is required"}), 400

        rag_chain = SESSIONS[session_id]["rag_chain"]
        answer = ask_question(rag_chain, question)

        return jsonify({
            "answer": answer,
            "question": question,
            "created_at": datetime.utcnow().isoformat() + "Z",
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.post("/api/clear")
def clear_session():
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")

        if session_id and session_id in SESSIONS:
            session_data = SESSIONS.pop(session_id)
            vector_store = session_data.get("vector_store")

            if vector_store:
                try:
                    vector_store.delete_collection()
                except Exception as inner_e:
                    print(f"Could not delete collection: {inner_e}")
 
            release_vector_store(vector_store)

        # Clear downloads folder
        if os.path.exists(UPLOAD_DIR):
            for f in os.listdir(UPLOAD_DIR):
                _safe_rmtree(os.path.join(UPLOAD_DIR, f))

        # Clear vector_db folder (delete_collection() doesn't remove the on-disk index folder)
        if os.path.exists(VECTOR_DIR):
            for f in os.listdir(VECTOR_DIR):
                _safe_rmtree(os.path.join(VECTOR_DIR, f))

        return jsonify({"message": "Session cleared", "session_id": session_id}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)