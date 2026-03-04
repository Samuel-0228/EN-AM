import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = Flask(__name__)

# Build Telegram Application (NO polling)
application = ApplicationBuilder().token(TOKEN).build()

# Message handler


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

# Add handler
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message)
)

# Health check route


@app.route("/")
def home():
    return "Bot is running!"

# Webhook route


@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK"


# Set webhook when app starts
@app.before_first_request
def set_webhook():
    application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
