import os
import requests
from datetime import datetime
from openai import OpenAI

# ================= CONFIG =================
ORBIS_URL = os.getenv("ORBIS_URL", "https://orbis-5gkk.onrender.com/procesar")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= CORE =================

def interpretar_instruccion(texto_usuario: str) -> str:
    """
    Usa GPT para convertir una frase natural en un comando Orbis (/registrar, /agenda, etc.)
    """
    prompt = f"""
    Convierte la siguiente instrucción en un comando válido de Orbis.
    Formatos válidos:
    - /agenda
    - /registrar YYYY-MM-DD HH:MM Tarea
    - /borrar YYYY-MM-DD HH:MM
    - /borrar_fecha YYYY-MM-DD
    - /borrar_todo
    - /buscar Palabra
    - /cuando Nombre
    - /reprogramar VIEJA_FECHA VIEJA_HORA NUEVA_FECHA NUEVA_HORA
    - /modificar YYYY-MM-DD HH:MM Nuevo texto
    - /buscar_fecha YYYY-MM-DD

    Ejemplo:
    Usuario: "Agéndame con Laura mañana a las 4pm"
    Salida: /registrar 2025-09-22 16:00 Reunión con Laura

    Usuario: "{texto_usuario}"
    Salida:
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # modelo rápido y económico
        messages=[{"role": "system", "content": "Eres un traductor a comandos de Orbis."},
                  {"role": "user", "content": prompt}],
        max_tokens=100
    )

    comando = resp.choices[0].message.content.strip()
    return comando

def llamar_orbis(comando: str, chat_id: str = None) -> dict:
    """
    Llama a la API de Orbis con el comando dado y devuelve la respuesta en JSON.
    """
    payload = {"texto": comando, "modo": "json"}
    if chat_id:
        payload["chat_id"] = chat_id

    r = requests.post(ORBIS_URL, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def mesa_gpt(texto_usuario: str, chat_id: str = None) -> str:
    """
    Flujo completo:
    - Interpretar instrucción
    - Llamar a Orbis
    - Devolver respuesta en lenguaje humano
    """
    comando = interpretar_instruccion(texto_usuario)
    resultado = llamar_orbis(comando, chat_id)

    # Convertir JSON en lenguaje natural
    if not resultado.get("ok"):
        return f"❌ No pude ejecutar la instrucción ({resultado.get('error')})"

    op = resultado.get("op")

    if op == "agenda":
        if not resultado["items"]:
            return "📭 Tu agenda está vacía."
        agenda_str = "\n".join([f"{i['fecha']} {i['hora']} → {i['texto']}" for i in resultado["items"]])
        return f"📝 Aquí tienes tu agenda:\n{agenda_str}"

    elif op == "registrar":
        item = resultado["item"]
        return f"✅ Agendado: {item['texto']} el {item['fecha']} a las {item['hora']}."

    elif op == "borrar":
        if "deleted" in resultado:
            d = resultado["deleted"]
            return f"🗑️ Eliminado: {d['texto']} el {d['fecha']} a las {d['hora']}."
        return "❌ No encontré esa cita para borrar."

    elif op == "borrar_fecha":
        if resultado["count"] > 0:
            return f"🗑️ Se borraron {resultado['count']} eventos del {resultado['items'][0]['fecha']}."
        return "📭 No había eventos en esa fecha."

    elif op == "borrar_todo":
        return f"🗑️ Se borró toda la agenda ({resultado['count']} eventos)."

    elif op == "buscar":
        if resultado["items"]:
            return "🔎 Encontré:\n" + "\n".join([f"{i['fecha']} {i['hora']} → {i['texto']}" for i in resultado["items"]])
        return f"❌ No encontré nada con '{resultado['q']}'."

    elif op == "cuando":
        if resultado["fechas"]:
            return f"📌 Tienes con {resultado['q']} en: {', '.join(resultado['fechas'])}"
        return f"❌ No tienes cita con {resultado['q']}."

    elif op == "reprogramar":
        return f"♻️ Reprogramado: {resultado['texto']} ahora en {resultado['to']}."

    elif op == "modificar":
        item = resultado["item"]
        return f"✏️ Modificado: {item['fecha']} {item['hora']} → {item['texto']}."

    elif op == "buscar_fecha":
        if resultado["items"]:
            return "\n".join([f"{i['fecha']} {i['hora']} → {i['texto']}" for i in resultado["items"]])
        return f"📭 No tienes eventos el {resultado['fecha']}."

    else:
        return "🤔 No entendí la operación."

# ================= TEST MANUAL =================
if __name__ == "__main__":
    while True:
        txt = input("Doctor: ")
        if txt.lower() in ["salir", "exit"]:
            break
        print("MesaGPT:", mesa_gpt(txt))
