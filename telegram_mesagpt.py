import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ApplicationBuilder
from openai import OpenAI

# === Configuración ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Bot Telegram
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Flask
app = Flask(__name__)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# === Función para enviar mensaje a ChatGPT ===
async def ask_chatgpt(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error con OpenAI: {e}")
        return "⚠️ Error al consultar ChatGPT."


# === Webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        asyncio.run(telegram_app.process_update(update))
    except Exception as e:
        logging.error(f"Error procesando update: {e}")
    return "ok"


# === Manejador de mensajes ===
@telegram_app.message_handler()
async def handle_message(update: Update, context):
    user_message = update.message.text
    logging.info(f"Mensaje recibido: {user_message}")

    reply = await ask_chatgpt(user_message)
    await update.message.reply_text(reply)


# === Inicio local ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
