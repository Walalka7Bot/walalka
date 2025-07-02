# walalkaTradeBot 🤖

Telegram bot for sending real-time Forex + Crypto signals with voice alerts, charts, and lot-size calculator.

## 🌐 Features
- 15M / 5M timeframe signals
- Chart image via quickchart.io
- Voice alerts (gTTS)
- Auto lot size calculation
- Flask + Webhook deployment
- Deployable on Render.com

## ⚙️ ENVIRONMENT VARIABLES
- `TELEGRAM_TOKEN`: Your bot token
- `WEBHOOK_URL`: Your live Render URL
- `CHAT_ID`: Your Telegram user/group/channel ID
- `ACCOUNT_BALANCE`: e.g., 5000
- `DAILY_MAX_RISK`: e.g., 250
- `PORT`: 10000

## 🚀 Deploy Guide
1. Upload to GitHub or ZIP
2. Deploy to [Render.com](https://render.com)
3. Add env vars
4. Set Start Command:
