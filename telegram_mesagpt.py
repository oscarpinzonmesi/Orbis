import os
import json
import requests
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 Tokens y URLs
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "") + "/webhook"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

AGENDA_FILE = "agenda.json"

# -------------------- 📒 Funciones de agenda --------------------
def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

# -------------------- 🤖 Cerebro GPT --------------------
def consultar_asistente(mensaje, chat_id):
    """
    GPT decide si responde normal o si debe manipular la agenda.
    """
    try:
        agenda = cargar_agenda()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Eres un asistente personal llamado Orbis.
Puedes conversar de cualquier tema (clima, significados, consejos, etc).
También manejas la agenda del usuario guardada en un archivo JSON.
Acciones posibles con la agenda:
- Agregar una tarea con hora.
- Consultar la agenda.
- Borrar una tarea por hora.
- Vaciar toda la agenda.

Responde siempre en español de forma natural, sin mostrar código ni estructuras técnicas."""},
                {"role": "user", "content": f"Agenda actual: {json.dumps(agenda, ensure_ascii=False)}"},
                {"role": "user", "content": mensaje}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error con el cerebro: {e}"

# -------------------- 📲 Telegram --------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text.strip()

    respuesta = consultar_asistente(texto_usuario, chat_id)
    await context.bot.send_message(chat_id=chat_id, text=respuesta)

telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

# -------------------- 🌐 Web --------------------
@flask_app.route("/", methods=["GET"])
def home():
    return "🤖 Asistente en línea y conectado a Telegram 🚀"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))  # ✅ corregido para Flask
    return "ok", 200

# -------------------- 🚀 Main --------------------
if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        raise RuntimeError("⚠️ Faltan variables de entorno TELEGRAM_TOKEN o OPENAI_API_KEY")

    async def setup_webhook():
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL)
        print(f"🤖 Asistente conectado a Telegram con Webhook en {WEBHOOK_URL}")

    asyncio.run(setup_webhook())
    flask_app.run(host="0.0.0.0", port=10000)
