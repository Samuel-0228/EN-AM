import logging
import inspect
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
try:
    from googletrans import Translator
except ImportError:
    Translator = None
    import logging
    logging.error(
        "googletrans module is not installed. Please install it with 'pip install googletrans==4.0.0-rc1'")
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()


if Translator:
    translator = Translator()
else:
    translator = None

# Read token from environment variable (safer for Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")


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

    if not translator:
        await update.message.reply_text(
            "Translation service is not available. Please contact the administrator to install 'googletrans'."
        )
        return

    try:
        result = translator.translate(english_text, src="en", dest="am")
        if inspect.isawaitable(result):
            result = await result
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


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set.")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), translate_handler)
    )

    application.add_error_handler(error_handler)

    logger.info("Bot is starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
