import os
import json
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "") + "/webhook"

client = OpenAI(api_key=OPENAI_API_KEY)
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

AGENDA_FILE = "agenda.json"

def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

def procesar_comando(texto: str):
    partes = texto.strip().split()
    comando = partes[0].lower()

    if comando == "/start":
        return "👋 Hola, soy tu asistente personal."

    elif comando == "/agenda":
        agenda = cargar_agenda()
        if not agenda:
            return "📭 No tienes tareas guardadas."
        return "📝 Agenda:\n" + "\n".join([f"{h} → {t}" for h, t in agenda.items()])

    elif comando == "/registrar":
        try:
            hora = partes[1]
            tarea = " ".join(partes[2:])
            agenda = cargar_agenda()
            agenda[hora] = tarea
            guardar_agenda(agenda)
            return f"✅ Guardado: {hora} → {tarea}"
        except:
            return "❌ Usa el formato: /registrar 09:00 Reunión"

    elif comando == "/borrar":
        try:
            hora = partes[1]
            agenda = cargar_agenda()
            if hora in agenda:
                eliminado = agenda.pop(hora)
                guardar_agenda(agenda)
                return f"🗑️ Eliminado: {hora} → {eliminado}"
            else:
                return f"❌ No hay nada en {hora}"
        except:
            return "❌ Usa el formato: /borrar 09:00"

    elif comando == "/borrar_todo":
        guardar_agenda({})
        return "🗑️ Se borró toda la agenda."

    return None

def consultar_gpt(mensaje, chat_id):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente personal que también maneja agenda."},
                {"role": "user", "content": mensaje}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error con GPT: {e}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text.strip()

    respuesta = None
    if texto_usuario.startswith("/"):
        respuesta = procesar_comando(texto_usuario)

    if not respuesta:
        respuesta = consultar_gpt(texto_usuario, chat_id)

    await context.bot.send_message(chat_id=chat_id, text=respuesta)

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(MessageHandler(filters.COMMAND, handle_message))

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    try:
        asyncio.run(telegram_app.process_update(update))
    except Exception as e:
        print(f"❌ Error procesando update: {e}")
    return "ok", 200

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        raise RuntimeError("⚠️ Faltan TELEGRAM_TOKEN u OPENAI_API_KEY")

    async def setup_webhook():
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL)
        print(f"🤖 Webhook conectado en {WEBHOOK_URL}")

    asyncio.run(setup_webhook())
    flask_app.run(host="0.0.0.0", port=10000)
