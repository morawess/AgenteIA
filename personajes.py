import os
import re
import json
from typing import Any, Dict, Optional


def _extract_pdf_text(pdf_path: str, max_chars: int = 5000) -> str:
    """Extrae texto de un PDF.

    Asume que el PDF tiene texto embebido.
    Si es escaneado (imagen), hace falta OCR (no implementado aquí).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"No existe el PDF: {pdf_path}")

    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError(
            "Falta dependencia para leer PDFs. Ejecutá: pip install pypdf"
        ) from e

    reader = PdfReader(pdf_path)
    parts = []
    total = 0
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)
            total += len(txt)
            if total >= max_chars:
                break

    text = "\n".join(parts).strip()
    if not text:
        raise ValueError(
            "No pude extraer texto del PDF. Si es un PDF escaneado, hace falta OCR."
        )
    return text


def _build_personaje_schema() -> Dict[str, Any]:
    return {
        "version": "dnd5e-sheet-v1",
        "fuente": {"pdf_path": None},
        "datos_personaje": {
            "nombre": None,
            "clase": None,
            "nivel": None,
            "raza": None,
            "alineamiento": None,
            "jugador": None,
            "fondo": None,
            "experiencia": None,
        },
        "atributos": {
            "STR": None,
            "DEX": None,
            "CON": None,
            "INT": None,
            "WIS": None,
            "CHA": None,
            "modificadores": {
                "STR": None,
                "DEX": None,
                "CON": None,
                "INT": None,
                "WIS": None,
                "CHA": None,
            },
        },
        "combat": {
            "CA": {"valor": None, "tipo": None},
            "puntos_vida": {"max": None, "actual": None, "temp": None},
            "velocidad": None,
            "iniciativa": None,
        },
        "competencias": {
            "proficiencia": None,
            "tiradas_ataque": None,
            "salvaciones": [],
            "habilidades": {},
            "skills_proficientes": [],
        },
        "rasgos": {
            "clase": [],
            "rasgos_raciales": [],
            "rasgos_fondo": [],
            "equipamiento_especial": [],
        },
        "caracteristicas": {
            "idiomas": [],
            "talismanes": [],
            "armas": [],
            "armaduras": [],
        },
        "habilidades": {"conjuros": {"lista": []}},
        "transfondo": {
            "texto": None,
            "eventos_clave": [],
            "vinculos": [],
            "ideales": [],
            "defectos": [],
        },
        "notas": {"texto": None},
        "acciones": {"ataques": []},
        "items": {"inventario": []},
        "estado_actualizacion": {
            "ultimo_pdf": None,
            "actualizado_por": "leer_personaje",
        },
    }


def _coerce_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, int):
        return x
    s = str(x).strip()
    if not s:
        return None
    try:
        return int(s)
    except Exception:
        m = re.search(r"-?\d+", s)
        return int(m.group(0)) if m else None


def _normalize_personaje_json(raw: Dict[str, Any], pdf_path: str) -> Dict[str, Any]:
    schema = _build_personaje_schema()

    def merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in src.items():
            if k in dst and isinstance(dst[k], dict) and isinstance(v, dict):
                merge(dst[k], v)
            else:
                dst[k] = v
        return dst

    merged = merge(schema, raw or {})
    merged["fuente"]["pdf_path"] = pdf_path

    for attr in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
        merged["atributos"][attr] = _coerce_int(merged["atributos"].get(attr))
        mods = merged["atributos"].get("modificadores", {})
        if isinstance(mods, dict) and attr in mods:
            mods[attr] = _coerce_int(mods.get(attr))

    merged["datos_personaje"]["nivel"] = _coerce_int(
        merged["datos_personaje"].get("nivel")
    )

    return merged


def cargar_personaje_json(
    personaje: Optional[Dict[str, Any]] = None,
    ruta_json: Optional[str] = None,
) -> Dict[str, Any]:
    """Normaliza un personaje D&D 5e que ya está en formato JSON.

    No lee archivos PDF directamente. Debe pasarse preferiblemente la ruta a
    un archivo .json generado previamente.
    """
    if ruta_json:
        if not isinstance(ruta_json, str) or not ruta_json.strip():
            return {"error": "ruta_json inválida"}
        if not os.path.exists(ruta_json):
            return {"error": f"No existe el archivo JSON: {ruta_json}"}
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                personaje = json.load(f)
        except Exception as e:
            return {"error": f"Error al leer JSON: {e}"}

    if not isinstance(personaje, dict):
        return {"error": "personaje debe ser un objeto JSON válido"}

    normalized = _normalize_personaje_json(
        personaje, personaje.get("fuente", {}).get("pdf_path")
    )
    return normalized


def _heuristic_pdf_to_raw(texto: str) -> Dict[str, Any]:
    raw: Dict[str, Any] = {
        "datos_personaje": {"nivel": None, "nombre": None},
        "transfondo": {"texto": None},
    }

    m_nivel = re.search(r"(?:Nivel|Level)\s*[:]?\s*(\d{1,2})\b", texto, re.I)
    if m_nivel:
        raw["datos_personaje"]["nivel"] = int(m_nivel.group(1))

    m_nombre = re.search(r"(?:Nombre)\s*[:]?\s*(.{0,40})\n", texto, re.I)
    if m_nombre:
        nombre = m_nombre.group(1).strip()
        raw["datos_personaje"]["nombre"] = nombre if nombre else None

    m_bg = re.search(r"(?:Transfondo|Background)\b[\s\S]{0,2000}", texto, re.I)
    if m_bg:
        block = m_bg.group(0)
        block = re.sub(
            r"^(?:.*?(?:Transfondo|Background)\b[:]?\s*)", "", block, flags=re.I
        )
        raw["transfondo"]["texto"] = block.strip()[:4000] if block.strip() else None

    return raw


def leer_personaje(ruta_pdf: str) -> Dict[str, Any]:
    """PDF -> JSON con heurísticas locales (sin LLM).

    Esto reduce tokens porque el modelo NO recibe el PDF.
    Aun así, la extracción depende de que el PDF tenga texto embebido.
    """
    if not ruta_pdf or not isinstance(ruta_pdf, str):
        return {"error": "ruta_pdf inválida"}

    texto = _extract_pdf_text(ruta_pdf)
    raw = _heuristic_pdf_to_raw(texto)
    normalized = _normalize_personaje_json(raw, ruta_pdf)
    normalized["estado_actualizacion"]["ultimo_pdf"] = ruta_pdf
    return normalized


def actualizar_personaje(personaje: Dict[str, Any], evento: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza campos derivados cuando el personaje sube de nivel.

    NO inventa datos.
    """
    if not isinstance(personaje, dict):
        return {"error": "personaje debe ser dict"}
    if not isinstance(evento, dict):
        return {"error": "evento debe ser dict"}

    tipo = evento.get("tipo")
    nivel_obj = evento.get("nivel")

    pj = personaje

    if tipo == "subir_nivel":
        nuevo_nivel = _coerce_int(nivel_obj)
        if nuevo_nivel is not None:
            pj.setdefault("datos_personaje", {})["nivel"] = nuevo_nivel

            # Proficiencia 5e (aprox por tablas)
            prof = pj.get("competencias", {}).get("proficiencia")
            if prof is None:
                if nuevo_nivel <= 4:
                    pj.setdefault("competencias", {})["proficiencia"] = 2
                elif nuevo_nivel <= 8:
                    pj.setdefault("competencias", {})["proficiencia"] = 3
                elif nuevo_nivel <= 12:
                    pj.setdefault("competencias", {})["proficiencia"] = 4
                elif nuevo_nivel <= 16:
                    pj.setdefault("competencias", {})["proficiencia"] = 5
                else:
                    pj.setdefault("competencias", {})["proficiencia"] = 6

            pj.setdefault("estado_actualizacion", {})["actualizado_por"] = (
                "actualizar_personaje"
            )
            pj.setdefault("estado_actualizacion", {})["ultimo_evento"] = evento

    return pj


def pdf_a_json_cache(ruta_pdf: str, cache_json_path: str) -> Dict[str, Any]:
    """Convierte PDF a JSON y lo cachea en disco.

    Útil para que el chat siempre use JSON guardado, evitando recalcular.
    """
    pj = leer_personaje(ruta_pdf)
    pj["fuente"]["pdf_path"] = ruta_pdf

    os.makedirs(os.path.dirname(cache_json_path) or ".", exist_ok=True)
    import json

    with open(cache_json_path, "w", encoding="utf-8") as f:
        json.dump(pj, f, ensure_ascii=False, indent=2)

    return pj

