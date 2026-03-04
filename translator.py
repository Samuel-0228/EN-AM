import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from googletrans import Translator

# ----------------- Logging -----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------------- Config -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Render
# e.g. https://your-service.onrender.com/webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set.")
if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL environment variable is not set.")

translator = Translator()

# ----------------- Telegram Application -----------------
application: Application = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

# ---------- Handlers ----------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Selam 👋\n"
        "Send me any English text and I will translate it to Amharic.\n\n"
        "Examples:\n"
        " - Hello, how are you?\n"
        " - I live in Addis Ababa."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "I am an English → Amharic translator bot.\n"
        "Just send English text, and I will reply in Amharic.\n\n"
        "Commands:\n"
        " /start  - introduction\n"
        " /help   - this help message"
    )
    await update.message.reply_text(text)


async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    english_text = update.message.text.strip()

    if english_text.startswith("/"):
        return

    try:
        result = translator.translate(english_text, src="en", dest="am")
        amharic_text = result.text

        reply = (
            "✅ Translation:\n\n"
            f"English:\n{english_text}\n\n"
            f"Amharic:\n{amharic_text}"
        )
        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception("Translation error: %s", e)
        await update.message.reply_text(
            "Sorry, I could not translate this right now. Please try again."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update %s caused error %s", update, context.error)


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(
    MessageHandler(filters.TEXT & (~filters.COMMAND), translate_handler)
)
application.add_error_handler(error_handler)

# ----------------- FastAPI app -----------------

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    # Delete old webhook, then set the new one
    logger.info("Starting bot and setting webhook...")
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=WEBHOOK_URL)
    # Start the bot (no polling; only webhook processing)
    await application.initialize()
    await application.start()
    logger.info("Webhook set to %s", WEBHOOK_URL)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Stopping bot...")
    await application.stop()
    await application.shutdown()


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram will POST updates to this endpoint.
    """
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.exception("Error processing update: %s", e)
        # Return 200 so Telegram does not retry forever
        return JSONResponse({"ok": False})
    return JSONResponse({"ok": True})


@app.get("/")
async def root():
    return {"status": "ok", "message": "English-Amharic bot is running."}
