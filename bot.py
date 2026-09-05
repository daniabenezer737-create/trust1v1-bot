import os
import logging
import random
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render Health Check Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8640582909:AAEWINflMuUocmywDZrvIMjV_up84BHDF6I")
ADMIN_ID = 5283089413
GROUP_USERNAME = "@trust1v1"
TELEBIRR_PHONE = "0940472271"
TELEBIRR_NAME = "Abenezer"

MIN_DEPOSIT = 100
MIN_WITHDRAW = 300
MIN_PLAY_BALANCE = 100

user_balances = {}
match_queues = {100: [], 200: [], 500: []}
private_rooms = {}

JOIN_ROOM_STATE, WITHDRAW_AMOUNT, WITHDRAW_PHONE = range(3)

def generate_room_code():
    return ''.join(random.choices(string.digits, k=5))

async def is_user_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    is_member = await is_user_member(context, user_id)
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("📢 ግሩፑን ይቀላቀሉ (Join Group)", url=f"https://t.me/trust1v1")],
            [InlineKeyboardButton("✅ አረጋግጥ (Verify)", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"⚠️ ቦቱን ለመጠቀም በመጀመሪያ የኛን ቴሌግራም ግሩፕ መቀላቀል አለብዎት፦\n{GROUP_USERNAME}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    reply_keyboard = [
        ['⚽ eFootball', '🎮 DLS'],
        ['💳 Recharge', '🏧 Withdraw'],
        ['💰 Balance']
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"እንኳን ወደ 1v1 Betting Bot በደህና መጡ!\n\n💳 **የአሁኑ ባላንስዎ፦** {user_balances[user_id]} ብር",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_member(context, user_id):
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ ግሩፑን ስለተቀላቀሉ እናመሰግናለን! አሁን ቦቱን መጠቀም ይችላሉ። /start ይበሉ።"
        )
    else:
        await query.message.edit_text(
            f"❌ አሁንም ግሩፑን አልተቀላቀሉም! እባክዎን {GROUP_USERNAME} ይቀላቀሉ።",
            reply_markup=query.message.reply_markup
        )

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)
    await update.message.reply_text(f"💳 **የእርስዎ ባላንስ፦** {bal} ብር", parse_mode="Markdown")

async def handle_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📥 **ብር ገቢ ማድረጊያ (Recharge)**\n\n"
        f"• አነስተኛ ገቢ መጠን፦ **{MIN_DEPOSIT} ብር**\n\n"
        f"📲 **Telebirr Details:**\n"
        f"• ስልክ፦ `{TELEBIRR_PHONE}`\n"
        f"• ስም፦ **{TELEBIRR_NAME}**\n\n"
        f"ብር ከላኩ በኋላ የግብይት ቁጥሩን (Transaction ID) ወይም ስክሪንሻት ለ Admin (@trust1v1) ይላኩ።"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)

    if bal < MIN_WITHDRAW:
        await update.message.reply_text(f"❌ ብር ለማውጣት በትንሹ **{MIN_WITHDRAW} ብር** ባላንስ መኖር አለበት።\nየእርስዎ ባላንስ፦ {bal} ብር", parse_mode="Markdown")
        return ConversationHandler.END

    await update.message.reply_text(f"ወጪ ማድረግ የሚፈልጉትን የብር መጠን ያስገቡ (ትንሹ {MIN_WITHDRAW} ብር)፦")
    return WITHDRAW_AMOUNT

async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = update.effective_user.id
        bal = user_balances.get(user_id, 0.0)

        if amount < MIN_WITHDRAW or amount > bal:
            await update.message.reply_text("❌ ያልተስተካከለ የብር መጠን ወይም በቂ ያልሆነ ባላንስ። እንደገና ይሞክሩ፦")
            return WITHDRAW_AMOUNT

        context.user_data['withdraw_amount'] = amount
        await update.message.reply_text("ብር የሚላክበትን የ Telebirr ስልክ ቁጥር ያስገቡ፦")
        return WITHDRAW_PHONE
    except ValueError:
        await update.message.reply_text("❌ እባክዎን ቁጥር ብቻ ያስገቡ፦")
        return WITHDRAW_AMOUNT

