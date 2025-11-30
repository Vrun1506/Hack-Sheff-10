import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI

# --- IMPORT EXISTING AGENT CONFIGS ---
# We import the system prompts to reuse the "personas" defined in your other files
try:
    from tech_agent import SYSTEM_PROMPT as TECH_SYSTEM_PROMPT
    from business_agent import SYSTEM_PROMPT as BUSINESS_SYSTEM_PROMPT
except ImportError:
    print("Error: Could not import agents. Make sure tech_agent.py and business_agent.py are in the same directory.")
    sys.exit(1)

# --- SETUP ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- CONFIG 3: THE MERGER / ROUTER ---
ROUTER_SYSTEM_PROMPT = """
You are the Principal Orchestrator for a multi-agent system.
Your goal is to route user requests to the correct specialized agent.

AGENTS AVAILABLE:
1. Tech Agent: Senior Staff Engineer. Handles system design, architecture, code patterns, scalability.
2. Business Agent: Financial Planner. Handles budgeting, costs, ROI, business strategy.

INSTRUCTIONS:
- Analyze the user's input.
- Decide if it requires the "TECH" agent, the "BUSINESS" agent, or "BOTH".
- "BOTH" is used when a request involves technical implementation AND cost/business implications (e.g., "Should we build microservices? What's the cost?").

OUTPUT FORMAT (JSON ONLY):
{
  "decision": "TECH" | "BUSINESS" | "BOTH",
  "reasoning": "Brief explanation"
}
"""

SYNTHESIZER_SYSTEM_PROMPT = """
You are the Final Synthesizer.
You have received inputs from two specialized agents (Tech and Business) regarding a user's query.
Your job is to combine their insights into a single, cohesive, professional response.

Structure the response clearly:
1. Technical Recommendation (Summarized)
2. Business/Financial Impact (Summarized)
3. Final Verdict/Next Steps
"""

# --- HELPER FUNCTIONS ---

def get_agent_response(system_prompt, user_input, context_messages=None):
    """Generic function to call an agent with a specific persona."""
    messages = [{"role": "system", "content": system_prompt}]
    if context_messages:
        messages.extend(context_messages)
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content

def run_orchestrator():
    print("--- Multi-Agent Orchestrator (Type 'quit' to exit) ---")
    print("   [Router Active: Deciding between Tech, Business, or Both]")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["quit", "exit"]:
                print("Orchestrator: Session ended.")
                break
            
            if not user_input.strip():
                continue

            # 1. ROUTING STEP
            print("...Thinking (Routing)...", end="\r")
            router_response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ]
            )
            routing = json.loads(router_response.choices[0].message.content)
            decision = routing.get("decision")
            reasoning = routing.get("reasoning")
            
            print(f"\n[Orchestrator]: Routing to -> {decision}")
            print(f"[Reasoning]: {reasoning}")

            # 2. EXECUTION STEP
            if decision == "TECH":
                response = get_agent_response(TECH_SYSTEM_PROMPT, user_input)
                print(f"\n[Tech Agent]:\n{response}")

            elif decision == "BUSINESS":
                response = get_agent_response(BUSINESS_SYSTEM_PROMPT, user_input)
                print(f"\n[Business Agent]:\n{response}")

            elif decision == "BOTH":
                print("\n[Orchestrator]: Initiating collaboration protocol...")
                
                # Step A: Tech Agent goes first to define the solution
                print("   -> Asking Tech Agent for architecture...")
                tech_response = get_agent_response(TECH_SYSTEM_PROMPT, user_input)
                
                # Step B: Business Agent critiques the Tech solution
                print("   -> Asking Business Agent to evaluate costs/ROI...")
                business_context = f"""
                CONTEXT: The user asked: "{user_input}"
                
                INPUT FROM TECH AGENT:
                "{tech_response}"
                
                TASK: Evaluate this technical approach from a financial/business perspective. 
                Identify costs, risks, and ROI. Do not redesign the tech, just analyze its business impact.
                """
                business_response = get_agent_response(BUSINESS_SYSTEM_PROMPT, business_context)

                # Step C: Synthesis
                print("   -> Synthesizing final response...")
                synthesis_context = f"""
                User Query: {user_input}
                
                Tech Agent Response:
                {tech_response}
                
                Business Agent Response:
                {business_response}
                """
                
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
                        {"role": "user", "content": synthesis_context}
                    ]
                ).choices[0].message.content
                
                print(f"\n[Collaborative Response]:\n{final_response}")

        except Exception as e:
            print(f"\n[Error]: {e}")

if __name__ == "__main__":
    run_orchestrator()