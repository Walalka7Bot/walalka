import os
import io
import requests
import tempfile
from decimal import Decimal
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from gtts import gTTS

# === Settings ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))

# === Lot size calculation ===
def calculate_lot_size(sl_pips: float, pip_value: float = 10.0) -> float:
    if sl_pips == 0:
        return 0.0
    lot = (DAILY_MAX_RISK / Decimal(str(sl_pips))) / Decimal(str(pip_value))
    return round(float(lot), 2)

# === Chart image generator ===
def generate_chart_image(pair: str, direction: str) -> bytes:
    chart_url = f"https://quickchart.io/chart?c={{type:'line',data:{{labels:['T1','T2','T3'],datasets:[{{label:'{pair}',data:[1.0,1.1,1.2]}}]}}}}"
    response = requests.get(chart_url)
    return response.content if response.status_code == 200 else None

# === Voice alert ===
async def send_voice(text: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tts.save(tmp.name)
    with open(tmp.name, "rb") as audio:
        await context.bot.send_voice(chat_id=chat_id, voice=audio)
    os.remove(tmp.name)

# === Send Forex/Crypto/Metals signals ===
async def send_forex_pro_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signals = [
        {"pair": "EURUSD", "dir": "BUY", "entry": 1.0950, "tp": 1.1000, "sl": 1.0910},
        {"pair": "GBPUSD", "dir": "SELL", "entry": 1.2700, "tp": 1.2600, "sl": 1.2750},
        {"pair": "USDJPY", "dir": "BUY", "entry": 157.80, "tp": 158.50, "sl": 157.30},
        {"pair": "AUDUSD", "dir": "SELL", "entry": 0.6650, "tp": 0.6580, "sl": 0.6685},
        {"pair": "USDCAD", "dir": "BUY", "entry": 1.3700, "tp": 1.3760, "sl": 1.3660},
        {"pair": "BTCUSD", "dir": "BUY", "entry": 61000, "tp": 63000, "sl": 60000},
        {"pair": "XAUUSD", "dir": "SELL", "entry": 2365, "tp": 2345, "sl": 2378},
        {"pair": "XAGUSD", "dir": "BUY", "entry": 29.50, "tp": 30.20, "sl": 29.10},
        {"pair": "ETHUSD", "dir": "BUY", "entry": 3400, "tp": 3550, "sl": 3320},
        {"pair": "XRPUSD", "dir": "SELL", "entry": 0.48, "tp": 0.45, "sl": 0.50}
    ]

    for signal in signals:
        pair = signal["pair"]
        direction = signal["dir"]
        entry = signal["entry"]
        tp = signal["tp"]
        sl = signal["sl"]
        sl_pips = abs(entry - sl) * 100 if isinstance(entry, float) else abs(entry - sl)
        lot_size = calculate_lot_size(sl_pips)
        chart_img = generate_chart_image(pair, direction)

        msg = (
            f"📊 *{pair} Signal*\n"
            f"Direction: {direction}\n"
            f"Entry: {entry}\n"
            f"TP: {tp}\n"
            f"SL: {sl}\n"
            f"📏 Lot Size: {lot_size} lots\n"
            f"🕒 Auto-close in 5 mins"
        )

        buttons = [
            [InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{pair}:{direction}:{lot_size}")],
            [InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")]
        ]
        markup = InlineKeyboardMarkup(buttons)

        if chart_img:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=chart_img,
                caption=msg,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=markup, parse_mode="Markdown")

        await send_voice(f"{pair} signal: {direction} now active.", context, update.effective_chat.id)

# === Bot Setup ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("👋 Bot is running.")))
app.add_handler(CommandHandler("forexpro", send_forex_pro_signals))

# === Run Bot ===
async def main():
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
