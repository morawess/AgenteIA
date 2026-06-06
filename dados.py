import random
import re

def tirar_dados(expresion):

    patron = r'(\d+)d(\d+)([+-]\d+)?'

    match = re.match(patron, expresion)

    if not match:
        return {"error": "Expresión inválida"}

    cantidad = int(match.group(1))
    caras = int(match.group(2))

    modificador = int(match.group(3) or 0)

    resultados = [
        random.randint(1, caras)
        for _ in range(cantidad)
    ]

    total = sum(resultados) + modificador

    return {
        "dados": expresion,
        "tiradas": resultados,
        "modificador": modificador,
        "total": total
    }