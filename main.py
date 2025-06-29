 # ✅ Cutubka 1 – Hussein7 TradeBot Initialization + /start + /help + Admin Checker

import os
import logging
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ✅ Bot Token from .env or hardcoded (for dev)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

# ✅ Admin list (add your Telegram ID here)
ADMINS = [123456789]  # Change to your actual Telegram user ID

# ✅ Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ✅ Bot app object
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ /start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_msg = (
        f"👋 Salaam {user.first_name},\n\n"
        "Ku soo dhawoow *Hussein7 TradeBot* 📊🤖\n\n"
        "✅ Forex Signals\n"
        "✅ Crypto Alerts\n"
        "✅ Stock Opportunities\n"
        "✅ Memecoin Webhook Detector\n\n"
        "Isticmaal `/help` si aad u aragto amarrada oo dhan."
    )
    await update.message.reply_markdown(welcome_msg)

# ✅ /help Command
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *Walalka Tradebot Activated!*\n\n"
        "Welcome to your personal AI trading assistant.\n\n"
        "📌 Use these commands to begin:\n"
        "/forex – Forex trade ideas\n"
        "/crypto – Crypto signals\n"
        "/stocks – Stock updates\n"
        "/memecoins – Memecoin alerts\n"
        "/polymarket – Polymarket insights\n"
        "/halalonly – Toggle Halal Coin Filter\n"
        "/profit – Log daily profit\n"
        "/withdraw_eth – Auto withdraw ETH\n"
        "/autotrade – Toggle Auto-Trade\n"
        "/report – Get daily PDF report\n"
        "\n🚀 Let's grow your capital together!"
    )
    await update.message.reply_markdown(welcome_text)

# ✅ Add handler to your application
app.add_handler(CommandHandler("start", start_command))

# ✅ Admin Checker (can be used for any admin-only command)
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS
# ✅ Cutubka 2: Profit Logger System
from telegram.ext import CommandHandler
from datetime import datetime
import json
import os

# Faylka loo keydiyo profits
PROFIT_FILE = "profits.json"

# ✅ Fuction: Save daily profit
def save_profit(amount):
    today = datetime.now().strftime("%Y-%m-%d")
    profits = load_profits()
    profits[today] = profits.get(today, 0) + amount
    with open(PROFIT_FILE, "w") as f:
        json.dump(profits, f)

# ✅ Fuction: Load profits
def load_profits():
    if not os.path.exists(PROFIT_FILE):
        return {}
    with open(PROFIT_FILE, "r") as f:
        return json.load(f)

# ✅ Command: /profit 100
async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        save_profit(amount)
        await update.message.reply_text(f"✅ Profit of ${amount} saved for today.")
    except (IndexError, ValueError):
        await update.message.reply_text("❗ Usage: /profit 120.5")

# ✅ Command: /profits
async def show_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profits = load_profits()
    if not profits:
        await update.message.reply_text("📭 No profit records found.")
        return

    msg = "📊 Daily Profit Log:\n"
    total = 0
    for date, amount in sorted(profits.items()):
        msg += f"{date}: ${amount:.2f}\n"
        total += amount
    msg += f"\n💰 Total: ${total:.2f}"
    await update.message.reply_text(msg)
# ✅ Cutubka 3: Forex Trade Signal Generator
from telegram.ext import CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ✅ Forex trade idea sender
async def send_forex_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Forex signal example
    pair = "EURUSD"
    direction = "BUY"
    entry = 1.0950
    tp = 1.1000
    sl = 1.0910

    # Halal label (optional, from Cutub 9)
    halal_status = "🟢 Halal"

    msg = (
        f"📈 Forex Trade Alert\n"
        f"Pair: {pair}\n"
        f"Direction: {direction}\n"
        f"Entry: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n"
        f"Status: {halal_status}"
    )

    # Buttons: Confirm or Ignore
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data="FOREX_CONFIRM")],
        [InlineKeyboardButton("❌ Ignore", callback_data="FOREX_IGNORE")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(msg, reply_markup=reply_markup)
# ✅ Cutubka 4: AutoTrade ON/OFF Toggle
from telegram.ext import CommandHandler

# ✅ Global variable to hold autotrade status
auto_trade_enabled = False

# ✅ Command to toggle autotrade
async def toggle_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = "✅ AutoTrade Mode is ON" if auto_trade_enabled else "❌ AutoTrade Mode is OFF"
    await update.message.reply_text(status)

# ✅ Function to check if autotrade is on
def is_autotrade_on() -> bool:
    return auto_trade_enabled
# 📁 webhook.py

from telegram import Update
from telegram.ext import ContextTypes
from flask import request

# ✅ Telegram Webhook Handler
# This function will be called by Flask when webhook receives POST
async def telegram_webhook_handler(app, update_json):
    try:
        update = Update.de_json(update_json, app.bot)
        await app.process_update(update)
        return "OK"
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return f"ERROR: {str(e)}"

# 🧠 Sida loogu daro main.py
# Ku dar route-kan hoosta Flask app-kaaga
# Waxa uu isticmaalaa handler-ka kore si uu nadiif u ahaado main.py
from flask import Flask
from webhook import telegram_webhook_handler

flask_app = Flask(__name__)

@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    return await telegram_webhook_handler(app, request.get_json(force=True))
from flask import request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os

# Optional halal filter function (use in crypto only)
def is_coin_halal(symbol: str) -> bool:
    haram_keywords = ["casino", "gambling", "loan", "riba", "liquor", "alcohol"]
    return not any(word in symbol.lower() for word in haram_keywords)

@flask_app.route('/signal-webhook', methods=['POST'])
def signal_webhook():
    try:
        data = request.get_json()

        # Extract fields from incoming JSON
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")
        sl = data.get("stop_loss", "N/A")
        tp = data.get("take_profit", "N/A")

        # Halal status for crypto
        halal_status = ""
        if market.lower() == "crypto":
            halal_status = "🟢 Halal" if is_coin_halal(symbol) else "🔴 Haram"

        # Construct message
        message = (
            f"🚨 New {market.upper()} Signal\n"
            f"Pair: {symbol}\n"
            f"Timeframe: {timeframe}\n"
            f"Direction: {direction}\n"
            f"TP: {tp}\nSL: {sl}\n"
            f"{halal_status}"
        )

        # Buttons for confirmation
        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Send message to Telegram chat
        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

        return "✅ Signal sent to Telegram"
    except Exception as e:
        return f"❌ Webhook error: {str(e)}"
from telegram.constants import ChatAction
from gtts import gTTS
import tempfile
import os

# Voice Alert Function
async def send_voice_alert(text: str, context, chat_id: str):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp:
            tts.save(tmp.name)
            with open(tmp.name, "rb") as audio:
                await context.bot.send_voice(chat_id=chat_id, voice=audio)
    except Exception as e:
        print(f"Voice Alert Error: {e}")
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# ✅ Halal Only Mode toggle state
halal_only_mode = False

# ✅ Toggle command: /halalonly
async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode is ON — Only halal coins will be shown." if halal_only_mode else "❌ Halal Only Mode is OFF — All coins will be shown."
    await update.message.reply_text(status)

# ✅ Coin checker function (simple haram keyword filter)
def is_coin_halal(symbol: str) -> bool:
    haram_keywords = ["casino", "gambling", "loan", "riba", "liquor", "alcohol", "beer"]
    return not any(word in symbol.lower() for word in haram_keywords)
import os
from decimal import Decimal

# ✅ Read from environment or fallback
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))      # Total account balance
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))         # Daily risk limit (e.g., 5% of $5,000 = $250)

# ✅ Function: Calculate lot size based on SL pips and pip value
def calculate_lot_size(sl_distance_pips: float, pip_value: float = 10.0) -> float:
    if sl_distance_pips == 0:
        return 0.0  # Avoid division by zero
    risk_per_trade = DAILY_MAX_RISK
    lot_size = (risk_per_trade / Decimal(sl_distance_pips)) / Decimal(pip_value)
    return round(float(lot_size), 2)
from flask import Flask, request
from telegram import Update
import asyncio

from telegram.ext import ApplicationBuilder

# ✅ Flask app + Telegram bot
flask_app = Flask(__name__)

# ✅ Telegram bot setup
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Home route (for Render)
@flask_app.route('/')
def home():
    return "✅ Hussein7 TradeBot is live!"

# ✅ Telegram webhook handler
@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await app.process_update(update)
    return "OK"

# ✅ Signal webhook endpoint (for JSON signals from TradingView, Notion, etc.)
@flask_app.route('/signal-webhook', methods=["POST"])
def signal_webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")

        message = f"🚨 New {market.upper()} Signal\nPair: {symbol}\nTime: {timeframe}\nDirection: {direction}"
        
        # Optional: add button handler here

        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message)
        return "Signal Sent"
    except Exception as e:
        return f"Webhook error: {str(e)}"

