from flask import Flask, request
from telegram_bot import iniciar_bot, procesar_update
import os

app = Flask(__name__)

# Ruta principal (solo para comprobar que Render está activo)
@app.route('/')
def home():
    return "✅ Orbis está funcionando en la nube 🚀"

# Ruta del webhook (usará el TOKEN como seguridad)
@app.route(f'/{os.getenv("TELEGRAM_TOKEN")}', methods=['POST'])
def webhook():
    update = request.get_json(force=True)
    procesar_update(update)
    return "OK", 200

if __name__ == "__main__":
    iniciar_bot()   # Inicializa la app de Telegram
    app.run(host="0.0.0.0", port=10000)
