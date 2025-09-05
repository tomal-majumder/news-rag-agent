from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv() 

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
def generate_llm_answer(prompt, model="llama-3.3-70b-versatile", max_tokens=2000):
    try:
        print(f"Generating answer with model {model}...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful news assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.5,
            top_p=0.95
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating answer: {e}"