async def handle_withdraw_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    amount = context.user_data.get('withdraw_amount')

    user_balances[user_id] -= amount

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **የብር ማውጣት ጥያቄ!**\n\n"
             f"• User ID: `{user_id}`\n"
             f"• መጠን: **{amount} ብር**\n"
             f"• Telebirr ስልክ: `{phone}`",
        parse_mode="Markdown"
    )

    await update.message.reply_text(f"✅ የ {amount} ብር ማውጣት ጥያቄዎ ለ Admin ተልኳል። በቅርቡ ገቢ ይደረጋል!")
    return ConversationHandler.END

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)

    if bal < MIN_PLAY_BALANCE:
        await update.message.reply_text(
            f"❌ ለመጫወት በአካውንትዎ በትንሹ **{MIN_PLAY_BALANCE} ብር** መኖር አለበት።\n"
            f"የእርስዎ ባላንስ፦ {bal} ብር\nእባክዎን በ 'Recharge' ቁልፍ ብር ገቢ ያድርጉ።",
            parse_mode="Markdown"
        )
        return

    text = update.message.text
    context.user_data['game'] = text

    keyboard = [
        [InlineKeyboardButton("🔍 1v1 ፈልግ (Random Match)", callback_data="mode_random")],
        [InlineKeyboardButton("👥 ከጓደኛ ጋር (Play with Friend)", callback_data="mode_friend")]
    ]
    await update.message.reply_text(f"ለ {text} የጨዋታ አይነት ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "mode_random":
        keyboard = [
            [InlineKeyboardButton("100 ብር", callback_data="queue_100"),
             InlineKeyboardButton("200 ብር", callback_data="queue_200"),
             InlineKeyboardButton("500 ብር", callback_data="queue_500")]
        ]
        await query.edit_message_text("የውርርድ መጠን ይምረጡ (Matchmaking Queue)፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "mode_friend":
        keyboard = [
            [InlineKeyboardButton("🏠 ሩም ፍጠር (Create)", callback_data="friend_create")],
            [InlineKeyboardButton("🔑 ሩም ተቀላቀል (Join)", callback_data="friend_join")]
        ]
        await query.edit_message_text("ከጓደኛ ጋር ለመጫወት ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("queue_"):
        amount = int(query.data.split("_")[1])
        user_id = query.from_user.id

        if user_id in match_queues[amount]:
            await query.edit_message_text("አስቀድመው Queue ውስጥ አሉ! ተጋጣሚ እስኪገኝ ይጠብቁ...")
            return

        match_queues[amount].append(user_id)

        if len(match_queues[amount]) >= 2:
            player1 = match_queues[amount].pop(0)
            player2 = match_queues[amount].pop(0)

            await context.bot.send_message(player1, f"🎉 ተጋጣሚ ተገኝቷል! የውርርድ መጠን፡ {amount} ብር።\nRoom ፈጥራችሁ ተጫወቱ።")
            await context.bot.send_message(player2, f"🎉 ተጋጣሚ ተገኝቷል! የውርርድ መጠን፡ {amount} ብር።\nRoom ፈጥራችሁ ተጫወቱ።")
            await query.edit_message_text("🎉 ተጋጣሚ ተገኝቷል! ጨዋታው ተጀምሯል።")
        else:
            await query.edit_message_text(f"⏳ ለ {amount} ብር ተጋጣሚ በመፈለግ ላይ... እባክዎን ትንሽ ይጠብቁ።")

    elif query.data == "friend_create":
        keyboard = [
            [InlineKeyboardButton("100 ብር", callback_data="create_100"),
             InlineKeyboardButton("200 ብር", callback_data="create_200"),
             InlineKeyboardButton("500 ብር", callback_data="create_500")]
        ]
        await query.edit_message_text("የሩም የውርርድ መጠን ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("create_"):
        amount = int(query.data.split("_")[1])
        room_code = generate_room_code()
        private_rooms[room_code] = {'host': query.from_user.id, 'amount': amount}

        await query.edit_message_text(
            f"✅ ሩም ተፈጥሯል!\n\n"
            f"📌 **የሩም ID (Code)**: `{room_code}`\n"
            f"💰 **የውርርድ መጠን**: {amount} ብር\n\n"
            f"ይህንን የሩም ID ለጓደኛዎ ይላኩለት።",
            parse_mode="Markdown"
        )

    elif query.data == "friend_join":
        await query.edit_message_text("እባክዎን የጓደኛዎን Room ID (5 ዲጂት ኮድ) ያስገቡ፡")
        return JOIN_ROOM_STATE

async def handle_join_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code in private_rooms:
        room = private_rooms.pop(code)
        host_id = room['host']
        amount = room['amount']

        await update.message.reply_text(f"🎉 ሩም ተቀላቅለዋል! የውርርድ መጠን፡ {amount} ብር። መልካም እድል!")
        await context.bot.send_message(host_id, f"🎉 ጓደኛዎ ሩሙን ተቀላቅሏል! የውርርድ መጠን፡ {amount} ብር።")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ የገባው Room ID አልተገኘም። /start ብለው እንደገና ይሞክሩ።")
        return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    withdraw_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏧 Withdraw$"), handle_withdraw_start)],
        states={
            WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)],
            WITHDRAW_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_phone)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    join_room_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_mode_callback, pattern="^friend_join$")],
        states={
            JOIN_ROOM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_join_code)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.Regex("^💰 Balance$"), handle_balance))
    app.add_handler(MessageHandler(filters.Regex("^💳 Recharge$"), handle_recharge))
    app.add_handler(MessageHandler(filters.Regex("^(⚽ eFootball|🎮 DLS)$"), handle_game_selection))
    
    app.add_handler(withdraw_conv)
    app.add_handler(join_room_conv)
    app.add_handler(CallbackQueryHandler(handle_mode_callback))

    print("Bot is running on Render...")
    app.run_polling()
