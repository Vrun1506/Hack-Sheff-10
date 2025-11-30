import os
import json
import logging
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Keys
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM" # Example Voice ID

# Global Memory (Stores the last 20 messages)
conversation_history = []
CONTEXT_LIMIT = 20

# --- HELPER: ELEVENLABS ---
def text_to_speech(text_content):
    """
    Accepts text, sends to ElevenLabs, returns audio binary.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text_content,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            logging.error(f"ElevenLabs Error: {response.text}")
            return None
    except Exception as e:
        logging.error(f"ElevenLabs connection failed: {e}")
        return None

# --- THE BRAIN (OpenAI JSON Generator) ---
def analyze_and_generate_json(history, user_input):
    """
    1. Reads history.
    2. Determines if user_input is a request for a summary.
    3. Returns JSON.
    """
    
    # Slice the last N messages
    context_slice = history[-CONTEXT_LIMIT:]
    transcript = "\n".join(context_slice)

    system_prompt = """
    You are a background conversation processor.
    
    INPUT DATA:
    1. A transcript of a chat conversation.
    2. The latest message from a user.
    
    YOUR TASK:
    Analyze the LATEST message. 
    - Does it look like a request for a summary, catch-up, recap, or "what happened"?
    - Or is it just normal conversation?
    
    OUTPUT FORMAT (JSON ONLY):
    You must output a valid JSON object with the following structure:
    {
      "trigger_audio": boolean,      // true if user wants a summary, false otherwise
      "summary_text": string | null, // The summary text to be spoken (if trigger is true)
      "reply_text": string           // A text reply to the user (e.g. "Sure, generating audio...")
    }
    
    If "trigger_audio" is true, write a concise, professional summary in "summary_text".
    If "trigger_audio" is false, "summary_text" should be null, and "reply_text" should be a normal conversational response.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # or gpt-3.5-turbo-0125
            response_format={"type": "json_object"}, # <--- ENFORCES JSON
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\nLATEST USER MESSAGE:\n{user_input}"}
            ]
        )
        
        # Parse the string response into a Python Dictionary
        json_content = json.loads(response.choices[0].message.content)
        return json_content

    except Exception as e:
        logging.error(f"LLM JSON Error: {e}")
        return None

# --- EVENT LISTENER ---
@app.event("message")
def handle_message_events(body, logger):
    event = body.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text", "")

    # Ignore self
    auth_test = app.client.auth_test()
    if user_id == auth_test["user_id"]:
        return

    # 1. Update Context
    conversation_history.append(f"User {user_id}: {text}")
    
    # 2. Send to OpenAI for JSON Decision
    # We pass the full history and the specific text that just came in
    logger.info(f"Analyzing message: {text}")
    decision_json = analyze_and_generate_json(conversation_history, text)

    if not decision_json:
        return # Error handling

    # 3. Act on the JSON
    trigger_audio = decision_json.get("trigger_audio", False)
    reply_text = decision_json.get("reply_text", "")
    summary_text = decision_json.get("summary_text", "")

    # Always reply with text if provided (e.g., "Here is your summary" or just "Hello")
    if reply_text:
        app.client.chat_postMessage(channel=channel_id, text=reply_text)

    # 4. If JSON said "True" for audio, call ElevenLabs
    if trigger_audio and summary_text:
        logger.info("Triggering ElevenLabs...")
        
        # Call Backend Audio API
        audio_data = text_to_speech(summary_text)
        
        if audio_data:
            # Upload Result to Slack
            app.client.files_upload_v2(
                channel=channel_id,
                file=audio_data,
                filename="summary.mp3",
                title="Audio Recap",
                initial_comment="🎧 Audio summary generated."
            )
        else:
            app.client.chat_postMessage(channel=channel_id, text="Error generating audio file.")

# --- STARTUP ---
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()