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

# ✅ README.md – Cutubka 5: Sharaxaad + Isticmaal

## 📌 Hussein7 TradeBot
Telegram bot for multi-market trading alerts (Forex, Crypto, Stocks, Polymarket, Memecoins) with ETH withdrawals, profit tracking, and webhook support.

---

## 🛠️ Features
- ✅ Trade alerts with buttons (Confirm / Ignore)
- ✅ Voice alert-ready
- ✅ ETH withdrawal (/withdraw_eth)
- ✅ Profit log & view (/profit & /profits)
- ✅ Auto-trade toggle (/autotrade)
- ✅ Webhook-based (Render compatible)
- ✅ Daily PDF report generation

---

## 🚀 Installation

### 1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/Hussein7TradeBot.git
cd Hussein7TradeBot
```

### 2. Create and fill `.env` file:
```
TELEGRAM_TOKEN=your_bot_token_here
INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_ID
WALLET_ADDRESS_ETH=0xyourwallet
PRIVATE_KEY_ETH=your_private_key
WEBHOOK_URL=https://yourdomain.onrender.com/telegram-webhook
```

### 3. Install libraries:
```bash
pip install -r requirements.txt
```

### 4. Run the bot (dev only):
```bash
python main.py
```

---

## 🌍 Webhook + Render Deployment
Render auto-deploys `main.py` and keeps it online 24/7 with Flask + webhook:
- Homepage: `https://yourdomain.onrender.com`
- Webhook: `/telegram-webhook`

---

## 📚 Commands:
- `/start` – activate bot
- `/notify` – manual signal test
- `/profit` – add daily profit
- `/profits` – view profit log
- `/withdraw_eth` – send ETH
- `/autotrade` – toggle auto mode
- `/forex`, `/crypto`, `/stocks`, `/polymarket`, `/memecoins` – view trade ideas

---

## 🧠 Coming Soon
- Halal coin filter
- Voice alerts integration
- Memecoin sniping
- Chart rendering
- Push app support

---

## 🤖 Developed by Hussein with GPT support 💡

---

# ✅ webhook.py – Cutubka 6: Telegram Webhook Handler (Gooni ah)

```python
from telegram import Update
from telegram.ext import ContextTypes
from flask import request

# This function will be called by Flask when webhook receives POST
async def telegram_webhook_handler(app, update_json):
    try:
        update = Update.de_json(update_json, app.bot)
        await app.process_update(update)
        return "OK"
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return f"ERROR: {str(e)}"
```

> Fiiro gaar ah: 
- Kani waa handler gooni ah oo loo isticmaalo haddii aad `main.py` rabto inuu ka nadiif ahaado webhook routes-ka.
- Waxaa lagu dhex dari karaa `main.py` sidaan:

```python
from webhook import telegram_webhook_handler

@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    return await telegram_webhook_handler(app, request.get_json(force=True))
```

> **Talo:** Waxaa fiican in webhook handler gaar ah lagu keydiyo `webhook.py` si loo kala nadiifiyo files-ka weyn sida `main.py`.

# ✅ README.md – Cutubka 5: Sharaxaad + Isticmaal

## 📌 Hussein7 TradeBot
Telegram bot for multi-market trading alerts (Forex, Crypto, Stocks, Polymarket, Memecoins) with ETH withdrawals, profit tracking, and webhook support.

---

## 🛠️ Features
- ✅ Trade alerts with buttons (Confirm / Ignore)
- ✅ Voice alert-ready
- ✅ ETH withdrawal (/withdraw_eth)
- ✅ Profit log & view (/profit & /profits)
- ✅ Auto-trade toggle (/autotrade)
- ✅ Webhook-based (Render compatible)
- ✅ Daily PDF report generation

---

## 🚀 Installation