import os
import logging
import random
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render Health Check Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8640582909:AAEWINflMuUocmywDZrvIMjV_up84BHDF6I")
ADMIN_ID = 5283089413
GROUP_USERNAME = "@trust1v1"
TELEBIRR_PHONE = "0940472271"
TELEBIRR_NAME = "Abenezer"

MIN_DEPOSIT = 100
MIN_WITHDRAW = 300
MIN_PLAY_BALANCE = 100

user_balances = {}
match_queues = {100: [], 200: [], 500: []}
private_rooms = {}

JOIN_ROOM_STATE, WITHDRAW_AMOUNT, WITHDRAW_PHONE = range(3)

def generate_room_code():
    return ''.join(random.choices(string.digits, k=5))

async def is_user_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    is_member = await is_user_member(context, user_id)
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("📢 ግሩፑን ይቀላቀሉ (Join Group)", url=f"https://t.me/trust1v1")],
            [InlineKeyboardButton("✅ አረጋግጥ (Verify)", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"⚠️ ቦቱን ለመጠቀም በመጀመሪያ የኛን ቴሌግራም ግሩፕ መቀላቀል አለብዎት፦\n{GROUP_USERNAME}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    reply_keyboard = [
        ['⚽ eFootball', '🎮 DLS'],
        ['💳 Recharge', '🏧 Withdraw'],
        ['💰 Balance']
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"እንኳን ወደ 1v1 Betting Bot በደህና መጡ!\n\n💳 **የአሁኑ ባላንስዎ፦** {user_balances[user_id]} ብር",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_member(context, user_id):
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ ግሩፑን ስለተቀላቀሉ እናመሰግናለን! አሁን ቦቱን መጠቀም ይችላሉ። /start ይበሉ።"
        )
    else:
        await query.message.edit_text(
            f"❌ አሁንም ግሩፑን አልተቀላቀሉም! እባክዎን {GROUP_USERNAME} ይቀላቀሉ።",
            reply_markup=query.message.reply_markup
        )

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)
    await update.message.reply_text(f"💳 **የእርስዎ ባላንስ፦** {bal} ብር", parse_mode="Markdown")

