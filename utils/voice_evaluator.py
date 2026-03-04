import speech_recognition as sr
from pydub import AudioSegment
import io
import os
import shutil

def is_ffmpeg_available():
    """Checks if ffmpeg is available on the system path."""
    return shutil.which("ffmpeg") is not None

def is_connected():
    """Checks for an internet connection."""
    import socket
    try:
        socket.create_connection(("www.google.com", 80), timeout=2)
        return True
    except (OSError, socket.timeout):
        return False

def evaluate_audio_answer(audio_bytes, audio_format="wav") -> dict:
    """
    Converts audio speech to text and evaluates the quality.
    """
    recognizer = sr.Recognizer()
    
    try:
        # Check for MP3 requires ffmpeg
        if audio_format.lower() == "mp3":
            if not is_ffmpeg_available():
                return {
                    "success": False, 
                    "error": "MP3 processing requires 'ffmpeg'. \n\nTo fix this on Windows, run 'winget install ffmpeg' in your terminal and restart your app."
                }
            
            audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            audio_bytes = wav_io.getvalue()

        # Load audio into recognition
        audio_file = io.BytesIO(audio_bytes)
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
        except Exception as e:
            # If standard sr.AudioFile fails, try pydub to normalize it to standard WAV (needs ffmpeg)
            if not is_ffmpeg_available():
                 return {
                    "success": False, 
                    "error": f"Audio format error: {e}. Please ensure you are uploading a standard 16-bit PCM WAV file."
                }
            
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            audio_file = io.BytesIO(wav_io.getvalue())
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
            
        if not is_connected():
            return {
                "success": False,
                "error": "Internet connection required for AI voice evaluation. Please check your connection."
            }

        # Perform recognition with chunking support
        # Note: Google API has a ~60s limit per request
        total_duration = audio_data.duration if hasattr(audio_data, 'duration') else 0
        if total_duration == 0:
             # Try to get duration from the AudioSegment if audio_data fails
             # audio_bytes is already normalized to WAV at this point if needed
             audio_seg = AudioSegment.from_wav(io.BytesIO(audio_bytes))
             total_duration = audio_seg.duration_seconds

        chunk_size = 45 # seconds
        full_text = []
        
        # Load back into AudioSegment for easy slicing
        full_audio_seg = AudioSegment.from_wav(io.BytesIO(audio_bytes))
        
        for i in range(0, int(total_duration * 1000), chunk_size * 1000):
            chunk = full_audio_seg[i : i + chunk_size * 1000]
            chunk_io = io.BytesIO()
            chunk.export(chunk_io, format="wav")
            chunk_io.seek(0)
            
            with sr.AudioFile(chunk_io) as source:
                chunk_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(chunk_data)
                    full_text.append(text)
                except sr.UnknownValueError:
                    continue # Skip silent/unintelligible chunks
                except sr.RequestError:
                    return {"success": False, "error": "Speech service error during chunk processing."}

        text = " ".join(full_text)
        
        if not text.strip():
             return {"success": False, "error": "AI could not understand any speech in the recording. Please speak clearly."}

        # Simple evaluation logic
        word_count = len(text.split())
        duration = total_duration
        words_per_min = (word_count / (duration / 60)) if duration > 0 else 0
        
        # Heuristics for "Confidence" and "Clarity"
        clarity = 85 if 100 < words_per_min < 170 else 65
        confidence = 90 if word_count > 15 else 50
        
        return {
            "success": True,
            "transcription": text,
            "metrics": {
                "Word Count": word_count,
                "Duration": f"{int(duration)}s",
                "Speech Rate": f"{int(words_per_min)} wpm",
                "Clarity Score": clarity,
                "Confidence": confidence
            },
            "feedback": "Great clarity!" if clarity > 80 else "Good attempt! Try to focus on pacing and clear articulation."
        }
        
    except sr.UnknownValueError:
        return {"success": False, "error": "AI could not understand the speech. Please speak more clearly or check your microphone."}
    except sr.RequestError:
        return {"success": False, "error": "Speech service is currently unavailable. Please check your internet connection."}
    except Exception as e:
        return {"success": False, "error": f"Internal Error: {str(e)}"}
