import json
import re
from pypdf import PdfReader


def extraer_texto_pdf(ruta_pdf):

    reader = PdfReader(ruta_pdf)

    texto = ""

    for pagina in reader.pages:
        contenido = pagina.extract_text()

        if contenido:
            texto += contenido + "\n"

    return texto


def buscar(texto, patron, default=""):

    match = re.search(
        patron,
        texto,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return default


def buscar_entero(texto, patron, default=0):

    valor = buscar(texto, patron)

    try:
        return int(valor)
    except:
        return default


def generar_personaje(texto):

    personaje = {}

    # -------------------------
    # DATOS GENERALES
    # -------------------------

    personaje["nombre"] = buscar(
        texto,
        r"^(.*?)\nNOMBRE DEL PERSONAJE"
    )

    clase_nivel = buscar(
        texto,
        r"*(.*?)\nCLASE Y NIVEL"
    )

    personaje["clase"] = clase_nivel
    personaje["nivel"] = 1

    match = re.match(r"(.+?)\s+(\d+)$", clase_nivel)

    if match:
        personaje["clase"] = match.group(1).strip()
        personaje["nivel"] = int(match.group(2))

    personaje["trasfondo"] = buscar(
        texto,
        r"*(.*?)\nTRASFONDO"
    )

    personaje["jugador"] = buscar(
        texto,
        r"*(.*?)\nJUGADOR"
    )

    personaje["especie"] = buscar(
        texto,
        r"JUGADOR\s*(.*?)\nESPECIE"
    )

    personaje["alineamiento"] = buscar(
        texto,
        r"*(.*?)\nALINEAMIENTO"
    )

    # -------------------------
    # ATRIBUTOS
    # -------------------------

    personaje["atributos"] = {
        "fuerza": buscar_entero(
            texto,
            r"FUERZA.*?\n(\d+)"
        ),
        "destreza": buscar_entero(
            texto,
            r"DESTREZA.*?\n(\d+)"
        ),
        "constitucion": buscar_entero(
            texto,
            r"CONSTITUCIÓN.*?\n(\d+)"
        ),
        "inteligencia": buscar_entero(
            texto,
            r"INTELIGENCIA.*?\n(\d+)"
        ),
        "sabiduria": buscar_entero(
            texto,
            r"SABIDURÍA.*?\n(\d+)"
        ),
        "carisma": buscar_entero(
            texto,
            r"CARISMA.*?\n(\d+)"
        )
    }

    # -------------------------
    # COMBATE
    # -------------------------

    personaje["combate"] = {
        "ca": buscar_entero(
            texto,
            r"(\d+)\s*CA"
        ),
        "velocidad": buscar_entero(
            texto,
            r"INICIATIVA\s*\+?\d+\s*(\d+)\s*VELOCIDAD"
        ),
        "hp_max": buscar_entero(
            texto,
            r"Puntos de Golpe Máximos\s*(\d+)"
        )
    }

    # -------------------------
    # HABILIDADES
    # -------------------------

    habilidades = {}

    patrones_habilidades = {
        "acrobacias": r"Acrobacias\s*([+-]?\d+)",
        "arcanos": r"Arcanos\s*([+-]?\d+)",
        "atletismo": r"Atletismo\s*([+-]?\d+)",
        "engañar": r"Engañar\s*([+-]?\d+)",
        "historia": r"Historia\s*([+-]?\d+)",
        "interpretacion": r"Interpretación\s*([+-]?\d+)",
        "intimidar": r"Intimidar\s*([+-]?\d+)",
        "investigacion": r"Investigación\s*([+-]?\d+)",
        "juego_de_manos": r"Juego de Manos\s*([+-]?\d+)",
        "medicina": r"Medicina\s*([+-]?\d+)",
        "naturaleza": r"Naturaleza\s*([+-]?\d+)",
        "percepcion": r"Percepción\s*([+-]?\d+)",
        "perspicacia": r"Perspicacia\s*([+-]?\d+)",
        "persuasion": r"Persuasión\s*([+-]?\d+)",
        "religion": r"Religión\s*([+-]?\d+)",
        "sigilo": r"Sigilo\s*([+-]?\d+)",
        "supervivencia": r"Supervivencia\s*([+-]?\d+)",
        "trato_animales": r"Trato con Animales\s*([+-]?\d+)"
    }

    for nombre, patron in patrones_habilidades.items():

        match = re.search(
            patron,
            texto
        )

        if match:
            habilidades[nombre] = int(
                match.group(1)
            )

    personaje["habilidades"] = habilidades

    # -------------------------
    # COMPETENCIAS
    # -------------------------

    comp_match = re.search(
        r"Competencias:(.*?)OTRAS COMPETENCIAS E IDIOMAS",
        texto,
        re.DOTALL
    )

    personaje["competencias"] = []

    if comp_match:

        competencias = comp_match.group(1)

        personaje["competencias"] = [
            linea.strip("- ").strip()
            for linea in competencias.split("\n")
            if linea.strip()
        ]

    # -------------------------
    # ATAQUES
    # -------------------------

    personaje["ataques"] = []

    ataque = re.search(
        r"Daga\s*\+(\d+)\s*1d4\s*\+(\d+)\s*perforante",
        texto
    )

    if ataque:

        personaje["ataques"].append(
            {
                "nombre": "Daga",
                "bonificador": int(
                    ataque.group(1)
                ),
                "daño": f"1d4+{ataque.group(2)} perforante"
            }
        )

    # -------------------------
    # RASGOS
    # -------------------------

    rasgos = []

    if "Acción astuta" in texto:
        rasgos.append("Acción astuta")

    if "Ataque furtivo" in texto:
        rasgos.append("Ataque furtivo")

    if "Jerga de Ladrones" in texto:
        rasgos.append("Jerga de Ladrones")

    personaje["rasgos"] = rasgos

    # -------------------------
    # PERSONALIDAD
    # -------------------------

    personaje["rasgos_personalidad"] = buscar(
        texto,
        r"RASGOS DE PERSONALIDAD(.*?)IDEALES"
    )

    personaje["ideales"] = buscar(
        texto,
        r"IDEALES(.*?)VÍNCULOS"
    )

    personaje["vinculos"] = buscar(
        texto,
        r"VÍNCULOS(.*?)DEFECTOS"
    )

    # -------------------------
    # HISTORIA
    # -------------------------

    personaje["historia"] = buscar(
        texto,
        r"HISTORIA DEL PERSONAJE(.*?)RASGOS"
    )

    return personaje


def guardar_personaje(personaje):

    with open(
        "personaje.json",
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            personaje,
            archivo,
            ensure_ascii=False,
            indent=4
        )


if __name__ == "__main__":

    ruta_pdf = input(
        "Ruta del PDF: "
    )

    texto = extraer_texto_pdf(
        ruta_pdf
    )

    personaje = generar_personaje(
        texto
    )

    guardar_personaje(
        personaje
    )

    print(
        "\nPersonaje guardado en personaje.json"
    )