async def handle_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📥 **ብር ገቢ ማድረጊያ (Recharge)**\n\n"
        f"• አነስተኛ ገቢ መጠን፦ **{MIN_DEPOSIT} ብር**\n\n"
        f"📲 **Telebirr Details:**\n"
        f"• ስልክ፦ `{TELEBIRR_PHONE}`\n"
        f"• ስም፦ **{TELEBIRR_NAME}**\n\n"
        f"ብር ከላኩ በኋላ የግብይት ቁጥሩን (Transaction ID) ወይም ስክሪንሻት ለ Admin (@trust1v1) ይላኩ።"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)

    if bal < MIN_WITHDRAW:
        await update.message.reply_text(f"❌ ብር ለማውጣት በትንሹ **{MIN_WITHDRAW} ብር** ባላንስ መኖር አለበት።\nየእርስዎ ባላንስ፦ {bal} ብር", parse_mode="Markdown")
        return ConversationHandler.END

    await update.message.reply_text(f"ወጪ ማድረግ የሚፈልጉትን የብር መጠን ያስገቡ (ትንሹ {MIN_WITHDRAW} ብር)፦")
    return WITHDRAW_AMOUNT

async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = update.effective_user.id
        bal = user_balances.get(user_id, 0.0)

        if amount < MIN_WITHDRAW or amount > bal:
            await update.message.reply_text("❌ ያልተስተካከለ የብር መጠን ወይም በቂ ያልሆነ ባላንስ። እንደገና ይሞክሩ፦")
            return WITHDRAW_AMOUNT

        context.user_data['withdraw_amount'] = amount
        await update.message.reply_text("ብር የሚላክበትን የ Telebirr ስልክ ቁጥር ያስገቡ፦")
        return WITHDRAW_PHONE
    except ValueError:
        await update.message.reply_text("❌ እባክዎን ቁጥር ብቻ ያስገቡ፦")
        return WITHDRAW_AMOUNT

