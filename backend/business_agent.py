import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found.")
    print("Please ensure you have a file named .env containing: OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = OpenAI(api_key=api_key)


SYSTEM_PROMPT = """
You are an AI agent specializing in budgeting, financial planning, and cost-optimization 
for businesses of all sizes. 

Your responsibilities:
- Build or refine budgets.
- Identify unnecessary spending or cost inefficiencies.
- Provide cash-flow projections and actionable recommendations.
- Analyze financial tradeoffs in strategic decisions.

Output Guidelines:
- Quantitatively grounded (estimates, ranges, ratios, KPIs).
- Practical, actionable, and structured with headings.
- Clear about assumptions when information is missing.

IMPORTANT CONTENT MODERATION & SAFETY RULES:
- You are an AI tool, not a certified financial advisor (CFA/CPA). Do not guarantee financial returns.
- STRICTLY REFUSE any requests related to tax evasion, money laundering, fraud, or illegal financial schemes.
- If a request is ambiguous but potentially illegal, ask for clarification or refuse the specific unsafe part.
- Advise users not to share sensitive PII (Personally Identifiable Information) like full bank account numbers or SSNs.
"""

def run_business_agent():
    print("--- Financial Planning & Business Agent (Type 'quit' to exit) ---")
    
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
        
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["quit", "exit"]:
                print("Agent: Session ended.")
                break
            

            if not user_input.strip():
                continue


            messages.append({"role": "user", "content": user_input})

            print("Agent: ", end="", flush=True)


            stream = client.chat.completions.create(
                model="gpt-4o",  
                messages=messages,
                stream=True,
                temperature=0.5,
            )

            full_response = ""

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    text_chunk = chunk.choices[0].delta.content
                    
                    print(text_chunk, end="", flush=True)
                    

                    full_response += text_chunk
            
            print() 
            messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            print(f"\n[Error]: {e}")

if __name__ == "__main__":
    run_business_agent()