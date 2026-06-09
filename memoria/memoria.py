import json
import os 
from datetime import datetime

CARPETA_MEMORIA = "memoria"
#TO DO: agregar función para que el agente guarde memoria

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


def guardar_sesion(sesion):

    ruta = os.path.join(
        CARPETA_MEMORIA,
        f"{sesion['id']}.json"
    )

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

    ruta = os.path.join(
        CARPETA_MEMORIA,
        f"{id_sesion}.json"
    )

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