# ✅ Start webhook on boot
async def run():
    await app.bot.set_webhook(url=os.getenv("WEBHOOK_URL"))

if __name__ == "__main__":
    asyncio.run(run())
    flask_app.run(host="0.0.0.0", port=10000)
from gtts import gTTS
from telegram.constants import ChatAction
import tempfile
import os

# ✅ Voice Alert Function
async def send_voice_alert(text, context, chat_id):
    try:
        # Show user that bot is recording
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)

        # Create TTS audio
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tts.save(tmp_file.name)
            with open(tmp_file.name, 'rb') as audio:
                await context.bot.send_voice(chat_id=chat_id, voice=audio)
        os.remove(tmp_file.name)
    except Exception as e:
        print(f"Voice Alert Error: {e}")
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from telegram import Update

# ✅ Halal Filter State (global)
halal_only_mode = False

# ✅ Halal/Haram Checker
def is_coin_halal(name: str) -> bool:
    haram_keywords = ["casino", "gambling", "riba", "loan", "liquor", "beer", "alcohol", "porn", "sex", "pepe"]
    return not any(x in name.lower() for x in haram_keywords)

# ✅ /halalonly toggle command
async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode ON" if halal_only_mode else "❌ Halal Only Mode OFF"
    await update.message.reply_text(status)

# ✅ Memecoin Signal Handler (Webhook-style)
async def send_memecoin_signal(context: ContextTypes.DEFAULT_TYPE, coin_data: dict):
    name = coin_data.get("name", "Unknown")
    address = coin_data.get("address", "N/A")
    chain = coin_data.get("chain", "Solana")
    reason = coin_data.get("reason", "🚀 Social spike")
    chart_url = coin_data.get("chart", "https://dexscreener.com/")

    # Halal filter check
    if halal_only_mode and not is_coin_halal(name):
        return

    status = "🟢 Halal" if is_coin_halal(name) else "🔴 Haram"

    msg = f"🚨 *New Memecoin Detected!*\n\n💎 *{name}*\n🔗 Chain: {chain}\n🪙 Address: `{address}`\n📈 Reason: {reason}\n🔍 Status: {status}\n📊 Chart: {chart_url}"

    buttons = [[
        InlineKeyboardButton("📈 View Chart", url=chart_url),
        InlineKeyboardButton("📥 Copy Address", callback_data=f"copy:{address}")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)

    chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
    await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup, parse_mode="Markdown")
from web3 import Web3
from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
import os

# ✅ Setup Web3 connection (Infura)
INFURA_URL = os.getenv("INFURA_URL")
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ Wallet details
BOT_WALLET = os.getenv("WALLET_ADDRESS_ETH")
BOT_PRIVATE_KEY = os.getenv("PRIVATE_KEY_ETH")
WITHDRAW_TO = os.getenv("WITHDRAW_TO", "0xReceiverWalletAddressHere")

# ✅ /withdraw_eth command
async def withdraw_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sender_address = BOT_WALLET
        receiver_address = WITHDRAW_TO

        # ✅ Check balance
        balance = w3.eth.get_balance(sender_address)
        eth_balance = w3.from_wei(balance, 'ether')

        if eth_balance < 0.002:
            await update.message.reply_text("❌ Not enough ETH to withdraw. Minimum 0.002 ETH required.")
            return

        # ✅ Prepare transaction
        nonce = w3.eth.get_transaction_count(sender_address)
        gas_price = w3.eth.gas_price
        value = balance - (21000 * gas_price)  # Leave enough for gas

        tx = {
            'nonce': nonce,
            'to': receiver_address,
            'value': value,
            'gas': 21000,
            'gasPrice': gas_price,
        }

        # ✅ Sign + send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=BOT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        await update.message.reply_text(f"✅ ETH Withdrawn\n🔗 TX Hash: {w3.to_hex(tx_hash)}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error during withdrawal: {str(e)}")
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from telegram import Update
from gtts import gTTS
import tempfile
import os

# ✅ Cod kala duwan oo loogu talagalay TP (guul) iyo SL (khasaaro)
def get_voice_text(status):
    if status == "TP":
        return "Congratulations! Take Profit hit! 💰"
    elif status == "SL":
        return "Stop Loss hit. Wax meynas galay... 😢"
    else:
        return "New signal alert."

