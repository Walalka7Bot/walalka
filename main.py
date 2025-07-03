import os, io, asyncio, requests, tempfile
from decimal import Decimal
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from gtts import gTTS
from asgiref.wsgi import WsgiToAsgi

# Flask App + ASGI wrapper
flask_app = Flask(__name__)
asgi_app = WsgiToAsgi(flask_app)

# ENV Vars
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHAT_ID = int(os.getenv("CHAT_ID", "123456789"))
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))

# Telegram Application
app = Application.builder().token(TELEGRAM_TOKEN).build()

# Lot Size Calculation
def calculate_lot_size(sl_pips: float, pip_value: float = 10.0) -> float:
    if sl_pips == 0:
        return 0.0
    lot = (DAILY_MAX_RISK / Decimal(str(sl_pips))) / Decimal(str(pip_value))
    return round(float(lot), 2)

# Chart Image
def generate_chart_image(pair: str, direction: str) -> bytes:
    url = f"https://quickchart.io/chart?c={{type:'line',data:{{labels:['T1','T2','T3'],datasets:[{{label:'{pair}',data:[1.0,1.1,1.2]}}]}}}}"
    response = requests.get(url)
    return response.content if response.status_code == 200 else None

# Voice Alert
async def send_voice(text: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tts.save(tmp.name)
    with open(tmp.name, "rb") as audio:
        await context.bot.send_voice(chat_id=chat_id, voice=audio)
    os.remove(tmp.name)

# Forex/Crypto/Index Signals
signals = [  # (same list as before – kept unchanged)
    {"pair": "EURUSD", "dir": "BUY", "entry": 1.0950, "tp": 1.1000, "sl": 1.0910, "tf": "15M"},
    {"pair": "GBPUSD", "dir": "SELL", "entry": 1.2700, "tp": 1.2600, "sl": 1.2750, "tf": "5M"},
    {"pair": "USDJPY", "dir": "BUY", "entry": 157.80, "tp": 158.50, "sl": 157.30, "tf": "15M"},
    {"pair": "AUDUSD", "dir": "SELL", "entry": 0.6650, "tp": 0.6580, "sl": 0.6685, "tf": "5M"},
    {"pair": "USDCAD", "dir": "BUY", "entry": 1.3700, "tp": 1.3760, "sl": 1.3660, "tf": "15M"},
    {"pair": "BTCUSD", "dir": "BUY", "entry": 61000, "tp": 63000, "sl": 60000, "tf": "5M"},
    {"pair": "XAUUSD", "dir": "SELL", "entry": 2365, "tp": 2345, "sl": 2378, "tf": "15M"},
    {"pair": "XAGUSD", "dir": "BUY", "entry": 29.50, "tp": 30.20, "sl": 29.10, "tf": "5M"},
    {"pair": "ETHUSD", "dir": "BUY", "entry": 3400, "tp": 3550, "sl": 3320, "tf": "15M"},
    {"pair": "XRPUSD", "dir": "SELL", "entry": 0.48, "tp": 0.45, "sl": 0.50, "tf": "5M"},
    {"pair": "EURJPY", "dir": "SELL", "entry": 170.40, "tp": 169.90, "sl": 170.70, "tf": "5M"},
    {"pair": "NZDUSD", "dir": "BUY", "entry": 0.6100, "tp": 0.6150, "sl": 0.6075, "tf": "15M"},
    {"pair": "USOIL", "dir": "SELL", "entry": 82.00, "tp": 81.30, "sl": 82.50, "tf": "5M"},
    {"pair": "NAS100", "dir": "BUY", "entry": 19400, "tp": 19600, "sl": 19200, "tf": "15M"},
    {"pair": "USDCHF", "dir": "BUY", "entry": 0.8950, "tp": 0.8995, "sl": 0.8920, "tf": "5M"},
    {"pair": "GOLD", "dir": "BUY", "entry": 2335, "tp": 2355, "sl": 2320, "tf": "5M"},
    {"pair": "SOLUSD", "dir": "BUY", "entry": 142, "tp": 148, "sl": 139, "tf": "15M"},
    {"pair": "ADAUSD", "dir": "SELL", "entry": 0.42, "tp": 0.40, "sl": 0.43, "tf": "5M"},
    {"pair": "GBPNZD", "dir": "BUY", "entry": 2.0700, "tp": 2.0800, "sl": 2.0650, "tf": "15M"},
    {"pair": "EURCAD", "dir": "SELL", "entry": 1.4600, "tp": 1.4550, "sl": 1.4625, "tf": "5M"},
]

# Signal Sender
async def send_signals(context: ContextTypes.DEFAULT_TYPE = None):
    bot = context.bot if context else app.bot
    for s in signals:
        sl_pips = abs(s["entry"] - s["sl"]) * 100
        lot_size = calculate_lot_size(sl_pips)
        chart = generate_chart_image(s["pair"], s["dir"])
        msg = (
            f"📊 *{s['pair']} Signal*\n"
            f"Timeframe: {s['tf']}\n"
            f"Direction: {s['dir']}\n"
            f"Entry: {s['entry']}\n"
            f"TP: {s['tp']}\n"
            f"SL: {s['sl']}\n"
            f"📏 Lot Size: {lot_size} lots\n"
            f"🕒 Auto-close in 5 mins"
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{s['pair']}:{s['dir']}:{lot_size}")]])
        if chart:
            await bot.send_photo(chat_id=CHAT_ID, photo=chart, caption=msg, reply_markup=markup, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=CHAT_ID, text=msg, reply_markup=markup, parse_mode="Markdown")
        await send_voice(f"{s['pair']} {s['tf']} signal {s['dir']} now active.", context or app, CHAT_ID)

# Flask Home
@flask_app.route("/")
async def home(): return "✅ Hussein7 Bot is Live!"

# Webhook Receiver
@flask_app.route("/telegram-webhook", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await app.process_update(update)
    return "OK"

# Command Handler
async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_signals(context)

# Add Handler
app.add_handler(CommandHandler("signals", signals_command))

# Init and Run
async def initialize_bot():
    await app.initialize()
    await app.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram-webhook")

if __name__ == "__main__":
    import uvicorn
    asyncio.run(initialize_bot())
    uvicorn.run(asgi_app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
