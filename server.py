import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

AGENDA_FILE = "agenda.json"
BRIDGE_TOKEN = os.getenv("TELEGRAM_TOKEN")  # mismo que usa BridgeBot
BRIDGE_API = f"https://api.telegram.org/bot{BRIDGE_TOKEN}/sendMessage"


# ===================== UTILS =====================

def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)


def enviar_recordatorio(chat_id, mensaje):
    try:
        requests.post(BRIDGE_API, json={"chat_id": chat_id, "text": mensaje})
    except Exception as e:
        print("❌ Error enviando recordatorio:", e, flush=True)


def programar_recordatorio(chat_id, fecha_hora, texto):
    """Crea dos recordatorios: 15 min antes y justo a la hora"""
    def worker():
        ahora = datetime.now()
        faltan = (fecha_hora - ahora).total_seconds()
        if faltan <= 0:
            return

        # Espera hasta 15 minutos antes
        if faltan > 900:
            time.sleep(faltan - 900)
            enviar_recordatorio(chat_id, f"🔔 En 15 minutos: {texto} ({fecha_hora.strftime('%H:%M')})")

        # Espera hasta la hora exacta
        ahora = datetime.now()
        faltan = (fecha_hora - ahora).total_seconds()
        if faltan > 0:
            time.sleep(faltan)
            enviar_recordatorio(chat_id, f"⏰ Ahora comienza: {texto} ({fecha_hora.strftime('%H:%M')})")

    threading.Thread(target=worker, daemon=True).start()


# ===================== LÓGICA PRINCIPAL =====================

def procesar_texto(texto: str, chat_id: str = None) -> str:
    partes = texto.strip().split()
    comando = partes[0].lower() if partes else ""
    agenda = cargar_agenda()

    # --- START ---
    if comando == "/start":
        return "👋 Hola, soy Orbis. Tu asistente de agenda está listo."

    # --- MOSTRAR AGENDA ---
    elif comando == "/agenda":
        if not agenda:
            return "📭 No tienes tareas guardadas."
        salida = "📝 Agenda:\n"
        for fecha_hora, tarea in agenda.items():
            salida += f"{fecha_hora} → {tarea}\n"
        return salida

    # --- REGISTRAR ---
    elif comando == "/registrar":
        try:
            fecha = partes[1]  # YYYY-MM-DD
            hora = partes[2]   # HH:MM
            tarea = " ".join(partes[3:])
            clave = f"{fecha} {hora}"
            agenda[clave] = tarea
            guardar_agenda(agenda)

            if chat_id:
                fecha_hora = datetime.strptime(clave, "%Y-%m-%d %H:%M")
                programar_recordatorio(chat_id, fecha_hora, tarea)

            return f"✅ Guardado: {clave} → {tarea}"
        except:
            return "❌ Usa el formato: /registrar YYYY-MM-DD HH:MM Tarea"

    # --- BORRAR ---
    elif comando == "/borrar":
        try:
            clave = f"{partes[1]} {partes[2]}"
            if clave in agenda:
                eliminado = agenda.pop(clave)
                guardar_agenda(agenda)
                return f"🗑️ Eliminado: {clave} → {eliminado}"
            else:
                return "❌ No hay nada guardado en esa fecha/hora."
        except:
            return "❌ Usa el formato: /borrar YYYY-MM-DD HH:MM"

    # --- BORRAR TODO ---
    elif comando == "/borrar_todo":
        agenda.clear()
        guardar_agenda(agenda)
        return "🗑️ Se borró toda la agenda."

    # --- BUSCAR POR NOMBRE ---
    elif comando == "/buscar":
        try:
            nombre = " ".join(partes[1:]).lower()
            resultados = [f"{h} → {t}" for h, t in agenda.items() if nombre in t.lower()]
            return "🔎 Encontré:\n" + "\n".join(resultados) if resultados else f"❌ No encontré citas con {nombre}"
        except:
            return "❌ Usa el formato: /buscar Nombre"

    # --- CUANDO CON ALGUIEN ---
    elif comando == "/cuando":
        try:
            nombre = " ".join(partes[1:]).lower()
            resultados = [h for h, t in agenda.items() if nombre in t.lower()]
            return f"📌 Tienes con {nombre} en: {', '.join(resultados)}" if resultados else f"❌ No tienes cita con {nombre}"
        except:
            return "❌ Usa el formato: /cuando Juan"

    # --- REPROGRAMAR ---
    elif comando == "/reprogramar":
        try:
            vieja = f"{partes[1]} {partes[2]}"
            nueva_fecha = partes[3]
            nueva_hora = partes[4]
            nueva_clave = f"{nueva_fecha} {nueva_hora}"
            if vieja in agenda:
                tarea = agenda[vieja]
                del agenda[vieja]
                agenda[nueva_clave] = tarea
                guardar_agenda(agenda)
                return f"♻️ Reprogramada: {tarea} ahora en {nueva_clave}"
            else:
                return "❌ No encontré esa cita para reprogramar."
        except:
            return "❌ Usa el formato: /reprogramar YYYY-MM-DD HH:MM NUEVA_FECHA NUEVA_HORA"

    # --- BUSCAR POR FECHA ---
    elif comando == "/buscar_fecha":
        try:
            fecha = partes[1]  # YYYY-MM-DD
            resultados = [f"{h} → {t}" for h, t in agenda.items() if h.startswith(fecha)]
            return "\n".join(resultados) if resultados else f"📭 No tienes citas el {fecha}."
        except:
            return "❌ Usa el formato: /buscar_fecha 2025-09-15"

    # --- DEFAULT ---
    else:
        return "🤔 No entendí. Usa /agenda, /registrar, /borrar, /borrar_todo, /buscar, /cuando, /reprogramar o /buscar_fecha."


# ===================== ENDPOINTS =====================

@app.route("/")
def home():
    return "✅ Orbis API funcionando en Render"

@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    chat_id = data.get("chat_id")  # opcional, para recordatorios
    print(f"➡️ Orbis recibió: {texto}", flush=True)

    respuesta = procesar_texto(texto, chat_id)
    return jsonify({"respuesta": respuesta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