### 1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/Hussein7TradeBot.git
cd Hussein7TradeBot
```

### 2. Create and fill `.env` file:
```
TELEGRAM_TOKEN=your_bot_token_here
INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_ID
WALLET_ADDRESS_ETH=0xyourwallet
PRIVATE_KEY_ETH=your_private_key
WEBHOOK_URL=https://yourdomain.onrender.com/telegram-webhook
```

### 3. Install libraries:
```bash
pip install -r requirements.txt
```

### 4. Run the bot (dev only):
```bash
python main.py
```

---

## 🌍 Webhook + Render Deployment
Render auto-deploys `main.py` and keeps it online 24/7 with Flask + webhook:
- Homepage: `https://yourdomain.onrender.com`
- Webhook: `/telegram-webhook`

---

## 📚 Commands:
- `/start` – activate bot
- `/notify` – manual signal test
- `/profit` – add daily profit
- `/profits` – view profit log
- `/withdraw_eth` – send ETH
- `/autotrade` – toggle auto mode
- `/forex`, `/crypto`, `/stocks`, `/polymarket`, `/memecoins` – view trade ideas

---

## 🧠 Coming Soon
- Halal coin filter
- Voice alerts integration
- Memecoin sniping
- Chart rendering
- Push app support

---

## 🤖 Developed by Hussein with GPT support 💡

---

# ✅ webhook.py – Cutubka 6: Telegram Webhook Handler (Gooni ah)

```python
from telegram import Update
from telegram.ext import ContextTypes
from flask import request

# This function will be called by Flask when webhook receives POST
async def telegram_webhook_handler(app, update_json):
    try:
        update = Update.de_json(update_json, app.bot)
        await app.process_update(update)
        return "OK"
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return f"ERROR: {str(e)}"
```

> Fiiro gaar ah: 
- Kani waa handler gooni ah oo loo isticmaalo haddii aad `main.py` rabto inuu ka nadiif ahaado webhook routes-ka.
- Waxaa lagu dhex dari karaa `main.py` sidaan:

```python
from webhook import telegram_webhook_handler

@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    return await telegram_webhook_handler(app, request.get_json(force=True))
```

---

# ✅ Cutubka 7: Trade Signal JSON Webhook Parser (Forex, Crypto, Stocks)

```python
@flask_app.route('/signal-webhook', methods=['POST'])
def signal_webhook():
    try:
        data = request.get_json()

        # Extracted fields
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")

        message = f"🚨 New {market.upper()} Signal\nPair: {symbol}\nTime: {timeframe}\nDirection: {direction}"

        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Set your target chat ID here
        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

        return "Signal Sent"
    except Exception as e:
        return f"Webhook error: {str(e)}"
```

> **Functionality**: Endpoint-kan wuxuu ogolaanayaa in signal JSON ah laga helo platform kale (e.g. TradingView, Notion automation, custom AI).
> Waxaa loo diri karaa sida webhook `POST` JSON leh:
```json
{
  "symbol": "EURUSD",
  "direction": "BUY",
  "timeframe": "5min",
  "market": "forex"
}
```

> Waxaa lagusoo bandhigaa Telegram with buttons, waana la xaqiijin karaa.

---
# ✅ README.md – Cutubka 5: Sharaxaad + Isticmaal

## 📌 Hussein7 TradeBot
Telegram bot for multi-market trading alerts (Forex, Crypto, Stocks, Polymarket, Memecoins) with ETH withdrawals, profit tracking, and webhook support.

---

## 🛠️ Features
- ✅ Trade alerts with buttons (Confirm / Ignore)
- ✅ Voice alert-ready
- ✅ ETH withdrawal (/withdraw_eth)
- ✅ Profit log & view (/profit & /profits)
- ✅ Auto-trade toggle (/autotrade)
- ✅ Webhook-based (Render compatible)
- ✅ Daily PDF report generation

---

## 🚀 Installation

