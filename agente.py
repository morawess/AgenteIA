import json

import google.generativeai as genai
import google.api_core.exceptions

from config import API_KEY
from prompts import SYSTEM_PROMPT
from dados import tirar_dados
from personajes.personaje import cargar_personaje


# Configurar Gemini
genai.configure(api_key=API_KEY)


# ==========================
# CARGAR PERSONAJE
# ==========================

personaje = cargar_personaje()

from personajes.personaje import (
    cargar_personaje,
    actualizar_personaje
)

prompt_final = SYSTEM_PROMPT

if personaje:

    prompt_final += "\n\n=== FICHA DEL PERSONAJE ===\n"

    prompt_final += json.dumps(
        personaje,
        ensure_ascii=False,
        indent=2
    )

    print(
        f"\n[INFO] Personaje cargado: {personaje.get('nombre', 'Desconocido')}"
    )

else:

    print(
        "\n[INFO] No se encontró personaje.json"
    )
    print(personaje)


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
            },

            {
                "name": "actualizar_personaje",
                "description": (
                    "Actualiza cualquier valor dentro del personaje usando una ruta JSON."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {

                        "ruta": {
                            "type": "STRING",
                            "description": (
                                "Ruta del campo. Ejemplo: "
                                "nivel, atributos.fuerza, combate.hp_actual"
                            )
                        },

                        "valor": {
                            "type": "STRING",
                            "description": (
                                "Nuevo valor para almacenar"
                            )
                        }

                    },
                    "required": [
                        "ruta",
                        "valor"
                    ]
                }
            }
        ]
    }
]


modelo = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=prompt_final,
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

        print(
            "\nDungeon Master: Que los dados estén siempre a tu favor, aventurero."
        )

        break

    # Reiniciar conversación
    if mensaje.lower() == "/limpiar":

        chat = modelo.start_chat()

        print(
            "\nDungeon Master: La campaña ha sido reiniciada.\n"
        )

        continue

    try:

        respuesta = chat.send_message(mensaje)

        MAX_FUNCTION_CALLS = 5

        contador = 0

        while True:

            contador += 1

            if contador > MAX_FUNCTION_CALLS:

                print(
                    "\nError: demasiadas llamadas consecutivas a funciones.\n"
                )

                break

            function_call = None

            if (
                respuesta.candidates
                and respuesta.candidates[0].content
                and respuesta.candidates[0].content.parts
            ):

                for part in respuesta.candidates[0].content.parts:

                    if (
                        hasattr(part, "function_call")
                        and part.function_call
                    ):

                        function_call = part.function_call

                        break

            if function_call is None:
                break

            if function_call.name == "tirar_dados":

                expresion = function_call.args.get(
                    "expresion"
                )

                resultado = tirar_dados(
                    expresion
                )

                if "error" in resultado:

                    print(
                        f"\nError en la tirada: {resultado['error']}\n"
                    )

                    break

                print("\n=== TIRADA DE DADOS ===")

                print(
                    f"{resultado['dados']} → "
                    f"{resultado['tiradas']} "
                    f"(Mod: {resultado['modificador']:+}) "
                    f"= {resultado['total']}"
                )

                respuesta = chat.send_message(
                    {
                        "function_response": {
                            "name": "tirar_dados",
                            "response": resultado,
                        }
                    }
                )

            elif function_call.name == "actualizar_personaje":
                ruta = function_call.args.get(
                    "ruta"
                )

                valor = function_call.args.get(
                    "valor"
                )

                try:

                    valor = json.loads(valor)

                except:

                    pass

                resultado = actualizar_personaje(
                    ruta,
                    valor
                )

                if "error" in resultado:

                    print(
                        f"\nError al actualizar personaje: {resultado['error']}\n"
                    )

                    break

                print(
                    f"\n[INFO] Personaje actualizado: {ruta} = {valor}\n"
                )

                respuesta = chat.send_message(
                    {
                        "function_response": {
                            "name": "actualizar_personaje",
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

            print(
                "\n".join(textos)
            )

        else:

            print(
                "(El Dungeon Master no generó una respuesta textual.)"
            )

        print()

    except google.api_core.exceptions.ResourceExhausted as e:

        print("\nERROR DE CUOTA:")

        print(e)

        print()

    except google.api_core.exceptions.DeadlineExceeded:

        print(
            "\nLa solicitud tardó demasiado. Intenta nuevamente.\n"
        )

    except Exception as e:

        print(
            f"\nError inesperado: {e}\n"
        )
