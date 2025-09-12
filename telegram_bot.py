import os
import json

AGENDA_FILE = "agenda.json"

def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

# --- Procesar texto y devolver string ---
def procesar_texto(texto: str) -> str:
    partes = texto.strip().split()
    comando = partes[0].lower()

    if comando == "/start":
        return "👋 Hola, soy Orbis. Tu asistente está listo."

    elif comando == "/agenda":
        agenda = cargar_agenda()
        if not agenda:
            return "📭 No tienes tareas guardadas."
        else:
            texto = "\n".join([f"{h} → {t}" for h, t in agenda.items()])
            return "📝 Agenda:\n" + texto

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

    elif comando == "/borrar":
        try:
            hora = partes[1]
            agenda = cargar_agenda()
            if hora in agenda:
                del agenda[hora]
                guardar_agenda(agenda)
                return f"🗑️ Borrada la tarea de las {hora}"
            else:
                return "❌ No hay nada guardado en esa hora."
        except:
            return "❌ Usa el formato: /borrar 09:00"

    else:
        return "🤔 No entendí. Usa /registrar o /agenda."
