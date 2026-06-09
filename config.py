import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

print("API KEY CARGADA:", API_KEY[:15] + "...")

if not API_KEY:
    raise ValueError("No se encontró GEMINI_API_KEY")

# Configurar cliente de Google Generative AI
client = genai.Client(api_key=API_KEY)