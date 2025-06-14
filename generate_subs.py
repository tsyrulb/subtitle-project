import os
import datetime
from moviepy.editor import VideoFileClip
import whisper
from deep_translator import GoogleTranslator

def format_time(seconds):
    """
    Converts a time in seconds to the SRT format (HH:MM:SS,ms).
    
    Args:
        seconds (float): The time in seconds.
    
    Returns:
        str: The time formatted as a string.
    """
    delta = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(delta.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_subtitles(video_path, model_name="base"):
    """
    Generates subtitles in English and Russian from a Korean video file.

    This function performs the following steps:
    1. Extracts audio from the video file.
    2. Transcribes the Korean audio to text with word-level timestamps using Whisper.
    3. Translates the transcribed text to English and Russian.
    4. Creates .srt subtitle files for each language.

    Args:
        video_path (str): The path to the input video file.
        model_name (str): The name of the Whisper model to use (e.g., "tiny", "base", "small", "medium", "large").
                          Larger models are more accurate but slower and require more memory.
    """
    print(f"Starting subtitle generation for: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    base_filename = os.path.splitext(os.path.basename(video_path))[0]
    
    # --- Step 1: Extract Audio from Video ---
    print("Step 1/4: Extracting audio from video...")
    audio_path = f"{base_filename}_temp_audio.wav"
    try:
        with VideoFileClip(video_path) as video:
            video.audio.write_audiofile(audio_path, codec='pcm_s16le')
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return

    # --- Step 2: Transcribe Audio with Whisper ---
    print(f"Step 2/4: Loading Whisper model '{model_name}'...")
    # The model will be downloaded automatically on the first run.
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        os.remove(audio_path)
        return
        
    print("Transcribing audio (this may take a while)...")
    try:
        # We specify the language as 'ko' for Korean.
        result = model.transcribe(audio_path, language='ko', word_timestamps=True)
    except Exception as e:
        print(f"Error during transcription: {e}")
        os.remove(audio_path)
        return

    print("Transcription complete.")
    
    # --- Step 3 & 4: Translate and Create SRT Files ---
    print("Step 3/4: Translating and formatting subtitles...")

    # Initialize translators
    try:
        translator_en = GoogleTranslator(source='ko', target='en')
        translator_ru = GoogleTranslator(source='ko', target='ru')
    except Exception as e:
        print(f"Error initializing translator: {e}")
        os.remove(audio_path)
        return

    srt_path_en = f"{base_filename}_en.srt"
    srt_path_ru = f"{base_filename}_ru.srt"

    try:
        with open(srt_path_en, "w", encoding="utf-8") as srt_file_en, \
             open(srt_path_ru, "w", encoding="utf-8") as srt_file_ru:

            for i, segment in enumerate(result['segments']):
                start_time = format_time(segment['start'])
                end_time = format_time(segment['end'])
                
                # Original Korean text
                korean_text = segment['text'].strip()
                if not korean_text:
                    continue

                # Translate text
                english_text = translator_en.translate(korean_text)
                russian_text = translator_ru.translate(korean_text)

                # Write English SRT entry
                srt_file_en.write(f"{i + 1}\n")
                srt_file_en.write(f"{start_time} --> {end_time}\n")
                srt_file_en.write(f"{english_text}\n\n")
                
                # Write Russian SRT entry
                srt_file_ru.write(f"{i + 1}\n")
                srt_file_ru.write(f"{start_time} --> {end_time}\n")
                srt_file_ru.write(f"{russian_text}\n\n")

    except Exception as e:
        print(f"Error writing SRT files: {e}")
    finally:
        # --- Cleanup ---
        print("Step 4/4: Cleaning up temporary files...")
        os.remove(audio_path)

    print("\n--- Process Complete! ---")
    print(f"English subtitles saved to: {srt_path_en}")
    print(f"Russian subtitles saved to: {srt_path_ru}")


if __name__ == '__main__':
    # --- CONFIGURATION ---
    VIDEO_FILE_PATH = "korean_video_sample.mp4" 
    
    # Choose your model. Options: "tiny", "base", "small", "medium", "large"
    WHISPER_MODEL = "base"
    
    # --- EXECUTION ---
    print("--- Starting Auto-Subtitle Script ---")
    # Add a placeholder file if the specified one doesn't exist, to allow the script to run.
    if not os.path.exists(VIDEO_FILE_PATH):
        print(f"Warning: The file '{VIDEO_FILE_PATH}' does not exist.")
        print("Creating a placeholder file for demonstration purposes.")
        print("Please replace 'korean_video_sample.mp4' with your actual video file path.")
        with open(VIDEO_FILE_PATH, "w") as f:
            f.write("This is a dummy file.")
        # We will exit here as a dummy file cannot be processed.
        print("Script will not run with a dummy file. Please provide a real video.")
    else:
        generate_subtitles(VIDEO_FILE_PATH, model_name=WHISPER_MODEL)