# ✅ Voice alert function
async def send_result_voice(status: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        text = get_voice_text(status)

        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tts.save(tmp.name + ".mp3")
            with open(tmp.name + ".mp3", "rb") as audio_file:
                await context.bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        print(f"[Voice Alert Error]: {e}")
import requests
import os

# ✅ URL-ka push app webhook (ka ku qor .env file)
PUSH_APP_WEBHOOK_URL = os.getenv("PUSH_APP_WEBHOOK_URL")

# ✅ Function: Dir push notification (text only)
def send_push_notification(message: str) -> str:
    try:
        if not PUSH_APP_WEBHOOK_URL:
            raise ValueError("PUSH_APP_WEBHOOK_URL not set.")

        payload = {
            "title": "📢 Hussein7 Trade Alert",
            "message": message
        }

        response = requests.post(PUSH_APP_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            return "✅ Push sent"
        else:
            return f"❌ Push failed: {response.text}"
    except Exception as e:
        return f"[Push Error]: {e}"
from fpdf import FPDF
import os
from datetime import datetime
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

# ✅ Folder-ka warbixinada
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# ✅ Diiwaanka ganacsiyada maalinlaha ah
trade_log = []

# ✅ Function: Abuur report PDF
def generate_daily_report(trades: list):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{REPORTS_DIR}/TradeReport_{today}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"📄 Trade Report – {today}", ln=True, align="C")
    pdf.ln(10)

    for i, trade in enumerate(trades, 1):
        text = (
            f"{i}. Pair: {trade['symbol']}\n"
            f"   Direction: {trade['direction']}\n"
            f"   Timeframe: {trade['timeframe']}\n"
            f"   Result: {trade['result']}\n"
            f"   P&L: {trade['pnl']}\n"
        )
        pdf.multi_cell(0, 10, txt=text)
        pdf.ln(2)

    pdf.output(filename)
    return filename

# ✅ Telegram command: /report
async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trade_log:
        await update.message.reply_text("Ma jiro trade maanta la qaaday.")
        return

    file_path = generate_daily_report(trade_log)
    with open(file_path, "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=file_path)

app.add_handler(CommandHandler("report", send_report))

# ✅ Jadwal: Automatic report 23:59 habeenkii
scheduler = BackgroundScheduler()

def daily_report_job():
    if trade_log:
        path = generate_daily_report(trade_log)
        # Optional: send to Telegram or email (add logic here)

scheduler.add_job(daily_report_job, "cron", hour=23, minute=59)
scheduler.start()
import requests
from datetime import datetime
import os

# ✅ ENV Variables
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def push_trade_to_notion(symbol, direction, timeframe, result, pnl):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Date": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
            "Symbol": {
                "title": [{"text": {"content": symbol}}]
            },
            "Direction": {
                "rich_text": [{"text": {"content": direction}}]
            },
            "Timeframe": {
                "rich_text": [{"text": {"content": timeframe}}]
            },
            "Result": {
                "rich_text": [{"text": {"content": result}}]
            },
            "P&L": {
                "number": float(pnl)
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("❌ Notion Push Failed:", response.text)
    else:
        print("✅ Trade pushed to Notion.")

# ✅ Example usage
# push_trade_to_notion("EURUSD", "BUY", "5min", "WIN", 150.25)
# ✅ Halal/Haram Coin Detector (Advanced)
import re

# Liiska erayada haramta ah
HARAM_KEYWORDS = [
    "casino", "bet", "gambling", "poker", "lottery", "loan", "riba", "interest",
    "liquor", "alcohol", "wine", "beer", "vodka", "whiskey", "xxx", "sex", "porn",
    "shisha", "cigarette", "hookah", "rum", "cocktail", "drunk", "bar"
]

# ✅ Function: go'aami haddii coin uu halal yahay iyadoo la eegayo magaca + sharaxaadiisa
def is_coin_halal_advanced(name: str, description: str = "") -> bool:
    combined_text = f"{name} {description}".lower()
    for haram_word in HARAM_KEYWORDS:
        if re.search(rf"\b{haram_word}\b", combined_text):
            return False
    return True

# ✅ Tusaale Isticmaal (console test)
coin_name = "LuckyBetToken"
coin_description = "A high-volume gambling dApp token"

status = "🟢 Halal" if is_coin_halal_advanced(coin_name, coin_description) else "🔴 Haram"
print(f"Token: {coin_name} → Status: {status}")

def send_signal_to_telegram(coin_name, coin_description, price, chart_url):
    if halal_only_mode:
        if not is_coin_halal_advanced(coin_name, coin_description):
            print(f"🚫 Coin-ka {coin_name} ma aha halal. Signal lama dirin.")
            return  # Ha dirin haddii coin-ku haram yahay marka toggle ON

    message = f"🚀 {coin_name}\nPrice: ${price}\nChart: {chart_url}"
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

msg = f"🚨 {coin_name} Opportunity\nStatus: {'🟢 Halal' if is_coin_halal_advanced(coin_name, coin_description) else '🔴 Haram'}"
await context.bot.send_message(chat_id=chat_id, text=msg)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

# ✅ Global state
halal_only_mode = False

# ✅ Command: /halalonly – toggle button ON/OFF
async def toggle_halal_only(update: Update, context: CallbackContext):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "🟢 Halal Only Mode ENABLED" if halal_only_mode else "🔴 Halal Only Mode DISABLED"
    await update.message.reply_text(status)

# ✅ Coin Checker Function (reuse from Cutubka 19)
def is_coin_halal(name: str, description: str = "") -> bool:
    haram_keywords = [
        "casino", "bet", "gambling", "poker", "lottery", "loan", "riba", "interest",
        "liquor", "alcohol", "wine", "beer", "vodka", "whiskey", "xxx", "sex", "porn",
        "shisha", "cigarette", "hookah", "rum", "cocktail", "drunk", "bar"
    ]
    full = f"{name} {description}".lower()
    return not any(word in full for word in haram_keywords)

# ✅ Use this in memecoin signal webhook
def send_coin_signal(coin_name, description, context, chat_id):
    global halal_only_mode

    if halal_only_mode and not is_coin_halal(coin_name, description):
        print(f"🔴 Skipped haram coin: {coin_name}")
        return  # Ha dirin haddii haram yahay

    msg = f"🚨 Memecoin Alert: {coin_name}\nStatus: {'🟢 Halal' if is_coin_halal(coin_name, description) else '🔴 Haram'}"
    buttons = [[
        InlineKeyboardButton("✅ Buy Now", callback_data=f"BUY:{coin_name}"),
        InlineKeyboardButton("🚫 Skip", callback_data="SKIP")
    ]]
    markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=markup)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

# ✅ Global state
hidden_markets = set()

# ✅ Toggle Market Visibility
async def toggle_market_visibility(update: Update, context: CallbackContext):
    markets = ["Forex", "Crypto", "Stocks", "Polymarket", "Memecoins"]
    buttons = []

    for mkt in markets:
        is_hidden = mkt.lower() in hidden_markets
        label = f"{'❌' if is_hidden else '✅'} {mkt}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"TOGGLE_MARKET:{mkt.lower()}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Toggle Market Visibility:", reply_markup=reply_markup)

# ✅ Callback Handler
async def handle_toggle_market_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    if data[0] == "TOGGLE_MARKET":
        market = data[1]
        if market in hidden_markets:
            hidden_markets.remove(market)
            await query.edit_message_text(f"✅ {market.capitalize()} market is now **VISIBLE**.")
        else:
            hidden_markets.add(market)
            await query.edit_message_text(f"❌ {market.capitalize()} market is now **HIDDEN**.")

# ✅ Usage in webhook (Forex example)
def send_forex_signal(symbol, direction, context, chat_id):
    if "forex" in hidden_markets:
        print(f"📵 Skipped {symbol} – Forex hidden")
        return
    message = f"📈 Forex Signal: {symbol} → {direction}"
    context.bot.send_message(chat_id=chat_id, text=message)
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, filters

# ✅ Command: /search
async def search_command(update: Update, context: CallbackContext):
    await update.message.reply_text("🔍 Please type the symbol or coin name you want to search.")

# ✅ Text Handler: Receives Search Query
async def handle_search_query(update: Update, context: CallbackContext):
    query = update.message.text.strip().upper()

    # Example fake signal DB
    fake_signals = {
        "EURUSD": {"market": "forex", "dir": "BUY", "tf": "5min"},
        "BTC": {"market": "crypto", "dir": "SELL", "tf": "15min"},
        "TSLA": {"market": "stocks", "dir": "BUY", "tf": "1H"},
        "TRUMP2024": {"market": "polymarket", "dir": "YES", "tf": "Event"},
    }

    if query in fake_signals:
        signal = fake_signals[query]
        message = f"🔍 Found Signal\nMarket: {signal['market'].capitalize()}\nSymbol: {query}\nDirection: {signal['dir']}\nTimeframe: {signal['tf']}"
    else:
        message = f"❌ No signal found for {query}"

    await update.message.reply_text(message)
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# ✅ ICT Filter ON/OFF state
ict_filter_enabled = True

# ✅ Toggle command: /ictfilter
async def toggle_ict_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ict_filter_enabled
    ict_filter_enabled = not ict_filter_enabled
    status = "✅ ICT Filter ENABLED" if ict_filter_enabled else "❌ ICT Filter DISABLED"
    await update.message.reply_text(f"{status}\nOnly high-probability ICT-style Forex trades will be shown.")


# ✅ ICT-style detection logic (very basic sample)
def is_ict_compliant(signal: dict) -> bool:
    """
    Signal example:
    {
        "symbol": "EURUSD",
        "direction": "BUY",
        "timeframe": "5min",
        "market": "forex",
        "liquidity": "grabbed",
        "order_block": True,
        "fvg": True,
        "time": "10:15"
    }
    """
    return (
        signal.get("market") == "forex"
        and signal.get("order_block") is True
        and signal.get("fvg") is True
        and signal.get("liquidity") == "grabbed"
    )


# ✅ Example usage inside signal webhook:
def should_send_signal(signal: dict) -> bool:
    if ict_filter_enabled and signal.get("market") == "forex":
        return is_ict_compliant(signal)
    return True  # send others like crypto/stocks/etc.
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from datetime import datetime, timedelta

# Goal Tracker
GOAL_AMOUNT = 650  # USD
GOAL_DAYS = 10
START_DATE = datetime(2025, 6, 20)
goal_progress = []  # Each element is (date_str, profit)

def calculate_goal_status():
    total_profit = sum(p[1] for p in goal_progress)
    days_passed = (datetime.now() - START_DATE).days + 1
    daily_target = GOAL_AMOUNT / GOAL_DAYS
    projected = days_passed * daily_target
    percent = round((total_profit / GOAL_AMOUNT) * 100, 1)
    return total_profit, projected, percent, days_passed

# ✅ Command: /goal
async def goal_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_profit, projected, percent, days_passed = calculate_goal_status()
    status = (
        f"🎯 *Goal Tracker*\n"
        f"Duration: {GOAL_DAYS} days\n"
        f"Goal: ${GOAL_AMOUNT}\n"
        f"Day: {days_passed}\n"
        f"Progress: ${total_profit:.2f} / ${GOAL_AMOUNT}\n"
        f"Projected by now: ${projected:.2f}\n"
        f"Completion: {percent}%"
    )
    await update.message.reply_text(status, parse_mode="Markdown")

# ✅ Command: /addprofit <amount>
async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        today_str = datetime.now().strftime("%Y-%m-%d")
        goal_progress.append((today_str, amount))
        await update.message.reply_text(f"✅ Added profit: ${amount:.2f}")
    except Exception:
        await update.message.reply_text("❌ Usage: /addprofit 100")
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from datetime import datetime, timedelta

# 🎯 Bartilmaameedka
GOAL_AMOUNT = 650   # Tirada guud ee la rabo ($)
GOAL_DAYS = 10      # Muddada
START_DATE = datetime(2025, 6, 20)  # Waxaad beddeli kartaa bilowga
goal_progress = []  # Liiska waxqabadka: (date_str, amount)

def calculate_goal_status():
    total_profit = sum(p[1] for p in goal_progress)
    days_passed = (datetime.now() - START_DATE).days + 1
    daily_target = GOAL_AMOUNT / GOAL_DAYS
    projected = days_passed * daily_target
    percent = round((total_profit / GOAL_AMOUNT) * 100, 1)
    return total_profit, projected, percent, days_passed

# ✅ Amarka: /goal
async def goal_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_profit, projected, percent, days_passed = calculate_goal_status()
    msg = (
        f"🎯 *Goal Tracker*\n"
        f"Target: ${GOAL_AMOUNT} in {GOAL_DAYS} days\n"
        f"Day: {days_passed}\n"
        f"Profit: ${total_profit:.2f}\n"
        f"Expected so far: ${projected:.2f}\n"
        f"Completion: {percent}%"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ✅ Amarka: /addprofit <amount>
async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        today = datetime.now().strftime("%Y-%m-%d")
        goal_progress.append((today, amount))
        await update.message.reply_text(f"✅ Added ${amount:.2f} to progress.")
    except Exception as e:
        await update.message.reply_text("❌ Usage: /addprofit 120")
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from fpdf import FPDF
from datetime import datetime
import os

# 📊 Ku kaydi profits meel memory ah
daily_profits = []  # Format: [("2025-06-25", 120), ("2025-06-26", 80)]

# ✅ Amarka /profit <lacag>
async def log_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        today = datetime.now().strftime("%Y-%m-%d")
        daily_profits.append((today, amount))
        await update.message.reply_text(f"✅ Profit ${amount} added for {today}")
    except:
        await update.message.reply_text("❌ Usage: /profit 100")

# ✅ Amarka /profits – tus liiska
async def view_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_profits:
        await update.message.reply_text("📭 Ma jiraan wax profit ah wali.")
        return

    msg = "*📈 Daily Profits:*\n\n"
    total = 0
    for date, amt in daily_profits:
        msg += f"- {date}: ${amt:.2f}\n"
        total += amt
    msg += f"\n*Total: ${total:.2f}*"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ✅ Amarka /report – soo saar PDF
async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_profits:
        await update.message.reply_text("📭 Ma jiraan wax profit ah si PDF loogu sameeyo.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="📊 Daily Profit Report", ln=1, align="C")
    pdf.ln(10)

    total = 0
    for date, amt in daily_profits:
        pdf.cell(200, 10, txt=f"{date}: ${amt:.2f}", ln=1)
        total += amt

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"TOTAL PROFIT: ${total:.2f}", ln=1)

    filename = f"profit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)

    with open(filename, "rb") as f:
        await update.message.reply_document(document=f)

    os.remove(filename)
import schedule
import time
from datetime import datetime
from telegram import Bot
import threading

# ✅ Ku keydi signal count
signals_today = 0

# ✅ Markasta signal lasoo diro, ku dar hal
def signal_received():
    global signals_today
    signals_today += 1

# ✅ Reset count @midnight
def reset_signal_count():
    global signals_today
    signals_today = 0

# ✅ Haddii wax signal ah aysan imaanin, bot ha soo diro xasuusin
def check_signals_and_remind():
    if signals_today == 0:
        msg = "📭 Ma jiro signal maanta. Fadlan hubi haddii wax khalad ah jiro ama suuqu xiran yahay."
        bot.send_message(chat_id=os.getenv("CHAT_ID"), text=msg)

# ✅ Jadwal maalinle ah
schedule.every().day.at("23:59").do(check_signals_and_remind)
schedule.every().day.at("00:00").do(reset_signal_count)

# ✅ Jadwal thread
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(30)

# ✅ Samee thread gaar ah
threading.Thread(target=run_schedule, daemon=True).start()

# ✅ Bot access
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
from telegram.ext import CommandHandler, CallbackContext
from telegram import Update
from web3 import Web3
import os

# ✅ Setup Web3
INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY_ETH")
BOT_WALLET_ADDRESS = os.getenv("WALLET_ADDRESS_ETH")
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ ETH Withdrawal Command
async def withdraw_eth(update: Update, context: CallbackContext):
    try:
        target_address = context.args[0]
        amount = float(context.args[1])

        nonce = web3.eth.get_transaction_count(BOT_WALLET_ADDRESS)
        tx = {
            'nonce': nonce,
            'to': target_address,
            'value': web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3.to_wei('20', 'gwei')
        }

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        await update.message.reply_text(f"✅ ETH withdrawal sent!\nTransaction: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ✅ Balance Check Command
async def eth_balance(update: Update, context: CallbackContext):
    try:
        balance = web3.eth.get_balance(BOT_WALLET_ADDRESS)
        eth = web3.from_wei(balance, 'ether')
        await update.message.reply_text(f"💰 Current ETH balance: {eth} ETH")
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking balance: {str(e)}")
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# Temporary memory (RAM-based)
user_wallets = {}

# ✅ /wallet ETH 0x123... | /wallet SOL yourSolAddress
async def set_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("💡 Isticmaal sidaan: /wallet ETH 0xYourWallet\nAma: /wallet SOL YourSolAddress")
        return

    chain, address = args
    if chain.upper() not in ["ETH", "SOL"]:
        await update.message.reply_text("❌ Fadlan dooro ETH ama SOL oo kaliya.")
        return

    user_wallets[user_id] = {"chain": chain.upper(), "address": address}
    await update.message.reply_text(f"✅ Wallet-kaaga {chain.upper()} waa la keydiyay: {address}")

# ✅ /mywallet – View stored wallet
async def view_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = user_wallets.get(user_id)

    if not wallet:
        await update.message.reply_text("❌ Wallet weli lama keydin. Isticmaal /wallet si aad u geliso.")
    else:
        await update.message.reply_text(f"👛 Wallet: {wallet['address']} ({wallet['chain']})")
import json
import os
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

WALLET_FILE = "user_wallets.json"

# ✅ Load wallets from file
def load_wallets():
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, "r") as f:
            return json.load(f)
    return {}

# ✅ Save wallets to file
def save_wallets(data):
    with open(WALLET_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Load existing wallets at startup
user_wallets = load_wallets()

# ✅ /wallet ETH 0x123...
async def set_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("💡 Isticmaal sidaan: /wallet ETH 0xYourWallet")
        return

    chain, address = args
    if chain.upper() not in ["ETH", "SOL"]:
        await update.message.reply_text("❌ Fadlan dooro ETH ama SOL oo kaliya.")
        return

    user_wallets[user_id] = {"chain": chain.upper(), "address": address}
    save_wallets(user_wallets)

    await update.message.reply_text(f"✅ Wallet-kaaga {chain.upper()} waa la keydiyay: {address}")

# ✅ /mywallet
async def view_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = user_wallets.get(user_id)

    if not wallet:
        await update.message.reply_text("❌ Wallet weli lama keydin. Isticmaal /wallet si aad u geliso.")
    else:
        await update.message.reply_text(f"👛 Wallet: {wallet['address']} ({wallet['chain']})")
# ✅ Cutubka 30 – ETH + SOL Wallet Auto Withdraw Feature (web3 + solana)

from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import os
from web3 import Web3

from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.system_program import TransferParams, transfer
from base58 import b58decode
from decimal import Decimal

# ✅ ENV SETUP
INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY_ETH = os.getenv("PRIVATE_KEY_ETH")  # hex string
BOT_WALLET_ETH = os.getenv("WALLET_ADDRESS_ETH")

PRIVATE_KEY_SOL = os.getenv("PRIVATE_KEY_SOL")  # base58 string
BOT_WALLET_SOL = os.getenv("WALLET_ADDRESS_SOL")

# ✅ Connect to Ethereum
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ Connect to Solana
solana_client = Client("https://api.mainnet-beta.solana.com")

# ✅ Load saved user wallets
from Cutubka29 import user_wallets


# ✅ ETH Withdraw Function
async def withdraw_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = user_wallets.get(user_id)
    if not wallet or wallet["chain"] != "ETH":
        await update.message.reply_text("❌ ETH wallet lama helin. Isticmaal /wallet si aad u keydiso.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("💡 Isticmaal sidaan: /withdraw_eth 0.01")
        return

    try:
        amount = float(context.args[0])
        to_address = wallet["address"]

        value = w3.to_wei(amount, 'ether')
        nonce = w3.eth.get_transaction_count(BOT_WALLET_ETH)

        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': value,
            'gas': 21000,
            'gasPrice': w3.to_wei('20', 'gwei'),
        }

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY_ETH)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        await update.message.reply_text(f"✅ ETH ({amount}) waa la diray.\nTX Hash: {tx_hash.hex()}")
    except Exception as e:
        await update.message.reply_text(f"❌ ETH Error: {str(e)}")


# ✅ SOL Withdraw Function
async def withdraw_sol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = user_wallets.get(user_id)
    if not wallet or wallet["chain"] != "SOL":
        await update.message.reply_text("❌ SOL wallet lama helin. Isticmaal /wallet si aad u keydiso.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("💡 Isticmaal sidaan: /withdraw_sol 0.01")
        return

    try:
        amount = float(context.args[0])
        to_address = wallet["address"]

        sender = Keypair.from_secret_key(b58decode(PRIVATE_KEY_SOL))
        lamports = int(amount * 1_000_000_000)  # 1 SOL = 1e9 lamports

        tx = Transaction()
        tx.add(transfer(TransferParams(from_pubkey=sender.public_key, to_pubkey=to_address, lamports=lamports)))

        response = solana_client.send_transaction(tx, sender)
        tx_sig = response['result']

        await update.message.reply_text(f"✅ SOL ({amount}) waa la diray.\nTX Signature: {tx_sig}")
    except Exception as e:
        await update.message.reply_text(f"❌ SOL Error: {str(e)}")

# ✅ Cutubka 31 – Solana Memecoin Auto Buyer (Jupiter + Phantom support)

from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import os
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from base58 import b58decode
import requests
import json

# ✅ Solana config
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
solana_client = Client(SOLANA_RPC_URL)

# ✅ ENV vars
PRIVATE_KEY_SOL = os.getenv("PRIVATE_KEY_SOL")
BOT_WALLET_SOL = os.getenv("WALLET_ADDRESS_SOL")

# ✅ Load user wallets
from Cutubka29 import user_wallets

# ✅ Auto Buy Memecoin using Jupiter Aggregator
async def buy_memecoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = user_wallets.get(user_id)

    if not wallet or wallet["chain"] != "SOL":
        await update.message.reply_text("❌ SOL wallet lama helin. Isticmaal /wallet si aad u keydiso.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("💡 Isticmaal sidaan: /buy SUI 0.1")
        return

    token_symbol = context.args[0].upper()
    sol_amount = float(context.args[1])
    buyer_address = wallet["address"]

    try:
        # 1. Hel Token Mint Address from your backend or static list
        TOKEN_MINTS = {
            "SUI": "EXAMPLE_SUI_MINT_ADDRESS",
            "DOGWIFHAT": "EXAMPLE_DOGWIFHAT_MINT",
        }

        if token_symbol not in TOKEN_MINTS:
            await update.message.reply_text("❌ Token-ka lama yaqaan. Fadlan dooro mid sax ah.")
            return

        token_mint = TOKEN_MINTS[token_symbol]

        # 2. Jupiter API Call for Best Route
        jupiter_url = f"https://quote-api.jup.ag/v6/swap"
        payload = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": token_mint,
            "amount": int(sol_amount * 1_000_000_000),
            "slippageBps": 50,
            "userPublicKey": buyer_address,
        }

        response = requests.post(jupiter_url, json=payload)
        swap_data = response.json()
        if "swapTransaction" not in swap_data:
            await update.message.reply_text("❌ Swap failed. Route not found.")
            return

        # 3. Decode and Sign the Transaction
        swap_tx = swap_data["swapTransaction"]
        swap_bytes = b58decode(swap_tx)

        keypair = Keypair.from_secret_key(b58decode(PRIVATE_KEY_SOL))
        tx = Transaction.deserialize(swap_bytes)

        tx.sign(keypair)
        tx_sig = solana_client.send_transaction(tx, keypair)["result"]

        await update.message.reply_text(f"✅ {token_symbol} coin bought successfully!\nTX: {tx_sig}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
# ✅ Cutubka 32 – Multi-Chain Memecoin Detector (Avalanche, Base, Sui)
# Description: Bot-ku wuxuu si toos ah u baaraa fursadaha cusub ee kasoo baxa Avalanche, Base, Sui
# Wuxuu dirayaa signal Telegram, address coinka, sababta breakout, iyo status Halal/Haram.

import random
import datetime
from telegram import Update
from telegram.ext import ContextTypes

# Chains taageero leh
chains_supported = ["Avalanche", "Base", "Sui"]

# Function-ka baaraya memecoins cusub
def scan_new_memecoins():
    new_coins = []
    for chain in chains_supported:
        # Tusaale fake ah (API ama webhook ayaa lagu beddeli karaa mustaqbalka)
        coin_name = f"{chain[:2]}Coin{random.randint(100,999)}"
        halal = random.choice([True, False])
        new_coins.append({
            "symbol": coin_name,
            "address": f"0x{random.randint(10**15, 10**16-1):x}",
            "chain": chain,
            "halal": halal,
            "reason": "Trending + Spike in mentions"
        })
    return new_coins

# Function signal u dira Telegram
def send_memecoin_signals(bot, chat_id):
    coins = scan_new_memecoins()
    for coin in coins:
        halal_status = "🟢 Halal" if coin["halal"] else "🔴 Haram"
        message = f"""🚨 New {coin['chain']} Memecoin Detected!

🪙 Name: {coin['symbol']}
🏷 Address: `{coin['address']}`
📊 Reason: {coin['reason']}
📍 Status: {halal_status}"""
        bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Command Telegram ah si loo adeegsado gacanta
async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_memecoin_signals(context.bot, update.effective_chat.id)
# ✅ Cutubka 32 – Multi-Chain Memecoin Detector (Avalanche, Base, Sui)
# Description: Bot-ku wuxuu si toos ah u baaraa fursadaha cusub ee kasoo baxa Avalanche, Base, Sui
# Wuxuu dirayaa signal Telegram, address coinka, sababta breakout, iyo status Halal/Haram.

import random
import datetime
from telegram import Update
from telegram.ext import ContextTypes

# Chains taageero leh
chains_supported = ["Avalanche", "Base", "Sui"]

# Function-ka baaraya memecoins cusub
def scan_new_memecoins():
    new_coins = []
    for chain in chains_supported:
        # Tusaale fake ah (API ama webhook ayaa lagu beddeli karaa mustaqbalka)
        coin_name = f"{chain[:2]}Coin{random.randint(100,999)}"
        halal = random.choice([True, False])
        new_coins.append({
            "symbol": coin_name,
            "address": f"0x{random.randint(10**15, 10**16-1):x}",
            "chain": chain,
            "halal": halal,
            "reason": "Trending + Spike in mentions"
        })
    return new_coins

# Function signal u dira Telegram
def send_memecoin_signals(bot, chat_id):
    coins = scan_new_memecoins()
    for coin in coins:
        halal_status = "🟢 Halal" if coin["halal"] else "🔴 Haram"
        message = f"""🚨 New {coin['chain']} Memecoin Detected!

🪙 Name: {coin['symbol']}
🏷 Address: `{coin['address']}`
📊 Reason: {coin['reason']}
📍 Status: {halal_status}"""
        bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Command Telegram ah si loo adeegsado gacanta
async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_memecoin_signals(context.bot, update.effective_chat.id)
# ✅ Cutubka 33 – Chart Image Generator for Coins (Auto Graph)
# Tani waxay si toos ah u soo saartaa sawir chart ah (line graph) oo coin-ka
# Volume, Price, ama data kale lagaga sameeyo matplotlib

import matplotlib.pyplot as plt
import random
import io
from telegram import InputFile

def generate_sample_chart(symbol: str):
    # Random sample data for demo
    prices = [round(random.uniform(0.1, 1.5), 3) for _ in range(20)]
    timestamps = list(range(1, 21))

    plt.figure(figsize=(6, 4))
    plt.plot(timestamps, prices, marker='o', linestyle='-', color='blue')
    plt.title(f"{symbol.upper()} Trend Chart")
    plt.xlabel("Time")
    plt.ylabel("Price ($)")
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# Telegram function to send chart
async def send_chart_image(update, context):
    symbol = "DEMO"
    chart_buf = generate_sample_chart(symbol)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(chart_buf, filename=f"{symbol}_chart.png"))
# ✅ Cutubka 34 – Daily Profit Goal Tracker

from datetime import datetime, timedelta
import json
import os

# File to store goal data
GOAL_FILE = "profit_goal.json"

# Default target
DEFAULT_GOAL = {
    "start_date": str(datetime.now().date()),
    "end_date": str((datetime.now() + timedelta(days=10)).date()),
    "target_profit": 650,
    "current_profit": 0
}

# ✅ Save goal progress
def save_goal(data):
    with open(GOAL_FILE, "w") as f:
        json.dump(data, f)

# ✅ Load goal
def load_goal():
    if not os.path.exists(GOAL_FILE):
        save_goal(DEFAULT_GOAL)
    with open(GOAL_FILE, "r") as f:
        return json.load(f)

# ✅ Add profit manually
async def add_daily_profit(update, context):
    try:
        amount = float(context.args[0])
        goal = load_goal()
        goal["current_profit"] += amount
        save_goal(goal)
        await update.message.reply_text(f"✅ Profit +${amount} added. Current: ${goal['current_profit']}")
    except:
        await update.message.reply_text("❌ Usage: /profit 50")

# ✅ Show goal status
async def show_goal(update, context):
    goal = load_goal()
    status = f"""
📊 Profit Goal Tracker (10 Days)
Start: {goal['start_date']}
End: {goal['end_date']}

🎯 Target: ${goal['target_profit']}
📈 Current: ${goal['current_profit']}

✅ Remaining: ${goal['target_profit'] - goal['current_profit']}
"""
    await update.message.reply_text(status)

# ✅ Reset goal
async def reset_goal(update, context):
    save_goal(DEFAULT_GOAL)
    await update.message.reply_text("🔄 Goal has been reset.")
# ✅ Cutubka 35 – Auto Reminder if No Trades Taken

import json
import os
from datetime import datetime, timedelta
from telegram.ext import Application
from apscheduler.schedulers.background import BackgroundScheduler

# ✅ File to track trade activity
TRADE_LOG_FILE = "trade_activity.json"

# ✅ Initialize file if missing
def init_trade_log():
    if not os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, "w") as f:
            json.dump({}, f)

# ✅ Record trade activity for today
def log_trade():
    init_trade_log()
    data = load_trade_log()
    today = str(datetime.now().date())
    data[today] = True
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(data, f)

# ✅ Load trade log
def load_trade_log():
    init_trade_log()
    with open(TRADE_LOG_FILE, "r") as f:
        return json.load(f)

# ✅ Check daily reminder
async def daily_trade_check(context):
    data = load_trade_log()
    today = str(datetime.now().date())
    if today not in data:
        await context.bot.send_message(
            chat_id=os.getenv("CHAT_ID", "YOUR_CHAT_ID"),
            text="⚠️ Ma jiro wax trade ah oo la qaaday maanta!"
        )

# ✅ APScheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(daily_trade_check, "cron", hour=23, minute=59, args=[app])
scheduler.start()

# ✅ Optional: Call log_trade() inside your trade execution function
# For example:
# log_trade()  → marka signal la xaqiijiyo ama auto trade dhacdo
# ✅ Cutubka 36 – Cron Job Signal Scanner (Avalanche, Sui, Base)

import requests
import os
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ✅ Target chains
CHAINS = ["Avalanche", "Sui", "Base"]

# ✅ Dummy source for signals (replace with real endpoint or database)
def fetch_signals(chain):
    # Tusaale ahaan waxaad geli kartaa API call, webhook, ama Notion DB
    dummy_signals = {
        "Avalanche": [{"symbol": "AVAXMOON", "direction": "BUY"}],
        "Sui": [{"symbol": "SUICAT", "direction": "SELL"}],
        "Base": [{"symbol": "BASEINU", "direction": "BUY"}]
    }
    return dummy_signals.get(chain, [])

# ✅ Send signal to Telegram
def send_signal_to_telegram(signal, chain, app):
    try:
        symbol = signal["symbol"]
        direction = signal["direction"]

        message = f"🚀 *{chain} Chain Signal*\nCoin: `{symbol}`\nDirection: {direction}"
        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Signal Send Error: {str(e)}")

# ✅ Cron job function
def scan_signals():
    print("🔍 Scanning memecoin signals...")
    for chain in CHAINS:
        signals = fetch_signals(chain)
        for signal in signals:
            send_signal_to_telegram(signal, chain, app)

# ✅ Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scan_signals, "interval", minutes=15)  # every 15 minutes
scheduler.start()
# ✅ Memecoin Early Sniper Strategy Module
# Detects newly launched coins on DEX (e.g., Solana, Base, SUI) and alerts user

import time
import os
import asyncio
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

# Global halal filter flag
halal_only_mode = True

# Keywords to filter haram coins
haram_keywords = ["casino", "gambling", "loan", "riba", "liquor", "alcohol"]

# ✅ Halal Check
def is_halal(name):
    return not any(k in name.lower() for k in haram_keywords)

# ✅ Get recent memecoins from Solana (replace URL with DEX API if needed)
def get_recent_memecoins():
    response = requests.get("https://api.dexscreener.com/latest/dex/pairs/solana")
    coins = response.json().get("pairs", [])
    new_coins = []

    for coin in coins:
        created = coin.get("pairCreatedAt", 0) / 1000
        minutes_ago = (time.time() - created) / 60

        if minutes_ago < 10:
            name = coin.get("baseToken", {}).get("name", "Unknown")
            volume = coin.get("volumeUsd", 0)
            liquidity = coin.get("liquidity", {}).get("usd", 0)

            if volume > 5000 and liquidity > 1000:
                if not halal_only_mode or is_halal(name):
                    new_coins.append({
                        "name": name,
                        "address": coin.get("baseToken", {}).get("address"),
                        "volume": volume,
                        "liquidity": liquidity,
                        "dex": coin.get("dexId")
                    })
    return new_coins

# ✅ Notify Telegram
async def notify_memecoin_sniper(context: ContextTypes.DEFAULT_TYPE):
    coins = get_recent_memecoins()
    for coin in coins:
        msg = f"🚀 *New Memecoin Detected*\n"
        msg += f"Name: {coin['name']}\n"
        msg += f"Liquidity: ${coin['liquidity']:,}\n"
        msg += f"Volume: ${coin['volume']:,}\n"
        msg += f"DEX: {coin['dex']}\n"
        msg += f"[📈 View on Dexscreener](https://dexscreener.com/{coin['dex']}/{coin['address']})"

        buttons = [[
            InlineKeyboardButton("✅ Watch", callback_data=f"WATCH:{coin['address']}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        await context.bot.send_message(
            chat_id=os.getenv("CHAT_ID"),
            text=msg,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

# ✅ Cron job setup (every 5 min)
def start_sniper_scheduler(context):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(notify_memecoin_sniper(context)), 'interval', minutes=5)
    scheduler.start()
# ✅ TradeGuard Risk Control System
# Protects account with a max drawdown and auto reset daily

from datetime import datetime, timedelta
from decimal import Decimal
import os
import json

# ✅ Configurable Risk Settings
MAX_DAILY_LOSS = Decimal(os.getenv("DAILY_MAX_RISK", "250"))
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
TRADE_LOG_PATH = "trade_log.json"
DAILY_RESET_HOUR = 0  # 0 = Midnight

# ✅ Check if trade is allowed
def can_take_trade():
    today = datetime.utcnow().date()
    if not os.path.exists(TRADE_LOG_PATH):
        return True

    with open(TRADE_LOG_PATH, "r") as f:
        data = json.load(f)

    day_data = data.get(str(today), {"loss": 0})
    current_loss = Decimal(day_data.get("loss", 0))
    return current_loss < MAX_DAILY_LOSS

# ✅ Record a loss or win (triggered after trade closes)
def record_trade_result(pnl_amount):
    today = str(datetime.utcnow().date())
    pnl_amount = Decimal(pnl_amount)

    if not os.path.exists(TRADE_LOG_PATH):
        data = {}
    else:
        with open(TRADE_LOG_PATH, "r") as f:
            data = json.load(f)

    if today not in data:
        data[today] = {"loss": 0, "profit": 0}

    if pnl_amount < 0:
        data[today]["loss"] += abs(pnl_amount)
    else:
        data[today]["profit"] += pnl_amount

    with open(TRADE_LOG_PATH, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Reset daily at midnight (UTC)
def reset_daily_trade_limit():
    if os.path.exists(TRADE_LOG_PATH):
        with open(TRADE_LOG_PATH, "w") as f:
            json.dump({}, f)

# ✅ Example usage
if can_take_trade():
    print("✅ Trade allowed. Risk is within limits.")
else:
    print("❌ Daily loss limit reached. No more trades allowed today.")

# Cron: Add to scheduler to reset daily at 00:00 UTC
from apscheduler.schedulers.background import BackgroundScheduler

def start_risk_guard_cron():
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_daily_trade_limit, 'cron', hour=DAILY_RESET_HOUR)
    scheduler.start()
# ✅ ICT Trade Filter – Only allow signals matching Inner Circle Trader (ICT) style

# Sample ICT keyword filters (you can expand this list)
ict_keywords = ["FVG", "liquidity grab", "OB", "breaker", "Judas swing", "PD array"]

# ✅ Toggle ICT filtering (optional command-based toggle)
ict_filter_enabled = True

def matches_ict_style(description: str) -> bool:
    """Check if the signal description or strategy matches ICT terms"""
    return any(keyword.lower() in description.lower() for keyword in ict_keywords)

# ✅ Modify your existing webhook signal handler
@flask_app.route('/signal-webhook', methods=['POST'])
def signal_webhook():
    try:
        data = request.get_json()

        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")
        description = data.get("description", "")

        # ✅ Only apply ICT filter to Forex signals
        if ict_filter_enabled and market == "forex":
            if not matches_ict_style(description):
                return "⚠️ Signal ignored: not ICT style."

        message = f"🚨 New {market.upper()} Signal\nPair: {symbol}\nTime: {timeframe}\nDirection: {direction}"

        # ✅ Optional: show ICT confirmation
        if market == "forex":
            ict_status = "🧠 ICT Signal ✅" if matches_ict_style(description) else "❌ Not ICT"
            message += f"\n{ict_status}"

        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

        return "Signal Sent"
    except Exception as e:
        return f"Webhook error: {str(e)}"
from fpdf import FPDF
from datetime import datetime
import os
from telegram.ext import ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ✅ PDF Report Generator
def generate_daily_pdf_report(trades: list):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"Trade_Report_{today}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"📊 Daily Trade Report – {today}", ln=True, align="C")
    pdf.ln(10)

    for idx, trade in enumerate(trades, 1):
        pdf.cell(200, 10, txt=f"{idx}. {trade}", ln=True)

    os.makedirs("reports", exist_ok=True)
    filepath = os.path.join("reports", filename)
    pdf.output(filepath)
    return filepath

# ✅ Telegram Send Function
async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    trades = context.bot_data.get("daily_trades", [])
    if not trades:
        return

    filepath = generate_daily_pdf_report(trades)
    chat_id = os.getenv("CHAT_ID")
    await context.bot.send_document(chat_id=chat_id, document=open(filepath, "rb"))

# ✅ Scheduler (23:59 daily)
scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_report, "cron", hour=23, minute=59, args=[None])
scheduler.start()
from datetime import datetime
import os
import json

# ✅ Folder to save results
os.makedirs("trade_logs", exist_ok=True)

# ✅ Save trade result to JSON log file
def save_trade_result(symbol: str, direction: str, result: str, pnl: float):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"trade_logs/{today}.json"

    # Load previous data if exists
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = []

    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "symbol": symbol,
        "direction": direction,
        "result": result,
        "pnl": pnl
    }

    data.append(entry)

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Example usage when a trade closes:
# result = "TP Hit" or "SL Hit"
# pnl = Profit or loss (e.g. 75 or -250)
save_trade_result("EURUSD", "BUY", "TP Hit", 75.0)
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import json
import os
from datetime import datetime

async def view_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"trade_logs/{today}.json"

    if not os.path.exists(filename):
        await update.message.reply_text("Ma jiro wax trade log ah maanta.")
        return

    with open(filename, "r") as f:
        trades = json.load(f)

    if not trades:
        await update.message.reply_text("Ma jiraan wax trades la diiwaan geliyay.")
        return

    total_pnl = sum([trade["pnl"] for trade in trades])
    message = f"📈 *Today's Trade Summary* ({today})\n\n"

    for trade in trades:
        message += f"🕒 {trade['time']} | {trade['symbol']} | {trade['direction']} | {trade['result']} | P&L: {trade['pnl']}\n"

    message += f"\n💰 *Total P&L:* {total_pnl}"

    await update.message.reply_text(message, parse_mode="Markdown")
from fpdf import FPDF
from datetime import datetime
import os
import json

# ✅ Create PDF summary of today's trades
def generate_daily_pdf():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"trade_logs/{today}.json"
    pdf_filename = f"pdf_reports/{today}_report.pdf"

    if not os.path.exists(filename):
        return None

    with open(filename, "r") as f:
        trades = json.load(f)

    if not trades:
        return None

    os.makedirs("pdf_reports", exist_ok=True)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"📄 Trade Summary – {today}", ln=True, align="C")
    pdf.ln(10)

    total_pnl = 0

    for trade in trades:
        line = f"{trade['time']} | {trade['symbol']} | {trade['direction']} | {trade['result']} | P&L: {trade['pnl']}"
        pdf.cell(200, 10, txt=line, ln=True)
        total_pnl += trade["pnl"]

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"💰 Total P&L: {total_pnl}", ln=True)

    pdf.output(pdf_filename)
    return pdf_filename
# ✅ Cutubka 45 – PDF Daily Report via /report Command

from telegram.ext import CommandHandler
from fpdf import FPDF
import datetime
import os

# ✅ Trade mock data (should come from your database or actual log)
daily_trades = [
    {"symbol": "EURUSD", "result": "WIN", "pnl": "+$120"},
    {"symbol": "BTCUSDT", "result": "LOSS", "pnl": "-$50"},
    {"symbol": "AAPL", "result": "WIN", "pnl": "+$95"},
]

# ✅ PDF Generator
def generate_daily_report(trades):
    today = datetime.date.today().strftime("%Y-%m-%d")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"📊 Daily Trade Report - {today}", ln=True, align="C")

    for trade in trades:
        symbol = trade.get("symbol", "N/A")
        result = trade.get("result", "N/A")
        pnl = trade.get("pnl", "N/A")
        pdf.cell(200, 10, txt=f"{symbol} | Result: {result} | P&L: {pnl}", ln=True)

    file_path = f"/mnt/data/trade_report_{today}.pdf"
    pdf.output(file_path)
    return file_path

