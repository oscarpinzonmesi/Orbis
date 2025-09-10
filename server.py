from flask import Flask, request
from telegram_bot import crear_app
import os

app = Flask(__name__)

# Crear la app del bot
bot_app = crear_app()

@app.route('/')
def home():
    return "✅ Orbis está funcionando en la nube 🚀"

@app.route(f"/{os.getenv('TELEGRAM_TOKEN')}", methods=["POST"])
async def webhook():
    """Recibe mensajes de Telegram"""
    update = await bot_app.update_queue.put(await request.get_json(force=True))
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
