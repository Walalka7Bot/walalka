import os
import logging
import json
import tempfile
import asyncio
import re
from datetime import datetime, timedelta
from decimal import Decimal

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.constants import ChatAction
from flask import Flask, request

from gtts import gTTS
from fpdf import FPDF
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from web3 import Web3

# --- Configuration and Initialization ---

# ✅ Bot Token and Admin list from .env
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(',') if admin_id] # Fetch from env, comma-separated
CHAT_ID = os.getenv("CHAT_ID") # Default chat ID for sending alerts

# ✅ Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Global state variables (for simplicity, ideally use persistent storage)
auto_trade_enabled = False
halal_only_mode = False
hidden_markets = set() # Stores markets that are hidden (e.g., {"forex", "crypto"})
ict_filter_enabled = True # For ICT Filter
trade_log = [] # Stores daily trades for PDF report
daily_profits = [] # For general profit logging
goal_progress = [] # For daily profit goal tracker

# Goal Tracker (from Cutub 18)
GOAL_AMOUNT = Decimal(os.getenv("GOAL_AMOUNT", "650"))
GOAL_DAYS = int(os.getenv("GOAL_DAYS", "10"))
# Set a default start date or fetch from env if needed. Example:
START_DATE_STR = os.getenv("GOAL_START_DATE", "2025-06-20")
START_DATE = datetime.strptime(START_DATE_STR, "%Y-%m-%d")

# Profit File (from Cutub 2)
PROFIT_FILE = "profits.json"

# Web3 Setup (from Cutub 16)
INFURA_URL = os.getenv("INFURA_URL")
w3 = None # Initialize to None, set up in main
BOT_WALLET = os.getenv("WALLET_ADDRESS_ETH")
BOT_PRIVATE_KEY = os.getenv("PRIVATE_KEY_ETH")
WITHDRAW_TO = os.getenv("WITHDRAW_TO_ADDRESS_ETH", "0xReceiverWalletAddressHere")

# Notion API (from Cutub 14)
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Push App Webhook (from Cutub 13)
PUSH_APP_WEBHOOK_URL = os.getenv("PUSH_APP_WEBHOOK_URL")

# --- Telegram Bot Application & Flask Setup ---

# ✅ Telegram bot app initialization
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Flask app
flask_app = Flask(__name__)

# --- Helper Functions ---

# ✅ Admin Checker (from Cutub 1)
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ✅ Halal/Haram Checker (Advanced - consolidated from Cutub 19 & 20)
HARAM_KEYWORDS = [
    "casino", "bet", "gambling", "poker", "lottery", "loan", "riba", "interest",
    "liquor", "alcohol", "wine", "beer", "vodka", "whiskey", "xxx", "sex", "porn",
    "shisha", "cigarette", "hookah", "rum", "cocktail", "drunk", "bar", "pepe"
]
def is_coin_halal(name: str, description: str = "") -> bool:
    combined_text = f"{name} {description}".lower()
    for haram_word in HARAM_KEYWORDS:
        if re.search(rf"\b{re.escape(haram_word)}\b", combined_text): # Use re.escape for special chars
            return False
    return True

# ✅ Voice Alert Function (from Cutub 7 & 17)
async def send_voice_alert(text: str, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp:
            tts.save(tmp.name)
            with open(tmp.name, "rb") as audio:
                await context.bot.send_voice(chat_id=chat_id, voice=audio)
    except Exception as e:
        logger.error(f"Voice Alert Error: {e}")

# ✅ Voice text for TP/SL (from Cutub 17)
def get_voice_text(status: str):
    if status == "TP":
        return "Congratulations! Take Profit hit! 💰"
    elif status == "SL":
        return "Stop Loss hit. Don't worry, we'll get it next time. 😢"
    else:
        return "New signal alert."

# ✅ Profit Logger Functions (from Cutub 2)
def save_profit_to_file(amount: float):
    today = datetime.now().strftime("%Y-%m-%d")
    profits = load_profits_from_file()
    profits[today] = profits.get(today, 0) + amount
    with open(PROFIT_FILE, "w") as f:
        json.dump(profits, f)

def load_profits_from_file() -> dict:
    if not os.path.exists(PROFIT_FILE):
        return {}
    with open(PROFIT_FILE, "r") as f:
        return json.load(f)

# ✅ Function: Send Push Notification (from Cutub 13)
def send_push_notification(message: str) -> str:
    try:
        if not PUSH_APP_WEBHOOK_URL:
            logger.warning("PUSH_APP_WEBHOOK_URL not set. Skipping push notification.")
            return "❌ Push app URL not set."

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
        logger.error(f"[Push Error]: {e}")
        return f"[Push Error]: {e}"

# ✅ Function: Calculate Lot Size (from Cutub 15)
ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))

