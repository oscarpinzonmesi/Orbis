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
        try:
            return json.load(f)
        except Exception:
            return {}

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

def _clean_token(s: str) -> str:
    # Limpia comillas/espacios sueltos en parámetros
    return (s or "").strip().strip("'\"`").strip()

def enviar_recordatorio(chat_id, mensaje):
    if not BRIDGE_TOKEN:
        return
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

def _ordenar_items(dic):
    # Retorna lista [(clave, tarea)] ordenada por fecha-hora
    try:
        return sorted(dic.items(), key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M"))
    except Exception:
        # Si hay claves corruptas, intentamos ignorarlas
        def _safe_dt(k):
            try:
                return datetime.strptime(k, "%Y-%m-%d %H:%M")
            except Exception:
                return datetime.max
        return sorted(dic.items(), key=lambda kv: _safe_dt(kv[0]))

# ===================== LÓGICA (texto plano, compatibilidad) =====================

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
        items = _ordenar_items(agenda)
        salida = "📝 Agenda:\n"
        for fecha_hora, tarea in items:
            salida += f"{fecha_hora} → {tarea}\n"
        return salida.strip()

    # --- REGISTRAR ---
    elif comando == "/registrar":
        try:
            fecha = _clean_token(partes[1])  # YYYY-MM-DD
            hora = _clean_token(partes[2])   # HH:MM
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
            fecha = _clean_token(partes[1])
            hora  = _clean_token(partes[2])
            clave = f"{fecha} {hora}"
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
            fecha_raw = _clean_token(partes[1])

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
            items = _ordenar_items(agenda)
            resultados = [f"{h} → {t}" for h, t in items if nombre in t.lower()]
            return "🔎 Encontré:\n" + "\n".join(resultados) if resultados else f"❌ No encontré citas con {nombre}"
        except Exception:
            return "❌ Usa el formato: /buscar Nombre"

    # --- CUANDO CON ALGUIEN ---
    elif comando == "/cuando":
        try:
            nombre = " ".join(partes[1:]).lower()
            items = _ordenar_items(agenda)
            resultados = [h for h, t in items if nombre in t.lower()]
            return f"📌 Tienes con {nombre} en: {', '.join(resultados)}" if resultados else f"❌ No tienes cita con {nombre}"
        except Exception:
            return "❌ Usa el formato: /cuando Juan"

    # --- REPROGRAMAR ---
    elif comando == "/reprogramar":
        try:
            vieja = f"{_clean_token(partes[1])} {_clean_token(partes[2])}"
            nueva_fecha = _clean_token(partes[3])
            nueva_hora  = _clean_token(partes[4])
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

    # --- MODIFICAR ---
    elif comando == "/modificar":
        try:
            clave = f"{_clean_token(partes[1])} {_clean_token(partes[2])}"   # YYYY-MM-DD HH:MM
            nuevo_texto = " ".join(partes[3:])
            if clave in agenda:
                agenda[clave] = nuevo_texto
                guardar_agenda(agenda)
                return f"✏️ Modificado: {clave} → {nuevo_texto}"
            else:
                return "❌ No encontré cita en esa fecha/hora."
        except Exception:
            return "❌ Usa el formato: /modificar YYYY-MM-DD HH:MM Nueva descripción"

    # --- BUSCAR POR FECHA ---
    elif comando == "/buscar_fecha":
        try:
            fecha = _clean_token(partes[1])  # YYYY-MM-DD
            items = sorted(
                ((h, t) for h, t in cargar_agenda().items() if h.startswith(fecha)),
                key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M")
            )
            return "\n".join(f"{h} → {t}" for h, t in items) if items else f"📭 No tienes citas el {fecha}."
        except Exception:
            return "❌ Usa el formato: /buscar_fecha 2025-09-15"

    # --- PROXIMOS (para BridgeBot scheduler) ---
    elif comando == "/proximos":
        # Nota: el scheduler de BridgeBot espera JSON, lo manejamos en /procesar;
        # aquí devolvemos texto por compatibilidad si alguien llama directo.
        return "ℹ️ Usa este comando a través del endpoint /procesar para obtener JSON de próximos eventos."

    # --- DEFAULT ---
    else:
        return "🤔 No entendí. Usa /agenda, /registrar, /borrar, /borrar_todo, /borrar_fecha, /buscar, /cuando, /reprogramar, /modificar o /buscar_fecha."

# ===================== LÓGICA (JSON para GPT/BridgeBot) =====================

def procesar_texto_json(texto: str, chat_id: str = None) -> dict:
    """
    Devuelve datos estructurados (sin redacción humana) para que GPT componga la respuesta.
    """
    partes = texto.strip().split()
    comando = partes[0].lower() if partes else ""
    agenda = cargar_agenda()

    try:
        if comando == "/agenda":
            items = [{"fecha": h[:10], "hora": h[11:], "texto": t} for h, t in _ordenar_items(agenda)]
            return {"ok": True, "op": "agenda", "items": items}

        elif comando == "/registrar":
            fecha = _clean_token(partes[1]); hora = _clean_token(partes[2]); tarea = " ".join(partes[3:])
            clave = f"{fecha} {hora}"
            datetime.strptime(clave, "%Y-%m-%d %H:%M")
            agenda[clave] = tarea
            guardar_agenda(agenda)
            if chat_id:
                programar_recordatorio(chat_id, datetime.strptime(clave, "%Y-%m-%d %H:%M"), tarea)
            return {"ok": True, "op": "registrar", "item": {"fecha": fecha, "hora": hora, "texto": tarea}}

        elif comando == "/borrar":
            fecha = _clean_token(partes[1]); hora = _clean_token(partes[2])
            clave = f"{fecha} {hora}"
            if clave in agenda:
                eliminado = {"fecha": fecha, "hora": hora, "texto": agenda.pop(clave)}
                guardar_agenda(agenda)
                return {"ok": True, "op": "borrar", "deleted": eliminado}
            return {"ok": False, "op": "borrar", "error": "no_encontrado"}

        elif comando == "/borrar_fecha":
            fecha_raw = _clean_token(partes[1])
            if "/" in fecha_raw:
                d, m, y = fecha_raw.split("/")
                fecha = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            else:
                fecha = fecha_raw
            afectados = [{"fecha": h[:10], "hora": h[11:], "texto": t} for h, t in agenda.items() if h.startswith(fecha)]
            if afectados:
                for h in list(agenda.keys()):
                    if h.startswith(fecha):
                        agenda.pop(h)
                guardar_agenda(agenda)
            return {"ok": True, "op": "borrar_fecha", "count": len(afectados), "items": afectados}

        elif comando == "/borrar_todo":
            cnt = len(agenda)
            agenda.clear()
            guardar_agenda(agenda)
            return {"ok": True, "op": "borrar_todo", "count": cnt}

        elif comando == "/buscar":
            nombre = " ".join(partes[1:]).lower()
            items = [{"fecha": h[:10], "hora": h[11:], "texto": t}
                     for h, t in _ordenar_items(agenda) if nombre in t.lower()]
            return {"ok": True, "op": "buscar", "q": nombre, "items": items}

        elif comando == "/cuando":
            nombre = " ".join(partes[1:]).lower()
            fechas = [h for h, t in _ordenar_items(agenda) if nombre in t.lower()]
            return {"ok": True, "op": "cuando", "q": nombre, "fechas": fechas}

        elif comando == "/reprogramar":
            vieja = f"{_clean_token(partes[1])} {_clean_token(partes[2])}"
            nueva_fecha = _clean_token(partes[3]); nueva_hora = _clean_token(partes[4])
            nueva = f"{nueva_fecha} {nueva_hora}"
            if vieja in agenda:
                tarea = agenda.pop(vieja)
                agenda[nueva] = tarea
                guardar_agenda(agenda)
                if chat_id:
                    programar_recordatorio(chat_id, datetime.strptime(nueva, "%Y-%m-%d %H:%M"), tarea)
                return {"ok": True, "op": "reprogramar", "from": vieja, "to": nueva, "texto": tarea}
            return {"ok": False, "op": "reprogramar", "error": "no_encontrado"}

        elif comando == "/modificar":
            clave = f"{_clean_token(partes[1])} {_clean_token(partes[2])}"
            nuevo_texto = " ".join(partes[3:])
            if clave in agenda:
                agenda[clave] = nuevo_texto
                guardar_agenda(agenda)
                return {"ok": True, "op": "modificar", "item": {"fecha": clave[:10], "hora": clave[11:], "texto": nuevo_texto}}
            return {"ok": False, "op": "modificar", "error": "no_encontrado"}

        elif comando == "/buscar_fecha":
            fecha = _clean_token(partes[1])
            items = [{"fecha": h[:10], "hora": h[11:], "texto": t}
                     for h, t in _ordenar_items(agenda) if h.startswith(fecha)]
            return {"ok": True, "op": "buscar_fecha", "fecha": fecha, "items": items}

        elif comando == "/proximos":
            ahora = datetime.now(); ventana = ahora + timedelta(minutes=1)
            eventos = []
            for clave, tarea in agenda.items():
                try:
                    fh = datetime.strptime(clave, "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                if ahora <= fh <= ventana:
                    eventos.append({"fecha": clave[:10], "hora": clave[11:], "texto": tarea})
            return {"ok": True, "op": "proximos", "eventos": eventos}

        else:
            return {"ok": False, "op": "desconocido", "error": "comando_no_reconocido"}

    except Exception as e:
        return {"ok": False, "op": comando or "ninguno", "error": f"excepcion:{e.__class__.__name__}"}

# ===================== ENDPOINTS =====================

@app.route("/")
def home():
    return "✅ Orbis API funcionando en Render"

@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    chat_id = data.get("chat_id")  # opcional, para recordatorios
    modo = (data.get("modo") or "").lower()
    print(f"➡️ Orbis recibió: {texto}", flush=True)

    # Si GPT/BridgeBot pide datos puros
    if modo == "json":
        payload = procesar_texto_json(texto, chat_id)
        return jsonify(payload)

    # Si nos piden /proximos desde el scheduler (sin modo=json), devolvemos JSON con eventos
    if texto.strip().lower().startswith("/proximos"):
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
                if chat_id:
                    eventos.append({
                        "chat_id": chat_id,
                        "mensaje": f"{tarea} a las {fecha_hora.strftime('%H:%M')}"
                    })
        return jsonify({"eventos": eventos})

    # Modo texto (compatibilidad)
    respuesta = procesar_texto(texto, chat_id)
    return jsonify({"respuesta": respuesta})

@app.route("/proximos", methods=["GET"])
def proximos():
    # Endpoint de prueba manual (GET), mantiene el mismo formato básico
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
                eventos.append({
                    "chat_id": None,
                    "mensaje": f"{tarea} a las {fecha_hora.strftime('%H:%M')}"
                })

    return jsonify({"eventos": eventos})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
