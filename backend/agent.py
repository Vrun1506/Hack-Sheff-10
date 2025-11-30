import requests
import os
import logging
import time
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timezone

# 1. Setup Environment
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI and Slack
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Configuration
BOT_ID = None  # Will be set on startup
CONTEXT_LIMIT = 15  # How many previous messages to read

# Grafana / Loki Configuration
LOKI_URL = os.environ.get("GRAFANA_URL")
USER_ID = os.environ.get("GRAFANA_USER_ID")
API_TOKEN = os.environ.get("GRAFANA_API_TOKEN")

# --- GRAFANA HELPER FUNCTIONS ---

def create_latency_payload(data_points, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
    output_list = []
    for agent_name, latency_value in data_points:
        record = {
            "timestamp": timestamp,
            "agent": agent_name,
            "latency": latency_value
        }
        output_list.append(record)
    return output_list

def create_token_payload(count, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
    data = {
       "timestamp": timestamp,
       "Tokens": "Tokens",
       "count": count
    }
    return [data]

def push_to_grafana(data_list, loki_url, user_id, api_token, labels={'app': 'token-tracker'}):
    streams = []
    for item in data_list:
        try:
            dt = datetime.strptime(item['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
            timestamp_ns = str(int(dt.timestamp() * 1e9))
            streams.append({
                "stream": labels,
                "values": [[timestamp_ns, json.dumps(item)]]
            })
        except ValueError as e:
            logging.warning(f"⚠️ Skipping item due to date error: {e}")
            continue

    if not streams:
        return

    payload = {"streams": streams}
    
    try:
        response = requests.post(
            loki_url, 
            json=payload, 
            headers={"Content-Type": "application/json"}, 
            auth=(user_id, api_token)
        )
        if response.status_code == 204:
            logging.info(f"✅ Pushed {len(streams)} records to Grafana.")
        else:
            logging.error(f"❌ Grafana Error {response.status_code}: {response.text}")
    except Exception as e:
        logging.error(f"❌ Grafana Connection Error: {e}")


# 2. The "Brain" - Decides to speak and generates content
def query_llm_agent(conversation_history):
    system_prompt = """
    You are a helpful assistant managed by a Viral LinkedIn Bot.
    YOUR GOAL:
    - Read the conversation transcript.
    - Generate a clear, detailed summary of the conversation context or a LinkedIn post draft.
    OUTPUT FORMAT:
    - Just the content. No "Here is the summary:" prefixes.
    """
    
    # [DEBUG] Log that we are about to call OpenAI
    logging.info("[DEBUG STAGE 3] Sending context to LLM...")

    try:
        start_time = time.perf_counter()
        request_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TRANSCRIPT:\n{conversation_history}"}
            ]
        )

        end_time = time.perf_counter()
        latency = end_time - start_time

        if response.usage:
            prompt_tokens = response.usage.prompt_tokens
            token_data = create_token_payload(prompt_tokens, request_timestamp)
            push_to_grafana(token_data, LOKI_URL, USER_ID, API_TOKEN, labels={'app': 'slack-bot-tokens'})
            
            latency_data = create_latency_payload([("LLM_Agent", latency)], request_timestamp)
            push_to_grafana(latency_data, LOKI_URL, USER_ID, API_TOKEN, labels={'app': 'slack-bot-latency'})

        content = response.choices[0].message.content.strip()
        
        # [DEBUG] Log what the LLM returned
        logging.info(f"[DEBUG STAGE 4] LLM Response received (First 50 chars): {content[:50]}...")
        return content

    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return None


# 3. Helper: Fetch and format chat history
def get_chat_context(channel_id):
    try:
        result = app.client.conversations_history(
            channel=channel_id,
            limit=CONTEXT_LIMIT
        )
        messages = result.get("messages", [])
        
        transcript = ""
        for msg in reversed(messages):
            user = msg.get("user", "Unknown")
            text = msg.get("text", "")
            if "subtype" in msg: 
                continue
            transcript += f"User {user}: {text}\n"
            
        return transcript
    except Exception as e:
        logging.error(f"History Fetch Error: {e}")
        return ""


# 4. Event Listener: The "Ear"
@app.event("message")
def handle_message_events(body, say, logger):
    event = body.get("event", {})
    text = event.get("text", "")
    user_id = event.get("user")
    channel_id = event.get("channel")

    # --- FILTER 1: IGNORE SELF ---
    if user_id == BOT_ID:
        return

    # --- FILTER 2: CHECK FOR MENTION ---
    if f"<@{BOT_ID}>" not in text:
        return 

    # Clean text
    cleaned_text = text.replace(f"<@{BOT_ID}>", "").strip()

    # --- BRANCH: SUMMARIZE vs ORCHESTRATE ---
    if "summarize" in cleaned_text.lower():
        # --- EXISTING SUMMARIZATION LOGIC ---
        logging.info("========================================")
        logging.info(f"[DEBUG STAGE 1] Accepted User Message: '{text}'")
        logging.info(f"[DEBUG STAGE 1] From User ID: {user_id}")
        logging.info("========================================")
        
        process_start = time.perf_counter()
        request_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        # 1. Acknowledge receipt
        say(f"On it! analyzing the last {CONTEXT_LIMIT} messages for you... 🧠")

        # 2. Fetch Context
        logging.info(f"[DEBUG STAGE 2] Fetching conversation history for channel {channel_id}...")
        transcript = get_chat_context(channel_id)

        # 3. Ask the Brain
        response = query_llm_agent(transcript + "\n[SYSTEM: THE USER HAS EXPLICITLY REQUESTED A POST. GENERATE IT NOW.]")

        # 4. Speak / Trigger Webhook
        if response:
            # --- NEW STEP: PRINT TO SLACK FIRST ---
            say(f"📝 *Here is the generated content:*\n\n{response}")
            
            n8n_webhook_url = "https://ermai.app.n8n.cloud/webhook/generate-post" 
            
            payload = {
                "summary": response,      
                "user_id": user_id,       
                "original_text": text     
            }
            
            # --- [DEBUG STAGE 5] ---
            logging.info("[DEBUG STAGE 5] Preparing to send payload to N8N:")
            logging.info(json.dumps(payload, indent=2)) 
            
            try:
                requests.post(n8n_webhook_url, json=payload)
                logging.info(f"✅ [DEBUG STAGE 6] Successfully sent to n8n.")
                say("✅ (Also sent to n8n for further processing)")
                
            except Exception as e:
                logging.error(f"Failed to send to n8n: {e}")
                say(f"❌ I showed you the content, but failed to send it to n8n. Error: {e}")
        else:
            say("I couldn't generate a response based on this context. Try chatting a bit more first!")

        # 5. Log Full Process Latency
        process_end = time.perf_counter()
        total_latency = process_end - process_start
        latency_data = create_latency_payload([("Full_Process", total_latency)], request_timestamp)
        push_to_grafana(latency_data, LOKI_URL, USER_ID, API_TOKEN, labels={'app': 'slack-bot-full-process'})

    else:
        # --- NEW ORCHESTRATOR LOGIC ---
        logging.info(f"Orchestrator triggered for: {cleaned_text}")
        status_msg = say(f"🧠 *Orchestrator:* Analyzing request...")
        
        try:
            # Call Router
            router_json = get_llm_response(ROUTER_SYSTEM_PROMPT, cleaned_text, json_mode=True)
            routing_data = json.loads(router_json)
            decision = routing_data.get("decision", "TECH")
            reasoning = routing_data.get("reasoning", "")

            # Update Status
            app.client.chat_update(
                channel=channel_id,
                ts=status_msg["ts"],
                text=f"🧠 *Orchestrator:* Routing to *{decision}* Agent.\n_Reasoning: {reasoning}_"
            )

            final_response = ""

            if decision == "TECH":
                say(f"🛠️ *Tech Agent* is working...", thread_ts=status_msg["ts"])
                final_response = get_llm_response(TECH_SYSTEM_PROMPT, cleaned_text)

            elif decision == "BUSINESS":
                say(f"💼 *Business Agent* is working...", thread_ts=status_msg["ts"])
                final_response = get_llm_response(BUSINESS_SYSTEM_PROMPT, cleaned_text)

            elif decision == "BOTH":
                say(f"🔄 *Collaborating* (Tech ⇄ Business)...", thread_ts=status_msg["ts"])
                
                # Step A: Tech
                tech_res = get_llm_response(TECH_SYSTEM_PROMPT, cleaned_text)
                
                # Step B: Business (Critique)
                biz_context = f"User Query: {cleaned_text}\n\nTech Proposal: {tech_res}\n\nTask: Analyze cost/ROI."
                biz_res = get_llm_response(BUSINESS_SYSTEM_PROMPT, biz_context)

                # Step C: Synthesize
                syn_context = f"Query: {cleaned_text}\n\nTech: {tech_res}\n\nBusiness: {biz_res}"
                final_response = get_llm_response(SYNTHESIZER_SYSTEM_PROMPT, syn_context)

            # Final Reply
            say(f"*Final Response:*\n\n{final_response}")

        except Exception as e:
            logger.error(f"Orchestrator Error: {e}")
            say(f"❌ Something went wrong with the agents: {e}")


# --- ORCHESTRATOR PROMPTS ---
ROUTER_SYSTEM_PROMPT = """
You are the Principal Orchestrator for a multi-agent system.
Your goal is to route user requests to the correct specialized agent.

AGENTS AVAILABLE:
1. Tech Agent: Senior Staff Engineer. Handles system design, architecture, code patterns.
2. Business Agent: Financial Planner. Handles budgeting, costs, ROI, strategy.

INSTRUCTIONS:
- Analyze the user's input.
- Decide if it requires the "TECH" agent, the "BUSINESS" agent, or "BOTH".
- "BOTH" is used when a request involves technical implementation AND cost/business implications.

OUTPUT FORMAT (JSON ONLY):
{
  "decision": "TECH" | "BUSINESS" | "BOTH",
  "reasoning": "Brief explanation"
}
"""

TECH_SYSTEM_PROMPT = """
You are an AI agent acting as a Senior Staff Software Engineer specializing in system design 
and technical architecture. 
Your Core Responsibilities:
- High-level system design (APIs, data flow, services, scalability).
- Architectural decision-making (Monolith vs Microservices, SQL vs NoSQL).
- Engineering best practices (Observability, Testing strategies).
"""

BUSINESS_SYSTEM_PROMPT = """
You are an AI agent acting as a Corporate Financial Planner and Business Strategist.
Your Core Responsibilities:
- Analyze costs (Cloud spend, headcount, licensing).
- Evaluate ROI (Return on Investment) and TCO (Total Cost of Ownership).
- Assess business risks and strategic alignment.
"""

SYNTHESIZER_SYSTEM_PROMPT = """
You are the Final Synthesizer.
You have received inputs from two specialized agents (Tech and Business).
Combine their insights into a single, cohesive, professional Slack response.
Use Slack formatting (bolding, bullet points) to make it readable.
"""

def get_llm_response(system_prompt, user_input, model="gpt-4o", json_mode=False):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.5
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return "Error contacting the AI brain."


# Startup
if __name__ == "__main__":
    auth_test = app.client.auth_test()
    BOT_ID = auth_test["user_id"]
    logging.info(f"Bot started! I am {BOT_ID}")

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()