def calculate_lot_size(sl_distance_pips: float, pip_value: float = 10.0) -> float:
    if sl_distance_pips == 0:
        return 0.0
    risk_per_trade = DAILY_MAX_RISK
    lot_size = (risk_per_trade / Decimal(sl_distance_pips)) / Decimal(pip_value)
    return round(float(lot_size), 2)

# ✅ ICT-style detection logic (from Cutub 22)
def is_ict_compliant(signal: dict) -> bool:
    # Example basic ICT compliance logic
    return (
        signal.get("market") == "forex"
        and signal.get("order_block") is True
        and signal.get("fvg") is True
        and signal.get("liquidity") == "grabbed"
    )

def should_send_signal_based_on_filters(signal: dict) -> bool:
    market = signal.get("market", "").lower()
    symbol = signal.get("symbol", "").lower()
    description = signal.get("description", "") # Assuming description for advanced halal check

    # Market visibility filter
    if market in hidden_markets:
        logger.info(f"Skipped signal for {symbol} – {market.capitalize()} market is hidden.")
        return False

    # Halal-only filter (primarily for crypto, but can apply generally)
    if halal_only_mode and not is_coin_halal(symbol, description):
        logger.info(f"Skipped signal for {symbol} – Not halal and halal-only mode is ON.")
        return False

    # ICT filter (only for forex if enabled)
    if ict_filter_enabled and market == "forex":
        if not is_ict_compliant(signal):
            logger.info(f"Skipped forex signal for {symbol} – Not ICT compliant and ICT filter is ON.")
            return False
    return True

# ✅ Notion Integration (from Cutub 14)
def push_trade_to_notion(symbol: str, direction: str, timeframe: str, result: str, pnl: float):
    if not (NOTION_API_TOKEN and NOTION_DATABASE_ID):
        logger.warning("Notion API token or database ID not set. Skipping Notion push.")
        return

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
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
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"❌ Notion Push Failed: {response.status_code} - {response.text}")
        else:
            logger.info("✅ Trade pushed to Notion.")
    except Exception as e:
        logger.error(f"❌ Error pushing to Notion: {e}")


# --- Telegram Commands ---

# ✅ /start Command (from Cutub 1)
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

# ✅ /help Command (from Cutub 1)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Walalka Tradebot Activated!*\n\n"
        "Welcome to your personal AI trading assistant.\n\n"
        "📌 Amarrada muhiimka ah:\n"
        "/forex – Forex trade ideas\n"
        "/crypto – Crypto signals (Simulated)\n"
        "/stocks – Stock updates (Simulated)\n"
        "/memecoins – Memecoin alerts (Simulated)\n"
        "/polymarket – Polymarket insights (Simulated)\n"
        "/halalonly – Toggle Halal Coin Filter\n"
        "/profit – Log daily profit\n"
        "/profits – Show all profit logs\n"
        "/withdraw_eth – Auto withdraw ETH (Admin Only)\n"
        "/autotrade – Toggle Auto-Trade\n"
        "/report – Get daily PDF report\n"
        "/ictfilter – Toggle ICT Filter for Forex\n"
        "/marketvisibility – Toggle market signal visibility\n"
        "/search – Search for past signals\n"
        "/goal – Check profit goal progress\n"
        "/addprofit <amount> – Add profit to goal tracker\n"
        "\n🚀 Let's grow your capital together!"
    )
    await update.message.reply_markdown(help_text)

# ✅ Command: /profit (for daily log - from Cutub 2)
async def log_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].replace('.', '', 1).isdigit():
        await update.message.reply_text("❗ Usage: `/profit 120.5`", parse_mode="Markdown")
        return
    try:
        amount = float(context.args[0])
        save_profit_to_file(amount)
        await update.message.reply_text(f"✅ Profit of ${amount:.2f} saved for today.")
    except ValueError:
        await update.message.reply_text("❗ Please enter a valid number for profit. Usage: `/profit 120.5`", parse_mode="Markdown")

