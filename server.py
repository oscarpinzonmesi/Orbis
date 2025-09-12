from flask import Flask, request, jsonify
from telegram_bot import procesar_texto
import os

app = Flask(__name__)

# Ruta de prueba
@app.route("/")
def home():
    return "✅ Orbis API lista en Render"

# Nueva ruta: recibe texto y devuelve respuesta como string
@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    respuesta = procesar_texto(texto)
    return jsonify({"respuesta": respuesta})