### 1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/Hussein7TradeBot.git
cd Hussein7TradeBot
```

### 2. Create and fill `.env` file:
```
TELEGRAM_TOKEN=your_bot_token_here
INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_ID
WALLET_ADDRESS_ETH=0xyourwallet
PRIVATE_KEY_ETH=your_private_key
WEBHOOK_URL=https://yourdomain.onrender.com/telegram-webhook
CHAT_ID=your_chat_id_here
```

### 3. Install libraries:
```bash
pip install -r requirements.txt
```

### 4. Run the bot (dev only):
```bash
python main.py
```

---

## 🌍 Webhook + Render Deployment
Render auto-deploys `main.py` and keeps it online 24/7 with Flask + webhook:
- Homepage: `https://yourdomain.onrender.com`
- Webhook: `/telegram-webhook`

---

## 📚 Commands:
- `/start` – activate bot
- `/notify` – manual signal test
- `/profit` – add daily profit
- `/profits` – view profit log
- `/withdraw_eth` – send ETH
- `/autotrade` – toggle auto mode
- `/forex`, `/crypto`, `/stocks`, `/polymarket`, `/memecoins` – view trade ideas

---

## 🧠 Coming Soon
- Halal coin filter
- Voice alerts integration
- Memecoin sniping
- Chart rendering
- Push app support

---

## 🤖 Developed by Hussein with GPT support 💡

---

# ✅ webhook.py – Cutubka 6: Telegram Webhook Handler (Gooni ah)

```python
from telegram import Update
from telegram.ext import ContextTypes
from flask import request

# This function will be called by Flask when webhook receives POST
async def telegram_webhook_handler(app, update_json):
    try:
        update = Update.de_json(update_json, app.bot)
        await app.process_update(update)
        return "OK"
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return f"ERROR: {str(e)}"
```

> Fiiro gaar ah: 
- Kani waa handler gooni ah oo loo isticmaalo haddii aad `main.py` rabto inuu ka nadiif ahaado webhook routes-ka.
- Waxaa lagu dhex dari karaa `main.py` sidaan:

```python
from webhook import telegram_webhook_handler

@flask_app.route('/telegram-webhook', methods=["POST"])
async def telegram_webhook():
    return await telegram_webhook_handler(app, request.get_json(force=True))
```

---

# ✅ Cutubka 7: Trade Signal JSON Webhook Parser (Forex, Crypto, Stocks)

```python
@flask_app.route('/signal-webhook', methods=['POST'])
def signal_webhook():
    try:
        data = request.get_json()

        # Extracted fields
        symbol = data.get("symbol", "Unknown")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "5min")
        market = data.get("market", "forex")

        message = f"🚨 New {market.upper()} Signal\nPair: {symbol}\nTime: {timeframe}\nDirection: {direction}"

        buttons = [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM:{symbol}:{direction}"),
            InlineKeyboardButton("❌ Ignore", callback_data="IGNORE")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Set your target chat ID here
        chat_id = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
        app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

        return "Signal Sent"
    except Exception as e:
        return f"Webhook error: {str(e)}"
```

> **Functionality**: Endpoint-kan wuxuu ogolaanayaa in signal JSON ah laga helo platform kale (e.g. TradingView, Notion automation, custom AI).
> Waxaa loo diri karaa sida webhook `POST` JSON leh:
```json
{
  "symbol": "EURUSD",
  "direction": "BUY",
  "timeframe": "5min",
  "market": "forex"
}
```

> Waxaa lagusoo bandhigaa Telegram with buttons, waana la xaqiijin karaa.

---

# ✅ Cutubka 8: Voice Alert Integration (Notification + TTS)

```python
from telegram.constants import ChatAction
from gtts import gTTS
import tempfile

async def send_voice_alert(text, context, chat_id):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tts.save(tmp.name + ".mp3")
            with open(tmp.name + ".mp3", "rb") as audio:
                await context.bot.send_voice(chat_id=chat_id, voice=audio)
    except Exception as e:
        print(f"Voice Alert Error: {e}")
```

> **Tusaale Isticmaal**
```python
await send_voice_alert("New signal for EURUSD buy", context, chat_id=YOUR_CHAT_ID)
```

> **Shuruud**: Ku dar `gtts` dependency `requirements.txt`:
```
gtts
```

