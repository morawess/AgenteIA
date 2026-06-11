import json
import os
import random
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_PERSONAJE = os.path.join(BASE_DIR, "personajes", "personaje.json")


def _cargar_personaje():
    if not os.path.exists(ARCHIVO_PERSONAJE):
        return None
    with open(ARCHIVO_PERSONAJE, "r", encoding="utf-8") as f:
        return json.load(f)


def _calc_mod(valor_atributo: int) -> int:
    return (valor_atributo - 10) // 2


def tirar_dados(expresion: str):
    """Realiza tiradas de dados para D&D.

    Soporta 2 formatos:
    - "NdM+X" (ej: "1d20-1")
    - Salvaciones (ej: "salvacion.destreza", "salvacion.inteligencia")
      donde el modificador se calcula desde personaje.json.
    """

    if not isinstance(expresion, str):
        return {"error": "Expresión inválida"}

    expresion = expresion.strip().lower()

    #expresión para salvaciones
    if expresion.startswith("salvacion."):
        atributo = expresion.split(".", 1)[1]
        personaje = _cargar_personaje()
        if not personaje:
            return {"error": "No existe personaje.json"}

        atributos = personaje.get("atributos", {})
        if atributo not in atributos:
            return {"error": f"Atributo inválido en salvacion: {atributo}"}

        mod = _calc_mod(int(atributos[atributo]))
        roll = random.randint(1, 20)
        total = roll + mod

        #devuelve en el formato esperado todos los datos relevantes para la salvación.
        return {
            "dados": f"1d20{mod:+d}",
            "tiradas": [roll],
            "modificador": mod,
            "total": total,
            "tipo": "salvacion",
            "atributo": atributo,
        }

    #expresión estándar NdM+/-X
    patron = r"(\d+)d(\d+)([+-]\d+)?"
    match = re.match(patron, expresion)

    if not match:
        return {"error": "Expresión inválida"}

    cantidad = int(match.group(1))
    caras = int(match.group(2))
    modificador = int(match.group(3) or 0)

    resultados = [random.randint(1, caras) for _ in range(cantidad)]
    total = sum(resultados) + modificador

    #devuelve los datos relevantes de la tirada estándar.
    return {
        "dados": expresion,
        "tiradas": resultados,
        "modificador": modificador,
        "total": total,
    }

