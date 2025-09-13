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

    # --- MOSTRAR AGENDA (ordenada) ---
    elif comando == "/agenda":
        if not agenda:
            return "📭 No tienes tareas guardadas."
        # Ordenar por fecha-hora
        items = sorted(agenda.items(), key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M"))
        salida = "📝 Agenda:\n"
        for fecha_hora, tarea in items:
            salida += f"{fecha_hora} → {tarea}\n"
        return salida.strip()

    # --- REGISTRAR ---
    elif comando == "/registrar":
        try:
            fecha = partes[1]  # YYYY-MM-DD
            hora = partes[2]   # HH:MM
            tarea = " ".join(partes[3:])
            clave = f"{fecha} {hora}"
            # validar fecha-hora
            datetime.strptime(clave, "%Y-%m-%d %H:%M")
            agenda[clave] = tarea
            guardar_agenda(agenda)

            if chat_id:
                fecha_hora = datetime.strptime(clave, "%Y-%m-%d %H:%M")
                programar_recordatorio(chat_id, fecha_hora, tarea)

            return f"✅ Guardado: {clave} → {tarea}"
        except Exception:
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
        except Exception:
            return "❌ Usa el formato: /borrar YYYY-MM-DD HH:MM"

    # --- BORRAR TODO ---
    elif comando == "/borrar_todo":
        agenda.clear()
        guardar_agenda(agenda)
        return "🗑️ Se borró toda la agenda."

    # --- BORRAR POR FECHA ---
    elif comando == "/borrar_fecha":
        try:
            fecha_raw = partes[1]

            # Normalizar fecha: soporta YYYY-MM-DD y DD/MM/YYYY
            if "/" in fecha_raw:
                d, m, y = fecha_raw.split("/")
                fecha = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            else:
                fecha = fecha_raw  # ya está en formato YYYY-MM-DD

            eliminados = {h: t for h, t in agenda.items() if h.startswith(fecha)}
            if eliminados:
                for h in list(eliminados.keys()):
                    agenda.pop(h)
                guardar_agenda(agenda)
                return f"🗑️ Se borraron todas las citas del {fecha}."
            else:
                return f"📭 No había citas el {fecha}."
        except Exception as e:
            print("❌ Error en /borrar_fecha:", e, flush=True)
            return "❌ Usa el formato: /borrar_fecha YYYY-MM-DD o DD/MM/YYYY"

    # --- BUSCAR POR NOMBRE ---
    elif comando == "/buscar":
        try:
            nombre = " ".join(partes[1:]).lower()
            # Ordenar resultados por fecha
            items = sorted(agenda.items(), key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M"))
            resultados = [f"{h} → {t}" for h, t in items if nombre in t.lower()]
            return "🔎 Encontré:\n" + "\n".join(resultados) if resultados else f"❌ No encontré citas con {nombre}"
        except Exception:
            return "❌ Usa el formato: /buscar Nombre"

    # --- CUANDO CON ALGUIEN ---
    elif comando == "/cuando":
        try:
            nombre = " ".join(partes[1:]).lower()
            items = sorted(agenda.items(), key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M"))
            resultados = [h for h, t in items if nombre in t.lower()]
            return f"📌 Tienes con {nombre} en: {', '.join(resultados)}" if resultados else f"❌ No tienes cita con {nombre}"
        except Exception:
            return "❌ Usa el formato: /cuando Juan"

    # --- REPROGRAMAR ---
    elif comando == "/reprogramar":
        try:
            vieja = f"{partes[1]} {partes[2]}"
            nueva_fecha = partes[3]
            nueva_hora = partes[4]
            nueva_clave = f"{nueva_fecha} {nueva_hora}"
            if vieja in agenda:
                # validar fechas
                datetime.strptime(vieja, "%Y-%m-%d %H:%M")
                datetime.strptime(nueva_clave, "%Y-%m-%d %H:%M")
                tarea = agenda[vieja]
                del agenda[vieja]
                agenda[nueva_clave] = tarea
                guardar_agenda(agenda)

                if chat_id:
                    fecha_hora = datetime.strptime(nueva_clave, "%Y-%m-%d %H:%M")
                    programar_recordatorio(chat_id, fecha_hora, tarea)

                return f"♻️ Reprogramada: {tarea} ahora en {nueva_clave}"
            else:
                return "❌ No encontré esa cita para reprogramar."
        except Exception:
            return "❌ Usa el formato: /reprogramar YYYY-MM-DD HH:MM NUEVA_FECHA NUEVA_HORA"

    # --- BUSCAR POR FECHA ---
    elif comando == "/buscar_fecha":
        try:
            fecha = partes[1]  # YYYY-MM-DD
            # Ordenar resultados por hora
            items = sorted(
                ((h, t) for h, t in agenda.items() if h.startswith(fecha)),
                key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M")
            )
            return "\n".join(f"{h} → {t}" for h, t in items) if items else f"📭 No tienes citas el {fecha}."
        except Exception:
            return "❌ Usa el formato: /buscar_fecha 2025-09-15"

    # --- PROXIMOS (para BridgeBot scheduler) ---
    elif comando == "/proximos":
        # NOTA: este comando se maneja en /procesar para devolver JSON especial.
        # Aquí devolvemos una cadena por compatibilidad si se invoca desde otro canal.
        return "ℹ️ Usa este comando a través del endpoint /procesar para obtener JSON de próximos eventos."

    # --- DEFAULT ---
    else:
        return "🤔 No entendí. Usa /agenda, /registrar, /borrar, /borrar_todo, /borrar_fecha, /buscar, /cuando, /reprogramar o /buscar_fecha."


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

    # Si nos piden /proximos desde BridgeBot, devolvemos JSON con eventos
    if texto.strip().lower().startswith("/proximos"):
        # ventana de 1 minuto para el scheduler (que corre cada minuto)
        ahora = datetime.now()
        ventana = ahora + timedelta(minutes=1)
        agenda = cargar_agenda()

        eventos = []
        for clave, tarea in agenda.items():
            try:
                fecha_hora = datetime.strptime(clave, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if ahora <= fecha_hora <= ventana:
                # BridgeBot espera: {"chat_id": ..., "mensaje": "..."}
                if chat_id:
                    eventos.append({
                        "chat_id": chat_id,
                        "mensaje": f"{tarea} a las {fecha_hora.strftime('%H:%M')}"
                    })
        return jsonify({"eventos": eventos})

    # Resto de comandos normales: devolvemos {"respuesta": "..."}
    respuesta = procesar_texto(texto, chat_id)
    return jsonify({"respuesta": respuesta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

@app.route("/proximos", methods=["GET"])
def proximos():
    ahora = datetime.now()
    ventana = ahora + timedelta(minutes=1)
    agenda = cargar_agenda()
    eventos = []
    chat_id = request.args.get("chat_id")  # opcional para pruebas

    for clave, tarea in agenda.items():
        try:
            fecha_hora = datetime.strptime(clave, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if ahora <= fecha_hora <= ventana:
            if chat_id:
                eventos.append({
                    "chat_id": chat_id,
                    "mensaje": f"{tarea} a las {fecha_hora.strftime('%H:%M')}"
                })
            else:
                # si no hay chat_id, exponemos al menos el mensaje
                eventos.append({
                    "chat_id": None,
                    "mensaje": f"{tarea} a las {fecha_hora.strftime('%H:%M')}"
                })

    return jsonify({"eventos": eventos})

