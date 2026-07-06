import os
import uuid
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

load_dotenv()

VECTOR_DIR = os.path.join(os.path.dirname(__file__), "vector_db")
os.makedirs(VECTOR_DIR, exist_ok=True)

app = Flask(__name__)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory session store: session_id -> { rag_chain, title, transcript, createdAt, ... }
# NOTE: this is fine for a single-process dev/demo server. For production, swap this
# for redis / a database, since rag_chain objects won't survive a process restart
# and won't be shared across multiple workers.
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
        rag_chain = build_rag_chain(transcript)

        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = {
            "rag_chain": rag_chain,
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": key_decisions,
            "questions": questions,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "uploaded_path": uploaded_path,  # None if source was a YouTube URL
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
    """
    Body: { "session_id": "..." }  (optional)

    Clears in-memory session data, deletes everything inside the downloads
    folder, and wipes the vector_db folder so storage doesn't keep filling up.
    """
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")

        if session_id and session_id in SESSIONS:
            SESSIONS.pop(session_id)

        # Clear downloads folder (covers YouTube-downloaded audio + uploaded files)
        if os.path.exists(UPLOAD_DIR):
            for f in os.listdir(UPLOAD_DIR):
                fpath = os.path.join(UPLOAD_DIR, f)
                try:
                    if os.path.isfile(fpath) or os.path.islink(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath)
                except Exception as inner_e:
                    print(f"Could not delete {fpath}: {inner_e}")

        # Clear vector_db folder
        if os.path.exists(VECTOR_DIR):
            for f in os.listdir(VECTOR_DIR):
                fpath = os.path.join(VECTOR_DIR, f)
                try:
                    if os.path.isfile(fpath) or os.path.islink(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath)
                except Exception as inner_e:
                    print(f"Could not delete {fpath}: {inner_e}")

        return jsonify({"message": "Session cleared", "session_id": session_id}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)