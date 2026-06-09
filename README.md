# Dungeon Master AI (Dungeon Master con Gemini)

DMAI es un **Dungeon Master** para **Dungeons & Dragons 5e**. El programa mantiene una **conversación interactiva** con un jugador, utilizando Gemini para generar narración y decisiones de la aventura.

## ¿Qué hace el agente?
- Lee y mantiene una **ficha persistente del personaje** (guardada en `personajes/personaje.json`).
- Maneja una **memoria persistente de sesiones**: podés continuar campañas guardadas.
- Provee **tools específicas** para que Gemini:
  - Realice tiradas de dados de D&D.
  - Lea valores actuales del personaje.
  - Actualice la ficha cuando ocurran cambios permanentes.

## Requisitos
- Tener una API key de **Gemini**.
- Python instalado.

## Configuración (API key)
1. Copiar `.env.example` a `.env`.
2. En `.env` guardar la key para Gemini (variable `GEMINI_API_KEY`).

> Ejemplo (según tu `.env.example`):
> - `GEMINI_API_KEY=tu_api_key_aqui`

## Instalación de dependencias
Instalar dependencias con:

```bash
pip install -r requirements.txt
```

## Ejecución
1. Asegurate de tener tu `.env` configurado.
2. Ejecutar el programa con:

```bash
python agente.py
```

El programa te muestra las sesiones disponibles y permite al usuario:
- Elegir una sesión existente, o crear una nueva.
- Usar comandos:
  - `/limpiar`: reinicia la campaña (vacía el historial de la sesión).
  - `/salir`: termina la ejecución.



