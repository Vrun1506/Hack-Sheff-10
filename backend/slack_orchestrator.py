import os
import json
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# --- IMPORT LOGIC FROM YOUR CLI TOOL ---
# This ensures the Slack bot behaves exactly like your CLI test
from orchestrator import (
    client, # Reuse the OpenAI client connection
    ROUTER_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    TECH_SYSTEM_PROMPT,
    BUSINESS_SYSTEM_PROMPT,
    get_agent_response
)

# --- SETUP ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Initialize Slack
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def handle_mentions(body, say, logger):
    event = body.get("event", {})
    text = event.get("text", "")
    user = event.get("user")
    channel = event.get("channel")

    # Clean the text (remove @BotName)
    bot_id = app.client.auth_test()["user_id"]
    cleaned_text = text.replace(f"<@{bot_id}>", "").strip()

    if not cleaned_text:
        say(f"Hi <@{user}>! I'm the Multi-Agent Orchestrator. Ask me a question!")
        return

    # 1. ROUTING STEP
    # Send a temporary "Thinking" message
    status_msg = say(f"🧠 *Orchestrator:* Analyzing request...")
    
    try:
        # Call the Router (Using the same prompt as orchestrator.py)
        router_response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": cleaned_text}
            ]
        )
        routing = json.loads(router_response.choices[0].message.content)
        decision = routing.get("decision")
        reasoning = routing.get("reasoning")

        # Update the status message on Slack
        app.client.chat_update(
            channel=channel,
            ts=status_msg["ts"],
            text=f"🧠 *Orchestrator:* Routing to *{decision}* Agent.\n_Reasoning: {reasoning}_"
        )

        final_response = ""

        # 2. EXECUTION STEP
        if decision == "TECH":
            say(f"🛠️ *Tech Agent* is working...", thread_ts=status_msg["ts"])
            final_response = get_agent_response(TECH_SYSTEM_PROMPT, cleaned_text)

        elif decision == "BUSINESS":
            say(f"💼 *Business Agent* is working...", thread_ts=status_msg["ts"])
            final_response = get_agent_response(BUSINESS_SYSTEM_PROMPT, cleaned_text)

        elif decision == "BOTH":
            say(f"🔄 *Collaborating* (Tech ⇄ Business)...", thread_ts=status_msg["ts"])
            
            # Step A: Tech Agent
            tech_res = get_agent_response(TECH_SYSTEM_PROMPT, cleaned_text)
            
            # Step B: Business Agent (Critique)
            biz_context = f"User Query: {cleaned_text}\n\nTech Proposal: {tech_res}\n\nTask: Analyze cost/ROI."
            biz_res = get_agent_response(BUSINESS_SYSTEM_PROMPT, biz_context)

            # Step C: Synthesis
            syn_context = f"Query: {cleaned_text}\n\nTech: {tech_res}\n\nBusiness: {biz_res}"
            final_response = get_agent_response(SYNTHESIZER_SYSTEM_PROMPT, syn_context)

        # 3. FINAL OUTPUT
        say(f"*Final Response:*\n\n{final_response}")

    except Exception as e:
        logger.error(f"Error: {e}")
        say(f"❌ Something went wrong: {e}")

if __name__ == "__main__":
    print("⚡️ Slack Orchestrator is running!")
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()