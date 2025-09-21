import os
import requests
from telegram.ext import Updater, MessageHandler, Filters
from mesagpt import mesa_gpt  # Importa el cerebro que ya hicimos

# ============= CONFIG =============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # ponlo en variables de entorno
ORBIS_URL = os.getenv("ORBIS_URL", "https://orbis-5gkk.onrender.com/procesar")

# ============= HANDLER =============
def handle_message(update, context):
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text

    try:
        respuesta = mesa_gpt(texto_usuario, chat_id=chat_id)
    except Exception as e:
        respuesta = f"❌ Error procesando: {e}"

    context.bot.send_message(chat_id=chat_id, text=respuesta)

# ============= MAIN =============
if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno")

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.command, handle_message))

    print("🤖 MesaGPT en Telegram está activo…")
    updater.start_polling()
    updater.idle()
