async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1v1 Betting Bot በ Render ላይ 24/7 መስራት ጀምሯል!")

if name == 'main':
    threading.Thread(target=run_health_check_server, daemon=True).start()

    token = os.getenv("BOT_TOKEN", "8640582909:AAEWINflMuUocmywDZrvIMjV_up84BHDF6I")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running on Render...")
    app.run_polling()