# ✅ Command: /profits (from Cutub 2)
async def show_profits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profits = load_profits_from_file()
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

# ✅ Forex Trade Idea Sender (from Cutub 3)
async def send_forex_trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "forex" in hidden_markets:
        await update.message.reply_text("📵 Forex signals are currently hidden.")
        return

    # Simulated Forex signal
    pair = "EURUSD"
    direction = "BUY"
    entry = 1.0950
    tp = 1.1000
    sl = 1.0910
    signal_data = {
        "symbol": pair, "direction": direction, "entry": entry, "tp": tp, "sl": sl,
        "market": "forex", "timeframe": "15min", # Added for ICT filtering simulation
        "liquidity": "grabbed", "order_block": True, "fvg": True, "time": "10:30"
    }

    if not should_send_signal_based_on_filters(signal_data):
        await update.message.reply_text("Forex signal filtered out by current settings (e.g., ICT filter).")
        return

    halal_status = "🟢 Halal" # Forex is generally considered halal

    msg = (
        f"📈 Forex Trade Alert\n"
        f"Pair: {pair}\n"
        f"Direction: {direction}\n"
        f"Entry: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n"
        f"Status: {halal_status}"
    )

    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data="FOREX_CONFIRM")],
        [InlineKeyboardButton("❌ Ignore", callback_data="FOREX_IGNORE")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(msg, reply_markup=reply_markup)
    await send_voice_alert(get_voice_text("signal"), context, str(update.effective_chat.id)) # Alert on new signal

# ✅ Command to toggle autotrade (from Cutub 4)
async def toggle_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = "✅ AutoTrade Mode is ON" if auto_trade_enabled else "❌ AutoTrade Mode is OFF"
    await update.message.reply_text(status)

# ✅ Command to toggle Halal Only Mode (from Cutub 9 & 20)
async def toggle_halal_only_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode is ON — Only halal coins will be shown." if halal_only_mode else "❌ Halal Only Mode is OFF — All coins will be shown."
    await update.message.reply_text(status)

# ✅ Command to toggle ICT Filter (from Cutub 22)
async def toggle_ict_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ict_filter_enabled
    ict_filter_enabled = not ict_filter_enabled
    status = "✅ ICT Filter ENABLED" if ict_filter_enabled else "❌ ICT Filter DISABLED"
    await update.message.reply_text(f"{status}\nOnly high-probability ICT-style Forex trades will be shown.")

# ✅ Command: /withdraw_eth (from Cutub 16)
async def withdraw_eth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not w3 or not w3.is_connected():
        await update.message.reply_text("❌ Ethereum connection not established. Check INFURA_URL.")
        return
    if not (BOT_WALLET and BOT_PRIVATE_KEY and WITHDRAW_TO):
        await update.message.reply_text("❌ ETH wallet details (address, private key, or recipient) are not set in environment variables.")
        return

    try:
        sender_address = w3.to_checksum_address(BOT_WALLET)
        receiver_address = w3.to_checksum_address(WITHDRAW_TO)

        # ✅ Check balance
        balance = w3.eth.get_balance(sender_address)
        eth_balance = w3.from_wei(balance, 'ether')

        # Estimate gas for a simple transfer (21000 gas units)
        gas_price = w3.eth.gas_price
        estimated_gas_cost_wei = 21000 * gas_price

        if balance < estimated_gas_cost_wei + w3.to_wei(0.001, 'ether'): # Ensure enough for gas + a small minimum
            await update.message.reply_text(f"❌ Not enough ETH to withdraw. Current balance: {eth_balance:.4f} ETH. Need more for gas.")
            return

        value_to_send_wei = balance - estimated_gas_cost_wei
        if value_to_send_wei <= 0:
            await update.message.reply_text("❌ Balance is too low after accounting for gas fees to make a meaningful withdrawal.")
            return

        # Prepare transaction
        nonce = w3.eth.get_transaction_count(sender_address)
        tx = {
            'nonce': nonce,
            'to': receiver_address,
            'value': value_to_send_wei,
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': w3.eth.chain_id # Recommended for EIP-155 replay protection
        }

        # ✅ Sign + send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=BOT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        await update.message.reply_text(f"✅ ETH Withdrawal Initiated!\nAmount: {w3.from_wei(value_to_send_wei, 'ether'):.4f} ETH\nTo: {receiver_address}\n🔗 TX Hash: {w3.to_hex(tx_hash)}")

    except Exception as e:
        logger.error(f"Error during ETH withdrawal: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error during withdrawal: {str(e)}")


# ✅ Command: /report (from Cutub 14)
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_daily_report(trades: list):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{REPORTS_DIR}/TradeReport_{today}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"📄 Trade Report – {today}", ln=True, align="C")
    pdf.ln(10)

    if not trades:
        pdf.multi_cell(0, 10, txt="No trades logged for today.")
    else:
        for i, trade in enumerate(trades, 1):
            text = (
                f"{i}. Pair: {trade.get('symbol', 'N/A')}\n"
                f"    Direction: {trade.get('direction', 'N/A')}\n"
                f"    Timeframe: {trade.get('timeframe', 'N/A')}\n"
                f"    Result: {trade.get('result', 'N/A')}\n"
                f"    P&L: ${trade.get('pnl', 0.0):.2f}\n"
            )
            pdf.multi_cell(0, 10, txt=text)
            pdf.ln(2)

    pdf.output(filename)
    return filename

