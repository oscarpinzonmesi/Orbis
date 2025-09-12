from flask import Flask, request, jsonify
from telegram_bot import procesar_texto

app = Flask(__name__)

# Ruta de prueba
@app.route("/")
def home():
    return "✅ Orbis API funcionando en Render"

# Ruta que procesa texto y devuelve respuesta en JSON
@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    print(f"➡️ Orbis recibió: {texto}", flush=True)

    respuesta = procesar_texto(texto)
    return jsonify({"respuesta": respuesta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
