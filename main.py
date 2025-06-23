# ✅ main.py – Telegram Bot Full Setup

import os
import json
import datetime
from decimal import Decimal
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from web3 import Web3
import nest_asyncio
nest_asyncio.apply()

# ✅ Load ENV variables
INFURA_URL = os.getenv("INFURA_URL")
WALLET_ADDRESS_ETH = os.getenv("WALLET_ADDRESS_ETH")
PRIVATE_KEY_ETH = os.getenv("PRIVATE_KEY_ETH")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Web3 setup
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ Profit Tracker
daily_profits = {}

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

# ✅ Auto-Trade Toggle
auto_trade_enabled = True

async def toggle_auto_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_trade_enabled
    auto_trade_enabled = not auto_trade_enabled
    status = "✅ ON" if auto_trade_enabled else "⛔ OFF"
    await update.message.reply_text(f"Auto-Trade is now: {status}")

# ✅ Start Bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("profit", add_profit))
app.add_handler(CommandHandler("profits", view_profits))
app.add_handler(CommandHandler("withdraw_eth", withdraw_eth))
app.add_handler(CommandHandler("autotrade", toggle_auto_trade))

from flask import Flask
import threading

app_web = Flask('dummy')  # Dummy Flask app to open a port

@app_web.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app_web.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()
# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Bot is now active.")

# ✅ Notification Command (Push Alert)
async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 New Trade Opportunity!\nPair: GOLD\nTime: 5min\nStatus: ⬆️ BUY Setup")

# ✅ Register Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("notify", notify))

app.run_polling()