async def handle_withdraw_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    amount = context.user_data.get('withdraw_amount')

    user_balances[user_id] -= amount

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **የብር ማውጣት ጥያቄ!**\n\n"
             f"• User ID: `{user_id}`\n"
             f"• መጠን: **{amount} ብር**\n"
             f"• Telebirr ስልክ: `{phone}`",
        parse_mode="Markdown"
    )

    await update.message.reply_text(f"✅ የ {amount} ብር ማውጣት ጥያቄዎ ለ Admin ተልኳል። በቅርቡ ገቢ ይደረጋል!")
    return ConversationHandler.END

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)

    if bal < MIN_PLAY_BALANCE:
        await update.message.reply_text(
            f"❌ ለመጫወት በአካውንትዎ በትንሹ **{MIN_PLAY_BALANCE} ብር** መኖር አለበት።\n"
            f"የእርስዎ ባላንስ፦ {bal} ብር\nእባክዎን በ 'Recharge' ቁልፍ ብር ገቢ ያድርጉ።",
            parse_mode="Markdown"
        )
        return

    text = update.message.text
    context.user_data['game'] = text

    keyboard = [
        [InlineKeyboardButton("🔍 1v1 ፈልግ (Random Match)", callback_data="mode_random")],
        [InlineKeyboardButton("👥 ከጓደኛ ጋር (Play with Friend)", callback_data="mode_friend")]
    ]
    await update.message.reply_text(f"ለ {text} የጨዋታ አይነት ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "mode_random":
        keyboard = [
            [InlineKeyboardButton("100 ብር", callback_data="queue_100"),
             InlineKeyboardButton("200 ብር", callback_data="queue_200"),
             InlineKeyboardButton("500 ብር", callback_data="queue_500")]
        ]
        await query.edit_message_text("የውርርድ መጠን ይምረጡ (Matchmaking Queue)፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "mode_friend":
        keyboard = [
            [InlineKeyboardButton("🏠 ሩም ፍጠር (Create)", callback_data="friend_create")],
            [InlineKeyboardButton("🔑 ሩም ተቀላቀል (Join)", callback_data="friend_join")]
        ]
        await query.edit_message_text("ከጓደኛ ጋር ለመጫወት ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("queue_"):
        amount = int(query.data.split("_")[1])
        user_id = query.from_user.id

        if user_id in match_queues[amount]:
            await query.edit_message_text("አስቀድመው Queue ውስጥ አሉ! ተጋጣሚ እስኪገኝ ይጠብቁ...")
            return

        match_queues[amount].append(user_id)

        if len(match_queues[amount]) >= 2:
            player1 = match_queues[amount].pop(0)
            player2 = match_queues[amount].pop(0)

            await context.bot.send_message(player1, f"🎉 ተጋጣሚ ተገኝቷል! የውርርድ መጠን፡ {amount} ብር።\nRoom ፈጥራችሁ ተጫወቱ።")
            await context.bot.send_message(player2, f"🎉 ተጋጣሚ ተገኝቷል! የውርርድ መጠን፡ {amount} ብር።\nRoom ፈጥራችሁ ተጫወቱ።")
            await query.edit_message_text("🎉 ተጋጣሚ ተገኝቷል! ጨዋታው ተጀምሯል።")
        else:
            await query.edit_message_text(f"⏳ ለ {amount} ብር ተጋጣሚ በመፈለግ ላይ... እባክዎን ትንሽ ይጠብቁ።")

    elif query.data == "friend_create":
        keyboard = [
            [InlineKeyboardButton("100 ብር", callback_data="create_100"),
             InlineKeyboardButton("200 ብር", callback_data="create_200"),
             InlineKeyboardButton("500 ብር", callback_data="create_500")]
        ]
        await query.edit_message_text("የሩም የውርርድ መጠን ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("create_"):
        amount = int(query.data.split("_")[1])
        room_code = generate_room_code()
        private_rooms[room_code] = {'host': query.from_user.id, 'amount': amount}

        await query.edit_message_text(
            f"✅ ሩም ተፈጥሯል!\n\n"
            f"📌 **የሩም ID (Code)**: `{room_code}`\n"
            f"💰 **የውርርድ መጠን**: {amount} ብር\n\n"
            f"ይህንን የሩም ID ለጓደኛዎ ይላኩለት።",
            parse_mode="Markdown"
        )

    elif query.data == "friend_join":
        await query.edit_message_text("እባክዎን የጓደኛዎን Room ID (5 ዲጂት ኮድ) ያስገቡ፡")
        return JOIN_ROOM_STATE

async def handle_join_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code in private_rooms:
        room = private_rooms.pop(code)
        host_id = room['host']
        amount = room['amount']

        await update.message.reply_text(f"🎉 ሩም ተቀላቅለዋል! የውርርድ መጠን፡ {amount} ብር። መልካም እድል!")
        await context.bot.send_message(host_id, f"🎉 ጓደኛዎ ሩሙን ተቀላቅሏል! የውርርድ መጠን፡ {amount} ብር።")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ የገባው Room ID አልተገኘም። /start ብለው እንደገና ይሞክሩ።")
        return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    withdraw_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏧 Withdraw$"), handle_withdraw_start)],
        states={
            WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)],
            WITHDRAW_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_phone)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    join_room_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_mode_callback, pattern="^friend_join$")],
        states={
            JOIN_ROOM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_join_code)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.Regex("^💰 Balance$"), handle_balance))
    app.add_handler(MessageHandler(filters.Regex("^💳 Recharge$"), handle_recharge))
    app.add_handler(MessageHandler(filters.Regex("^(⚽ eFootball|🎮 DLS)$"), handle_game_selection))
    
    app.add_handler(withdraw_conv)
    app.add_handler(join_room_conv)
    app.add_handler(CallbackQueryHandler(handle_mode_callback))

    print("Bot is running on Render...")
    app.run_polling()