async def send_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trade_log:
        await update.message.reply_text("Ma jiro trade maanta la qaaday.")
        return

    file_path = generate_daily_report(trade_log)
    with open(file_path, "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=os.path.basename(file_path))
    os.remove(file_path) # Clean up the generated PDF

# ✅ Jadwal: Automatic report 23:59 habeenkii
def daily_report_job():
    global trade_log
    if trade_log:
        file_path = generate_daily_report(trade_log)
        # In a real scenario, you'd want to send this to a specific chat_id
        # For this example, let's just log that it was generated.
        logger.info(f"Daily report generated: {file_path}. Trades: {len(trade_log)}")
        # You might want to send it to ADMINS here
        # for admin_id in ADMINS:
        #     with open(file_path, "rb") as f:
        #         asyncio.create_task(app.bot.send_document(chat_id=admin_id, document=f, filename=os.path.basename(file_path)))
        # os.remove(file_path) # Clean up
    trade_log.clear() # Reset for the new day

# Setup scheduler
scheduler = BackgroundScheduler()
# Schedule for 23:59 daily, timezone-aware
# It's important to set a timezone or use UTC and adjust accordingly
scheduler.add_job(daily_report_job, "cron", hour=23, minute=59, timezone='Asia/Riyadh') # Example: Set your desired timezone
# scheduler.add_job(daily_report_job, "interval", minutes=1) # For testing, runs every minute
scheduler.start()


# ✅ Command: /marketvisibility (from Cutub 21)
async def toggle_market_visibility_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markets = ["Forex", "Crypto", "Stocks", "Polymarket", "Memecoins"]
    buttons = []

    for mkt in markets:
        is_hidden = mkt.lower() in hidden_markets
        label = f"{'❌' if is_hidden else '✅'} {mkt}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"TOGGLE_MARKET:{mkt.lower()}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Toggle Market Visibility:", reply_markup=reply_markup)

# ✅ Command: /search (from Cutub 23)
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Please type the symbol or coin name you want to search.")
    # Here you might set a state for the user to expect the next message as a search query
    # For now, it will just listen to the next message.

# ✅ Text Handler: Receives Search Query (from Cutub 23)
async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().upper()

    # Example fake signal DB (replace with actual search in your data)
    fake_signals = {
        "EURUSD": {"market": "forex", "dir": "BUY", "tf": "5min", "price": 1.0960},
        "BTC": {"market": "crypto", "dir": "SELL", "tf": "15min", "price": 60000},
        "TSLA": {"market": "stocks", "dir": "BUY", "tf": "1H", "price": 180},
        "TRUMP2024": {"market": "polymarket", "dir": "YES", "tf": "Event", "price": 0.55},
        "WIF": {"market": "memecoins", "dir": "BUY", "tf": "Spot", "price": 3.2},
        "LUCKYBETTOKEN": {"market": "crypto", "dir": "BUY", "tf": "Daily", "price": 0.00123, "description": "A gambling token"},
        "ETH": {"market": "crypto", "dir": "HOLD", "tf": "Long Term", "price": 3500, "description": "Decentralized platform"},
    }

    if query in fake_signals:
        signal = fake_signals[query]
        halal_status = "🟢 Halal" if is_coin_halal(query, signal.get("description", "")) else "🔴 Haram" if signal.get("market").lower() == "crypto" else ""

        message = (
            f"🔍 Found Signal for *{query}*\n"
            f"Market: {signal['market'].capitalize()}\n"
            f"Direction: {signal['dir']}\n"
            f"Timeframe: {signal['tf']}\n"
            f"Current Price: ${signal['price']}\n"
            f"Status: {halal_status}"
        )
    else:
        message = f"❌ No signal found for *{query}*. Please try another symbol."

    await update.message.reply_markdown(message)


# ✅ Command: /goal (from Cutub 24/25)
def calculate_goal_status():
    total_profit = sum(p[1] for p in goal_progress)
    days_passed = (datetime.now() - START_DATE).days + 1
    daily_target = GOAL_AMOUNT / GOAL_DAYS
    projected = days_passed * daily_target
    percent = round((total_profit / float(GOAL_AMOUNT)) * 100, 1)
    return total_profit, projected, percent, days_passed

async def goal_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_profit, projected, percent, days_passed = calculate_goal_status()
    msg = (
        f"🎯 *Goal Tracker*\n"
        f"Target: ${GOAL_AMOUNT:.2f} in {GOAL_DAYS} days\n"
        f"Start Date: {START_DATE.strftime('%Y-%m-%d')}\n"
        f"Day: {days_passed}\n"
        f"Profit: ${total_profit:.2f}\n"
        f"Expected so far: ${projected:.2f}\n"
        f"Completion: {percent}%"
    )
    await update.message.reply_markdown(msg)

# ✅ Command: /addprofit <amount> (for goal tracker - from Cutub 24/25)
async def add_profit_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].replace('.', '', 1).isdigit():
        await update.message.reply_text("❌ Usage: `/addprofit 120.5`", parse_mode="Markdown")
        return
    try:
        amount = float(context.args[0])
        today_str = datetime.now().strftime("%Y-%m-%d")
        goal_progress.append((today_str, amount))
        await update.message.reply_text(f"✅ Added ${amount:.2f} to goal progress.")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for profit. Usage: `/addprofit 120.5`", parse_mode="Markdown")


