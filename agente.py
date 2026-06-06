import google.generativeai as genai
import google.api_core.exceptions

from config import API_KEY
from prompts import SYSTEM_PROMPT
from dados import tirar_dados



# Configurar Gemini
genai.configure(api_key=API_KEY)

# Declaración de herramientas
herramientas = [
    {
        "function_declarations": [
            {
                "name": "tirar_dados",
                "description": (
                    "Realiza tiradas de dados para Dungeons & Dragons. "
                    "Acepta expresiones como 1d20, 1d20+5 o 2d6."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "expresion": {
                            "type": "STRING",
                            "description": "Expresión de dados en formato XdY+Z",
                        }
                    },
                    "required": ["expresion"],
                },
            }
        ]
    }
]


modelo = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
    tools=herramientas,
)

chat = modelo.start_chat()

print("=== DungeonMasterGPT ===")
print("Escribe '/salir' para terminar.")
print("Escribe '/limpiar' para reiniciar la campaña.\n")

while True:
    mensaje = input("Jugador: ")

    # Salir
    if mensaje.lower() == "/salir":
        print("\nDungeon Master: Que los dados estén siempre a tu favor, aventurero.")
        break

    # Reiniciar conversación
    if mensaje.lower() == "/limpiar":
        chat = modelo.start_chat()
        print("\nDungeon Master: La campaña ha sido reiniciada.\n")
        continue

    try:
        respuesta = chat.send_message(mensaje)

        MAX_FUNCTION_CALLS = 5
        contador = 0

        while True:
            contador += 1

            if contador > MAX_FUNCTION_CALLS:
                print("\nError: demasiadas llamadas consecutivas a funciones.\n")
                break

            function_call = None
            if (
                respuesta.candidates
                and respuesta.candidates[0].content
                and respuesta.candidates[0].content.parts
            ):
                for part in respuesta.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        function_call = part.function_call
                        break

            if function_call is None:
                break

            if function_call.name == "tirar_dados":
                expresion = function_call.args.get("expresion")
                resultado = tirar_dados(expresion)

                if "error" in resultado:
                    print(f"\nError en la tirada: {resultado['error']}\n")
                    break

                print("\n=== TIRADA DE DADOS ===")
                print(
                    f"{resultado['dados']} → {resultado['tiradas']} "
                    f"(Mod: {resultado['modificador']:+}) = {resultado['total']}"
                )

                respuesta = chat.send_message(
                    {
                        "function_response": {
                            "name": "tirar_dados",
                            "response": resultado,
                        }
                    }
                )


        print("\nDM:")
        textos = []
        if (
            respuesta.candidates
            and respuesta.candidates[0].content
            and respuesta.candidates[0].content.parts
        ):
            for part in respuesta.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    textos.append(part.text)

        if textos:
            print("\n".join(textos))
        else:
            print("(El Dungeon Master no generó una respuesta textual.)")

        print()

    except google.api_core.exceptions.ResourceExhausted as e:
        print("\nERROR DE CUOTA:")
        print(e)
        print()

    except google.api_core.exceptions.DeadlineExceeded:
        print("\nLa solicitud tardó demasiado. Intenta nuevamente.\n")

    except Exception as e:
        print(f"\nError inesperado: {e}\n")

