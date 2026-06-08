import json

from google import genai

from config import client
from prompts import SYSTEM_PROMPT
from dados import tirar_dados as tirar_dados_func
from personajes.personaje import (
    cargar_personaje,
    actualizar_personaje as actualizar_personaje_func,
)

# ==========================
# CARGAR PERSONAJE
# ==========================

personaje = cargar_personaje()

prompt_final = SYSTEM_PROMPT

if personaje:

    prompt_final += "\n\n=== FICHA DEL PERSONAJE ===\n"

    prompt_final += json.dumps(
        personaje,
        ensure_ascii=False,
        indent=2,
    )

    print(
        f"\n[INFO] Personaje cargado: "
        f"{personaje.get('nombre', 'Desconocido')}"
    )

else:

    print(
        "\n[INFO] No se encontró personaje.json"
    )


# ==========================
# TOOLS
# ==========================

def tirar_dados(expresion: str) -> dict:
    """
    Realiza tiradas de dados para D&D.
    """

    resultado = tirar_dados_func(expresion)

    if "error" not in resultado:

        print("\n=== TIRADA DE DADOS ===")

        print(
            f"{resultado['dados']} → "
            f"{resultado['tiradas']} "
            f"(Mod: {resultado['modificador']:+}) "
            f"= {resultado['total']}"
        )

        print()

    return resultado


def actualizar_personaje(ruta: str, valor: str) -> dict:
    """
    Actualiza cualquier valor dentro del personaje usando
    una ruta JSON.
    """

    if isinstance(valor, str):

        try:
            valor_procesado = json.loads(valor)

        except json.JSONDecodeError:
            valor_procesado = valor

    else:

        valor_procesado = valor

    print(
        f"\n[INFO] Actualizando personaje: "
        f"{ruta} = {valor_procesado}"
    )

    resultado = actualizar_personaje_func(
        ruta,
        valor_procesado,
    )

    return resultado


# ==========================
# CREAR CHAT
# ==========================

def crear_chat():

    return client.chats.create(
        model="gemini-2.5-flash",
        config=genai.types.GenerateContentConfig(
            system_instruction=prompt_final,
            tools=[
                tirar_dados,
                actualizar_personaje,
            ],
        ),
    )


chat = crear_chat()

print("=== DungeonMasterGPT ===")
print("Escribe '/salir' para terminar.")
print("Escribe '/limpiar' para reiniciar la campaña.\n")

# ==========================
# LOOP PRINCIPAL
# ==========================

while True:

    mensaje = input("Jugador: ")

    # ----------------------
    # Salir
    # ----------------------

    if mensaje.lower() == "/salir":

        print(
            "\nDungeon Master: "
            "Que los dados estén siempre a tu favor, aventurero."
        )

        break

    # ----------------------
    # Limpiar
    # ----------------------

    if mensaje.lower() == "/limpiar":

        chat = crear_chat()

        print(
            "\nDungeon Master: "
            "La campaña ha sido reiniciada.\n"
        )

        continue

    try:

        respuesta = chat.send_message(mensaje)

        print("\nDM:")

        if hasattr(respuesta, "text") and respuesta.text:

            print(respuesta.text)

        else:

            print(
                "(El Dungeon Master no generó una respuesta textual.)"
            )

        print()

    except Exception as e:

        error = str(e).lower()

        if "quota" in error or "429" in error:

            print("\nERROR DE CUOTA:")
            print(e)

        elif (
            "deadline" in error
            or "timeout" in error
        ):

            print(
                "\nLa solicitud tardó demasiado. "
                "Intenta nuevamente.\n"
            )

        elif "503" in error or "unavailable" in error:

            print(
                "\nGemini está saturado temporalmente. "
                "Intenta nuevamente en unos segundos.\n"
            )

        else:

            print(
                f"\nError inesperado: {e}\n"
            )