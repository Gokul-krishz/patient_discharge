import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

# Get API key from .env file
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("Available Gemini Models:")
print("=" * 50)

for model in genai.list_models():
    print(f"\nModel Name: {model.name}")
    print(f"Display Name: {model.display_name}")
    print(f"Supported Methods: {model.supported_generation_methods}")
    print("-" * 50)
