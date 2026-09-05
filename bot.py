import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1v1 Betting Bot መስራት ጀምሯል!")

if name == 'main':
    token = os.getenv("BOT_TOKEN", "8640582909:AAEWINflMuUocmywDZrvIMjV_up84BHDF6I")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running...")
    app.run_polling()
