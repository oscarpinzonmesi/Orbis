from flask import Flask, request
import os
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler

# Cargar token desde las variables de entorno en Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

# 👉 Dispatcher: se encarga de manejar los mensajes entrantes
dispatcher = Dispatcher(bot, None, workers=0)

# ====== Aquí conectamos con su lógica ======
def start(update, context):
    update.message.reply_text("👋 Hola Doctor Mesa, Orbis está listo en la nube 🚀")

def echo(update, context):
    # Aquí puede llamar funciones de su agenda
    texto = update.message.text
    update.message.reply_text(f"📌 Recibí: {texto}")

# Registrar comandos y mensajes
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
# ===========================================

@app.route('/')
def home():
    return "✅ Orbis está funcionando en la nube 🚀"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"
