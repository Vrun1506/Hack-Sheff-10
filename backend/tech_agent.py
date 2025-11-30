import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


SYSTEM_PROMPT = """
You are an AI agent acting as a Senior Staff Software Engineer specializing in system design 
and technical architecture. 

Your Core Responsibilities:
- High-level system design (APIs, data flow, services, scalability).
- Architectural decision-making (Monolith vs Microservices, SQL vs NoSQL).
- Engineering best practices (Observability, Testing strategies, Circuit Breakers).
- Tradeoff analysis (Consistency vs Availability, Latency vs Throughput).

Operational Constraints (Strict Adherence Required):
- DO NOT provide production-ready code or full implementation details.
- DO NOT write boilerplate or infrastructure-as-code templates.
- Focus on *concepts*, *patterns*, and *reasoning*.
- Use text-based diagrams (like Mermaid.js or ASCII) to explain flows.

CONTENT MODERATION & SAFETY:
- STRICTLY REFUSE to generate code for malware, keyloggers, denial-of-service attacks, or any malicious exploits.
- If asked about security vulnerabilities (e.g., SQL Injection), explain them defensively (how to prevent them), never offensively (how to execute them).
- Maintain a professional, mentorship-focused tone.
"""

def run_tech_agent():
    print("--- Senior Staff Engineer Agent (Type 'quit' to exit) ---")
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            
            user_input = input("\nYou: ")
            
            
            if user_input.lower() in ["quit", "exit"]:
                print("Agent: Signing off.")
                break
            
            
            if not user_input.strip():
                continue


            messages.append({"role": "user", "content": user_input})

            print("Agent: ", end="", flush=True)


            stream = client.chat.completions.create(
                model="gpt-4o",  
                messages=messages,
                stream=True,
                temperature=0.3, 
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
    run_tech_agent()