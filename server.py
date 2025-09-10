from flask import Flask
from telegram_bot import iniciar_bot
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Orbis está funcionando en la nube 🚀"

if __name__ == "__main__":
    # Ejecutar Flask en un hilo
    def run_flask():
        app.run(host="0.0.0.0", port=10000)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Iniciar el bot en el hilo principal (con asyncio)
    iniciar_bot()
