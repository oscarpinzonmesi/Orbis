import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Token desde variables de entorno
TOKEN = os.getenv("TELEGRAM_TOKEN", "AQUI_VA_TU_TOKEN")

app = Flask(__name__)

# Crear aplicación de Telegram
application = Application.builder().token(TOKEN).build()

# --------- Handlers ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola Doctor Mesa, soy Orbis Asistente. ¡Listo para ayudarte con tu agenda!")

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()

    if "agenda" in texto:
        await update.message.reply_text("📅 Aquí tienes tu agenda (simulada por ahora).")
    elif "recordatorio" in texto:
        await update.message.reply_text("🔔 Te anotaré un recordatorio.")
    else:
        await update.message.reply_text("🤖 Entendido, sigo aprendiendo a organizar tu día.")

# --------- Rutas de Flask ---------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
def index():
    return "Orbis está vivo 🚀"

# --------- Inicializar Handlers ---------
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))

# --------- Ejecutar Flask ---------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
