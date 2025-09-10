import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

AGENDA_FILE = "agenda.json"

# --- Funciones para manejar la agenda ---
def cargar_agenda():
    if not os.path.exists(AGENDA_FILE):
        return {}
    with open(AGENDA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=4)

# --- Handlers del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, soy Orbis. Tu asistente está listo.")

async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agenda = cargar_agenda()
    try:
        hora = context.args[0]
        tarea = " ".join(context.args[1:])
        agenda[hora] = tarea
        guardar_agenda(agenda)
        await update.message.reply_text(f"✅ Guardado: {hora} → {tarea}")
    except:
        await update.message.reply_text("❌ Usa el formato: /registrar 09:00 Reunión")

async def ver_agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agenda = cargar_agenda()
    if not agenda:
        await update.message.reply_text("📭 No tienes tareas guardadas.")
    else:
        texto = "\n".join([f"{h} → {t}" for h, t in agenda.items()])
        await update.message.reply_text("📝 Agenda:\n" + texto)

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agenda = cargar_agenda()
    try:
        hora = context.args[0]
        if hora in agenda:
            del agenda[hora]
            guardar_agenda(agenda)
            await update.message.reply_text(f"🗑️ Borrada la tarea de las {hora}")
        else:
            await update.message.reply_text("❌ No hay nada guardado en esa hora.")
    except:
        await update.message.reply_text("❌ Usa el formato: /borrar 09:00")

# --- Iniciar el bot ---
def iniciar_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("⚠️ TELEGRAM_TOKEN no está configurado")

    app = ApplicationBuilder().token(token).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))
    app.add_handler(CommandHandler("agenda", ver_agenda))
    app.add_handler(CommandHandler("borrar", borrar))

    # Mensajes de texto (ej: "qué tengo hoy")
    async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
        texto = update.message.text.lower()
        if "qué tengo" in texto or "que tengo" in texto:
            await ver_agenda(update, context)
        else:
            await update.message.reply_text("🤔 No entendí. Usa /registrar o /agenda.")

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

    print("🤖 Orbis está corriendo...")
    app.run_polling()
