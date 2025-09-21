import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

AGENDA_FILE = "agenda.json"

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
    return (s or "").strip().strip("'\"`").strip()

def _ordenar_items(dic):
    try:
        return sorted(dic.items(), key=lambda kv: datetime.strptime(kv[0], "%Y-%m-%d %H:%M"))
    except Exception:
        def _safe_dt(k):
            try:
                return datetime.strptime(k, "%Y-%m-%d %H:%M")
            except Exception:
                return datetime.max
        return sorted(dic.items(), key=lambda kv: _safe_dt(kv[0]))

# ========= HELPER para claves válidas =========

PATRON_CLAVE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

def items_validos(dic):
    return [(h, t) for h, t in _ordenar_items(dic) if PATRON_CLAVE.match(h)]

# ===================== LÓGICA (texto plano) =====================

def procesar_texto(texto: str) -> str:
    partes = texto.strip().split()
    comando = partes[0].lower() if partes else ""
    agenda = cargar_agenda()

    if comando == "/start":
        return "👋 Hola, soy Orbis. Tu asistente de agenda está listo."

    elif comando == "/agenda":
        if not agenda:
            return "📭 No tienes tareas guardadas."
        salida = "📝 Agenda:\n"
        for fecha_hora, tarea in _ordenar_items(agenda):
            salida += f"{fecha_hora} → {tarea}\n"
        return salida.strip()

    elif comando == "/registrar":
        try:
            fecha = _clean_token(partes[1])
            hora  = _clean_token(partes[2])
            tarea = " ".join(partes[3:])
            clave = f"{fecha} {hora}"
            datetime.strptime(clave, "%Y-%m-%d %H:%M")
            agenda[clave] = tarea
            guardar_agenda(agenda)
            return f"✅ Guardado: {clave} → {tarea}"
        except Exception:
            return "❌ Usa el formato: /registrar YYYY-MM-DD HH:MM Tarea"

    elif comando == "/borrar":
        try:
            clave = f"{_clean_token(partes[1])} {_clean_token(partes[2])}"
            if clave in agenda:
                eliminado = agenda.pop(clave)
                guardar_agenda(agenda)
                return f"🗑️ Eliminado: {clave} → {eliminado}"
            else:
                return "❌ No hay nada guardado en esa fecha/hora."
        except Exception:
            return "❌ Usa el formato: /borrar YYYY-MM-DD HH:MM"

    elif comando == "/borrar_todo":
        agenda.clear()
        guardar_agenda(agenda)
        return "🗑️ Se borró toda la agenda."

    elif comando == "/buscar":
        q = " ".join(partes[1:]).lower()
        resultados = [f"{h} → {t}" for h, t in _ordenar_items(agenda) if q in t.lower()]
        return "🔎 Encontré:\n" + "\n".join(resultados) if resultados else f"❌ No encontré citas con {q}"

    else:
        return "🤔 No entendí. Usa /agenda, /registrar, /borrar, /borrar_todo o /buscar."

# ===================== LÓGICA (JSON) =====================

def procesar_texto_json(texto: str) -> dict:
    partes = texto.strip().split()
    comando = partes[0].lower() if partes else ""
    agenda = cargar_agenda()

    try:
        if comando == "/agenda":
            items = [{"fecha": h[:10], "hora": h[11:], "texto": t} for h, t in items_validos(agenda)]
            return {"ok": True, "op": "agenda", "items": items}

        elif comando == "/registrar":
            fecha = _clean_token(partes[1])
            hora  = _clean_token(partes[2])
            tarea = " ".join(partes[3:])
            clave = f"{fecha} {hora}"
            datetime.strptime(clave, "%Y-%m-%d %H:%M")
            agenda[clave] = tarea
            guardar_agenda(agenda)
            return {"ok": True, "op": "registrar", "item": {"fecha": fecha, "hora": hora, "texto": tarea}}

        elif comando == "/borrar":
            clave = f"{_clean_token(partes[1])} {_clean_token(partes[2])}"
            if clave in agenda:
                eliminado = {"fecha": clave[:10], "hora": clave[11:], "texto": agenda.pop(clave)}
                guardar_agenda(agenda)
                return {"ok": True, "op": "borrar", "deleted": eliminado}
            return {"ok": False, "op": "borrar", "error": "no_encontrado"}

        elif comando == "/borrar_todo":
            cnt = len(agenda)
            agenda.clear()
            guardar_agenda(agenda)
            return {"ok": True, "op": "borrar_todo", "count": cnt}

        else:
            return {"ok": False, "op": "desconocido", "error": "comando_no_reconocido"}

    except Exception as e:
        return {"ok": False, "op": comando or "ninguno", "error": str(e)}

# ===================== ENDPOINTS =====================

@app.route("/")
def home():
    return "✅ Orbis API funcionando en Render"

@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    modo = (data.get("modo") or "").lower()
    print(f"➡️ Orbis recibió: {texto}", flush=True)

    if modo == "json":
        return jsonify(procesar_texto_json(texto))
    else:
        return jsonify({"respuesta": procesar_texto(texto)})

@app.route("/proximos", methods=["GET"])
def proximos():
    ahora = datetime.now()
    ventana = ahora + timedelta(minutes=1)
    agenda = cargar_agenda()
    eventos = []
    for clave, tarea in items_validos(agenda):
        fecha_hora = datetime.strptime(clave, "%Y-%m-%d %H:%M")
        if ahora <= fecha_hora <= ventana:
            eventos.append({"mensaje": f"{tarea} a las {fecha_hora.strftime('%H:%M')}"})
    return jsonify({"eventos": eventos})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