# --- Callback Query Handlers ---

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Always answer the callback query

    data = query.data.split(":")
    action = data[0]

    if action == "FOREX_CONFIRM":
        await query.edit_message_text(f"{query.message.text}\n\n✅ Trade Confirmed!")
        # Log trade to PDF and Notion
        # Extract details from message if needed, or pass from initial signal
        trade_details = {
            "symbol": "EURUSD", "direction": "BUY", "timeframe": "15min",
            "result": "Pending", "pnl": 0.0 # Update P&L later
        }
        trade_log.append(trade_details)
        push_trade_to_notion(trade_details["symbol"], trade_details["direction"], trade_details["timeframe"], trade_details["result"], trade_details["pnl"])

    elif action == "FOREX_IGNORE":
        await query.edit_message_text(f"{query.message.text}\n\n❌ Trade Ignored.")

    elif action == "CONFIRM": # For generic signals from webhook
        symbol = data[1]
        direction = data[2]
        await query.edit_message_text(f"{query.message.text}\n\n✅ Confirmed {direction} {symbol}")
        # Logic to execute trade if auto_trade_enabled
        if auto_trade_enabled:
            await query.message.reply_text(f"🤖 AutoTrade: Executing {direction} {symbol}...")
            # Simulate trade execution and result
            await asyncio.sleep(2) # Simulate delay
            result_status = "WIN" if "BUY" in direction else "LOSS"
            pnl_amount = 50.0 if result_status == "WIN" else -25.0
            await query.message.reply_text(f"🚀 AutoTrade Result for {symbol}: {result_status}! P&L: ${pnl_amount:.2f}")
            await send_voice_alert(get_voice_text(result_status), context, str(query.message.chat.id))

            # Log this trade
            trade_log.append({
                "symbol": symbol, "direction": direction, "timeframe": "Webhook",
                "result": result_status, "pnl": pnl_amount
            })
            save_profit_to_file(pnl_amount) # Log profit to general logger
            goal_progress.append((datetime.now().strftime("%Y-%m-%d"), pnl_amount)) # Log profit to goal tracker
            push_trade_to_notion(symbol, direction, "Webhook", result_status, pnl_amount)
            send_push_notification(f"AutoTrade result: {symbol} - {result_status}!")


    elif action == "IGNORE": # For generic signals from webhook
        await query.edit_message_text(f"{query.message.text}\n\n❌ Signal Ignored.")

    elif action == "copy": # For memecoin address copy
        address_to_copy = data[1]
        await query.answer(f"Address copied: {address_to_copy}", show_alert=True)
        # Telegram does not allow directly copying text to clipboard via bot, this just confirms.
        # User needs to manually copy from the message.

    elif action == "BUY": # For memecoin "Buy Now" button
        coin_name = data[1]
        await query.edit_message_text(f"{query.message.text}\n\n✅ Attempting to buy {coin_name}...")
        if auto_trade_enabled:
             await query.message.reply_text(f"🤖 AutoTrade: Executing BUY for {coin_name}...")
             # Simulate memecoin trade (e.g., using a DEX aggregator API)
             # Add actual trading logic here
        else:
             await query.message.reply_text(f"Auto-Trade is OFF. Please buy {coin_name} manually.")

    elif action == "SKIP": # For memecoin "Skip" button
        await query.edit_message_text(f"{query.message.text}\n\n🚫 Skipped this memecoin.")

    elif action == "TOGGLE_MARKET": # For market visibility
        market = data[1]
        if market in hidden_markets:
            hidden_markets.remove(market)
            await query.edit_message_text(f"✅ {market.capitalize()} market is now **VISIBLE**.", parse_mode="Markdown")
        else:
            hidden_markets.add(market)
            await query.edit_message_text(f"❌ {market.capitalize()} market is now **HIDDEN**.", parse_mode="Markdown")


