from dotenv import load_dotenv
from utils.audio_processor import process_input
from CORE.transcriber import transcribe_all
from CORE.summarize import summarize, generate_title
from CORE.extractor import extract_actionable_items, extract_key_decisions, extract_questions
from CORE.rag_engine import build_rag_chain, ask_question


load_dotenv()


def run_pipeline(source: str, translate: bool = False):
    print("Starting AI Video Assistance..........")

    chunks = process_input(source)  # list of chunk .wav file paths for this session
    transcript = transcribe_all(chunks, translate)
    print(f"raw transcription (first 300 characters): {transcript[:300]}")

    title = generate_title(transcript)
    summary = summarize(transcript)
    action_items = extract_actionable_items(transcript)
    key_decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)

    rag_chain, vector_store = build_rag_chain(transcript)   # tuple unpack

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": key_decisions,
        "questions": questions,
        "rag_chain": rag_chain,
        "vector_store": vector_store,
        "audio_files": chunks,   # <-- naya field: is session ki saari chunk files ka path, cleanup ke liye
    }


if __name__ == "__main__":
    run_pipeline("https://www.youtube.com/watch?v=dQw4w9WgXcQ")