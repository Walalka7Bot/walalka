import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Sirtaada
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INFURA_URL = os.getenv("INFURA_URL")  # optional, blockchain support
