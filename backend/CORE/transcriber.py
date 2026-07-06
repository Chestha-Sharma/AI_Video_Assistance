#whisper works on hindi and english videos





import whisper 
import os 

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model = None # if model is already download then do not download again

def get_model():
    global _model
    if _model is None:
        print("Downloading whisper model...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model downloaded successfully.")
    return _model


def transcribe_chuncks(chunck_path : str , translate : bool = False) -> str: # transcribe single chunck
    model = get_model()
    task = "translate" if translate else "transcribe" # ternary if else

    result = model.transcribe(chunck_path, task=task)
    return result['text']


def transcribe_all(chuncks : list , translate : bool = False) -> str: # passes chuncks to transcribe_chunck
    full_transcript = ""
    for i,chunck in enumerate(chuncks):
        print(f"Transcribing chunck {i+1}/{len(chuncks)}")
        transcript = transcribe_chuncks(chunck , translate)
        full_transcript += transcript + " "
    print("Transcription completed.")
    return full_transcript