# ✅ /report Command Handler
async def report_command(update, context):
    try:
        file_path = generate_daily_report(daily_trades)
        await update.message.reply_document(document=open(file_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating report: {e}")
# ✅ Cutubka 46 – Scheduler for Daily PDF Report at 23:59

from apscheduler.schedulers.background import BackgroundScheduler
from telegram import InputFile
import datetime

# Same PDF generator function from Cutubka 45
def generate_daily_report(trades):
    today = datetime.date.today().strftime("%Y-%m-%d")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"📊 Daily Trade Report - {today}", ln=True, align="C")

    for trade in trades:
        symbol = trade.get("symbol", "N/A")
        result = trade.get("result", "N/A")
        pnl = trade.get("pnl", "N/A")
        pdf.cell(200, 10, txt=f"{symbol} | Result: {result} | P&L: {pnl}", ln=True)

    file_path = f"/mnt/data/trade_report_{today}.pdf"
    pdf.output(file_path)
    return file_path

# ✅ Scheduled job
def send_daily_report_job():
    try:
        file_path = generate_daily_report(daily_trades)
        app.bot.send_document(chat_id=os.getenv("CHAT_ID"), document=InputFile(file_path))
        print("✅ Daily report sent automatically.")
    except Exception as e:
        print(f"❌ Error sending daily report: {e}")

# ✅ Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_report_job, trigger='cron', hour=23, minute=59)
scheduler.start()
# ✅ Cutubka 47 – Market Filter for Daily Report Summary

from telegram import Update
from telegram.ext import CommandHandler
from datetime import datetime

# Sample in-memory trade log (can be loaded from file/db in real usage)
trade_log = [
    {"market": "forex", "symbol": "EURUSD", "result": "WIN", "pnl": "+35"},
    {"market": "crypto", "symbol": "SOL", "result": "LOSS", "pnl": "-20"},
    {"market": "forex", "symbol": "GBPUSD", "result": "WIN", "pnl": "+50"},
    {"market": "stocks", "symbol": "TSLA", "result": "LOSS", "pnl": "-15"},
]

async def filter_trades_by_market(update: Update, context):
    try:
        if len(context.args) != 1:
            await update.message.reply_text("❗ Isticmaal sidaan: /trades forex")
            return

        market = context.args[0].lower()
        filtered = [t for t in trade_log if t["market"].lower() == market]

        if not filtered:
            await update.message.reply_text(f"❌ Ma jiro trade la helay for market: {market}")
            return

        msg = f"📋 Trades for market: {market.upper()}\n"
        for t in filtered:
            msg += f"{t['symbol']} - {t['result']} ({t['pnl']})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error filtering trades: {str(e)}")

