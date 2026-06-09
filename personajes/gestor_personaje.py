import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARCHIVO_PERSONAJE = os.path.join(
    BASE_DIR,
    "personaje.json"
)


def cargar_personaje():

    if not os.path.exists(ARCHIVO_PERSONAJE):
        return None

    with open(
        ARCHIVO_PERSONAJE,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)
    

def guardar_personaje(personaje):

    with open(
        ARCHIVO_PERSONAJE,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            personaje,
            archivo,
            ensure_ascii=False,
            indent=4
        )


def actualizar_personaje(
    ruta,
    valor
):

    personaje = cargar_personaje()

    if personaje is None:

        return {
            "error": "No existe personaje.json"
        }

    claves = ruta.split(".")

    actual = personaje

    for clave in claves[:-1]:

        if clave not in actual:

            actual[clave] = {}

        actual = actual[clave]

    actual[claves[-1]] = valor

    guardar_personaje(personaje)

    return {
        "ok": True,
        "ruta": ruta,
        "valor": valor
    }

