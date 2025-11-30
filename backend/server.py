from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
import io

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)


@app.route('/')
def home():
    return "Hello, World!"


load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def text_to_speech(text, voice_id=VOICE_ID):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if not response.ok:
        raise Exception(f"ElevenLabs API request failed: {response.status_code} {response.text}")
    return response.content

@app.route('/api/tts', methods=['POST'])
def api_tts(voice_id=VOICE_ID):
    
    payload = request.get_json(silent=True)
    if not payload or 'text' not in payload:
        return {"error": "No text provided"}, 400
    
    text = payload["text"]

    try:
        audio_bytes = text_to_speech(text, voice_id)
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="output.mp3"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

