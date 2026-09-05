import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1v1 Betting Bot ስራ ጀምሯል!")

if name == 'main':
    # Retrieve the bot token from environment variables
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        raise ValueError("BOT_TOKEN environment variable አልተገኘም!")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running...")
    app.run_polling()
