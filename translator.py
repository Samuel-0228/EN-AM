import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is not set")

app = Flask(__name__)

application = ApplicationBuilder().token(TOKEN).build()


async def translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        try:
            translated = GoogleTranslator(
                source="auto",
                target="en"
            ).translate(update.message.text)

            await update.message.reply_text(translated)

        except Exception:
            await update.message.reply_text("Translation error occurred.")

application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message)
)


@app.route("/")
def home():
    return "Bot is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK"


@app.before_first_request
def setup():
    asyncio.run(application.initialize())
    asyncio.run(application.bot.set_webhook(f"{WEBHOOK_URL}/webhook"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
