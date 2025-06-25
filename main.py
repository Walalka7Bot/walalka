import os
import nest_asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from datetime import datetime
from decimal import Decimal
from web3 import Web3

nest_asyncio.apply()

# ✅ Load ENV variables
INFURA_URL = os.getenv("INFURA_URL")
WALLET_ADDRESS_ETH = os.getenv("WALLET_ADDRESS_ETH")
PRIVATE_KEY_ETH = os.getenv("PRIVATE_KEY_ETH")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Setup Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ Profit tracking
daily_profits = {}
auto_trade_enabled = True  # default ON

# ✅ Command: /profit 50
async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /profit 50")
    amount = Decimal(context.args[0])
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in daily_profits:
        daily_profits[today] = Decimal("0")
    daily_profits[today] += amount
    await update.message.reply_text(f"✅ Profit added: ${amount} for {today}")

# ✅ Command: /profits
async def view_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_profits:
        return await update.message.reply_text("🚫 No profits recorded.")
    msg = "📊 Daily Profits:\n"
    for day, amount in daily_profits.items():
        msg += f"{day}: ${amount}\n"
    await update.message.reply_text(msg)

# ✅ Command: /withdraw_eth 0.01 0xYourOtherAddress
async def withdraw_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /withdraw_eth 0.01 0xYourOtherAddress")
    try:
        amount = Decimal(context.args[0])
        to_address = context.args[1]
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS_ETH)
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': w3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': w3.to_wei('50', 'gwei')
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY_ETH)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        await update.message.reply_text(f"✅ Withdraw Success: {w3.to_hex(tx_hash)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ✅ Command: /autotrade (toggle ON/OFF)
async def toggle_auto_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = "✅ ON" if auto_trade_enabled else "⛔ OFF"
    await update.message.reply_text(f"Auto-Trade is now: {status}")

from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import threading
import os
import nest_asyncio
nest_asyncio.apply()

# ✅ ENV Variables
INFURA_URL = os.getenv("INFURA_URL")
WALLET_ADDRESS_ETH = os.getenv("WALLET_ADDRESS_ETH")
PRIVATE_KEY_ETH = os.getenv("PRIVATE_KEY_ETH")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Telegram App
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Bot is now active.")

# ✅ Push notify command (manual test)
async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚨 New Trade Opportunity!\nPair: GOLD\nTime: 5min\nStatus: ⬆️ BUY Setup"
    buttons = [[
        InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM:GOLD:BUY"),
        InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
    ]]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(msg, reply_markup=markup)

# ✅ Button click handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("CONFIRM"):
        _, symbol, direction = query.data.split(":")
        await query.edit_message_text(text=f"✅ Confirmed: {symbol} → {direction}")
    elif query.data == "IGNORE":
        await query.edit_message_text(text="❌ Signal ignored.")

# ✅ Register commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("notify", notify))
app.add_handler(CallbackQueryHandler(button_handler))

# ✅ Flask + Webhook route
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route('/webhook', methods=["POST"])
def webhook_handler():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY/SELL")
        time_frame = data.get("time", "5min")

        msg = f"🚨 Signal Received!\nPair: {symbol}\nTime: {time_frame}\nDirection: {direction}"
        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        markup = InlineKeyboardMarkup(buttons)

        # ✅ Bedel CHAT ID hoose
        app.bot.send_message(chat_id=CHAT_ID, text=msg, reply_markup=markup)
        return "✅ Signal sent"
    except Exception as e:
        return f"❌ Error: {str(e)}"
# ✅ CUTUBKA 11: Daily Report Generator (Single File)
import os, json, asyncio
from datetime import datetime
from fpdf import FPDF
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

LOG_FILE = "daily_trades.json"
CHAT_ID = os.getenv("CHAT_ID")

# 1️⃣ Trade Logger
def log_trade_result(symbol, result, pnl):
    today = datetime.now().strftime("%Y-%m-%d")
    log_entry = {"date": today, "symbol": symbol, "result": result, "pnl": pnl}

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# 2️⃣ PDF Generator
def generate_daily_report():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except:
        return None

    today_trades = [d for d in data if d["date"] == today]
    if not today_trades:
        return None

    win_count = sum(1 for d in today_trades if d["result"].upper() == "WIN")
    loss_count = sum(1 for d in today_trades if d["result"].upper() == "LOSS")
    total_pnl = sum(float(d["pnl"]) for d in today_trades)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"📊 Daily Report – {today}", ln=True, align='C')
    pdf.ln(10)

    for trade in today_trades:
        line = f"{trade['symbol']} - {trade['result']} - P&L: ${trade['pnl']}"
        pdf.cell(200, 10, txt=line, ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, txt=f"✅ Wins: {win_count} | ❌ Losses: {loss_count} | 💰 Net P&L: ${round(total_pnl, 2)}", ln=True)

    file_path = f"report_{today}.pdf"
    pdf.output(file_path)
    return file_path

