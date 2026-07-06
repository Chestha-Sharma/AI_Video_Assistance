

# for youtube video



import os
import yt_dlp
import imageio_ffmpeg
from pydub import AudioSegment

AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR,exist_ok = True) # directory noe exist then it will make it


def download_youtube_audio(url : str) -> str : # to download audio from youtube
    output_path = os.path.join(DOWNLOAD_DIR,"%(title)s.%(ext)s")  # %(title)s.%(ext)s means example i have note.wav then %(title)s = note(title) and %(ext)s=wav(extension)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ], 
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: # with functionality kisi file ko open krne ke baad apne aap close bhi kar deta h
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
    return filename
 



def convert_audio_to_wav(audio_file_path : str) -> str : # to download audio of local video file
    output_path = os.path.splitext(audio_file_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(audio_file_path) # automatic detect krta h ki input file kkis type ki h .webd or mp4 etc
    audio = audio.set_channels(1).set_frame_rate(16000) # set_channels(1) converts dual audio into monoaudio and next set frame rate 16khz
    audio.export(output_path, format="wav") #saved
    return output_path




def  chunck_audio(wav_path : str,chunck_minutes : float = 10) ->str:
    audio = AudioSegment.from_wav(wav_path)
    chunck_ms = int(chunck_minutes * 60 * 1000)  # converted in ms bcz chunck works in ms

    chuncks = []

    for i , start in enumerate(range(0,len(audio), chunck_ms)): # taking step at every chunck_ms
        chunck = audio[start:start+chunck_ms] # chunck is audio chunck
        chunck_path = f"{wav_path}_chunck_{i}.wav" # chunck path
        chunck.export(chunck_path, format="wav") # chunck saved
        chuncks.append(chunck_path) # chunck path saved in list
    return chuncks




def process_input(source : str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detectced youtube url.Downloading audio....")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file.Converting to wav....")
        wav_path = convert_audio_to_wav(source)
    print("Chunking audio....")
    chuncks = chunck_audio(wav_path)
    print("Chuncking audio.....")
    return chuncks