# --- Simulated Market Commands (for demonstration) ---
# In a real bot, these would likely be driven by webhooks or external APIs.

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "crypto" in hidden_markets:
        await update.message.reply_text("📵 Crypto signals are currently hidden.")
        return
    # Simulate a crypto signal
    coin_name = "ETH"
    description = "Leading smart contract platform"
    signal_data = {"symbol": coin_name, "direction": "BUY", "timeframe": "Daily", "market": "crypto", "description": description}

    if not should_send_signal_based_on_filters(signal_data):
        await update.message.reply_text("Crypto signal filtered out by current settings (e.g., Halal filter).")
        return

    status = "🟢 Halal" if is_coin_halal(coin_name, description) else "🔴 Haram"
    msg = f"📈 Crypto Alert: *{coin_name}*\nDirection: BUY\nTimeframe: Daily\nStatus: {status}"
    buttons = [[InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{coin_name}:BUY")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_markdown(msg, reply_markup=reply_markup)

async def stocks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "stocks" in hidden_markets:
        await update.message.reply_text("📵 Stock signals are currently hidden.")
        return
    # Simulate a stock signal
    signal_data = {"symbol": "GOOGL", "direction": "BUY", "timeframe": "4H", "market": "stocks"}
    if not should_send_signal_based_on_filters(signal_data):
        await update.message.reply_text("Stock signal filtered out by current settings.")
        return
    msg = "📊 Stock Alert: *GOOGL*\nDirection: BUY\nTarget: $180\nSL: $165"
    buttons = [[InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM:GOOGL:BUY")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_markdown(msg, reply_markup=reply_markup)

async def memecoins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "memecoins" in hidden_markets:
        await update.message.reply_text("📵 Memecoin alerts are currently hidden.")
        return
    # Simulate a memecoin signal
    coin_data = {
        "name": "Hussein7Coin",
        "address": "0xExampleHussein7CoinAddress",
        "chain": "Solana",
        "reason": "🚀 New listing, strong community",
        "chart": "https://dexscreener.com/solana/Hussein7CoinAddress",
        "description": "The official coin of Hussein7"
    }

    signal_data = {"symbol": coin_data["name"], "direction": "BUY", "timeframe": "Spot", "market": "memecoins", "description": coin_data["description"]}
    if not should_send_signal_based_on_filters(signal_data):
        await update.message.reply_text("Memecoin signal filtered out by current settings (e.g., Halal filter).")
        return

    status = "🟢 Halal" if is_coin_halal(coin_data["name"], coin_data["description"]) else "🔴 Haram"
    msg = (
        f"🚨 *New Memecoin Detected!*\n\n💎 *{coin_data['name']}*\n"
        f"🔗 Chain: {coin_data['chain']}\n"
        f"🪙 Address: `{coin_data['address']}`\n"
        f"📈 Reason: {coin_data['reason']}\n"
        f"🔍 Status: {status}\n"
        f"📊 Chart: {coin_data['chart']}"
    )
    buttons = [[
        InlineKeyboardButton("📈 View Chart", url=coin_data['chart']),
        InlineKeyboardButton("📥 Copy Address", callback_data=f"copy:{coin_data['address']}")
    ],[
        InlineKeyboardButton("✅ Buy Now", callback_data=f"BUY:{coin_data['name']}"),
        InlineKeyboardButton("🚫 Skip", callback_data="SKIP")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_markdown(msg, reply_markup=reply_markup)

async def polymarket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "polymarket" in hidden_markets:
        await update.message.reply_text("📵 Polymarket signals are currently hidden.")
        return
    # Simulate a Polymarket signal
    signal_data = {"symbol": "US_ELECTION_2024", "direction": "YES_TRUMP", "timeframe": "Event", "market": "polymarket"}
    if not should_send_signal_based_on_filters(signal_data):
        await update.message.reply_text("Polymarket signal filtered out by current settings.")
        return
    msg = "📊 Polymarket Insight: *Will Trump win US 2024 Election?*\nPrediction: YES (55% implied probability)"
    buttons = [[InlineKeyboardButton("✅ Trade Now", url="https://polymarket.com/market/trump-win")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_markdown(msg, reply_markup=reply_markup)


# --- Webhook Handlers (Flask Routes) ---

# ✅ Home route (for Render/Health Check)
@flask_app.route('/')
def home():
    return "✅ Hussein7 TradeBot is live!"

# ✅ Telegram webhook handler (from webhook.py and main.py snippets)
@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    update_json = request.get_json(force=True)
    try:
        update = Update.de_json(update_json, app.bot)
        await app.process_update(update)
        return "OK"
    except Exception as e:
        logger.error(f"Telegram Webhook Error: {str(e)}", exc_info=True)
        return f"ERROR: {str(e)}", 500

# ✅ Signal webhook endpoint (from signal_webhook.py)
@flask_app.route('/signal-webhook', methods=['POST'])
async def signal_webhook(): # Changed to async for send_voice_alert
    try:
        data = request.get_json()
        logger.info(f"Received signal webhook data: {data}")

        # Extract fields from incoming JSON
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")
        sl = data.get("stop_loss", "N/A")
        tp = data.get("take_profit", "N/A")
        entry_price = data.get("entry_price", "N/A")
        description = data.get("description", "") # Added for advanced halal filter

        signal_data_for_filter = {
            "symbol": symbol, "direction": direction, "timeframe": timeframe,
            "market": market, "description": description,
            # Add other ICT relevant fields if they come from webhook
            "liquidity": data.get("liquidity"), "order_block": data.get("order_block"), "fvg": data.get("fvg")
        }

        if not should_send_signal_based_on_filters(signal_data_for_filter):
            return f"Signal for {symbol} filtered out by bot settings."

        # Halal status for crypto/memecoins
        halal_status_text = ""
        if market.lower() in ["crypto", "memecoins"]:
            halal_status_text = "🟢 Halal" if is_coin_halal(symbol, description) else "🔴 Haram"

        # Construct message
        message = (
            f"🚨 New {market.upper()} Signal\n"
            f"Pair: {symbol}\n"
            f"Timeframe: {timeframe}\n"
            f"Direction: {direction}\n"
            f"Entry: {entry_price}\n"
            f"TP: {tp}\nSL: {sl}\n"
            f"{halal_status_text}"
        )

        # Buttons for confirmation
        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Send message to Telegram chat
        if CHAT_ID:
            await app.bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup)
            await send_voice_alert(get_voice_text("signal"), app.bot, CHAT_ID) # Pass app.bot as context
        else:
            logger.error("CHAT_ID not set in environment variables. Cannot send webhook signal to Telegram.")
            return "❌ CHAT_ID not set, signal not sent.", 500

        return "✅ Signal sent to Telegram"
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}", exc_info=True)
        return f"❌ Webhook error: {str(e)}", 500


# --- Main Execution ---

async def main():
    # Set up Web3 connection if INFURA_URL is provided
    global w3
    if INFURA_URL:
        try:
            w3 = Web3(Web3.HTTPProvider(INFURA_URL))
            if not w3.is_connected():
                logger.warning("Failed to connect to Infura. ETH withdrawal might not work.")
        except Exception as e:
            logger.error(f"Error connecting to Web3: {e}")

    # Add all command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profit", log_profit_command)) # General profit logger
    app.add_handler(CommandHandler("profits", show_profits_command))
    app.add_handler(CommandHandler("forex", send_forex_trade_command))
    app.add_handler(CommandHandler("autotrade", toggle_autotrade))
    app.add_handler(CommandHandler("halalonly", toggle_halal_only_command))
    app.add_handler(CommandHandler("withdraw_eth", withdraw_eth_command))
    app.add_handler(CommandHandler("report", send_report_command))
    app.add_handler(CommandHandler("marketvisibility", toggle_market_visibility_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_search_query)) # Handles text not starting with /
    app.add_handler(CommandHandler("ictfilter", toggle_ict_filter_command))
    app.add_handler(CommandHandler("goal", goal_status_command))
    app.add_handler(CommandHandler("addprofit", add_profit_goal_command)) # For goal tracker

    # Simulated market commands (for demonstration/testing via Telegram)
    app.add_handler(CommandHandler("crypto", crypto_command))
    app.add_handler(CommandHandler("stocks", stocks_command))
    app.add_handler(CommandHandler("memecoins", memecoins_command))
    app.add_handler(CommandHandler("polymarket", polymarket_command))


    # Add callback query handler for inline keyboard buttons
    app.add_handler(CallbackQueryHandler(handle_callback_query))


    # Set webhook for Telegram updates
    WEBHOOK_URL = os.getenv("WEBHOOK_URL") # This should be your public URL /telegram-webhook
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL environment variable is not set. Webhook will not be set.")
        # Fallback to polling for local testing if webhook not set
        # For production, webhook is essential.
        await app.run_polling()
    else:
        full_webhook_url = f"{WEBHOOK_URL}/telegram-webhook"
        logger.info(f"Setting webhook to: {full_webhook_url}")
        await app.bot.set_webhook(url=full_webhook_url, allowed_updates=Update.ALL_TYPES)
        logger.info("Telegram webhook set successfully.")

    # Start the Flask app (non-blocking in an async context)
    # The Flask app needs to be run in a way that doesn't block the asyncio event loop.
    # Uvicorn (or Gunicorn with uvicorn workers) is typically used for this in production.
    # For a simple single-file setup like this, we'll let Flask run the server,
    # but the `run_webhook` part of `python-telegram-bot` will process incoming updates.
    # The flask_app.run() call should ideally be within a separate process or handled by a WSGI server.
    # For demonstration/simple deployment, we run it in the main thread and assume it's exposed externally.

if __name__ == "__main__":
    # This block ensures that everything runs correctly when the script is executed.
    # Flask's `app.run()` is blocking, so we need to ensure the Telegram bot's async loop
    # is also running. A common pattern for combined Flask/Telegram is to run Flask
    # with an ASGI server (like uvicorn) and have the Telegram bot's `process_update`
    # called from Flask's webhook route.

    # To run Flask and the Telegram Application in the same script without blocking,
    # you'd typically use `uvicorn` to serve the Flask app, and inside the Flask app's
    # webhook route, call `app.process_update`.

    # For a simple `python main.py` execution, Flask's `app.run()` will block.
    # A robust setup for production would look like this (using uvicorn):
    # `uvicorn main:flask_app --host 0.0.0.0 --port 10000`
    # And then the `main()` async function would just set the webhook.

    # For this consolidated file, let's explicitly run both, but understand
    # that `flask_app.run()` will block, so the `asyncio.run(main())` will
    # set the webhook, but the event loop won't be actively polling unless
    # flask's processing of updates keeps it alive.
    # The current setup relies on Flask's endpoint triggering app.process_update.

    # Run the main async setup for the Telegram bot first
    # This will set the webhook before Flask starts listening
    asyncio.run(main())

    # Then run the Flask application. This is a blocking call.
    # For production, consider using Gunicorn/Uvicorn to run Flask.
    # Example: uvicorn main:flask_app --host 0.0.0.0 --port $PORT
    PORT = int(os.getenv("PORT", 10000))
    logger.info(f"Starting Flask app on 0.0.0.0:{PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False) # Set debug=True for local development
