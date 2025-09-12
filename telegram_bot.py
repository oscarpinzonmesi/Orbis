import os
import json
from datetime import datetime

AGENDA_FILE = "agenda.json"

# --- Manejo de archivo ---
def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

# --- Procesar texto y devolver respuesta ---
def procesar_texto(texto: str) -> str:
    partes = texto.strip().split()
    comando = partes[0].lower() if partes else ""

    # --- Start ---
    if comando == "/start":
        return "👋 Hola, soy Orbis. Tu asistente de agenda está listo."

    # --- Mostrar agenda ---
    elif comando == "/agenda":
        agenda = cargar_agenda()
        if not agenda:
            return "📭 No tienes tareas guardadas."
        else:
            return "📝 Agenda:\n" + "\n".join([f"{h} → {t}" for h, t in agenda.items()])

    # --- Registrar tarea ---
    elif comando == "/registrar":
        try:
            hora = partes[1]
            tarea = " ".join(partes[2:])
            agenda = cargar_agenda()
            agenda[hora] = tarea
            guardar_agenda(agenda)
            return f"✅ Guardado: {hora} → {tarea}"
        except:
            return "❌ Usa el formato: /registrar 09:00 Reunión"

    # --- Borrar tarea puntual ---
    elif comando == "/borrar":
        try:
            hora = partes[1]
            agenda = cargar_agenda()
            if hora in agenda:
                eliminado = agenda.pop(hora)
                guardar_agenda(agenda)
                return f"🗑️ Eliminado: {hora} → {eliminado}"
            else:
                return f"❌ No hay nada guardado en {hora}"
        except:
            return "❌ Usa el formato: /borrar 09:00"

    # --- Borrar toda la agenda ---
    elif comando == "/borrar_todo":
        agenda = {}
        guardar_agenda(agenda)
        return "🗑️ Se borró toda la agenda."

    # --- Reprogramar toda la agenda ---
    elif comando == "/reprogramar":
        try:
            nueva_hora = partes[1]
            agenda = cargar_agenda()
            if not agenda:
                return "⚠️ No hay citas para reprogramar."
            nueva_agenda = {}
            for _, tarea in agenda.items():
                nueva_agenda[nueva_hora] = tarea
            guardar_agenda(nueva_agenda)
            return f"⏰ Agenda reprogramada a {nueva_hora}"
        except:
            return "❌ Usa el formato: /reprogramar 11:00"

    # --- Buscar por nombre ---
    elif comando == "/buscar":
        try:
            nombre = " ".join(partes[1:])
            agenda = cargar_agenda()
            resultados = [f"{h} → {t}" for h, t in agenda.items() if nombre.lower() in t.lower()]
            return "\n".join(resultados) if resultados else f"❌ No tienes citas con {nombre}."
        except:
            return "❌ Usa el formato: /buscar Pedro"

    # --- Buscar por fecha ---
    elif comando == "/buscar_fecha":
        try:
            fecha = partes[1]  # formato YYYY-MM-DD
            agenda = cargar_agenda()
            resultados = [f"{h} → {t}" for h, t in agenda.items() if h.startswith(fecha)]
            return "\n".join(resultados) if resultados else f"📭 No tienes citas el {fecha}."
        except:
            return "❌ Usa el formato: /buscar_fecha 2025-09-15"

    # --- Consultar "cuando con alguien" ---
    elif comando == "/cuando":
        try:
            nombre = " ".join(partes[1:])
            agenda = cargar_agenda()
            resultados = [h for h, t in agenda.items() if nombre.lower() in t.lower()]
            return f"📌 Tienes con {nombre} a las: {', '.join(resultados)}" if resultados else f"❌ No tienes cita con {nombre}."
        except:
            return "❌ Usa el formato: /cuando Juan"

    # --- Por defecto ---
    else:
        return "🤔 No entendí. Usa /registrar, /agenda, /borrar, /borrar_todo, /reprogramar, /buscar, /buscar_fecha o /cuando."
