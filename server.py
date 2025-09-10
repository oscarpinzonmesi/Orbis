from flask import Flask
import threading
from telegram_bot import iniciar_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Orbis está funcionando en la nube 🚀"

def run_bot():
    iniciar_bot()

if __name__ == "__main__":
    # Lanzar bot en segundo plano
    hilo = threading.Thread(target=run_bot, daemon=True)
    hilo.start()

    # Iniciar Flask en el puerto que Render da
    app.run(host="0.0.0.0", port=10000)
