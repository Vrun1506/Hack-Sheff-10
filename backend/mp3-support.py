import os
import json
import logging
import requests
import io
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

# Add a global BOT_ID to ignore self-mentions
BOT_ID = None

# --- HELPER: ELEVENLABS ---
def text_to_speech(text_content):
    """
    Accepts text, sends to ElevenLabs, returns audio binary (MP3) or None.
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
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.content
        else:
            logging.error(f"ElevenLabs Error [{response.status_code}]: {response.text}")
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

# --- HELPER: SLACK UPLOAD ---
def _upload_mp3_to_slack(channel_id, audio_bytes, filename="summary.mp3", title="Audio Recap"):
    """
    Upload MP3 audio bytes to Slack using files_upload_v2 if available,
    otherwise fall back to files_upload. Returns True on success.
    """
    file_obj = io.BytesIO(audio_bytes)
    file_obj.seek(0)

    # Try files_upload_v2 (recommended/stable)
    try:
        if hasattr(app.client, "files_upload_v2"):
            # file_info holds metadata (channels must be a list)
            file_info = {
                "name": filename,
                "title": title,
                "initial_comment": "🎧 Audio summary generated.",
                "channels": [channel_id]
            }
            resp = app.client.files_upload_v2(file=file_obj, file_info=file_info)
            # Slack SDK returns a dict-like response
            if isinstance(resp, dict) and not resp.get("ok", True):
                logging.error(f"files_upload_v2 failed: {resp}")
                return False
            return True

        # Fallback to older files_upload (may be deprecated)
        resp = app.client.files_upload(
            channels=channel_id,
            file=file_obj,
            filename=filename,
            title=title,
            initial_comment="🎧 Audio summary generated.",
            filetype="mp3"
        )
        if isinstance(resp, dict) and not resp.get("ok", True):
            logging.error(f"files_upload failed: {resp}")
            return False
        return True

    except Exception as e:
        logging.error(f"Slack upload exception: {e}")
        return False

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
    # Keep history bounded
    if len(conversation_history) > 200:
        # trim older entries
        del conversation_history[0: len(conversation_history) - 200]
    
    # 2. Send to OpenAI for JSON Decision
    logger.info(f"Analyzing message: {text}")
    decision_json = analyze_and_generate_json(conversation_history, text)

    if not decision_json:
        logger.error("Decision JSON is empty; aborting.")
        return

    # 3. Act on the JSON
    trigger_audio = decision_json.get("trigger_audio", False)
    reply_text = decision_json.get("reply_text", "")
    summary_text = decision_json.get("summary_text", "")

    # Always reply with text reply_text if provided
    if reply_text:
        try:
            app.client.chat_postMessage(channel=channel_id, text=reply_text)
        except Exception as e:
            logger.error(f"Failed to post reply_text: {e}")

    # If trigger_audio is true and we have a summary, post the summary (like agent.py) and upload MP3
    if trigger_audio and summary_text:
        try:
            # Post the textual summary first (mirrors agent.py behavior)
            app.client.chat_postMessage(
                channel=channel_id,
                text=f"📝 *Here is the generated content:*\n\n{summary_text}"
            )
        except Exception as e:
            logger.error(f"Failed to post textual summary: {e}")

        logger.info("Triggering ElevenLabs for audio generation...")
        audio_data = text_to_speech(summary_text)

        if audio_data:
            success = _upload_mp3_to_slack(channel_id, audio_data)
            if not success:
                logger.error("Failed to upload MP3 via helper.")
                try:
                    app.client.chat_postMessage(channel=channel_id, text="Error uploading audio file to Slack.")
                except Exception:
                    pass
        else:
            try:
                app.client.chat_postMessage(channel=channel_id, text="Error generating audio file.")
            except Exception:
                pass

@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    """
    Handle explicit @mentions. Reuses the same decision -> summary -> mp3 flow
    as the message handler but only triggers when the bot is mentioned.
    """
    event = body.get("event", {}) or {}
    text = event.get("text", "") or ""
    user_id = event.get("user")
    channel_id = event.get("channel")

    # Safe guard: ensure we don't respond to ourselves
    try:
        auth = app.client.auth_test()
        bot_user = BOT_ID or auth.get("user_id")
    except Exception as e:
        logger.warning(f"auth_test failed: {e}")
        bot_user = BOT_ID

    if not user_id or user_id == bot_user:
        return

    # Update context
    conversation_history.append(f"User {user_id}: {text}")
    if len(conversation_history) > 200:
        del conversation_history[0: len(conversation_history) - 200]

    logger.info(f"Analyzing mention from {user_id}: {text}")
    decision_json = analyze_and_generate_json(conversation_history, text)
    if not decision_json:
        logger.error("Decision JSON empty for app_mention")
        try:
            say("Sorry, I couldn't analyze that message.")
        except Exception:
            pass
        return

    trigger_audio = decision_json.get("trigger_audio", False)
    reply_text = decision_json.get("reply_text", "")
    summary_text = decision_json.get("summary_text", "")

    if reply_text:
        try:
            # prefer say() for in-thread ack
            say(reply_text)
        except Exception:
            try:
                app.client.chat_postMessage(channel=channel_id, text=reply_text)
            except Exception as e:
                logger.error(f"Failed to post reply_text: {e}")

    if trigger_audio and summary_text:
        try:
            app.client.chat_postMessage(
                channel=channel_id,
                text=f"📝 *Here is the generated content:*\n\n{summary_text}"
            )
        except Exception as e:
            logger.error(f"Failed to post textual summary: {e}")

        logger.info("Generating audio from summary...")
        audio_data = text_to_speech(summary_text)
        if audio_data:
            success = _upload_mp3_to_slack(channel_id, audio_data)
            if not success:
                logger.error("Failed to upload MP3 via helper.")
                try:
                    app.client.chat_postMessage(channel=channel_id, text="Error uploading audio file to Slack.")
                except Exception:
                    pass
        else:
            try:
                app.client.chat_postMessage(channel=channel_id, text="Error generating audio file.")
            except Exception:
                pass

# --- STARTUP ---
if __name__ == "__main__":
    # determine BOT_ID on startup (same approach as agent.py)
    try:
        auth_test = app.client.auth_test()
        BOT_ID = auth_test.get("user_id")
        logging.info(f"Bot started! I am {BOT_ID}")
    except Exception as e:
        logging.warning(f"Could not determine BOT_ID on startup: {e}")
        BOT_ID = None

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()