# 3️⃣ /report Command Handler
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_path = generate_daily_report()
    if not pdf_path:
        await update.message.reply_text("⚠️ Ma jiro report maanta.")
        return

    with open(pdf_path, "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=pdf_path)

# ✅ Add this in your main.py:
# app.add_handler(CommandHandler("report", report_command))

# 4️⃣ Automatic Schedule @ 23:59
def schedule_daily_report(bot):
    scheduler = BackgroundScheduler()

    def job():
        pdf_path = generate_daily_report()
        if pdf_path and CHAT_ID:
            asyncio.run(bot.send_document(chat_id=CHAT_ID, document=open(pdf_path, "rb"), filename=pdf_path))

    scheduler.add_job(job, 'cron', hour=23, minute=59)
    scheduler.start()
## ✅ Cutubka 12: Trade Result Buttons (WIN / LOSS / BE)

### 🎯 Ujeeddo
Markaad gujiso `Confirm` signal-ka, bot-ku wuxuu kuusoo bandhigayaa **3 buttons** si aad u sheegto natiijada ganacsiga:

- ✅ `WIN`
- ❌ `LOSS`
- 🤝 `BE` (Breakeven)

Bot-ka wuxuu si toos ah:
- U keydiyaa result-kii
- U xisaabiyaa P&L
- U diiwaangeliyaa file JSON ah (`daily_trades.json`)
- Waxaana lagu dari karaa `PDF` report-ka habeen kasta 23:59

---

### 🧠 Tallaabooyinka Code-ka:

#### ✅ Update `signal_webhook` – Add callback to "Confirm"

```python
buttons = [[
    InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
    InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
]]
```

#### ✅ Add Callback for "CONFIRM" – Show Result Options

```python
@app.callback_query_handler(lambda c: c.data and c.data.startswith("CONFIRM:"))
async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, symbol, direction = query.data.split(":")

    buttons = [
        [
            InlineKeyboardButton("✅ WIN", callback_data=f"RESULT:WIN:{symbol}"),
            InlineKeyboardButton("❌ LOSS", callback_data=f"RESULT:LOSS:{symbol}"),
            InlineKeyboardButton("🤝 BE", callback_data=f"RESULT:BE:{symbol}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.reply_text(f"📊 What was the result for {symbol}?", reply_markup=reply_markup)
```

#### ✅ Handle Result Selection + Save to JSON

```python
import json
from datetime import datetime

DAILY_LOG = "daily_trades.json"

@app.callback_query_handler(lambda c: c.data and c.data.startswith("RESULT:"))
async def handle_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, result, symbol = query.data.split(":")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    trade_entry = {
        "symbol": symbol,
        "result": result,
        "time": timestamp
    }

    try:
        with open(DAILY_LOG, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(trade_entry)

    with open(DAILY_LOG, "w") as f:
        json.dump(data, f, indent=2)

    await query.message.reply_text(f"✅ Result saved: {symbol} → {result}")
```

---

### 🧾 Tusaale JSON Format:
```json
[
  {
    "symbol": "EURUSD",
    "result": "WIN",
    "time": "2025-06-25 15:15"
  }
]
```

---

## 🔄 Xiriir la leh:
- ✅ **Cutubka 11**: Jadwal PDF report oo uu ka akhrisanayo file-ka `daily_trades.json`
- ✅ **Cutubka 10**: Auto Lot Calculation si aad ugu xisaabiso result kasta
# ✅ Cutubka 13: Memecoin Detector + Auto Halal Filter
# Waxay raadisaa memecoins cusub, u diraa Telegram signal + halal status, wallet & chain info

import requests, asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler

# 🔒 Halal filter keywords
HARAM_KEYWORDS = ["casino", "bet", "gamble", "loan", "alcohol", "riba", "sex"]

# 🔎 Halal Checker
def is_halal_coin(symbol: str) -> bool:
    return not any(haram in symbol.lower() for haram in HARAM_KEYWORDS)

# 📡 Fetch trending memecoins (from DEXscreener sample API)
def fetch_trending_coins():
    try:
        response = requests.get("https://api.dexscreener.com/latest/dex/pairs")
        data = response.json()

        coins = []
        for pair in data.get("pairs", [])[:5]:  # Top 5 only
            coin = {
                "name": pair["baseToken"]["name"],
                "symbol": pair["baseToken"]["symbol"],
                "chain": pair["chainId"],
                "wallet": pair["pairAddress"],
                "image": pair.get("imageUrl", None)
            }
            coins.append(coin)

        return coins
    except Exception as e:
        print(f"Memecoin fetch error: {e}")
        return []

# 🚀 Send Telegram Alert with Halal status
async def send_memecoin_alert(app, chat_id):
    trending = fetch_trending_coins()
    for coin in trending:
        status = "🟢 Halal" if is_halal_coin(coin["symbol"]) else "🔴 Haram"
        msg = (
            f"🚀 *Trending Memecoin Alert!*\n\n"
            f"Name: {coin['name']}\n"
            f"Symbol: `{coin['symbol']}`\n"
            f"Chain: {coin['chain']}\n"
            f"Wallet: `{coin['wallet']}`\n"
            f"Status: {status}"
        )

        buttons = [[
            InlineKeyboardButton("🧾 View on DexTools", url=f"https://www.dexscreener.com/{coin['chain']}/{coin['wallet']}"),
            InlineKeyboardButton("📥 Add to Watchlist", callback_data=f"WATCH_{coin['symbol']}")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        try:
            if coin["image"]:
                await app.bot.send_photo(chat_id=chat_id, photo=coin["image"], caption=msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            print(f"Send error: {e}")

# 🧪 /memecoins command
app.add_handler(CommandHandler("memecoins", lambda u, c: asyncio.create_task(send_memecoin_alert(app, u.effective_chat.id))))

# ⏰ Jadwal automatic ah – 60 daqiiqo kasta
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(send_memecoin_alert(app, chat_id=os.getenv("CHAT_ID"))), 'interval', minutes=60)
scheduler.start()
# ✅ Cutubka 14: Auto Withdraw ETH
# Si fudud ETH uga dir bot-ka wallet-kiisa adigoo isticmaalaya command /withdraw_eth

import os, json
from web3 import Web3
from telegram.ext import CommandHandler

INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY_ETH = os.getenv("PRIVATE_KEY_ETH")
WALLET_ADDRESS_ETH = os.getenv("WALLET_ADDRESS_ETH")

web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# 🏦 Function: ETH Transfer
def send_eth(destination: str, amount_eth: float) -> str:
    try:
        account = web3.eth.account.from_key(PRIVATE_KEY_ETH)
        nonce = web3.eth.get_transaction_count(account.address)
        tx = {
            'nonce': nonce,
            'to': destination,
            'value': web3.to_wei(amount_eth, 'ether'),
            'gas': 21000,
            'gasPrice': web3.eth.gas_price
        }
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY_ETH)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return web3.to_hex(tx_hash)
    except Exception as e:
        return f"❌ Error: {e}"

# 💬 Telegram Command: /withdraw_eth <wallet> <amount>
async def withdraw_eth(update, context):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("❗ Format: /withdraw_eth <wallet_address> <amount>")
            return

        dest_wallet = args[0]
        amount = float(args[1])

        tx_hash = send_eth(dest_wallet, amount)
        if tx_hash.startswith("0x"):
            await update.message.reply_text(f"✅ ETH sent successfully!\nTransaction: https://etherscan.io/tx/{tx_hash}")
        else:
            await update.message.reply_text(tx_hash)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# 🧩 Add command handler
app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))
# ✅ TP/SL Voice Alerts – Gool & Guuldarro Codad kala duwan
from gtts import gTTS
import tempfile
from telegram.constants import ChatAction
from telegram.ext import CommandHandler

