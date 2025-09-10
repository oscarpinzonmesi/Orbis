from flask import Flask
import threading
import os
from telegram_bot import iniciar_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Orbis está funcionando en la nube 🚀"

def run_bot():
    iniciar_bot()

if __name__ == "__main__":
    # Lanzar el bot en segundo plano
    hilo = threading.Thread(target=run_bot, daemon=True)
    hilo.start()

    # Render exige usar el puerto de la variable de entorno
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
