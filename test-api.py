import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("Falta la API Key. Revisá tu archivo .env")
    exit(1)


print("Conectando con la API de Groq")
cliente = Groq(api_key=api_key)

try:
    
    respuesta = cliente.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[
            {"role": "user", "content": "Hola, respondé solo con la frase: '¡Conexión exitosa, listo para el TP!'"}
        ]
    )
    
    print("\nRespuesta del modelo:")
    print(respuesta.choices[0].message.content)

except Exception as e:
    print(f"\nHubo un error al conectar: {e}")