# 🔊 Play voice alert based on trade result
async def play_result_voice(result_type: str, context, chat_id: str):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)

        if result_type == "TP":
            message = "Congratulations! Take Profit hit. Ka-ching!"
        elif result_type == "SL":
            message = "Stop Loss hit. Wax meynas galay!"
        else:
            message = "Unknown trade result."

        tts = gTTS(message)
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tts.save(tmp.name + ".mp3")
            with open(tmp.name + ".mp3", "rb") as audio:
                await context.bot.send_voice(chat_id=chat_id, voice=audio)
    except Exception as e:
        print(f"Voice alert error: {e}")

# ✅ Manual Test Commands: /tp and /sl
async def tp_alert(update, context):
    await play_result_voice("TP", context, update.effective_chat.id)

async def sl_alert(update, context):
    await play_result_voice("SL", context, update.effective_chat.id)

# ✅ Add handlers
app.add_handler(CommandHandler("tp", tp_alert))
app.add_handler(CommandHandler("sl", sl_alert))
from flask import Flask, request
import requests
import os

flask_app = Flask(__name__)

# ✅ Env setup
PUSH_APP_WEBHOOK_URL = os.getenv("PUSH_APP_WEBHOOK_URL", "https://your-push-service.com/api/send")

# ✅ Push Notification function
def send_push_notification(title: str, message: str):
    try:
        payload = {
            "title": title,
            "message": message
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(PUSH_APP_WEBHOOK_URL, json=payload, headers=headers)
        print("✅ Push Notification sent:", response.status_code)
    except Exception as e:
        print(f"❌ Push Notification Error: {e}")

# ✅ Webhook endpoint: Signal + Push Notification
@flask_app.route('/push-signal-webhook', methods=["POST"])
def push_signal_webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        market = data.get("market", "forex")
        timeframe = data.get("timeframe", "5min")

        title = f"📈 {market.upper()} Signal"
        message = f"{symbol} → {direction} ({timeframe})"

        # Send push notification
        send_push_notification(title, message)

        return "✅ Push Notification Sent"
    except Exception as e:
        return f"❌ Error in webhook: {str(e)}"
from fpdf import FPDF
from datetime import datetime
import os
import asyncio
import pytz
from telegram.ext import CommandHandler

# ✅ Storage path
REPORTS_FOLDER = "reports"
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# ✅ Sample profit log (Replace this with real DB/file read)
profit_log = []

# ✅ PDF Generation Function
def generate_daily_report():
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(REPORTS_FOLDER, f"report_{today_str}.pdf")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"📊 Daily Trade Report – {today_str}", ln=True, align="C")
    pdf.ln(10)
    
    if not profit_log:
        pdf.cell(200, 10, txt="No trades recorded today.", ln=True)
    else:
        for idx, entry in enumerate(profit_log, 1):
            pdf.cell(200, 10, txt=f"{idx}. {entry}", ln=True)

    pdf.output(filename)
    return filename

# ✅ Manual Command: /report
async def send_report(update, context):
    file_path = generate_daily_report()
    with open(file_path, 'rb') as pdf_file:
        await update.message.reply_document(pdf_file, filename=os.path.basename(file_path))

# ✅ Add command to bot
app.add_handler(CommandHandler("report", send_report))

