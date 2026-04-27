import os
from dotenv import load_dotenv
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise SystemExit("ERROR: Set OPENAI_API_KEY in your environment or .env file.")

openai.api_key = OPENAI_API_KEY

response = openai.Completion.create(
    model="code-davinci-002",
    prompt="# Python function to reverse a string\n",
    max_tokens=100,
    temperature=0.2,
    n=1,
    stop=["\n\n"]
)

print(response.choices[0].text.strip())
