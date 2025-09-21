import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ORBIS_URL = os.getenv("ORBIS_URL", "https://orbis-5gkk.onrender.com/procesar")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "") + "/webhook"  # Render da la URL base

# Flask para exponer el webhook
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text

    try:
        respuesta = f"➡️ Orbis recibió: {texto_usuario}"
        # Aquí llamarías a Orbis/cerebro si quieres:
        # r = requests.post(ORBIS_URL, json={"texto": texto_usuario, "chat_id": chat_id})
        # respuesta = r.json().get("respuesta", respuesta)
    except Exception as e:
        respuesta = f"❌ Error procesando: {e}"

    await context.bot.send_message(chat_id=chat_id, text=respuesta)

# Captura todos los mensajes
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(MessageHandler(filters.COMMAND, handle_message))

# Ruta webhook
@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok", 200

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        raise RuntimeError("⚠️ Falta TELEGRAM_TOKEN en variables de entorno")

    # Configura el webhook en Telegram
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    print(f"🤖 Orbis conectado a Telegram con Webhook en {WEBHOOK_URL}")
    flask_app.run(host="0.0.0.0", port=10000)