# ✅ Add this command handler
# ✅ Cutubka 48 – Push App Custom JSON Tester Tool

from flask import Flask, request, jsonify

push_tester = Flask(__name__)

@push_tester.route('/push-test', methods=["POST"])
def push_test():
    try:
        data = request.get_json(force=True)
        print("✅ Received Push Test JSON:")
        print(data)
        return jsonify({"status": "✅ JSON Received", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "❌ Error", "error": str(e)}), 400

if __name__ == '__main__':
    # You can change the port number if needed
    push_tester.run(port=5000)
# ✅ Cutubka 49 – Multi-user Wallet Encryption & Security

import json
import os
from cryptography.fernet import Fernet

# 🔐 Key generation (same once, then store safely!)
ENCRYPTION_KEY_PATH = "wallet_encryption.key"
WALLETS_FILE = "secure_wallets.json"

# Create key if not exists
if not os.path.exists(ENCRYPTION_KEY_PATH):
    with open(ENCRYPTION_KEY_PATH, "wb") as f:
        f.write(Fernet.generate_key())

# Load encryption key
with open(ENCRYPTION_KEY_PATH, "rb") as f:
    ENCRYPTION_KEY = f.read()

fernet = Fernet(ENCRYPTION_KEY)

# ✅ Save wallet securely for a user
def save_wallet(user_id: str, wallet_data: dict):
    encrypted_data = fernet.encrypt(json.dumps(wallet_data).encode())
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "r") as f:
            db = json.load(f)
    else:
        db = {}
    db[user_id] = encrypted_data.decode()
    with open(WALLETS_FILE, "w") as f:
        json.dump(db, f)
    print(f"✅ Wallet saved for user: {user_id}")

