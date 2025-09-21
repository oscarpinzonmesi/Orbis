import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ORBIS_URL = os.getenv("ORBIS_URL", "https://orbis-5gkk.onrender.com/procesar")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text

    try:
        resp = requests.post(
            ORBIS_URL,
            json={"texto": texto_usuario, "chat_id": chat_id},
            timeout=10
        )
        data = resp.json()
        # Orbis devuelve {"respuesta": "..."} en modo texto
        respuesta = data.get("respuesta", "❌ Orbis no respondió correctamente.")
    except Exception as e:
        respuesta = f"❌ Error procesando con Orbis: {e}"

    await context.bot.send_message(chat_id=chat_id, text=respuesta)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Captura todos los mensajes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_message))

    print("🤖 Orbis en Telegram (PTB 20.3) está activo…")
    app.run_polling()
