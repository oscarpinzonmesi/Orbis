import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

AGENDA_FILE = "agenda.json"

def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

@app.route("/")
def home():
    return "✅ Orbis API funcionando"

@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    print(f"➡️ Orbis recibió: {texto}", flush=True)

    partes = texto.strip().split()
    comando = partes[0].lower() if partes else ""

    if comando == "/start":
        return jsonify({"respuesta": "👋 Hola, soy Orbis. Tu agenda está lista."})

    elif comando == "/agenda":
        agenda = cargar_agenda()
        if not agenda:
            return jsonify({"respuesta": "📭 No tienes tareas guardadas."})
        return jsonify({"respuesta": "📝 Agenda:\n" + "\n".join([f"{h} → {t}" for h, t in agenda.items()])})

    elif comando == "/registrar":
        try:
            hora = partes[1]
            tarea = " ".join(partes[2:])
            agenda = cargar_agenda()
            agenda[hora] = tarea
            guardar_agenda(agenda)
            return jsonify({"respuesta": f"✅ Guardado: {hora} → {tarea}"})
        except:
            return jsonify({"respuesta": "❌ Usa el formato: /registrar 09:00 Reunión"})

    elif comando == "/borrar":
        try:
            hora = partes[1]
            agenda = cargar_agenda()
            if hora in agenda:
                del agenda[hora]
                guardar_agenda(agenda)
                return jsonify({"respuesta": f"🗑️ Borrada la tarea de las {hora}"})
            else:
                return jsonify({"respuesta": "❌ No hay nada guardado en esa hora."})
        except:
            return jsonify({"respuesta": "❌ Usa el formato: /borrar 09:00"})

    elif comando == "/buscar":
        try:
            nombre = " ".join(partes[1:]).lower()
            agenda = cargar_agenda()
            resultados = [f"{h} → {t}" for h, t in agenda.items() if nombre in t.lower()]
            if resultados:
                return jsonify({"respuesta": "🔎 Encontré estas coincidencias:\n" + "\n".join(resultados)})
            else:
                return jsonify({"respuesta": f"❌ No encontré nada con '{nombre}'"})
        except:
            return jsonify({"respuesta": "❌ Usa el formato: /buscar Pedro"})

    else:
        return jsonify({"respuesta": "🤔 No entendí. Usa /registrar, /agenda, /borrar, /buscar."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
