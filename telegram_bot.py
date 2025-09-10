import json
import re
import os
import threading
import time
from datetime import datetime, timedelta
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
from telegram import Update

# 🔑 Token desde variable de entorno (Render lo provee)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AGENDA_FILE = "agenda.json"
CHAT_ID = None  # Se registra con /registrar

# -------------------------------
# Gestión de la agenda
# -------------------------------
def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, indent=4, ensure_ascii=False)

# -------------------------------
# Interpretar frases en español
# -------------------------------
def interpretar_frase(frase: str):
    frase = frase.lower()
    ahora = datetime.now()

    # Detectar hora
    hora_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", frase)
    if hora_match:
        horas = int(hora_match.group(1))
        minutos = int(hora_match.group(2)) if hora_match.group(2) else 0
        ampm = hora_match.group(3)
        if ampm and "p" in ampm and horas < 12:
            horas += 12
        elif ampm and "a" in ampm and horas == 12:
            horas = 0
    else:
        horas, minutos = 9, 0  # Default 9:00 AM si no se dice hora

    # Detectar día
    if "hoy" in frase:
        fecha = ahora.date()
    elif "mañana" in frase:
        fecha = (ahora + timedelta(days=1)).date()
    elif "pasado mañana" in frase:
        fecha = (ahora + timedelta(days=2)).date()
    else:
        fecha = ahora.date()

    fecha_hora = datetime.combine(fecha, datetime.min.time()).replace(hour=horas, minute=minutos)

    # Extraer tarea
    tarea = re.sub(r"(hoy|mañana|pasado mañana|\d{1,2}(:\d{2})?\s*(am|pm|a\.m\.|p\.m\.)?)",
                   "", frase, flags=re.IGNORECASE).strip()
    if not tarea:
        tarea = "Tarea pendiente"

    return fecha_hora.strftime("%Y-%m-%d %H:%M"), tarea

# -------------------------------
# Funciones del bot
# -------------------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Hola Doctor Mesa, soy Orbis Asistente 🪐.\n\n"
        "Puedes decirme cosas como:\n"
        "- 'Recuérdame audiencia mañana a las 9'\n"
        "- 'Borra la reunión de las 3'\n"
        "- '¿Qué tengo hoy?'"
    )

def procesar_mensaje(update: Update, context: CallbackContext):
    texto = update.message.text.lower()
    agenda = cargar_agenda()

    # Conversaciones simples
    if texto in ["hola", "buenos días", "buenas tardes", "estás ahí", "me escuchas"]:
        update.message.reply_text("👋 Claro Doctor Mesa, aquí estoy para ayudarle.")
        return

    # Consultar agenda de hoy
    if "qué tengo hoy" in texto or "agenda de hoy" in texto:
        hoy = datetime.now().date()
        tareas = [f"🕒 {h} → {t}" for h, t in agenda.items()
                  if datetime.strptime(h, "%Y-%m-%d %H:%M").date() == hoy]
        update.message.reply_text("📅 Tareas de hoy:\n" + "\n".join(tareas) if tareas else "📭 Hoy no tienes tareas.")
        return

    # Consultar agenda completa
    if "agenda completa" in texto or "todo" in texto:
        tareas = [f"🕒 {h} → {t}" for h, t in sorted(agenda.items())]
        update.message.reply_text("📅 Agenda completa:\n" + "\n".join(tareas) if tareas else "📭 No tienes tareas.")
        return

    # Consultar mañana
    if "mañana" in texto and "agenda" in texto:
        mañana = (datetime.now() + timedelta(days=1)).date()
        tareas = [f"🕒 {h} → {t}" for h, t in agenda.items()
                  if datetime.strptime(h, "%Y-%m-%d %H:%M").date() == mañana]
        update.message.reply_text("📅 Agenda de mañana:\n" + "\n".join(tareas) if tareas else "📭 No tienes tareas mañana.")
        return

    # Eliminar
    if "borra" in texto or "elimina" in texto or "quita" in texto:
        hora_match = re.search(r"\d{1,2}(:\d{2})?", texto)
        if hora_match:
            hora_str = hora_match.group()
            for h in list(agenda.keys()):
                if h.endswith(hora_str.zfill(5)):
                    tarea = agenda.pop(h)
                    guardar_agenda(agenda)
                    update.message.reply_text(f"🗑️ Eliminada: {h} → {tarea}")
                    return
        update.message.reply_text("⚠️ No encontré la tarea a borrar.")
        return

    # Agregar tarea
    fecha_hora, tarea = interpretar_frase(texto)
    agenda[fecha_hora] = tarea
    guardar_agenda(agenda)
    update.message.reply_text(f"✅ Tarea agendada: {fecha_hora} → {tarea}")

def obtener_chatid(update: Update, context: CallbackContext):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    update.message.reply_text("✅ Chat registrado para recordatorios.")

# -------------------------------
# Motor de recordatorios
# -------------------------------
def enviar_recordatorios(bot):
    while True:
        agenda = cargar_agenda()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
        if CHAT_ID and ahora in agenda:
            tarea = agenda[ahora]
            bot.send_message(chat_id=CHAT_ID, text=f"⏰ Recordatorio: {tarea}\n¿Completada ✅ o Reprogramar ⏳?")
        time.sleep(60)

# -------------------------------
# Main
# -------------------------------
def iniciar_bot():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("registrar", obtener_chatid))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_mensaje))

    # Hilo paralelo para recordatorios
    hilo = threading.Thread(target=enviar_recordatorios, args=(updater.bot,), daemon=True)
    hilo.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    iniciar_bot()