# ✅ Automatic Scheduler (every 23:59)
async def schedule_daily_report(context):
    while True:
        now = datetime.now(pytz.timezone("Africa/Nairobi"))
        target_time = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now > target_time:
            target_time = target_time.replace(day=now.day + 1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Send report to main chat
        file_path = generate_daily_report()
        chat_id = os.getenv("CHAT_ID")
        if chat_id:
            with open(file_path, 'rb') as pdf_file:
                await context.bot.send_document(chat_id=chat_id, document=pdf_file, filename=os.path.basename(file_path))

# ✅ Launch scheduler in background
app.job_queue.run_once(lambda ctx: asyncio.create_task(schedule_daily_report(ctx)), when=0)
from telegram.ext import CallbackQueryHandler, CommandHandler
from datetime import datetime

# ✅ In-memory confirmed trades list (can be saved to file or DB)
confirmed_trades = []

# ✅ Callback handler for confirmation button
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("CONFIRM:"):
        _, symbol, direction = query.data.split(":")
        entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - {symbol} {direction}"
        confirmed_trades.append(entry)
        await query.edit_message_text(text=f"✅ Trade confirmed:\n{entry}")

    elif query.data == "IGNORE":
        await query.edit_message_text(text="❌ Signal ignored.")

# ✅ Add handler to app
app.add_handler(CallbackQueryHandler(handle_callback))

# ✅ /confirmed command – Show list of confirmed trades
async def show_confirmed_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not confirmed_trades:
        await update.message.reply_text("⚠️ No trades confirmed yet.")
    else:
        text = "📋 *Confirmed Trades List:*\n"
        text += "\n".join(f"{i+1}. {t}" for i, t in enumerate(confirmed_trades))
        await update.message.reply_text(text, parse_mode="Markdown")

# ✅ Add /confirmed command to bot
app.add_handler(CommandHandler("confirmed", show_confirmed_trades))
import requests
from io import BytesIO
from PIL import Image
from telegram import InputFile

# ✅ Sample function to render a chart using third-party API or webhook
def get_chart_image(symbol: str, timeframe: str = "5m") -> BytesIO:
    # Tusaale API image URL – beddel haddii aad leedahay API kale
    url = f"https://quickchart.io/chart?c={{type:'line',data:{{labels:['1','2','3'],datasets:[{{label:'{symbol}',data:[1,2,3]}}]}}}}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Chart image fetch failed")
    return BytesIO(response.content)

# ✅ Usage inside signal webhook
def get_coin_type_label(coin_name: str) -> str:
    if "break" in coin_name.lower():
        return "📈 Breakout"
    elif "volume" in coin_name.lower():
        return "🔥 High Volume"
    else:
        return "🪙 Coin"

@flask_app.route('/signal-webhook', methods=['POST'])
def signal_webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "crypto")

        label = get_coin_type_label(symbol)
        halal_status = "🟢 Halal" if is_coin_halal(symbol) else "🔴 Haram"

        msg = f"{label} Signal 📊\nCoin: {symbol}\nTimeframe: {timeframe}\nDirection: {direction}\nStatus: {halal_status}"

        chart_image = get_chart_image(symbol)
        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        
        app.bot.send_photo(chat_id=chat_id, photo=InputFile(chart_image, filename=f"{symbol}_chart.png"), caption=msg)

        return "Signal with chart sent"
    except Exception as e:
        return f"Webhook error: {str(e)}"
from datetime import datetime, timedelta
import json
import os

# Faylka la keydiyo profits
PROFIT_FILE = "profits.json"
GOAL_AMOUNT = float(os.getenv("PROFIT_GOAL_AMOUNT", 650))
GOAL_DAYS = int(os.getenv("PROFIT_GOAL_DAYS", 10))

