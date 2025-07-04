from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# BOT TOKEN (ku beddel token-kaaga gaarka ah)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Menu layout (Forex, Crypto, Metals)
menu_buttons = [
    ['📈 Get Signal', '📄 My Journal'],
    ['💰 Upgrade to VIP', '🔕 Mute Voice Alerts'],
    ['🪙 Crypto: BTC / ETH / SOL / XRP'],
    ['📊 Forex: EURUSD / GBPUSD / USDJPY / AUDUSD / USDCAD'],
    ['🥇 Metals: GOLD / SILVER']
]

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Salaam!* \nKu soo dhowow *ICT Forex Signals Bot* 📈\n\n"
        "➤ Fadlan dooro qaybta aad xiiseyneyso:\n\n"
        "🪙 *Crypto:* BTC, ETH, SOL, XRP\n"
        "🥇 *Metals:* GOLD, SILVER\n"
        "📊 *Forex:* EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD",
        reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True),
        parse_mode='Markdown'
    )

# App main runner
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("✅ MODULE 1 READY — /start diyaarsan yahay")
    app.run_polling()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import re

# TOKEN-ka botka (ku beddel kanaga)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# /sendsignal command
async def sendsignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = " ".join(context.args)

        # Signal format: SYMBOL EN=1.0 TP=2.0 SL=0.5 TF=15min Exp=ICT explanation
        pattern = r'(\w+)\s+EN=(\d+\.\d+)\s+TP=(\d+\.\d+)\s+SL=(\d+\.\d+)\s+TF=(\w+)\s+Exp=(.+)'
        match = re.search(pattern, text)

        if not match:
            await update.message.reply_text(
                "❌ *Format khaldan!*\nFadlan isticmaal sidaan:\n"
                "`/sendsignal EURUSD EN=1.0845 TP=1.0880 SL=1.0825 TF=15min Exp=FVG + SMT`",
                parse_mode='Markdown'
            )
            return

        symbol, en, tp, sl, tf, explanation = match.groups()

        signal_msg = f"""
📈 *New ICT Signal - {symbol.upper()} ({tf})*

*ENTRY:* {en}  
*TP:* 🎯 {tp}  
*SL:* 🔻 {sl}  

📚 *Explanation:* {explanation}
⏰ *Time:* Auto Detected (London/NYC Session)
"""
        await update.message.reply_text(signal_msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# App main runner
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("sendsignal", sendsignal))

    print("✅ MODULE 2 READY — Signal-ka diyaarsan yahay: /sendsignal")
    app.run_polling()
from telegram import Update, Audio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token-kaaga Telegram bot
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# File paths (MP3 sounds must exist in same folder)
TP_SOUND = "tp_sound.mp3"
SL_SOUND = "sl_sound.mp3"
EN_SOUND = "entry_sound.mp3"

# TP alert command
async def tp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ *TP hit!* 💰", parse_mode='Markdown')
    with open(TP_SOUND, 'rb') as audio:
        await update.message.reply_audio(audio=audio)

# SL alert command
async def sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ *SL hit!* 😢", parse_mode='Markdown')
    with open(SL_SOUND, 'rb') as audio:
        await update.message.reply_audio(audio=audio)

# Entry alert command
async def entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟡 *Entry reached!*", parse_mode='Markdown')
    with open(EN_SOUND, 'rb') as audio:
        await update.message.reply_audio(audio=audio)

# Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("tp", tp))
    app.add_handler(CommandHandler("sl", sl))
    app.add_handler(CommandHandler("entry", entry))

    print("✅ MODULE 3 READY — Voice alerts: /tp /sl /entry")
    app.run_polling()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token kaaga Telegram
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# PATH fileka image-ka (bedel magaca & location haddii loo baahdo)
CHART_PATH = "chart_sample.jpg"  # chart_sample.jpg waa sawirka la dirayo

# Command /sendchart
async def sendchart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(CHART_PATH, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption="🖼️ *Chart-ka la xiriira signalka*", parse_mode='Markdown')
    except FileNotFoundError:
        await update.message.reply_text("❌ Chart image ma jiro. Fadlan geli file: `chart_sample.jpg`.")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("sendchart", sendchart))

    print("✅ MODULE 4 READY — /sendchart image signal")
    app.run_polling()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token-kaaga bot
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Balance & daily max drawdown
BALANCE = 5000
MAX_DRAWDOWN = 250

# Formula: Lot Size = (Risk $ / SL in pips) / 10 for standard
def calculate_lot(risk_percent, sl_pips):
    risk_dollars = (risk_percent / 100) * BALANCE
    lot_size = risk_dollars / (sl_pips * 10)  # assuming 1 lot = $10/pip
    return round(lot_size, 2), risk_dollars

