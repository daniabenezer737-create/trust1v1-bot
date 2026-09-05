import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1v1 Betting Bot ስራ ጀምሯል!")

if name == 'main':
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        raise ValueError("BOT_TOKEN አልተገኘም!")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running...")
    app.run_polling()
