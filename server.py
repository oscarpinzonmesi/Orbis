import os
from flask import Flask, request
from telegram_bot import crear_app

PORT = int(os.environ.get("PORT", 10000))
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://orbis-5gkk.onrender.com")

app_flask = Flask(__name__)
bot_app = crear_app()

@app_flask.route(f"/webhook/{bot_app.bot.id}", methods=["POST"])
async def webhook():
    update = await request.get_json(force=True)
    await bot_app.update_queue.put(update)
    return "ok", 200

if __name__ == "__main__":
    import asyncio

    # Configurar Webhook
    async def main():
        await bot_app.bot.set_webhook(f"{URL}/webhook/{bot_app.bot.id}")
        print(f"🚀 Webhook configurado en {URL}/webhook/{bot_app.bot.id}")
        app_flask.run(host="0.0.0.0", port=PORT)

    asyncio.run(main())