# ✅ Helper function: save profit
def save_profit(amount):
    try:
        if not os.path.exists(PROFIT_FILE):
            with open(PROFIT_FILE, "w") as f:
                json.dump([], f)
        with open(PROFIT_FILE, "r") as f:
            data = json.load(f)
        data.append({"amount": amount, "date": datetime.now().isoformat()})
        with open(PROFIT_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Profit Save Error: {e}")

# ✅ Helper function: get progress
def get_goal_progress():
    try:
        if not os.path.exists(PROFIT_FILE):
            return 0.0, 0
        with open(PROFIT_FILE, "r") as f:
            data = json.load(f)
        start_date = datetime.now() - timedelta(days=GOAL_DAYS)
        recent_profits = [
            float(x["amount"]) for x in data
            if datetime.fromisoformat(x["date"]) >= start_date
        ]
        total = sum(recent_profits)
        remaining = max(GOAL_AMOUNT - total, 0)
        return total, remaining
    except Exception as e:
        print(f"Progress Error: {e}")
        return 0.0, GOAL_AMOUNT

# ✅ Command: /profit <amount>
async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        save_profit(amount)
        total, remaining = get_goal_progress()
        await update.message.reply_text(
            f"💰 Profit added: ${amount:.2f}\n📈 Progress: ${total:.2f} / ${GOAL_AMOUNT}\n⏳ Remaining: ${remaining:.2f}"
        )
    except Exception as e:
        await update.message.reply_text("Usage: /profit 50.00")

# ✅ Command: /profits (view progress only)
async def view_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, remaining = get_goal_progress()
    await update.message.reply_text(
        f"📊 Goal Progress\nTarget: ${GOAL_AMOUNT:.2f} in {GOAL_DAYS} days\nProgress: ${total:.2f}\nRemaining: ${remaining:.2f}"
    )

# ✅ Handlers
app.add_handler(CommandHandler("profit", add_profit))
app.add_handler(CommandHandler("profits", view_progress))
# ✅ Cutubka 21: Bot UI Buttons – Mute, Market Filter, Halal Toggle, Search
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# ✅ Voice Alerts Toggle
voice_alerts_enabled = True

async def toggle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global voice_alerts_enabled
    voice_alerts_enabled = not voice_alerts_enabled
    state = "🔊 Voice Alerts ON" if voice_alerts_enabled else "🔇 Voice Alerts OFF"
    await update.message.reply_text(state)

app.add_handler(CommandHandler("mute", toggle_voice))

# ✅ Market Filter (Forex, Crypto, etc.)
visible_markets = {
    "forex": True,
    "crypto": True,
    "stocks": True,
    "polymarket": True,
    "memecoins": True,
}

async def toggle_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        market = context.args[0].lower()
        if market in visible_markets:
            visible_markets[market] = not visible_markets[market]
            state = "✅ ON" if visible_markets[market] else "❌ OFF"
            await update.message.reply_text(f"{market.upper()} visibility: {state}")
        else:
            await update.message.reply_text("Unknown market. Use one of: forex, crypto, stocks, polymarket, memecoins")
    except:
        await update.message.reply_text("Usage: /togglemarket forex")

app.add_handler(CommandHandler("togglemarket", toggle_market))

# ✅ Halal Filter Toggle (Already Exists in Cutubka 9, reused here)
halal_only_mode = False

async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode ON" if halal_only_mode else "❌ Halal Only Mode OFF"
    await update.message.reply_text(f"{status}")

app.add_handler(CommandHandler("halalonly", toggle_halal_only))

# ✅ Search Function (Symbol / Coin)
sample_signals = [
    {"symbol": "EURUSD", "market": "forex", "direction": "BUY"},
    {"symbol": "SOL", "market": "crypto", "direction": "SELL"},
    {"symbol": "TSLA", "market": "stocks", "direction": "BUY"},
]

async def search_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = context.args[0].upper()
        matches = [s for s in sample_signals if query in s["symbol"]]
        if matches:
            for m in matches:
                await update.message.reply_text(f"{m['market'].upper()} Signal\nSymbol: {m['symbol']}\nDirection: {m['direction']}")
        else:
            await update.message.reply_text("No matching signal found.")
    except:
        await update.message.reply_text("Usage: /search EURUSD")

app.add_handler(CommandHandler("search", search_signal))
# ✅ ICT Forex Style Filter Integration

from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# Toggle flag
ict_mode_enabled = True

# ✅ Toggle Command
async def toggle_ict_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ict_mode_enabled
    ict_mode_enabled = not ict_mode_enabled
    state = "✅ ICT Filter ON" if ict_mode_enabled else "❌ ICT Filter OFF"
    await update.message.reply_text(state)

app.add_handler(CommandHandler("ictmode", toggle_ict_mode))

# ✅ Example ICT Style Criteria
def matches_ict_criteria(signal: dict) -> bool:
    """
    Sample logic:
    Only allow:
    - Timeframe = 5min
    - Direction must be 'BUY' at discount or 'SELL' at premium (mocked here)
    """
    if signal["market"] != "forex":
        return True  # Only apply filter to Forex

    # Mocked logic for now (you can improve with real ICT concepts later)
    allowed_timeframes = ["5min"]
    direction = signal.get("direction", "").upper()
    symbol = signal.get("symbol", "")

    if signal.get("timeframe", "") not in allowed_timeframes:
        return False

    # Simulated example: Accept EURUSD only if BUY
    if symbol == "EURUSD" and direction == "BUY":
        return True
    return False

# ✅ Usage in signal webhook
# Inside your /signal-webhook handler, update like this:
if ict_mode_enabled and not matches_ict_criteria(data):
    return "❌ Rejected by ICT Filter"

# Example JSON signal:
"""
{
  "symbol": "EURUSD",
  "direction": "BUY",
  "timeframe": "5min",
  "market": "forex"
}
"""

# ✅ Now only ICT-compliant trades will be forwarded when ict_mode_enabled = True
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# ✅ Set timezone
TIMEZONE = pytz.timezone("Africa/Nairobi")  # Ku beddel hadii timezone kale tahay

# ✅ Signal tracking
signals_today = []

def mark_signal_received(symbol):
    today_str = date.today().isoformat()
    signals_today.append((symbol, today_str))

def has_signal_today():
    today_str = date.today().isoformat()
    return any(day == today_str for _, day in signals_today)

# ✅ Signal webhook update (mark signal received)
# Inside /signal-webhook:
mark_signal_received(symbol)  # Add this when signal is processed

# ✅ Reminder function
def daily_signal_check():
    if not has_signal_today():
        app.bot.send_message(chat_id=os.getenv("CHAT_ID"), text="⚠️ No signals were sent today. Please review system.")

# ✅ Scheduler
scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(daily_signal_check, trigger="cron", hour=23, minute=59)
scheduler.start()
from telegram.ext import CommandHandler
from datetime import datetime, timedelta
import json
import os

GOAL_FILE = "goal.json"

# ✅ Set or update profit goal
async def set_goal(update, context):
    try:
        amount = float(context.args[0])
        days = int(context.args[1])
        start_date = datetime.now().strftime("%Y-%m-%d")

        goal_data = {
            "target_profit": amount,
            "target_days": days,
            "start_date": start_date,
            "daily_profits": []
        }

        with open(GOAL_FILE, "w") as f:
            json.dump(goal_data, f)

        await update.message.reply_text(f"✅ Goal set: ${amount} in {days} days starting from {start_date}")
    except Exception as e:
        await update.message.reply_text("❌ Usage: /setgoal 650 10")

# ✅ Add daily profit
async def add_profit(update, context):
    try:
        profit = float(context.args[0])
        today = datetime.now().strftime("%Y-%m-%d")

        if not os.path.exists(GOAL_FILE):
            await update.message.reply_text("⚠️ No goal set. Use /setgoal first.")
            return

        with open(GOAL_FILE, "r") as f:
            goal_data = json.load(f)

        goal_data["daily_profits"].append({"date": today, "amount": profit})

        with open(GOAL_FILE, "w") as f:
            json.dump(goal_data, f)

        await update.message.reply_text(f"✅ Profit added: ${profit} on {today}")
    except:
        await update.message.reply_text("❌ Usage: /profit 130")

# ✅ Check progress
async def check_goal(update, context):
    if not os.path.exists(GOAL_FILE):
        await update.message.reply_text("⚠️ No goal set.")
        return

    with open(GOAL_FILE, "r") as f:
        goal_data = json.load(f)

    total_profit = sum([p["amount"] for p in goal_data["daily_profits"]])
    days_passed = (datetime.now() - datetime.strptime(goal_data["start_date"], "%Y-%m-%d")).days + 1
    target_days = goal_data["target_days"]
    target_profit = goal_data["target_profit"]

    msg = (
        f"🎯 **Goal Progress**\n"
        f"Target: ${target_profit} in {target_days} days\n"
        f"Elapsed: {days_passed} days\n"
        f"Current Profit: ${total_profit}\n"
        f"Remaining: ${round(target_profit - total_profit, 2)}"
    )
    await update.message.reply_text(msg)

# ✅ Register handlers
app.add_handler(CommandHandler("setgoal", set_goal))
app.add_handler(CommandHandler("profit", add_profit))
app.add_handler(CommandHandler("goal", check_goal))
# ✅ Cutubka 25 – Bot Final Test Mode Script

from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os

# ✅ /start command – activate all
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 Welcome to *Hussein7 TradeBot*!\n\n"
        "✅ I am now online and monitoring markets.\n"
        "📊 You can send signals, test commands, or trigger webhooks.\n\n"
        "Try using:\n"
        "/notify – test alert\n"
        "/profits – view log\n"
        "/halalonly – toggle halal coins\n"
        "/autotrade – toggle auto trade\n"
        "/withdraw_eth – send ETH\n"
        "/report – get daily PDF\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ✅ Callback handler for signal buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("CONFIRM"):
        parts = query.data.split(":")
        symbol = parts[1]
        direction = parts[2]
        await query.edit_message_text(f"✅ Trade confirmed for {symbol} – {direction}")
    elif query.data == "IGNORE":
        await query.edit_message_text("❌ Signal ignored.")

# ✅ Notify test signal
async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚨 Test Signal\nPair: EURUSD\nTime: 5min\nDirection: BUY"

    buttons = [[
        InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM:EURUSD:BUY"),
        InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
    ]]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(msg, reply_markup=markup)

# ✅ Add command handlers to app
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("notify", notify))
app.add_handler(CallbackQueryHandler(button_handler))

