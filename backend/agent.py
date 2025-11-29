import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv

# 1. Setup Environment
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI and Slack
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Configuration
BOT_ID = None  # Will be set on startup
CONTEXT_LIMIT = 15  # How many previous messages to read

# 2. The "Brain" - Decides to speak and generates content
def query_llm_agent(conversation_history):
    """
    Sends the chat transcript to the LLM.
    The LLM decides whether to reply or stay silent (async group member behavior).
    """
    system_prompt = """
    You are 'DevBot', a helpful, cynical, but brilliant senior developer in a group chat.
    
    YOUR GOAL:
    - Read the conversation transcript.
    - If the users are asking for help, discussing code, or if you have a brilliant suggestion, REPLY.
    - If the conversation is casual noise or not relevant to you, DO NOT REPLY.
    - If you reply, keep it short (1-2 sentences) and chatty. Do not be formal.
    
    OUTPUT FORMAT:
    - If you want to stay silent, output exactly: NO_RESPONSE
    - If you want to speak, just output your message.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or gpt-3.5-turbo for speed/cost
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TRANSCRIPT:\n{conversation_history}"}
            ]
        )
        content = response.choices[0].message.content.strip()
        return None if content == "NO_RESPONSE" else content
    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return None

# 3. Helper: Fetch and format chat history
def get_chat_context(channel_id):
    try:
        # Fetch history from Slack
        result = app.client.conversations_history(
            channel=channel_id,
            limit=CONTEXT_LIMIT
        )
        messages = result.get("messages", [])
        
        # Reverse to chronological order (oldest -> newest)
        transcript = ""
        for msg in reversed(messages):
            user = msg.get("user", "Unknown")
            text = msg.get("text", "")
            # Skip join/leave messages
            if "subtype" in msg: 
                continue
            transcript += f"User {user}: {text}\n"
            
        return transcript
    except Exception as e:
        logging.error(f"History Fetch Error: {e}")
        return ""

# 4. Event Listener: The "Ear"
@app.event("message")
def handle_message_events(body, logger):
    event = body.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    # IGNORE our own messages to prevent infinite loops
    if user_id == BOT_ID:
        return

    logger.info(f"Received message from {user_id}: {text}")

    # A. Fetch Context
    transcript = get_chat_context(channel_id)

    # B. Ask the Brain
    response = query_llm_agent(transcript)

    # C. Speak (if the brain had something to say)
    if response:
        app.client.chat_postMessage(
            channel=channel_id,
            text=response
        )

# Startup: Get Bot ID to ignore self
@app.event("app_mention")
def handle_app_mentions(body, say, logger):
    # Force a reply if directly mentioned
    logger.info("Direct mention received")
    event = body.get("event", {})
    channel_id = event.get("channel")
    
    transcript = get_chat_context(channel_id)
    # Add a specific prompt override for direct mentions if needed
    response = query_llm_agent(transcript + "\n[SYSTEM: USER MENTIONED YOU DIRECTLY. YOU MUST ANSWER.]")
    
    if response:
        say(response)
    else:
        say("I'm looking into that...") # Fallback

if __name__ == "__main__":
    # Fetch our own Bot ID on startup
    auth_test = app.client.auth_test()
    BOT_ID = auth_test["user_id"]
    logging.info(f"Bot started! I am {BOT_ID}")

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()