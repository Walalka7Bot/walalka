from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from gtts import gTTS
from decimal import Decimal
import tempfile
import asyncio
import os

# Initialize Flask app and Telegram bot
flask_app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# -----------------------------
# Halal Coin Filter Toggle
# -----------------------------
halal_only_mode = False

async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode ON" if halal_only_mode else "❌ Halal Only Mode OFF"
    await update.message.reply_text(status)

def is_coin_halal(symbol: str) -> bool:
    haram_keywords = ["casino", "gambling", "loan", "riba", "liquor", "alcohol"]
    return not any(word in symbol.lower() for word in haram_keywords)

# -----------------------------
# Auto Lot Size Calculator
# -----------------------------
def calculate_lot_size(sl_distance_pips: float, pip_value: float = 10.0) -> float:
    risk_per_pip = DAILY_MAX_RISK / Decimal(sl_distance_pips)
    lot_size = risk_per_pip / Decimal(pip_value)
    return round(float(lot_size), 2)

# -----------------------------
# Voice Alert Sender
# -----------------------------
async def send_voice_alert(text, context, chat_id):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            audio_path = tmp.name + ".mp3"
            tts.save(audio_path)
            with open(audio_path, "rb") as audio:
                await context.bot.send_voice(chat_id=chat_id, voice=audio)
    except Exception as e:
        print(f"Voice Alert Error: {e}")

# -----------------------------
# Telegram Webhook Handler
# -----------------------------
@flask_app.route("/telegram-webhook", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await app.process_update(update)
    return "OK"

# -----------------------------
# Signal Webhook Endpoint
# -----------------------------
@flask_app.route("/signal-webhook", methods=['POST'])
def signal_webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")

        halal_status = ""
        if market == "crypto":
            halal_status = "🟢 Halal" if is_coin_halal(symbol) else "🔴 Haram"
            if halal_only_mode and "Haram" in halal_status:
                return "Skipped (Haram coin)"

        message = f"🚨 New {market.upper()} Signal\nPair: {symbol}\nTime: {timeframe}\nDirection: {direction}"
        if halal_status:
            message += f"\nStatus: {halal_status}"

        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        asyncio.run(app.bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup))
        return "Signal Sent"
    except Exception as e:
        return f"Webhook error: {str(e)}"

# -----------------------------
# Flask Home Route
# -----------------------------
@flask_app.route('/')
def home():
    return "Bot is live!"

# -----------------------------
# Startup and Webhook Register
# -----------------------------
import nest_asyncio
nest_asyncio.apply()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.bot.set_webhook(WEBHOOK_URL))
    app.add_handler(CommandHandler("halalonly", toggle_halal_only))
    flask_app.run(host="0.0.0.0", port=10000)