# ✅ Reminder: Run everything at the end
if __name__ == "__main__":
    import asyncio
    asyncio.run(run())  # Start webhook
    flask_app.run(host="0.0.0.0", port=10000)
# ✅ CUTUBKA 26 – Auto Report Export to Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import atexit

# ✅ Jadwalka (report export @ 23:59 daily)
scheduler = BackgroundScheduler(timezone="Africa/Nairobi")

# ✅ Google Sheets Setup
def log_profit_to_google(amount: float, market: str, date=None):
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("Hussein7_Profit_Log").sheet1
        sheet.append_row([date, market.upper(), f"${amount}"])
        print("✅ Profit logged to Google Sheets")
    except Exception as e:
        print(f"Google Sheets Error: {e}")

# ✅ Jadwalka: 23:59 habeen kasta
@scheduler.scheduled_job("cron", hour=23, minute=59)
def daily_report_scheduler():
    # Tusaale xog been ah – waxaad u badali kartaa xogta dhabta ah ee PDF ka imaneyso
    log_profit_to_google(amount=97.5, market="forex")

# ✅ Bilow Scheduler
scheduler.start()
atexit.register(lambda: scheduler.shutdown())
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_profit_to_google(83.3, "crypto")
    await update.message.reply_text("📊 Report has been sent to Google Sheets!")

app.add_handler(CommandHandler("report", report))
# ✅ CHART IMAGE GENERATOR (Cutubka 27)
import matplotlib.pyplot as plt
import io
import datetime
from PIL import Image
from telegram import InputMediaPhoto

# ⬇️ Mock chart data generator (real data comes from TradingView, Binance API, etc.)
def generate_mock_chart(symbol, direction="BUY"):
    now = datetime.datetime.now()
    times = [now - datetime.timedelta(minutes=i*5) for i in range(20)][::-1]
    prices = [1.1000 + (i * 0.0005 if direction == "BUY" else -i * 0.0005) for i in range(20)]

    plt.figure(figsize=(8, 4))
    plt.plot(times, prices, marker='o', color='green' if direction == "BUY" else 'red')
    plt.title(f"{symbol} – {direction}")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # Save to memory
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return buf

# ⬇️ Send chart image with message (Telegram)
async def send_trade_chart(symbol, direction, context, chat_id):
    try:
        chart_image = generate_mock_chart(symbol, direction)
        await context.bot.send_photo(chat_id=chat_id, photo=chart_image, caption=f"📊 {symbol} – {direction} Chart")
    except Exception as e:
        print(f"Chart Error: {e}")
