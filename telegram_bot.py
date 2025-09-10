import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Aquí tus handlers como ya los tienes (start, registrar, agenda, borrar...)

def crear_app():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("⚠️ TELEGRAM_TOKEN no está configurado")

    app = ApplicationBuilder().token(token).build()

    # Handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))
    app.add_handler(CommandHandler("agenda", ver_agenda))
    app.add_handler(CommandHandler("borrar", borrar))

    # Mensajes normales
    async def mensajes(update, context: ContextTypes.DEFAULT_TYPE):
        texto = update.message.text.lower()
        if "qué tengo" in texto or "que tengo" in texto:
            await ver_agenda(update, context)
        else:
            await update.message.reply_text("🤔 No entendí. Usa /registrar o /agenda.")

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

    return app