# Command: /risk 1% 20pips
async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("❌ Format: `/risk 1 20` → (1% risk, 20 pips SL)", parse_mode='Markdown')
            return

        risk_percent = float(context.args[0])
        sl_pips = float(context.args[1])

        lot, dollars = calculate_lot(risk_percent, sl_pips)

        await update.message.reply_text(
            f"📊 *Lot Size Calculation*\n\n"
            f"- Risk: {risk_percent}% (${dollars:.2f})\n"
            f"- Stop Loss: {sl_pips} pips\n"
            f"- 🔢 Lot Size: *{lot}* lots\n"
            f"- 💰 Account: ${BALANCE} | Max Daily Risk: ${MAX_DRAWDOWN}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("risk", risk))

    print("✅ MODULE 5 READY — Command: /risk 1 20")
    app.run_polling()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fpdf import FPDF
from datetime import datetime
import os

# Telegram Bot Token (bedelkan)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Tijaabo fursado (mock data)
trades = [
    {"symbol": "EURUSD", "EN": "1.0845", "TP": "1.0880", "SL": "1.0825", "result": "WIN", "pnl": "+35 pips"},
    {"symbol": "GOLD", "EN": "2310.0", "TP": "2330.0", "SL": "2290.0", "result": "LOSS", "pnl": "-20 pips"},
    {"symbol": "BTC", "EN": "65000", "TP": "67000", "SL": "64000", "result": "WIN", "pnl": "+2000"}
]

# PDF sameynta
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="📊 Daily Trade Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)

    for trade in trades:
        pdf.cell(200, 10, txt=f"{trade['symbol']} | EN: {trade['EN']} | TP: {trade['TP']} | SL: {trade['SL']}", ln=True)
        pdf.cell(200, 10, txt=f"Result: {trade['result']} | P&L: {trade['pnl']}", ln=True)
        pdf.ln(5)

    filepath = "daily_report.pdf"
    pdf.output(filepath)
    return filepath

# /getreport command
async def getreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filepath = generate_pdf()
    try:
        with open(filepath, 'rb') as doc:
            await update.message.reply_document(document=doc, filename=filepath, caption="📄 *Daily Trade Report*", parse_mode='Markdown')
        os.remove(filepath)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("getreport", getreport))

    print("✅ MODULE 6 READY — use /getreport to download PDF")
    app.run_polling()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import csv
import os
from datetime import datetime

# Token-kaaga Telegram bot
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Lacagaha la oggol yahay (11-ka aad codsatay)
VALID_SYMBOLS = [
    "BTC", "ETH", "SOL", "XRP",
    "GOLD", "SILVER",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"
]

CSV_FILE = "results.csv"

# /result command: e.g. /result BTC WIN +2000
async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 3:
            await update.message.reply_text("❌ Format: `/result SYMBOL WIN|LOSS +PIPS`\nTusaale: `/result GOLD WIN +180`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        outcome = context.args[1].upper()
        pnl = context.args[2]

        if symbol not in VALID_SYMBOLS:
            await update.message.reply_text(f"❌ SYMBOL-ka lama aqoonsan: `{symbol}`\nKu isticmaal: {', '.join(VALID_SYMBOLS)}", parse_mode='Markdown')
            return

        if outcome not in ["WIN", "LOSS"]:
            await update.message.reply_text("❌ Qeybta labaad waa in ay noqotaa WIN ama LOSS", parse_mode='Markdown')
            return

        date = datetime.now().strftime("%Y-%m-%d")
        row = [date, symbol, outcome, pnl]

        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Date", "Symbol", "Result", "P&L"])
            writer.writerow(row)

        await update.message.reply_text(f"✅ Result saved: {symbol} → {outcome} {pnl}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("result", result))

    print("✅ MODULE 7 READY — use /result SYMBOL WIN +PIPS")
    app.run_polling()
from flask import Flask, request
from telegram import Bot
import threading

# Telegram bot token
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"  # Bedel chat id-ga (group ama user)

bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/signal', methods=['POST'])
def webhook_signal():
    data = request.json
    symbol = data.get("symbol", "Unknown")
    en = data.get("EN", "N/A")
    tp = data.get("TP", "N/A")
    sl = data.get("SL", "N/A")
    tf = data.get("TF", "15min")
    explanation = data.get("Exp", "No explanation")

    message = f"""
📡 *New Signal via Webhook*

*{symbol}* ({tf})

▶️ EN: {en}  
🎯 TP: {tp}  
🛑 SL: {sl}

📚 {explanation}
"""
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    return {"status": "sent"}, 200

def run_flask():
    app.run(port=5000)

if __name__ == "__main__":
    print("✅ MODULE 8 READY — Webhook server running on http://localhost:5000/signal")
    threading.Thread(target=run_flask).start()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Telegram bot token
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# ✅ Liiska VIP ama Admin users (Telegram user ID)
VIP_USERS = [123456789, 987654321]  # Ku beddel user ID-yada VIP

# ➕ Add VIP-only command
async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in VIP_USERS:
        await update.message.reply_text("❌ Amarkan waxaa heli kara kaliya VIP / Admin.")
        return

    await update.message.reply_text("✅ Ku soo dhawoow VIP! Amar gaar ah ayaad gashay.")

# ➕ Public command (cid kasta isticmaali karo)
async def public_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Amarkan waxaa isticmaali kara cid kasta.")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("vip", vip_command))
    app.add_handler(CommandHandler("start", public_command))

    print("✅ MODULE 9 READY — Commands: /vip (restricted), /start (public)")
    app.run_polling()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# Token Telegram
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Static data (mock)
def get_market_summary():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""
📊 *Daily Market Overview*  
🕒 {today}

🔸 *Crypto*
- BTC: $64,300 ↑
- ETH: $3,250 ↑
- SOL: $145 ↑

🔸 *Forex*
- EURUSD: 1.0845 ↓
- GBPUSD: 1.2750 →
- USDJPY: 158.30 ↑

🔸 *Stocks*
- AAPL: $210.50 ↑
- TSLA: $690.20 ↓
- AMZN: $134.10 →

📈 Xogtan waa guudmarka suuqa maanta.
"""

# /market command
async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = get_market_summary()
    await update.message.reply_text(summary, parse_mode='Markdown')

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("market", market))

    print("✅ MODULE 10 READY — Command: /market")
    app.run_polling()
