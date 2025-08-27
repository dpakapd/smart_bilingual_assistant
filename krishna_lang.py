import os
import struct
import pyaudio
import pvporcupine
import speech_recognition as sr
import openai
from openai import OpenAI
from dotenv import load_dotenv
from gtts import gTTS
import pygame
import time

# --- 1. Configuration ---
load_dotenv()
PICOVOICE_ACCESS_KEY = os.environ.get("PICOVOICE_ACCESS_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# --- Ensure this is the correct, simple filename for your wake word model ---
KEYWORD_PATHS = ["Krishna_en_raspberry-pi_v3_0_0.ppn"]

# --- Use a valid, working model from Perplexity ---
MODEL_NAME = "sonar"
PERPLEXITY_API_BASE_URL = "https://api.perplexity.ai"

# --- 2. Sanity Checks ---
if not all([PICOVOICE_ACCESS_KEY, PERPLEXITY_API_KEY]):
    print("FATAL ERROR: An API key is missing from the .env file.")
    exit()
if not os.path.exists(KEYWORD_PATHS[0]):
    print(f"FATAL ERROR: Wake word file '{KEYWORD_PATHS[0]}' not found.")
    exit()

# --- 3. Initialize Perplexity Client ---
try:
    perplexity_client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url=PERPLEXITY_API_BASE_URL)
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Perplexity client: {e}")
    exit()

# --- 4. Core Functions ---

def speak_text(text, lang_code='en'):
    """Converts text to speech in the specified language."""
    print(f"Assistant ({lang_code}): {text}")
    try:
        pygame.mixer.init()
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save("response.mp3")
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        os.remove("response.mp3")
    except Exception as e:
        print(f"Error in speak_text: {e}")

def recognize_bilingual_with_confidence(recognizer, audio_data):
    """
    Attempts to transcribe audio in both Tamil and English, then returns
    the result with the higher confidence score.
    """
    tamil_text, tamil_confidence = None, 0.0
    english_text, english_confidence = None, 0.0

    # Attempt to recognize as Tamil
    try:
        response_tamil = recognizer.recognize_google(audio_data, language='ta-IN', show_all=True)
        if response_tamil and 'alternative' in response_tamil:
            top_alt = response_tamil['alternative'][0]
            tamil_text = top_alt['transcript']
            tamil_confidence = top_alt.get('confidence', 0.8) # Default high confidence
    except sr.UnknownValueError:
        pass # This is expected if the speech is not Tamil

    # Attempt to recognize as English
    try:
        response_english = recognizer.recognize_google(audio_data, language='en-US', show_all=True)
        if response_english and 'alternative' in response_english:
            top_alt = response_english['alternative'][0]
            english_text = top_alt['transcript']
            english_confidence = top_alt.get('confidence', 0.8) # Default high confidence
    except sr.UnknownValueError:
        pass # This is expected if the speech is not English

    # Compare confidence scores and return the winner
    print(f"Confidence Scores -> Tamil: {tamil_confidence:.2f}, English: {english_confidence:.2f}")
    if tamil_confidence > english_confidence:
        return tamil_text, "ta" # Return 'ta' for gTTS
    elif english_confidence > tamil_confidence:
        return english_text, "en" # Return 'en' for gTTS
    else:
        return None, None

# --- 5. Main Application ---
def main():
    porcupine, paudio, audio_stream = None, None, None
    recognizer = sr.Recognizer()
    
    try:
        porcupine = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keyword_paths=KEYWORD_PATHS)
        paudio = pyaudio.PyAudio()
        audio_stream = paudio.open(
            rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
            input=True, frames_per_buffer=porcupine.frame_length
        )

        print("Assistant is ready. Listening for 'Krishna'...")
        speak_text("Assistant is ready.")

        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            if porcupine.process(pcm) >= 0:
                print("Wake word detected!")
                speak_text("Yes?")
                
                frames = []
                print("Listening for command...")
                for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * 6)):
                    frames.append(audio_stream.read(porcupine.frame_length))
                
                audio_data = sr.AudioData(b"".join(frames), porcupine.sample_rate, paudio.get_sample_size(pyaudio.paInt16))
                
                command, language = recognize_bilingual_with_confidence(recognizer, audio_data)
                
                if command and language:
                    print(f"You ({language}): {command}")

                    if command.lower().strip() in ["exit", "quit", "goodbye", "stop"]:
                        speak_text("Goodbye!", lang_code=language)
                        break

                    messages = [{"role": "system", "content": "You are an AI assistant. You are located in Twinsburg, Ohio. All answers must be relevant to Cleveland, Ohio unless asked for differently by the user.  You MUST answer all questions in a single and VERY concise sentence. "
                "Do not elaborate. Do not ask follow-up questions. If a question is complex, provide the most direct and simple summary possible in one sentence. "
                "For conversational greetings, respond simply. For example, if asked 'how are you?', respond 'I am always fine.'"}]
                    messages.append({"role": "user", "content": command})
                    
                    print("Processing your request...")
                    response = perplexity_client.chat.completions.create(model=MODEL_NAME, messages=messages)
                    assistant_response_text = response.choices[0].message.content.strip()
                    
                    speak_text(assistant_response_text, lang_code=language)
                else:
                    speak_text("Sorry, I didn't catch that.")
                
                print("\nReturning to wake word listening...")

    except KeyboardInterrupt:
        print("Stopping assistant.")
    finally:
        if porcupine: porcupine.delete()
        if audio_stream: audio_stream.close()
        if paudio: paudio.terminate()
        print("Cleanup complete.")

if __name__ == '__main__':
    main()