# ✅ Load wallet securely
def load_wallet(user_id: str) -> dict:
    if not os.path.exists(WALLETS_FILE):
        return {}
    with open(WALLETS_FILE, "r") as f:
        db = json.load(f)
    encrypted_data = db.get(user_id)
    if not encrypted_data:
        return {}
    decrypted = fernet.decrypt(encrypted_data.encode())
    return json.loads(decrypted)

# ✅ Tusaale isticmaal
if __name__ == "__main__":
    user_id = "user_742465040"  # Replace with Telegram user ID
    wallet_info = {
        "eth": "0x123abc...eth",
        "sol": "solanaWalletExample...123",
        "base": "baseAddressHere...",
    }

    save_wallet(user_id, wallet_info)
# ✅ Cutubka 49 – Multi-user Wallet Encryption & Security

import json
import os
from cryptography.fernet import Fernet

# 🔐 Key generation (same once, then store safely!)
ENCRYPTION_KEY_PATH = "wallet_encryption.key"
WALLETS_FILE = "secure_wallets.json"

# Create key if not exists
if not os.path.exists(ENCRYPTION_KEY_PATH):
    with open(ENCRYPTION_KEY_PATH, "wb") as f:
        f.write(Fernet.generate_key())

# Load encryption key
with open(ENCRYPTION_KEY_PATH, "rb") as f:
    ENCRYPTION_KEY = f.read()

