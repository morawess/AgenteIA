import json
import os 
from datetime import datetime

CARPETA_MEMORIA = "memoria"
# El guardado/persistencia lo maneja guardar_sesion().
# Este módulo actúa como gestor de sesiones (un solo JSON por sesión).


def inicializar_memoria():
    os.makedirs(CARPETA_MEMORIA, exist_ok=True)


def crear_sesion():
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    sesion = {
        "id": fecha,
        "fecha": fecha,
        "historial": []
    }

    guardar_sesion(sesion)

    return sesion


def _ruta_sesion(id_sesion: str) -> str:
    return os.path.join(CARPETA_MEMORIA, f"{id_sesion}.json")


def guardar_sesion(sesion):

    ruta = _ruta_sesion(sesion['id'])

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            sesion,
            archivo,
            ensure_ascii=False,
            indent=4
        )


def borrar_sesion(id_sesion: str) -> bool:
    """Borra el JSON persistente de la sesión.

    Returns:
        bool: True si se borró o no existía, False si falló.
    """
    inicializar_memoria()
    ruta = _ruta_sesion(id_sesion)
    try:
        if os.path.exists(ruta):
            os.remove(ruta)
        return True
    except Exception:
        return False


def vaciar_historial_sesion(id_sesion: str) -> bool:
    """Vacía el historial de una sesión existente (mantiene el ID)."""
    inicializar_memoria()
    ruta = _ruta_sesion(id_sesion)

    if not os.path.exists(ruta):
        return False

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            sesion = json.load(f)

        sesion["historial"] = []

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(sesion, f, ensure_ascii=False, indent=4)

        return True
    except Exception:
        return False


def borrar_memoria_interna_chat(sesion: dict) -> None:
    """Sincroniza el objeto en memoria (sesion) con el historial vacío.

    Importante: en el loop principal, /limpiar opera sobre el objeto `sesion`
    que ya está cargado en RAM. Si solo escribimos al JSON pero no vaciamos
    `sesion['historial']`, al guardar después volverá a reaparecer lo viejo.
    """
    if isinstance(sesion, dict) and "historial" in sesion:
        sesion["historial"] = []


def listar_sesiones():

    inicializar_memoria()

    archivos = sorted(
        os.listdir(CARPETA_MEMORIA),
        reverse=True
    )

    sesiones = []

    for archivo in archivos:

        if archivo.endswith(".json"):

            sesiones.append(
                archivo.replace(".json", "")
            )

    return sesiones


def cargar_sesion(id_sesion):

    ruta = _ruta_sesion(id_sesion)

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)


def agregar_mensaje(
    sesion,
    rol,
    contenido
):

    sesion["historial"].append(
        {
            "rol": rol,
            "contenido": contenido
        }
    )


def convertir_historial_gemini(sesion):

    historial = []

    for mensaje in sesion["historial"]:

        if mensaje["rol"] == "user":

            historial.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": mensaje["contenido"]
                        }
                    ]
                }
            )

        elif mensaje["rol"] == "assistant":

            historial.append(
                {
                    "role": "model",
                    "parts": [
                        {
                            "text": mensaje["contenido"]
                        }
                    ]
                }
            )

    return historial

