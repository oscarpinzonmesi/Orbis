import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ApplicationBuilder
from openai import OpenAI

# ========= Configuración ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Crear app Flask
app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Telegram (sin Updater, solo Application)
telegram_app: Application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ========= Funciones ==========
async def handle_message(update: Update, context):
    user_text = update.message.text

    # Enviar a ChatGPT
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente personal conectado a Telegram."},
                {"role": "user", "content": user_text}
            ]
        )
        reply_text = response.choices[0].message.content
    except Exception as e:
        reply_text = f"Error al conectar con ChatGPT: {e}"

    await update.message.reply_text(reply_text)

telegram_app.add_handler(
    telegram.ext.MessageHandler(telegram.ext.filters.TEXT & ~telegram.ext.filters.COMMAND, handle_message)
)

# ========= Webhook ==========
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

# ========= Inicio local ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