# Markaad signal dirayso, kudar sawirka
await send_trade_chart("EURUSD", "BUY", context, update.effective_chat.id)
import json
import os
from datetime import datetime

# ✅ FAYLKA TAARIIKHDA
HISTORY_FILE = "trade_history.json"

# ✅ Helper: Load history
def load_trade_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as file:
        return json.load(file)

# ✅ Helper: Save history
def save_trade_history(history):
    with open(HISTORY_FILE, "w") as file:
        json.dump(history, file, indent=2)

# ✅ Add new trade result
def log_trade(symbol, direction, result, profit=0.0, market="forex"):
    history = load_trade_history()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "direction": direction,
        "result": result,  # "TP" or "SL"
        "profit": profit,
        "market": market
    }
    history.append(entry)
    save_trade_history(history)

# ✅ Win Rate & Stats
def get_trade_stats():
    history = load_trade_history()
    if not history:
        return "❌ No trade history available."

    total = len(history)
    wins = sum(1 for trade in history if trade["result"].upper() == "TP")
    losses = sum(1 for trade in history if trade["result"].upper() == "SL")
    win_rate = round((wins / total) * 100, 2)

    summary = f"""
📊 Trade Performance Summary
-----------------------------
✅ Total Trades: {total}
🏆 Wins (TP): {wins}
❌ Losses (SL): {losses}
📈 Win Rate: {win_rate}%
-----------------------------
"""
    return summary.strip()

# ✅ Command: /stats
from telegram.ext import CommandHandler

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = get_trade_stats()
    await update.message.reply_text(summary)

app.add_handler(CommandHandler("stats", stats_command))

# ✅ Tusaale: Marka TP ama SL la xaqiijiyo
# log_trade("EURUSD", "BUY", "TP", profit=70.5)
# log_trade("BTCUSDT", "SELL", "SL", profit=-45.2)
# ✅ Cutubka 28 – TradingView Webhook JSON Signal Handler (Forex/Crypto/Stocks)

from flask import request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

@flask_app.route('/tradingview-alert', methods=['POST'])
def tradingview_alert():
    try:
        data = request.get_json()

        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")

        # Optional fields
        sl = data.get("sl", "N/A")
        tp = data.get("tp", "N/A")
        reason = data.get("reason", "No reason provided.")

        message = f"""🚨 <b>{market.upper()} Trade Signal</b>
📈 Symbol: <code>{symbol}</code>
🕒 Timeframe: <code>{timeframe}</code>
📍 Direction: <b>{direction}</b>
🎯 TP: <code>{tp}</code> | 🛑 SL: <code>{sl}</code>
💬 Reason: <i>{reason}</i>"""

        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode='HTML')

        return "✅ Alert received and sent to Telegram."
    except Exception as e:
        print(f"Webhook Error: {e}")
        return f"❌ Error: {str(e)}"
# ✅ Cutubka 29 – Notion P&L Dashboard Sync