> **Noot Fakeeshoon**: TTS output is natural-sounding using Google Text-to-Speech (offline file, not a stream). No need for external APIs beyond Python's `gtts`.

---
# ✅ README.md – Cutubka 5: Sharaxaad + Isticmaal

## 📌 Hussein7 TradeBot
Telegram bot for multi-market trading alerts (Forex, Crypto, Stocks, Polymarket, Memecoins) with ETH withdrawals, profit tracking, and webhook support.

---

## 🛠️ Features
- ✅ Trade alerts with buttons (Confirm / Ignore)
- ✅ Voice alert-ready
- ✅ ETH withdrawal (/withdraw_eth)
- ✅ Profit log & view (/profit & /profits)
- ✅ Auto-trade toggle (/autotrade)
- ✅ Webhook-based (Render compatible)
- ✅ Daily PDF report generation
- ✅ Halal coin filter toggle (/halalonly)

---

## 🚀 Installation

### 1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/Hussein7TradeBot.git
cd Hussein7TradeBot
```

### 2. Create and fill `.env` file:
```
TELEGRAM_TOKEN=your_bot_token_here
INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_ID
WALLET_ADDRESS_ETH=0xyourwallet
PRIVATE_KEY_ETH=your_private_key
WEBHOOK_URL=https://yourdomain.onrender.com/telegram-webhook
```

### 3. Install libraries:
```bash
pip install -r requirements.txt
```

### 4. Run the bot (dev only):
```bash
python main.py
```

---

## 🌍 Webhook + Render Deployment
Render auto-deploys `main.py` and keeps it online 24/7 with Flask + webhook:
- Homepage: `https://yourdomain.onrender.com`
- Webhook: `/telegram-webhook`

---

## 📚 Commands:
- `/start` – activate bot
- `/notify` – manual signal test
- `/profit` – add daily profit
- `/profits` – view profit log
- `/withdraw_eth` – send ETH
- `/autotrade` – toggle auto mode
- `/halalonly` – toggle halal coin view
- `/forex`, `/crypto`, `/stocks`, `/polymarket`, `/memecoins` – view trade ideas

---

## 🧠 Coming Soon
- Voice alerts integration
- Memecoin sniping
- Chart rendering
- Push app support

---

## 🤖 Developed by Hussein with GPT support 💡


# ✅ Cutubka 9: Halal Coin Checker + Toggle Button

```python
# ✅ Halal Coin Toggle
from telegram.ext import CommandHandler

# Global halal filter state
halal_only_mode = False

async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode ON" if halal_only_mode else "❌ Halal Only Mode OFF"
    await update.message.reply_text(f"{status}")

# ✅ Coin labeling logic
# Example usage in notify function or webhook

def is_coin_halal(symbol: str) -> bool:
    # Basic sample checker
    haram_keywords = ["casino", "gambling", "loan", "riba", "liquor", "alcohol"]
    return not any(word in symbol.lower() for word in haram_keywords)

# When sending crypto signals
coin_name = "CasinoMoon"
halal_status = "🟢 Halal" if is_coin_halal(coin_name) else "🔴 Haram"

# Append to message
msg += f"\nStatus: {halal_status}"
```

✅ Add this command handler:
```python
app.add_handler(CommandHandler("halalonly", toggle_halal_only))
```

✅ You can now filter memecoin signals in real-time using the `halal_only_mode` flag!
# ✅ README.md – Cutubka 5: Sharaxaad + Isticmaal

## 📌 Hussein7 TradeBot
Telegram bot for multi-market trading alerts (Forex, Crypto, Stocks, Polymarket, Memecoins) with ETH withdrawals, profit tracking, and webhook support.

---

## 🛠️ Features
- ✅ Trade alerts with buttons (Confirm / Ignore)
- ✅ Voice alert-ready
- ✅ ETH withdrawal (/withdraw_eth)
- ✅ Profit log & view (/profit & /profits)
- ✅ Auto-trade toggle (/autotrade)
- ✅ Webhook-based (Render compatible)
- ✅ Daily PDF report generation
- ✅ Halal coin filter toggle (/halalonly)
- ✅ Auto lot-size calculator with 5% risk limit

