import os
import asyncio
import logging
import json
import re
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from flask import Flask, request, jsonify
from web3 import Web3
from gtts import gTTS
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import io

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ChatAction
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Global Variables and Environment Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # This should be your public URL, e.g., https://your-app-name.onrender.com
INFURA_URL = os.getenv("INFURA_URL")
ETH_PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(',')] if ADMIN_IDS_STR else [123456789] # Change to your actual Telegram user ID

PROFIT_FILE = "profits.json"
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
trade_log = [] # Diiwaanka ganacsiyada maalinlaha ah

# Goal Tracker
GOAL_AMOUNT = Decimal(os.getenv("GOAL_AMOUNT", "650")) # USD
GOAL_DAYS = int(os.getenv("GOAL_DAYS", "10"))
START_DATE_STR = os.getenv("START_DATE", "2025-06-20")
START_DATE = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
goal_progress = [] # Each element is (date_str, profit)

# Autotrade state
auto_trade_enabled = False

# Halal Only Mode toggle state
halal_only_mode = False

# Hidden Markets state
hidden_markets = set()

# Account Balance for lot size calculation
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))

# Web3 setup
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
BOT_WALLET = os.getenv("WALLET_ADDRESS_ETH")
BOT_PRIVATE_KEY = os.getenv("PRIVATE_KEY_ETH")
WITHDRAW_TO = os.getenv("WITHDRAW_TO", "0xReceiverWalletAddressHere")

# Push App Webhook URL
PUSH_APP_WEBHOOK_URL = os.getenv("PUSH_APP_WEBHOOK_URL")

# Notion API
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ICT Filter state
ict_filter_enabled = True

# Global Application instance for Telegram
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Flask app instance
flask_app = Flask(__name__)

# Liiska erayada haramta ah for advanced check
HARAM_KEYWORDS = [
    "casino", "bet", "gambling", "poker", "lottery", "loan", "riba", "interest",
    "liquor", "alcohol", "wine", "beer", "vodka", "whiskey", "xxx", "sex", "porn",
    "shisha", "cigarette", "hookah", "rum", "cocktail", "drunk", "bar", "pepe" # Added pepe from snippet 16
]

# --- Helper Functions ---

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# Function to check if autotrade is on
def is_autotrade_on() -> bool:
    return auto_trade_enabled

# Function: Save daily profit
def save_profit(amount: float):
    today = datetime.now().strftime("%Y-%m-%d")
    profits = load_profits()
    profits[today] = profits.get(today, 0) + amount
    with open(PROFIT_FILE, "w") as f:
        json.dump(profits, f)

# Function: Load profits
def load_profits():
    if not os.path.exists(PROFIT_FILE):
        return {}
    with open(PROFIT_FILE, "r") as f:
        return json.load(f)

# Function: Calculate lot size based on SL pips and pip value
def calculate_lot_size(sl_distance_pips: float, pip_value: float = 10.0) -> float:
    if sl_distance_pips == 0:
        return 0.0  # Avoid division by zero
    risk_per_trade = DAILY_MAX_RISK
    # Ensure all calculations are with Decimal for precision
    lot_size = (risk_per_trade / Decimal(str(sl_distance_pips))) / Decimal(str(pip_value))
    return round(float(lot_size), 2)

# Function: Dir push notification (text only)
def send_push_notification(message: str) -> str:
    try:
        if not PUSH_APP_WEBHOOK_URL:
            raise ValueError("PUSH_APP_WEBHOOK_URL not set.")
        payload = {
            "title": " 📢  Hussein7 Trade Alert",
            "message": message
        }
        response = requests.post(PUSH_APP_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            return " ✅  Push sent"
        else:
            return f" ❌  Push failed: {response.text}"
    except Exception as e:
        return f"[Push Error]: {e}"

# Function: Abuur report PDF
def generate_daily_report(trades: list):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{REPORTS_DIR}/TradeReport_{today}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f" 📄 Trade Report – {today}", ln=True, align="C")
    pdf.ln(10)
    for i, trade in enumerate(trades, 1):
        text = (
            f"{i}. Pair: {trade.get('symbol', 'N/A')}\n"
            f" Direction: {trade.get('direction', 'N/A')}\n"
            f" Timeframe: {trade.get('timeframe', 'N/A')}\n"
            f" Result: {trade.get('result', 'N/A')}\n"
            f" P&L: {trade.get('pnl', 'N/A')}\n"
        )
        pdf.multi_cell(0, 10, txt=text)
        pdf.ln(2)
    pdf.output(filename)
    return filename

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
    response = requests.post(url, headers=NOTION_HEADERS, json=payload)
    if response.status_code != 200:
        logger.error(f" ❌ Notion Push Failed: {response.text}")
    else:
        logger.info(" ✅ Trade pushed to Notion.")

