import google.generativeai as genai

from config import API_KEY
from prompts import SYSTEM_PROMPT

genai.configure(api_key=API_KEY)

modelo = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

chat = modelo.start_chat(history=[])

print("=== DungeonMasterGPT ===")
print("Escribe '/salir' para terminar.\n")

while True:

    mensaje = input("Jugador: ")

    if mensaje.lower() == "/salir":
        print("\nDungeon Master: Que los dados estén siempre a tu favor, aventurero.")
        break

    try:

        respuesta = chat.send_message(mensaje)

        print("\nDM:")
        print(respuesta.text)
        print()

    except Exception as e:
        print(f"\nError: {e}")