import json

from google import genai

from config import client
from prompts import SYSTEM_PROMPT
from dados import tirar_dados as tirar_dados_func
from personajes.personaje import (
    cargar_personaje,
    actualizar_personaje as actualizar_personaje_func,
)

from memoria.memoria import (
    inicializar_memoria,
    crear_sesion,
    listar_sesiones,
    cargar_sesion,
    agregar_mensaje,
    guardar_sesion,
    vaciar_historial_sesion,
)



# ==========================
# STATE (sin inyectar ficha en system prompt)
# ==========================

def _calcular_modificadores(personaje: dict) -> dict:

    if not personaje:
        return personaje

    atributos = personaje.get("atributos", {})

    personaje["modificadores"] = {
        atributo: (valor - 10) // 2
        for atributo, valor in atributos.items()
    }

    return personaje


# Solo para logs de arranque (NO para el prompt del modelo)
personaje = cargar_personaje()
if personaje:
    _calcular_modificadores(personaje)
    print(
        f"\n[INFO] Personaje cargado: {personaje.get('nombre', 'Desconocido')}"
    )
else:
    print("\n[INFO] No se encontró personaje.json")


# Importamos el prompt base, pero en este archivo el sistema puede tener una copia distinta.
# Para evitar inconsistencias, usamos SIEMPRE el de prompts.py.
prompt_final = SYSTEM_PROMPT

# ==========================
# TOOLS
# ==========================


def tirar_dados(expresion: str) -> dict:

    """Realiza tiradas de dados para D&D."""

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
    """Actualiza cualquier valor dentro del personaje usando una ruta JSON."""

    if isinstance(valor, str):

        try:
            valor_procesado = json.loads(valor)

        except json.JSONDecodeError:
            valor_procesado = valor

    else:
        valor_procesado = valor

    print(
        f"\n[INFO] Actualizando personaje: {ruta} = {valor_procesado}"
    )

    resultado = actualizar_personaje_func(ruta, valor_procesado)

    # Luego de actualizar, recalcular modificadores si corresponde.
    # (Esto mantiene coherencia para futuras lecturas.)
    personaje_actual = cargar_personaje()
    if personaje_actual:
        # Calculamos modificadores para coherencia de lectura futura.
        _calcular_modificadores(personaje_actual)

        # Persistimos cada modificador recalculado.
        modificadores = personaje_actual.get("modificadores", {})
        for atributo, mod in modificadores.items():
            actualizar_personaje_func(f"modificadores.{atributo}", mod)

    return resultado


def leer_personaje(ruta: str | None = None) -> dict:
    """Devuelve la ficha actual del personaje.

    - Si `ruta` es None: retorna la ficha completa.
    - Si `ruta` tiene notación con puntos (ej: "atributos.fuerza"), retorna el valor.
    """

    personaje_actual = cargar_personaje()

    if personaje_actual is None:
        return {"error": "No existe personaje.json"}

    personaje_actual = _calcular_modificadores(personaje_actual)

    if not ruta:
        return personaje_actual

    claves = ruta.split(".")
    actual = personaje_actual

    for clave in claves:
        if not isinstance(actual, dict) or clave not in actual:
            return {"error": f"Ruta inválida: {ruta}"}
        actual = actual[clave]

    return {"ruta": ruta, "valor": actual}


# ==========================
# CREAR CHAT (con memoria de sesión)
# ==========================


def crear_chat():

    return client.chats.create(
        model="gemini-2.5-flash",
        config=genai.types.GenerateContentConfig(
            system_instruction=prompt_final,
            tools=[
                tirar_dados,
                actualizar_personaje,
                leer_personaje,
            ],
        ),
    )


def obtener_respuesta_textual(respuesta) -> str:
    """Extrae el texto final (si existe) desde la respuesta del SDK."""

    texto = []

    if hasattr(respuesta, "candidates"):
        for candidate in respuesta.candidates:
            if hasattr(candidate, "content"):
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        texto.append(part.text)

    return "".join(texto).strip()


# ==========================
# INICIO + SESIÓN
# ==========================

inicializar_memoria()

print("=== DungeonMasterGPT ===")
print("Escribe '/salir' para terminar.")
print("Escribe '/limpiar' para reiniciar la campaña.\n")

print("Sesiones disponibles (memoria persistente):")

sesiones = listar_sesiones()
if sesiones:
    for s in sesiones[:10]:
        print(f"- {s}")
else:
    print("(No hay sesiones guardadas aún)")

seleccion = input(
    "\nIngresá el ID de una sesión para continuar (o dejá vacío para crear una nueva): "
).strip()

if seleccion:
    sesion = cargar_sesion(seleccion)
    print(f"\n[INFO] Cargando sesión: {seleccion}\n")
else:
    sesion = crear_sesion()
    print(f"\n[INFO] Creando sesión nueva: {sesion['id']}\n")

chat = crear_chat()

# Contexto pendiente: para que el modelo recuerde lo que ya se dijo
# (workaround sin re-ejecutar tools por cada mensaje previo).
contexto_pendiente = ""
for m in sesion.get("historial", []):
    if m.get("rol") == "user":
        contexto_pendiente += f"Jugador: {m.get('contenido', '').strip()}\n"
    elif m.get("rol") == "assistant":
        contexto_pendiente += f"DM: {m.get('contenido', '').strip()}\n"

contexto_pendiente = contexto_pendiente.strip()


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

        guardar_sesion(sesion)
        break

    # ----------------------
    # Limpiar
    # ----------------------

    if mensaje.lower() == "/limpiar":

        # Reinicio REAL: borrar historial persistente y también sincronizar el objeto en RAM.
        vaciar_historial_sesion(sesion.get("id"))
        sesion["historial"] = []

        contexto_pendiente = ""


        # recrear chat para cortar contexto interno del SDK
        chat = crear_chat()

        print(
            "\nDungeon Master: "
            "La campaña ha sido reiniciada.\n"
        )

        continue

    # Guardar mensaje del usuario
    agregar_mensaje(sesion, "user", mensaje)
    guardar_sesion(sesion)

    try:

        # Si cargamos una sesión previa, inyectamos el contexto anterior SOLO una vez.
        mensaje_a_enviar = mensaje
        if contexto_pendiente:
            mensaje_a_enviar = (
                f"Contexto de la sesión anterior:\n{contexto_pendiente}\n\n"
                f"Ahora el jugador dice: {mensaje}"
            )
            contexto_pendiente = ""

        respuesta = chat.send_message(mensaje_a_enviar)


        texto = obtener_respuesta_textual(respuesta)

        print("\nDM:")

        if texto:
            print(texto)
        else:
            print("(El Dungeon Master no generó una respuesta textual.)")

        print()

        # Guardar respuesta del asistente
        agregar_mensaje(sesion, "assistant", texto if texto else "")
        guardar_sesion(sesion)

    except Exception as e:

        error = str(e).lower()

        if "quota" in error or "429" in error:

            print("\nERROR DE CUOTA:")
            print(e)

        elif ("deadline" in error or "timeout" in error):

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
            print(f"\nError inesperado: {e}\n")

