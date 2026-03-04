import os
import requests
from flask import Flask, request, jsonify
from deep_translator import GoogleTranslator

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is not set")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# Home route (health check)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

# Webhook endpoint


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data:
        return jsonify({"status": "no data"}), 400

    message = data.get("message")

    if message and "text" in message:
        chat_id = message["chat"]["id"]
        user_text = message["text"]

        try:
            translated = GoogleTranslator(
                source="auto",
                target="en"
            ).translate(user_text)

        except Exception:
            translated = "Translation error occurred."

        # Send reply back to Telegram
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": translated
            }
        )

    return jsonify({"status": "ok"}), 200


# Set webhook automatically on startup
@app.before_first_request
def set_webhook():
    requests.post(
        f"{TELEGRAM_API}/setWebhook",
        json={"url": f"{WEBHOOK_URL}/webhook"}
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
