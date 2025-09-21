import os
import json
from openai import OpenAI

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

AGENDA_FILE = "agenda.json"

# -------------------------------
# Funciones locales de agenda
# -------------------------------
def cargar_agenda():
    try:
        with open(AGENDA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

def registrar_tarea(hora, tarea):
    agenda = cargar_agenda()
    agenda[hora] = tarea
    guardar_agenda(agenda)
    return f"✅ He registrado '{tarea}' a las {hora}."

def borrar_tarea(hora):
    agenda = cargar_agenda()
    if hora in agenda:
        tarea = agenda.pop(hora)
        guardar_agenda(agenda)
        return f"🗑️ He borrado la tarea '{tarea}' programada para {hora}."
    return f"⚠️ No encontré ninguna tarea a las {hora}."

def mostrar_agenda():
    agenda = cargar_agenda()
    if not agenda:
        return "📭 Tu agenda está vacía."
    return "📝 Agenda:\n" + "\n".join([f"{h} → {t}" for h, t in agenda.items()])

# -------------------------------
# GPT como asistente + agenda
# -------------------------------
def mesa_gpt(texto, chat_id=None):
    """
    GPT responde como asistente y puede llamar funciones de agenda.
    """

    tools = [
        {
            "type": "function",
            "function": {
                "name": "registrar_tarea",
                "description": "Registrar una nueva tarea en la agenda",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hora": {"type": "string", "description": "Fecha y hora en formato YYYY-MM-DD HH:MM"},
                        "tarea": {"type": "string", "description": "Descripción de la tarea"}
                    },
                    "required": ["hora", "tarea"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "borrar_tarea",
                "description": "Borrar una tarea existente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hora": {"type": "string", "description": "Fecha y hora exacta de la tarea a borrar"}
                    },
                    "required": ["hora"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mostrar_agenda",
                "description": "Mostrar todas las tareas actuales de la agenda",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres Orbis, un asistente personal. Habla en lenguaje natural y administra una agenda personal con recordatorios. Si el usuario da una orden de agenda, llama a las funciones correspondientes."},
                {"role": "user", "content": texto}
            ],
            tools=tools
        )

        msg = response.choices[0].message

        # Si GPT decide llamar una función
        if msg.tool_calls:
            for call in msg.tool_calls:
                if call.function.name == "registrar_tarea":
                    args = json.loads(call.function.arguments)
                    return registrar_tarea(args["hora"], args["tarea"])
                elif call.function.name == "borrar_tarea":
                    args = json.loads(call.function.arguments)
                    return borrar_tarea(args["hora"])
                elif call.function.name == "mostrar_agenda":
                    return mostrar_agenda()

        # Si es respuesta normal
        return msg.content or "🤔 No entendí tu solicitud."

    except Exception as e:
        return f"❌ Error en mesa_gpt: {e}"
