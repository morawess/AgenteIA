# AgenteIA

Agente de Dungeon Master para una aventura interactiva con Gemini.

## Requisitos

- Python 3.10 o superior.
- `pip` instalado.
- Clave de API de Gemini en la variable de entorno `GEMINI_API_KEY`.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env`:

```powershell
copy .env.example .env
```

2. Abre `.env` y reemplaza `tu_api_key_aqui` con tu clave real de Gemini.

## Ejecución

```powershell
python agente.py
```

## Notas

- El archivo `.env` está incluido en `.gitignore` para que no se suba al repositorio.
- Si un compañero clona este repo, debe instalar las dependencias y crear su propio `.env`.
- El paquete `google-generativeai` está en desuso; para futuras actualizaciones, considera migrar a `google-genai`.