import requests
import datetime
import os

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ✅ Function to log daily profit to Notion
def log_profit_to_notion(date: str, profit: float):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Date": {
                "date": {"start": date}
            },
            "Profit": {
                "number": profit
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200 or response.status_code == 201:
        print("✅ Profit logged to Notion.")
    else:
        print(f"❌ Notion logging error: {response.text}")

# ✅ Example command to trigger from bot (/profit_notion 120)
from telegram.ext import CommandHandler

async def profit_notion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        date = datetime.date.today().isoformat()
        log_profit_to_notion(date, amount)
        await update.message.reply_text(f"✅ Profit ${amount} logged to Notion.")
    except:
        await update.message.reply_text("❌ Usage: /profit_notion 120")

app.add_handler(CommandHandler("profit_notion", profit_notion))
# ✅ Cutubka 30 – Voice Reminder if No Trade Taken

import asyncio
import datetime
from gtts import gTTS
import tempfile
import os

# Path to track daily trade activity
TRADE_LOG_FILE = "daily_trade_log.txt"

# ✅ Call this whenever a trade is confirmed
def log_trade_today():
    today = datetime.date.today().isoformat()
    with open(TRADE_LOG_FILE, "a") as f:
        f.write(f"{today}\n")

# ✅ Check if a trade was taken today
def trade_taken_today():
    today = datetime.date.today().isoformat()
    if not os.path.exists(TRADE_LOG_FILE):
        return False
    with open(TRADE_LOG_FILE, "r") as f:
        lines = f.read().splitlines()
    return today in lines

# ✅ Send voice reminder if no trade was taken
async def remind_if_no_trade(context):
    chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
    if not trade_taken_today():
        text = "Ma jiraan wax trade ah oo aad qaaday maanta. Fadlan dib u eeg suuqyada!"
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tts_path = tmp.name + ".mp3"
            tts.save(tts_path)
        with open(tts_path, "rb") as audio:
            await context.bot.send_voice(chat_id=chat_id, voice=audio)
        os.remove(tts_path)

# ✅ Scheduler at 23:30 daily
import schedule

def setup_reminder_job(app_context):
    def wrapper():
        asyncio.run(remind_if_no_trade(app_context))
    schedule.every().day.at("23:30").do(wrapper)

# ✅ Add to your main loop to trigger schedule
def schedule_loop():
    while True:
        schedule.run_pending()
        time.sleep(30)
# ✅ Cutubka 31 – Auto Trade Toggle + Execution Execution

from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import os

# Auto mode status
auto_trade_enabled = False

# ✅ Toggle Command
async def toggle_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = "✅ AutoTrade ON" if auto_trade_enabled else "❌ AutoTrade OFF"
    await update.message.reply_text(f"{status}")

# ✅ Command handler
app.add_handler(CommandHandler("autotrade", toggle_autotrade))

# ✅ Execution Function
def execute_trade(symbol: str, direction: str, market: str):
    if not auto_trade_enabled:
        print("AutoTrade is OFF. Skipping execution.")
        return

    print(f"🟢 Executing trade → {market.upper()} | {symbol} | {direction}")
    # Placeholder: Add your API/broker call here (e.g., MetaTrader, TradingView broker, Exchange)

    # Log or notify
    app.bot.send_message(
        chat_id=os.getenv("CHAT_ID", "YOUR_CHAT_ID"),
        text=f"✅ AutoTrade Executed\nMarket: {market}\nPair: {symbol}\nDirection: {direction}"
    )
import json
import os
from telegram import Update
from telegram.ext import CallbackContext

CONFIRM_LOG_FILE = "confirmed_signals.json"

def log_signal(action, symbol, direction):
    signal = {
        "action": action,
        "symbol": symbol,
        "direction": direction,
        "timestamp": str(datetime.datetime.now())
    }

    if not os.path.exists(CONFIRM_LOG_FILE):
        with open(CONFIRM_LOG_FILE, "w") as f:
            json.dump([], f)

    with open(CONFIRM_LOG_FILE, "r+") as f:
        logs = json.load(f)
        logs.append(signal)
        f.seek(0)
        json.dump(logs, f, indent=2)

async def confirm_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        _, symbol, direction = query.data.split(":")
        log_signal("CONFIRMED", symbol, direction)
        await query.edit_message_text(f"✅ Signal Confirmed: {symbol} - {direction}")
    except Exception as e:
        await query.edit_message_text("⚠️ Invalid confirmation data")

async def ignore_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        log_signal("IGNORED", "N/A", "N/A")
        await query.edit_message_text("❌ Signal Ignored.")
    except Exception as e:
        await query.edit_message_text("⚠️ Failed to ignore signal")
from confirm_ignore_handler import confirm_callback, ignore_callback
from telegram.ext import CallbackQueryHandler

app.add_handler(CallbackQueryHandler(confirm_callback, pattern="^CONFIRM:"))
app.add_handler(CallbackQueryHandler(ignore_callback, pattern="^IGNORE$"))
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import tempfile

def generate_chart(symbol, interval="1d", days_back=5):
    try:
        # Download historical data
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days_back)
        df = yf.download(symbol, start=start_date, end=end_date, interval=interval)

        if df.empty:
            return None

        fig, ax = plt.subplots()
        df["Close"].plot(ax=ax, title=f"{symbol.upper()} Chart ({interval})")
        ax.set_ylabel("Price")
        ax.grid(True)

        # Save image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            image_path = tmpfile.name
            plt.savefig(image_path)
            plt.close(fig)
            return image_path

    except Exception as e:
        print(f"Chart generation failed: {e}")
        return None
from chart_generator import generate_chart

# Inside your webhook or notify logic
symbol = "AAPL"  # or BTC-USD, ETH-USD
interval = "5m" if market == "crypto" else "1d"
image_path = generate_chart(symbol, interval=interval)

if image_path:
    context.bot.send_photo(chat_id=chat_id, photo=open(image_path, "rb"))
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import tempfile

# Sample function for generating chart image (sample data used here)
def generate_chart_image(symbol="BTCUSD", data=None):
    if data is None:
        # Sample data: 10 candles
        now = datetime.datetime.now()
        data = pd.DataFrame({
            "time": [now - datetime.timedelta(minutes=5*i) for i in range(10)][::-1],
            "open": [100 + i for i in range(10)],
            "high": [102 + i for i in range(10)],
            "low": [99 + i for i in range(10)],
            "close": [101 + i for i in range(10)],
            "volume": [1000 + i*10 for i in range(10)]
        })

    fig, ax = plt.subplots(figsize=(8, 4))

    for idx, row in data.iterrows():
        color = 'green' if row['close'] >= row['open'] else 'red'
        ax.plot([row['time'], row['time']], [row['low'], row['high']], color=color)
        ax.plot([row['time'], row['time']], [row['open'], row['close']], color=color, linewidth=5)

    ax.set_title(f"{symbol} Chart")
    ax.set_ylabel("Price")
    ax.set_xticks([])

    # Save to temporary file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.tight_layout()
    plt.savefig(tmp.name)
    plt.close(fig)

    return tmp.name
from chart_generator import generate_chart_image

async def send_chart(update, context):
    symbol = "BTCUSD"  # You can customize this based on signal
    chart_path = generate_chart_image(symbol)
    with open(chart_path, "rb") as img:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)
from telegram.ext import CommandHandler
app.add_handler(CommandHandler("chart", send_chart))
img_path = generate_chart_image("ETHUSD", eth_data)
bot.send_photo(chat_id=chat_id, photo=open(img_path, "rb"))

# ✅ Run Flask thread + bot
def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()
app.run_polling()

# ✅ Run bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("profit", add_profit))
app.add_handler(CommandHandler("profits", view_profits))
app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))
app.add_handler(CommandHandler("autotrade", toggle_auto_trade))

if __name__ == '__main__':
    app.run_polling()
