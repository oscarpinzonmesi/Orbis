import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from mesagpt import mesa_gpt  # Importa el cerebro

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text

    print(f"➡️ Orbis recibió: {texto_usuario}")

    respuesta = mesa_gpt(texto_usuario, chat_id=chat_id)
    await context.bot.send_message(chat_id=chat_id, text=respuesta)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Captura todos los mensajes (texto y comandos)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_message))

    print("🤖 Orbis conectado a Telegram y listo para conversar + manejar agenda.")
    app.run_polling()