# Function: go'aami haddii coin uu halal yahay iyadoo la eegayo magaca + sharaxaadiisa (Advanced Version)
def is_coin_halal_advanced(name: str, description: str = "") -> bool:
    combined_text = f"{name} {description}".lower()
    for haram_word in HARAM_KEYWORDS:
        # Use regex to match whole words only
        if re.search(rf"\b{re.escape(haram_word)}\b", combined_text):
            return False
    return True

# Helper to get voice text based on status
def get_voice_text(status: str) -> str:
    if status == "TP":
        return "Congratulations! Take Profit hit! 💰 "
    elif status == "SL":
        return "Stop Loss hit. Wax meynas galay... 😢 "
    else:
        return "New signal alert."

def calculate_goal_status():
    total_profit = sum(p[1] for p in goal_progress)
    days_passed = (datetime.now() - START_DATE).days + 1
    daily_target = GOAL_AMOUNT / GOAL_DAYS
    projected = days_passed * daily_target
    percent = round((total_profit / GOAL_AMOUNT) * 100, 1)
    return total_profit, projected, percent, days_passed

# --- Telegram Bot Commands & Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_msg = (
        f" 👋  Salaam {user.first_name},\n\n"
        "Ku soo dhawoow *Hussein7 TradeBot* 📊🤖 \n\n"
        " ✅  Forex Signals\n"
        " ✅  Crypto Alerts\n"
        " ✅  Stock Opportunities\n"
        " ✅  Memecoin Webhook Detector\n\n"
        "Isticmaal `/help` si aad u aragto amarrada oo dhan."
    )
    await update.message.reply_markdown(welcome_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = (
        " 🧠  *Amarada la heli karo:*\n\n"
        "/start – Bilow botka\n"
        "/help – Liiska amarada\n"
        "/profit – Ku dar profit\n"
        "/profits – Fiiri profits\n"
        "/withdraw_eth – ETH u dir\n"
        "/autotrade – Auto Trade On/Off\n"
        "/halalonly – Filter Halal Coins\n"
        "/forex, /crypto, /stocks, /polymarket, /memecoins – Arag signalada\n"
        "/report – Daily PDF report\n"
        "/goal – Fiiri horumarka goal-ka\n"
        "/addprofit – Ku dar profit goal-ka"
    )
    await update.message.reply_markdown(help_msg)

async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        save_profit(amount)
        await update.message.reply_text(f" ✅  Profit of ${amount} saved for today.")
    except (IndexError, ValueError):
        await update.message.reply_text(" ❗  Usage: /profit 120.5")

async def show_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profits = load_profits()
    if not profits:
        await update.message.reply_text(" 📭  No profit records found.")
        return
    msg = " 📊  Daily Profit Log:\n"
    total = 0
    for date, amount in sorted(profits.items()):
        msg += f"{date}: ${amount:.2f}\n"
        total += amount
    msg += f"\n 💰  Total: ${total:.2f}"
    await update.message.reply_text(msg)

async def send_forex_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Forex signal example
    pair = "EURUSD"
    direction = "BUY"
    entry = 1.0950
    tp = 1.1000
    sl = 1.0910
    
    # Check if market is hidden
    if "forex" in hidden_markets:
        await update.message.reply_text(f" 📵 Skipped {pair} – Forex market is currently hidden.")
        return

    # Halal label (optional, using advanced check for consistency)
    halal_status = " 🟢  Halal" if is_coin_halal_advanced(pair) else " 🔴  Haram"
    msg = (
        f" 📈  Forex Trade Alert\n"
        f"Pair: {pair}\n"
        f"Direction: {direction}\n"
        f"Entry: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n"
        f"Status: {halal_status}"
    )
    # Buttons: Confirm or Ignore
    buttons = [
        [InlineKeyboardButton(" ✅  Confirm", callback_data="FOREX_CONFIRM")],
        [InlineKeyboardButton(" ❌  Ignore", callback_data="FOREX_IGNORE")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def toggle_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = " ✅  AutoTrade Mode is ON" if auto_trade_enabled else " ❌  AutoTrade Mode is OFF"
    await update.message.reply_text(status)

async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = (" ✅  Halal Only Mode is ON  —  Only halal coins will be shown."
              if halal_only_mode else
              " ❌  Halal Only Mode is OFF  —  All coins will be shown.")
    await update.message.reply_text(status)

async def withdraw_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(" ❌  You are not authorized to use this command.")
        return
    try:
        sender_address = BOT_WALLET
        receiver_address = WITHDRAW_TO

        # Check balance
        balance = w3.eth.get_balance(sender_address)
        eth_balance = w3.from_wei(balance, 'ether')
        if eth_balance < 0.002:
            await update.message.reply_text(" ❌  Not enough ETH to withdraw. Minimum 0.002 ETH required.")
            return

        # Prepare transaction
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
        # Sign + send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=BOT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        await update.message.reply_text(f" ✅  ETH Withdrawn\n 🔗  TX Hash: {w3.to_hex(tx_hash)}")
    except Exception as e:
        await update.message.reply_text(f" ❌  Error during withdrawal: {str(e)}")

async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trade_log:
        await update.message.reply_text("Ma jiro trade maanta la qaaday.")
        return
    file_path = generate_daily_report(trade_log)
    with open(file_path, "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=os.path.basename(file_path))
    os.remove(file_path) # Clean up the generated PDF

async def goal_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_profit, projected, percent, days_passed = calculate_goal_status()
    status = (
        f" 🎯 *Goal Tracker*\n"
        f"Duration: {GOAL_DAYS} days\n"
        f"Goal: ${GOAL_AMOUNT:.2f}\n"
        f"Day: {days_passed}\n"
        f"Progress: ${total_profit:.2f} / ${GOAL_AMOUNT:.2f}\n"
        f"Projected by now: ${projected:.2f}\n"
        f"Completion: {percent}%"
    )
    await update.message.reply_text(status, parse_mode="Markdown")

async def add_profit_to_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        today_str = datetime.now().strftime("%Y-%m-%d")
        goal_progress.append((today_str, amount))
        await update.message.reply_text(f" ✅ Added profit: ${amount:.2f}")
    except Exception:
        await update.message.reply_text(" ❌ Usage: /addprofit 100")

async def toggle_market_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markets = ["Forex", "Crypto", "Stocks", "Polymarket", "Memecoins"]
    buttons = []
    for mkt in markets:
        is_hidden = mkt.lower() in hidden_markets
        label = f"{' ❌ ' if is_hidden else ' ✅ '} {mkt}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"TOGGLE_MARKET:{mkt.lower()}")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Toggle Market Visibility:", reply_markup=reply_markup)

async def handle_toggle_market_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    if data[0] == "TOGGLE_MARKET":
        market = data[1]
        if market in hidden_markets:
            hidden_markets.remove(market)
            await query.edit_message_text(f" ✅ {market.capitalize()} market is now **VISIBLE**.", parse_mode="Markdown")
        else:
            hidden_markets.add(market)
            await query.edit_message_text(f" ❌ {market.capitalize()} market is now **HIDDEN**.", parse_mode="Markdown")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(" 🔍 Please type the symbol or coin name you want to search.")

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().upper()
    # Example fake signal DB (replace with actual data source)
    fake_signals = {
        "EURUSD": {"market": "forex", "dir": "BUY", "tf": "5min"},
        "BTC": {"market": "crypto", "dir": "SELL", "tf": "15min"},
        "TSLA": {"market": "stocks", "dir": "BUY", "tf": "1H"},
        "TRUMP2024": {"market": "polymarket", "dir": "YES", "tf": "Event"},
    }
    if query in fake_signals:
        signal = fake_signals[query]
        message = (
            f" 🔍 Found Signal\n"
            f"Market: {signal['market'].capitalize()}\n"
            f"Symbol: {query}\n"
            f"Direction: {signal['dir']}\n"
            f"Timeframe: {signal['tf']}"
        )
    else:
        message = f" ❌ No signal found for {query}"
    await update.message.reply_text(message)

async def toggle_ict_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ict_filter_enabled
    ict_filter_enabled = not ict_filter_enabled
    status = " ✅ ICT Filter ENABLED" if ict_filter_enabled else " ❌ ICT Filter DISABLED"
    await update.message.reply_text(f"{status}\nOnly high-probability ICT-style Forex trades will be shown.")

# ICT-style detection logic (very basic sample)
def is_ict_compliant(signal: dict) -> bool:
    """
    Signal example: {
        "symbol": "EURUSD", "direction": "BUY", "timeframe": "5min", "market": "forex",
        "liquidity": "grabbed", "order_block": True, "fvg": True, "time": "10:15"
    }
    """
    return (
        signal.get("market") == "forex" and
        signal.get("order_block") is True and
        signal.get("fvg") is True and
        signal.get("liquidity") == "grabbed"
    )

def should_send_signal_based_on_ict_filter(signal: dict) -> bool:
    if ict_filter_enabled and signal.get("market") == "forex":
        return is_ict_compliant(signal)
    return True # send others like crypto/stocks/etc.

async def send_voice_alert(text: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tts.save(tmp_file.name)
        with open(tmp_file.name, "rb") as audio:
            await context.bot.send_voice(chat_id=chat_id, voice=audio)
        os.remove(tmp_file.name) # Clean up the temporary file
    except Exception as e:
        logger.error(f"Voice Alert Error: {e}")

async def send_result_voice(status: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        text = get_voice_text(status)
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp:
            tts.save(tmp.name)
            with open(tmp.name, "rb") as audio_file:
                await context.bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        logger.error(f"[Voice Alert Error]: {e}")

async def send_memecoin_signal(context: ContextTypes.DEFAULT_TYPE, coin_data: dict):
    name = coin_data.get("name", "Unknown")
    address = coin_data.get("address", "N/A")
    chain = coin_data.get("chain", "Solana")
    reason = coin_data.get("reason", " 🚀  Social spike")
    chart_url = coin_data.get("chart", "https://dexscreener.com/")

    # Halal filter check
    if halal_only_mode and not is_coin_halal_advanced(name):
        logger.info(f" 🔴 Skipped haram coin (Halal Only Mode ON): {name}")
        return

    status_text = " 🟢  Halal" if is_coin_halal_advanced(name) else " 🔴  Haram"
    msg = (
        f" 🚨  *New Memecoin Detected!*\n\n"
        f" 💎  *{name}*\n"
        f" 🔗  Chain: {chain}\n"
        f" 🪙  Address: `{address}`\n"
        f" 📈  Reason: {reason}\n"
        f" 🔍  Status: {status_text}\n"
        f" 📊  Chart: {chart_url}"
    )
    buttons = [[
        InlineKeyboardButton(" 📈  View Chart", url=chart_url),
        InlineKeyboardButton(" 📥  Copy Address", callback_data=f"copy:{address}")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, reply_markup=reply_markup, parse_mode="Markdown")


# --- Telegram Bot Handler Registration ---
def register_handlers():
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profit", add_profit)) # Renamed from log_profit for consistency with Word doc
    app.add_handler(CommandHandler("profits", show_profits)) # Renamed from view_profits
    app.add_handler(CommandHandler("forex", send_forex_trade))
    app.add_handler(CommandHandler("autotrade", toggle_autotrade))
    app.add_handler(CommandHandler("halalonly", toggle_halal_only))
    app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))
    app.add_handler(CommandHandler("report", send_report))
    app.add_handler(CommandHandler("goal", goal_status))
    app.add_handler(CommandHandler("addprofit", add_profit_to_goal)) # This is for goal tracking
    app.add_handler(CommandHandler("ictfilter", toggle_ict_filter))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query))
    app.add_handler(CommandHandler("togglemarkets", toggle_market_visibility))
    app.add_handler(CallbackQueryHandler(handle_toggle_market_callback, pattern="^TOGGLE_MARKET:"))
    # Add other handlers as needed (e.g., for crypto, stocks, polymarket, memecoins if they have commands)

    # Callback query for general confirmations (e.g., FOREX_CONFIRM, IGNORE)
    async def handle_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        if data.startswith("CONFIRM:"):
            # Example: CONFIRM:EURUSD:BUY
            _, symbol, direction = data.split(':')
            await query.edit_message_text(f" ✅  Confirmed trade for {symbol} ({direction}).")
            # Log this trade for report
            trade_log.append({"symbol": symbol, "direction": direction, "timeframe": "N/A", "result": "Confirmed", "pnl": 0})
            push_trade_to_notion(symbol, direction, "N/A", "Confirmed", 0) # Push to Notion
            await send_result_voice("TP", context, query.message.chat_id) # Example voice alert
        elif data == "IGNORE":
            await query.edit_message_text(" ❌  Trade ignored.")
        elif data.startswith("copy:"):
            _, address_to_copy = data.split(':')
            await query.answer(text=f"Address copied: {address_to_copy}", show_alert=True)
            # Cannot directly copy to user's clipboard via Telegram bot, this is just a confirmation.
        elif data == "FOREX_CONFIRM":
            await query.edit_message_text(" ✅  Forex trade confirmed.")
        elif data == "FOREX_IGNORE":
            await query.edit_message_text(" ❌  Forex trade ignored.")

    app.add_handler(CallbackQueryHandler(handle_confirmation_callback))

# --- Flask Routes (for Webhooks) ---

@flask_app.route('/')
def home():
    return " ✅  Hussein7 TradeBot is live!"

@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    update_json = request.get_json(force=True)
    try:
        update = Update.de_json(update_json, app.bot)
        await app.process_update(update)
        return "OK"
    except Exception as e:
        logger.error(f"Webhook Error: {str(e)}")
        return f"ERROR: {str(e)}"

@flask_app.route('/signal-webhook', methods=['POST'])
async def signal_webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")
        sl = data.get("stop_loss", "N/A")
        tp = data.get("take_profit", "N/A")
        pnl = data.get("pnl", 0) # Assume pnl is provided for logging
        trade_result = data.get("result", "N/A") # "WIN", "LOSS", "N/A"

        # Apply ICT filter for forex signals if enabled
        if not should_send_signal_based_on_ict_filter(data):
            logger.info(f" 📵 Skipped {symbol} signal – Not ICT compliant or ICT filter enabled for Forex.")
            return "Skipped: Not ICT compliant"

        # Halal status for crypto (using the advanced function)
        halal_status = ""
        if market.lower() == "crypto" or market.lower() == "memecoins":
            halal_status = " 🟢  Halal" if is_coin_halal_advanced(symbol, data.get("description", "")) else " 🔴  Haram"
            if halal_only_mode and "haram" in halal_status.lower():
                logger.info(f" 🔴 Skipped haram coin (Halal Only Mode ON): {symbol}")
                return "Skipped: Haram coin in Halal Only Mode"

        # Construct message
        message = (
            f" 🚨  New {market.upper()} Signal\n"
            f"Pair: {symbol}\n"
            f"Timeframe: {timeframe}\n"
            f"Direction: {direction}\n"
            f"TP: {tp}\nSL: {sl}\n"
            f"{halal_status}"
        )
        # Buttons for confirmation
        buttons = [[
            InlineKeyboardButton(" ✅  Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton(" ❌  Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Send message to Telegram chat
        await app.bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup, parse_mode="Markdown")

        # Log trade and push to Notion
        trade_log.append({
            "symbol": symbol,
            "direction": direction,
            "timeframe": timeframe,
            "result": trade_result,
            "pnl": pnl
        })
        push_trade_to_notion(symbol, direction, timeframe, trade_result, pnl)
        send_push_notification(f"New {market.upper()} Signal: {symbol} {direction}")

        # Voice alert for specific conditions (e.g., TP/SL)
        if trade_result == "WIN":
            await send_result_voice("TP", app.bot, CHAT_ID)
        elif trade_result == "LOSS":
            await send_result_voice("SL", app.bot, CHAT_ID)

        return " ✅  Signal sent to Telegram"
    except Exception as e:
        logger.error(f" ❌  Webhook error: {str(e)}")
        return f" ❌  Webhook error: {str(e)}"

# --- Scheduled Jobs ---
scheduler = BackgroundScheduler()

def daily_report_job_func():
    if trade_log:
        path = generate_daily_report(trade_log)
        # Assuming app is running and can send document via bot
        # This part requires the app.bot context which might not be available directly in a background job
        # For simplicity, we just generate the report here. Sending should be handled by an async context.
        # Alternatively, the bot can check a folder for new reports and send them.
        logger.info(f"Daily report generated: {path}")

# Schedule the daily report job
scheduler.add_job(daily_report_job_func, "cron", hour=23, minute=59)

# --- Main Execution ---
async def setup_bot_webhook():
    """Sets up the Telegram bot webhook."""
    if WEBHOOK_URL and TELEGRAM_TOKEN:
        webhook_url_full = f"{WEBHOOK_URL}/telegram-webhook"
        logger.info(f"Setting webhook to {webhook_url_full}")
        await app.bot.set_webhook(url=webhook_url_full)
        logger.info("Telegram webhook set successfully.")
    else:
        logger.warning("WEBHOOK_URL or TELEGRAM_TOKEN not set. Webhook not configured.")

    # Start polling for local development if webhook is not set
    # This block is typically for local development when not using webhooks
    # For production with uvicorn and webhooks, this would not be needed.
    # if not WEBHOOK_URL:
    #     logger.info("Starting Telegram bot polling...")
    #     await app.run_polling()

if __name__ == "__main__":
    register_handlers()
    scheduler.start() # Start the scheduler

    # For development on Render or local testing with uvicorn:
    # The `uvicorn main:flask_app` command will handle running Flask
    # and the /telegram-webhook endpoint will process updates.
    # The webhook setup should run once when the app starts.

    # We need to run the webhook setup as an async task
    # A common pattern for Flask + Async bot is to use Flask's before_first_request
    # or handle it during app startup if using a server like Gunicorn/Uvicorn
    # For simplicity here, we'll ensure webhook is set.

    # This part needs to be run inside an asyncio event loop, but flask_app.run() is blocking.
    # This is why uvicorn is recommended to manage the event loop.

    # If running with `uvicorn main:flask_app --host 0.0.0.0 --port $PORT`:
    # Uvicorn will manage the event loop for both Flask and the async Telegram handlers.
    # The webhook needs to be set once. A common way is to set it on the first request or on app startup.

    # We'll use a simple approach for local testing here.
    # For production (Render), `uvicorn` will handle running `flask_app` directly.
    # The webhook setup needs to happen outside the main flask_app.run() blocking call.

    # To ensure webhook is set when the application starts with Uvicorn, you might
    # need to have a startup event in your main application or a separate script.
    # Here, we'll define a simple startup hook for Flask that runs the webhook setup.
    # In a real Uvicorn deployment, this would be part of your ASGI app startup.

    @flask_app.before_first_request
    def set_webhook_on_startup():
        logger.info("Running before_first_request to set Telegram webhook...")
        # Running async function in a sync context (Flask's before_first_request)
        # This is generally not ideal, but often done for webhook setup.
        # For production, consider using `gunicorn --worker-class uvicorn.workers.UvicornWorker main:flask_app`
        # and handle startup in `main (3).py`'s original structure.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(setup_bot_webhook())
            else:
                loop.run_until_complete(setup_bot_webhook())
        except RuntimeError: # Occurs if no event loop is running (e.g., when not run with uvicorn directly)
            asyncio.run(setup_bot_webhook())
        logger.info("Webhook setup initiation attempted.")

    logger.info(f"Starting Flask app with uvicorn (or locally via flask_app.run())...")
    # This line is for local debugging/running directly as a script
    # For production, your start command will be `uvicorn main:flask_app --host 0.0.0.0 --port $PORT`
    PORT = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=PORT, debug=True) # debug=True for local, False for prod
