# Smart Bilingual Voice Assistant

Bilingual Voice Assistant for Raspberry Pi
This project is a hands-free, voice-activated AI assistant that runs on a Raspberry Pi. Its key feature is the ability to dynamically detect whether a user is speaking English or Tamil and then process the entire request in that language.

It uses a custom wake word to activate and leverages the Perplexity API to provide fast, accurate, and up-to-date answers in both languages, making it a powerful tool for bilingual users.

Features
Dynamic Bilingual Support: Automatically identifies and responds in either English or Tamil on a per-query basis.

Intelligent Language Detection: Uses a "Confidence Score" algorithm to reliably determine the spoken language without needing a separate language model.

Hands-Free Activation: Powered by a custom wake word ("Krishna") using the PicoVoice Porcupine engine.

Real-Time Answers: Integrates with the Perplexity API (llama-3-sonar-large-32k-online) for search-augmented, conversational responses.

Standalone Operation: Designed to run automatically on boot as a systemd user service on a headless Raspberry Pi.

Hardware Requirements
Raspberry Pi 4 or 5 (Raspberry Pi 5 recommended)

A quality USB Microphone

A USB-powered Speaker

A reliable Power Supply for the Raspberry Pi

A microSD Card (16GB or larger)

Software & API Setup
Before you begin, you will need to sign up for two free services to get the necessary API keys.

Perplexity API Key:

Go to the Perplexity Labs Platform and create a free account.

Generate a new API key and save it.

PicoVoice Porcupine Access Key & Wake Word:

Create a free account at the PicoVoice Console.

Copy your AccessKey from the main dashboard.

Go to the Porcupine tab, train a custom wake word (e.g., "Krishna"), and select Raspberry Pi as the platform.

Download the resulting .ppn model file.

Create the .env File:
Create a file named .env in the project directory and add your secret keys:

PERPLEXITY_API_KEY="your_perplexity_key_goes_here"
PICOVOICE_ACCESS_KEY="your_picovoice_access_key_goes_here"

Add Your Wake Word File:
Place the .ppn file you downloaded from PicoVoice into the project directory. Ensure its filename matches the KEYWORD_PATHS variable in the Python script.

Set Up the Python Environment:
It is highly recommended to use a virtual environment.

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

(Note: Create a requirements.txt file containing openai, python-dotenv, SpeechRecognition, PyAudio, gTTS, pygame, and pvporcupine).

Configure Raspberry Pi Audio:
For reliable operation, you must configure your Pi's audio. Use arecord -l and aplay -l to find the card numbers for your USB mic and speaker, then create a file at /etc/asound.conf with the correct configuration. (See the associated Medium article for details).

Usage
You can run the assistant directly for testing or set it up as a service to run automatically on boot.

Manual Execution
Activate the virtual environment:

source venv/bin/activate

Run the script (e.g., krishna_lang.py):

python krishna_lang.py

Running as a Service (Recommended)
Create a systemd user service file at ~/.config/systemd/user/perplexity_assistant.service. (See the associated Medium article for the full configuration).

Enable linger to allow the service to run on boot, even when you are not logged in:

sudo loginctl enable-linger your_username

Enable and start the service:

systemctl --user enable perplexity_assistant.service
systemctl --user start perplexity_assistant.service

To view the live logs, use:

journalctl --user -u perplexity_assistant.service -f

How It Works
The core of the bilingual capability is the "Confidence Score" method.

The script starts and passively listens for the wake word using PicoVoice Porcupine.

When the wake word is detected, the assistant records the user's command.

This audio is sent to the Google Speech-to-Text API twice in parallel: once with language='ta-IN' and once with language='en-US'.

The script receives two transcriptions, each with a confidence score.

It compares the scores and selects the language with the higher confidence.

The winning transcription is sent to the Perplexity API.

The text response from Perplexity is converted to audio using gTTS, using the language code detected in step 5.

The assistant returns to its passive listening state.