fernet = Fernet(ENCRYPTION_KEY)

# ✅ Save wallet securely for a user
def save_wallet(user_id: str, wallet_data: dict):
    encrypted_data = fernet.encrypt(json.dumps(wallet_data).encode())
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "r") as f:
            db = json.load(f)
    else:
        db = {}
    db[user_id] = encrypted_data.decode()
    with open(WALLETS_FILE, "w") as f:
        json.dump(db, f)
    print(f"✅ Wallet saved for user: {user_id}")

# ✅ Load wallet securely
def load_wallet(user_id: str) -> dict:
    if not os.path.exists(WALLETS_FILE):
        return {}
    with open(WALLETS_FILE, "r") as f:
        db = json.load(f)
    encrypted_data = db.get(user_id)
    if not encrypted_data:
        return {}
    decrypted = fernet.decrypt(encrypted_data.encode())
    return json.loads(decrypted)

# ✅ Tusaale isticmaal
if __name__ == "__main__":
    user_id = "user_742465040"  # Replace with Telegram user ID
    wallet_info = {
        "eth": "0x123abc...eth",
        "sol": "solanaWalletExample...123",
        "base": "baseAddressHere...",
    }

    save_wallet(user_id, wallet_info)
# ✅ Cutubyada 50 ilaa 55 (Isku dhafan oo hal file ah)

