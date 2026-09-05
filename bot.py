import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1v1 Betting Bot በ Render ላይ 24/7 መስራት ጀምሯል!")

if __name__ == '__main__':
    threading.Thread(target=run_health_check_server, daemon=True).start()

    token = os.getenv("BOT_TOKEN", "8640582909:AAEWINflMuUocmywDZrvIMjV_up84BHDF6I")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running on Render...")
    app.run_polling()