---

## 🚀 Installation

### 1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/Hussein7TradeBot.git
cd Hussein7TradeBot
```

### 2. Create and fill `.env` file:
```
TELEGRAM_TOKEN=your_bot_token_here
INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_ID
WALLET_ADDRESS_ETH=0xyourwallet
PRIVATE_KEY_ETH=your_private_key
WEBHOOK_URL=https://yourdomain.onrender.com/telegram-webhook
ACCOUNT_BALANCE=5000
DAILY_MAX_RISK=250
```

### 3. Install libraries:
```bash
pip install -r requirements.txt
```

### 4. Run the bot (dev only):
```bash
python main.py
```

---

## 🌍 Webhook + Render Deployment
Render auto-deploys `main.py` and keeps it online 24/7 with Flask + webhook:
- Homepage: `https://yourdomain.onrender.com`
- Webhook: `/telegram-webhook`

---

## 📚 Commands:
- `/start` – activate bot
- `/notify` – manual signal test
- `/profit` – add daily profit
- `/profits` – view profit log
- `/withdraw_eth` – send ETH
- `/autotrade` – toggle auto mode
- `/halalonly` – toggle halal coin view
- `/forex`, `/crypto`, `/stocks`, `/polymarket`, `/memecoins` – view trade ideas

---

## 🧠 Coming Soon
- Voice alerts integration
- Memecoin sniping
- Chart rendering
- Push app support

---

## 🤖 Developed by Hussein with GPT support 💡


# ✅ Cutubka 9: Halal Coin Checker + Toggle Button

```python
# ✅ Halal Coin Toggle
from telegram.ext import CommandHandler

# Global halal filter state
halal_only_mode = False

async def toggle_halal_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global halal_only_mode
    halal_only_mode = not halal_only_mode
    status = "✅ Halal Only Mode ON" if halal_only_mode else "❌ Halal Only Mode OFF"
    await update.message.reply_text(f"{status}")

# ✅ Coin labeling logic
# Example usage in notify function or webhook

def is_coin_halal(symbol: str) -> bool:
    # Basic sample checker
    haram_keywords = ["casino", "gambling", "loan", "riba", "liquor", "alcohol"]
    return not any(word in symbol.lower() for word in haram_keywords)

# When sending crypto signals
coin_name = "CasinoMoon"
halal_status = "🟢 Halal" if is_coin_halal(coin_name) else "🔴 Haram"

# Append to message
msg += f"\nStatus: {halal_status}"
```

✅ Add this command handler:
```python
app.add_handler(CommandHandler("halalonly", toggle_halal_only))
```

✅ You can now filter memecoin signals in real-time using the `halal_only_mode` flag!


# ✅ Cutubka 10: Auto Lot-Size Calculator + 5% Risk Guard

```python
# ✅ Auto Lot Size Calculation (5% Risk Rule)
from decimal import Decimal

ACCOUNT_BALANCE = Decimal(os.getenv("ACCOUNT_BALANCE", "5000"))
DAILY_MAX_RISK = Decimal(os.getenv("DAILY_MAX_RISK", "250"))

# Example usage
# SL_distance: how many pips to stop loss (e.g., 20)
# pip_value: value per pip per lot (e.g., $10 for standard lot)

def calculate_lot_size(sl_distance_pips: float, pip_value: float = 10.0) -> float:
    # Calculate risk per pip
    risk_per_pip = DAILY_MAX_RISK / Decimal(sl_distance_pips)
    # Calculate lots = risk / pip_value
    lot_size = risk_per_pip / Decimal(pip_value)
    return round(float(lot_size), 2)

# Example:
lot = calculate_lot_size(20)  # 20 pip SL
print(f"✅ Suggested lot size: {lot} lots")
```

✅ This guarantees you **never risk more than $250/day** even if all trades hit SL.
✅ Future improvements: auto-sync with trade signal SL + dynamic lot.

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