# ✅ Cutubka 50 – Signal Accuracy Logger
from datetime import datetime
import json

def log_trade_result(symbol: str, result: str):
    log_entry = {
        "symbol": symbol,
        "result": result,  # "win" or "loss"
        "timestamp": datetime.now().isoformat()
    }
    with open("trade_accuracy_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# Isticmaal marka signal kasta uu dhamaado:
# log_trade_result("EURUSD", "win")

# ✅ Cutubka 51 – Auto Cleanup Old Logs
import os
from datetime import timedelta

def cleanup_old_logs(file_path="trade_accuracy_log.json", days=30):
    if not os.path.exists(file_path):
        return
    new_logs = []
    cutoff = datetime.now() - timedelta(days=days)
    with open(file_path, "r") as f:
        for line in f:
            try:
                log = json.loads(line)
                if datetime.fromisoformat(log["timestamp"]) > cutoff:
                    new_logs.append(line)
            except:
                continue
    with open(file_path, "w") as f:
        f.writelines(new_logs)

# ✅ Cutubka 52 – VPS Watchdog (auto restart if crash)
import subprocess
import time

def run_with_watchdog(script_path="main.py"):
    while True:
        try:
            subprocess.run(["python", script_path])
        except Exception as e:
            print("❌ Bot crashed, restarting...", e)
        time.sleep(5)

# ✅ Cutubka 53 – Chart OCR Reader (optional)
import pytesseract
from PIL import Image

def extract_text_from_chart(image_path: str) -> str:
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Usage:
# print(extract_text_from_chart("chart.png"))

# ✅ Cutubka 54 – Multi-language Support
lang_messages = {
    "en": {
        "start": "Welcome!",
        "halal_only": "Halal Only Mode is now ON"
    },
    "so": {
        "start": "Ku soo dhawoow!",
        "halal_only": "Xulashada Halal kaliya waa ON"
    }
}

def get_msg(key: str, lang: str = "en") -> str:
    return lang_messages.get(lang, {}).get(key, key)

# Usage:
# user_lang = "so"
# bot.send_message(chat_id, get_msg("start", user_lang))

# ✅ Cutubka 55 – Auto P&L Sync with Notion
# This requires setting up Notion API access & token
import requests

def send_to_notion(profit: float, date: str):
    notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": "Bearer YOUR_NOTION_API_TOKEN",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"database_id": "YOUR_DATABASE_ID"},
        "properties": {
            "Date": {"date": {"start": date}},
            "Profit": {"number": profit}
        }
    }
    response = requests.post(notion_url, headers=headers, json=data)
    return response.status_code == 200
    print("✅ Recovered Wallet:", load_wallet(user_id))
    print("✅ Recovered Wallet:", load_wallet(user_id))
app.add_handler(CommandHandler("trades", filter_trades_by_market))
# ✅ Add handler
app.add_handler(CommandHandler("report", report_command))
# ✅ Register command
app.add_handler(CommandHandler("profits", view_profits))
# ✅ Handler for manual test
from telegram.ext import CommandHandler
async def remind_me(update, context):
    await daily_trade_check(context)
app.add_handler(CommandHandler("checktrades", remind_me))
# ✅ Telegram command handlers
from telegram.ext import CommandHandler
app.add_handler(CommandHandler("profit", add_daily_profit))
app.add_handler(CommandHandler("profits", show_goal))
app.add_handler(CommandHandler("resetgoal", reset_goal))
# Telegram command handler
from telegram.ext import CommandHandler
app.add_handler(CommandHandler("chartdemo", send_chart_image))
# Ku dar handler
app.add_handler(CommandHandler("scan_memecoins", scan_cmd))
# Ku dar handler
app.add_handler(CommandHandler("scan_memecoins", scan_cmd))

# ✅ Ku dar command handler
app.add_handler(CommandHandler("buy", buy_memecoin))
# ✅ Ku dar command handler
app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))
app.add_handler(CommandHandler("withdraw_sol", withdraw_sol)) 
# ✅ Ku dar handlers-ka
app.add_handler(CommandHandler("wallet", set_wallet))
app.add_handler(CommandHandler("mywallet", view_wallet))
# ✅ Ku dar handlers-ka
app.add_handler(CommandHandler("wallet", set_wallet))
app.add_handler(CommandHandler("mywallet", view_wallet))
# ✅ Register Commands
app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))  # /withdraw_eth <wallet> <amount>
app.add_handler(CommandHandler("eth_balance", eth_balance))    # /eth_balance
# ✅ Ku dar command handlers:
app.add_handler(CommandHandler("profit", log_profit))
app.add_handler(CommandHandler("profits", view_profits))
app.add_handler(CommandHandler("report", generate_report))
# ✅ Ku dar handlers-ka
app.add_handler(CommandHandler("goal", goal_status))
app.add_handler(CommandHandler("addprofit", add_profit))
# ✅ Register handlers
app.add_handler(CommandHandler("goal", goal_status))
app.add_handler(CommandHandler("addprofit", add_profit))

# ✅ Add the ICT filter command handler
app.add_handler(CommandHandler("ictfilter", toggle_ict_filter))
# ✅ Add to handlers
app.add_handler(CommandHandler("search", search_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query))
# ✅ Register handlers
app.add_handler(CommandHandler("togglemarkets", toggle_market_visibility))
app.add_handler(CallbackQueryHandler(handle_toggle_market_callback, pattern="^TOGGLE_MARKET:"))
# ✅ Register command
app.add_handler(CommandHandler("halalonly", toggle_halal_only))
app.add_handler(CommandHandler("halalonly", toggle_halal_only))
# ✅ Register command handler
app.add_handler(CommandHandler("autotrade", toggle_autotrade))
# ✅ Register handler
app.add_handler(CommandHandler("forex", send_forex_trade))
# ✅ Register Handlers
app.add_handler(CommandHandler("profit", add_profit))
app.add_handler(CommandHandler("profits", show_profits))
# ✅ Register Commands
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
