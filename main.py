import os
import json
import datetime
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
from flask import Flask, request
from web3 import Web3
import threading
import nest_asyncio
import asyncio
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()
nest_asyncio.apply()

# ✅ ENV Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
INFURA_URL = os.getenv("INFURA_URL")
WALLET_ADDRESS_ETH = os.getenv("WALLET_ADDRESS_ETH")
PRIVATE_KEY_ETH = os.getenv("PRIVATE_KEY_ETH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ✅ Web3 Setup
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ Telegram Bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Profit & Trade Logs
daily_profits = {}
trade_logs = []

# ✅ PDF Report Generator
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trade_logs:
        await update.message.reply_text("🚫 No trades to report.")
        return
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Daily Trade Report", ln=True, align='C')
    pdf.ln()
    for trade in trade_logs:
        line = f"{trade['time']} | {trade['pair']} | {trade['direction']} | {trade['status']}"
        pdf.cell(200, 10, txt=line, ln=True)
    file_path = "/tmp/report.pdf"
    pdf.output(file_path)
    with open(file_path, 'rb') as f:
        await update.message.reply_document(document=f, filename="report.pdf")

# ✅ Profit Tracker
async def add_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /profit 50")
        return
    amount = Decimal(context.args[0])
    today = datetime.date.today().strftime("%Y-%m-%d")
    if today not in daily_profits:
        daily_profits[today] = Decimal("0")
    daily_profits[today] += amount
    await update.message.reply_text(f"✅ Profit added: ${amount} for {today}")

async def view_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_profits:
        await update.message.reply_text("🚫 No profits recorded yet.")
        return
    msg = "📊 Daily Profits:\n"
    for day, amount in daily_profits.items():
        msg += f"{day}: ${amount}\n"
    await update.message.reply_text(msg)

# ✅ ETH Withdraw
async def withdraw_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /withdraw_eth 0.01 0xYourOtherAddress")
        return
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
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY_ETH)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        await update.message.reply_text(f"✅ Withdraw Success! TX: {w3.to_hex(tx_hash)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ✅ Auto Trade Toggle
auto_trade_enabled = True
async def toggle_auto_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = "✅ ON" if auto_trade_enabled else "⛔ OFF"
    await update.message.reply_text(f"Auto-Trade is now: {status}")

# ✅ Market Sections
async def forex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Forex Market:\n- EURUSD: ⬆️ BUY\n- GBPUSD: ⬇️ SELL\n- USDJPY: ⬆️ BUY")

async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("₿ Crypto Market:\n- BTC: ⬆️ Breakout\n- ETH: ⬇️ Rejection\n- SOL: ⬆️ Volume Surge")

async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Stocks:\n- TSLA: ⬆️ Bullish\n- AAPL: ⬇️ Pullback\n- AMZN: ⬆️ Recovery")

async def polymarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔮 Polymarket:\n- Trump Wins 2024? 65%\n- BTC > $100k by Dec? 20%")

async def memecoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦍 Memecoins:\n- $PEPE (Halal) ⬆️\n- $FLOKI (Haram) ⬇️\n- $LOOT (Trending)")

# ✅ Basic Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Bot is now active via webhook ✅")

async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚨 New Trade Opportunity!\nPair: GOLD\nTime: 5min\nStatus: ⬆️ BUY Setup"
    buttons = [[
        InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM:GOLD:BUY"),
        InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
    ]]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(msg, reply_markup=markup)
    trade_logs.append({
        'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        'pair': 'GOLD',
        'direction': 'BUY',
        'status': 'SENT'
    })

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("CONFIRM"):
        _, symbol, direction = query.data.split(":")
        await query.edit_message_text(text=f"✅ Confirmed: {symbol} → {direction}")
    elif query.data == "IGNORE":
        await query.edit_message_text(text="❌ Signal ignored.")

# ✅ Register All Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("notify", notify))
app.add_handler(CommandHandler("profit", add_profit))
app.add_handler(CommandHandler("profits", view_profits))
app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))
app.add_handler(CommandHandler("autotrade", toggle_auto_trade))
app.add_handler(CommandHandler("forex", forex))
app.add_handler(CommandHandler("crypto", crypto))
app.add_handler(CommandHandler("stocks", stocks))
app.add_handler(CommandHandler("polymarket", polymarket))
app.add_handler(CommandHandler("memecoins", memecoins))
app.add_handler(CommandHandler("report", report))
app.add_handler(CallbackQueryHandler(button_handler))

# ✅ Flask Webhook Setup
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is live!"

@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await app.process_update(update)
    return "OK"

# ✅ Start Everything
async def run():
    await app.bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    asyncio.run(run())
    flask_app.run(host="0.0.0.0", port=10000)
