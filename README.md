# walalka ForexPro Bot
 (Render Version)
A 24/7 Telegram bot that sends Forex PRO signals with:
- Entry, TP, SL
- Lot size calculator
- Auto chart image
- Voice alert
- Every 4 hours (6x daily)

## Deployment (Render)
1. Upload all files to GitHub
2. Create new Render → Web Service
3. Set Python Build & `requirements.txt`
4. Use this Start Command:
```bash
uvicorn main:flask_app --host 0.0.0.0 --port 10000
