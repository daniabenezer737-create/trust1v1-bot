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
active_matches = {}

JOIN_ROOM_STATE = 1
RECHARGE_TXID = 2
WITHDRAW_AMOUNT, WITHDRAW_PHONE = 3, 4

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
    first_name = update.effective_user.first_name or "ወዳጃችን"

    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    is_member = await is_user_member(context, user_id)
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("📢 ግሩፑን ይቀላቀሉ (Join Group)", url=f"https://t.me/trust1v1")],
            [InlineKeyboardButton("✅ አረጋግጥ (Verify)", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"ሰላም {first_name} 👋\n\n"
            f"⚠️ ቦቱን መጠቀም ለመጀመር በመጀመሪያ የቴሌግራም ግሩፓችንን ይቀላቀሉ፦\n{GROUP_USERNAME}\n\n"
            f"ግሩፑን ከተቀላቀሉ በኋላ **'✅ አረጋግጥ'** የሚለውን ቁልፍ ይጫኑ።",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    reply_keyboard = [
        ['⚽ eFootball', '🎮 DLS'],
        ['💳 Recharge', '🏧 Withdraw'],
        ['💰 Balance']
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    welcome_text = (
        f"ሰላም {first_name}! 👋\n"
        f"እንኳን ወደ **1v1 Gaming Betting Bot** በደህና መጡ! 🎮⚽\n\n"
        f"እዚህ ጋር ከሌሎች ተጫዋቾች ጋር በመወዳደርና በማሸነፍ የገንዘብ ሽልማቶችን ማግኘት ይችላሉ።\n\n"
        f"💳 **የአሁኑ ባላንስዎ፦** `{user_balances[user_id]} ብር`\n\n"
        f"👇 ለመጀመር ከታች ካሉት አማራጮች የሚፈልጉትን ይምረጡ፦"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    first_name = query.from_user.first_name or "ወዳጃችን"

    if await is_user_member(context, user_id):
        await query.message.delete()
        if user_id not in user_balances:
            user_balances[user_id] = 0.0

        reply_keyboard = [
            ['⚽ eFootball', '🎮 DLS'],
            ['💳 Recharge', '🏧 Withdraw'],
            ['💰 Balance']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        welcome_text = (
            f"ሰላም {first_name}! 👋\n"
            f"እንኳን ወደ **1v1 Gaming Betting Bot** በደህና መጡ! 🎮⚽\n\n"
            f"እዚህ ጋር ከሌሎች ተጫዋቾች ጋር በመወዳደርና በማሸነፍ የገንዘብ ሽልማቶችን ማግኘት ይችላሉ።\n\n"
            f"💳 **የአሁኑ ባላንስዎ፦** `{user_balances[user_id]} ብር`\n\n"
            f"👇 ለመጀመር ከታች ካሉት አማራጮች የሚፈልጉትን ይምረጡ፦"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            reply_markup=markup,
            parse_mode="Markdown"
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

# Recharge Handler
async def handle_recharge_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📥 **ብር ገቢ ማድረጊያ (Recharge)**\n\n"
        f"• አነስተኛ ገቢ መጠን፦ **{MIN_DEPOSIT} ብር**\n\n"
        f"📲 **Telebirr Details:**\n"
        f"• ስልክ፦ `{TELEBIRR_PHONE}`\n"
        f"• ስም፦ **{TELEBIRR_NAME}**\n\n"
        f"እባክዎን ብር ከላኩ በኋላ የ **Transaction ID** (ግብይት ቁጥር) ወይም የላኩበትን መጠን እና TXID እዚህ ጽፈው ይላኩ፦"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return RECHARGE_TXID

async def handle_recharge_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    user_id = update.effective_user.id

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve 100 ETB", callback_data=f"app_rec_{user_id}_100"),
            InlineKeyboardButton("✅ Approve 200 ETB", callback_data=f"app_rec_{user_id}_200")
        ],
        [
            InlineKeyboardButton("✅ Approve 500 ETB", callback_data=f"app_rec_{user_id}_500"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_rec_{user_id}")
        ]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **አዲስ የ Recharge ጥያቄ!**\n\n"
             f"• User ID: `{user_id}`\n"
             f"• TXID/የተላከ ጽሁፍ: `{txid}`\n\n"
             f"እባክዎን ሂሳቡን በ Telebirr አረጋግጠው ይምረጡ፦",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ የገቢ ጥያቄዎ ለ Admin ተልኳል። እንደተረጋገጠ ባላንስዎ ላይ ይጨመራል!")
    return ConversationHandler.END

# Withdraw Handler
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

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve (ልኬአለሁ)", callback_data=f"app_wd_{user_id}_{amount}"),
            InlineKeyboardButton("❌ Reject (ሰርዝ)", callback_data=f"rej_wd_{user_id}_{amount}")
        ]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **አዲስ የብር ማውጣት ጥያቄ!**\n\n"
             f"• User ID: `{user_id}`\n"
             f"• መጠን: **{amount} ብር**\n"
             f"• Telebirr ስልክ: `{phone}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(f"✅ የ {amount} ብር ማውጣት ጥያቄዎ ለ Admin ተልኳል። በቅርቡ ገቢ ይደረጋል!")
    return ConversationHandler.END

# Admin Callbacks
async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("app_rec_"):
        _, _, user_id, amount = data.split("_")
        user_id, amount = int(user_id), float(amount)
        user_balances[user_id] = user_balances.get(user_id, 0.0) + amount
        await query.edit_message_text(f"✅ ለ User `{user_id}` {amount} ብር ገቢ ተደርጓል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"🎉 የ {amount} ብር ገቢ ጥያቄዎ ጸድቋል! አዲሱ ባላንስዎ፡ {user_balances[user_id]} ብር")

    elif data.startswith("rej_rec_"):
        user_id = int(data.split("_")[2])
        await query.edit_message_text(f"❌ ለ User `{user_id}` የገቢ ጥያቄ ተሰርዟል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, "❌ የገቢ ጥያቄዎ አልፀደቀም። እባክዎን የላኩትን Transaction ID አረጋግጠው እንደገና ይሞክሩ።")

    elif data.startswith("app_wd_"):
        _, _, user_id, amount = data.split("_")
        user_id, amount = int(user_id), float(amount)
        await query.edit_message_text(f"✅ ለ User `{user_id}` የ {amount} ብር ወጪ ጥያቄ ተፈጽሟል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"🎉 የ {amount} ብር ወጪ ጥያቄዎ ጸድቋል! ብሩ ወደ Telebirr አካውንትዎ ተልኳል።")

    elif data.startswith("rej_wd_"):
        _, _, user_id, amount = data.split("_")
        user_id, amount = int(user_id), float(amount)
        user_balances[user_id] = user_balances.get(user_id, 0.0) + amount
        await query.edit_message_text(f"❌ ለ User `{user_id}` የ {amount} ብር ወጪ ጥያቄ ተሰርዟል፤ ብሩ ተመልሷል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"❌ የብር ማውጣት ጥያቄዎ አልፀደቀም። የተቀነሰው {amount} ብር ወደ ባላንስዎ ተመልሷል።")

    elif data.startswith("dispute_win_"):
        _, _, winner_id, loser_id, amount = data.split("_")
        winner_id, loser_id, amount = int(winner_id), int(loser_id), float(amount)
        prize = amount * 2
        user_balances[winner_id] = user_balances.get(winner_id, 0.0) + prize

        await query.edit_message_text(f"✅ አሸናፊው User `{winner_id}` ተለይቷል። {prize} ብር ተጨምሮለታል።", parse_mode="Markdown")
        await context.bot.send_message(winner_id, f"🎉 Admin ውጤቱን አረጋግጧል! የ {prize} ብር ሽልማት ባላንስዎ ላይ ተጨምሯል።")
        await context.bot.send_message(loser_id, f"❌ Admin ውጤቱን አረጋግጧል! በጨዋታው ተሸንፈዋል።")

# Game Selection
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

async def start_match(context, p1, p2, amount):
    match_id = f"{p1}_{p2}_{amount}"
    active_matches[match_id] = {'p1': p1, 'p2': p2, 'amount': amount, 'claims': {}}

    user_balances[p1] -= amount
    user_balances[p2] -= amount

    keyboard = [
        [InlineKeyboardButton("🏆 እኔ አሸንፌአለሁ", callback_data=f"claim_win_{match_id}")],
        [InlineKeyboardButton("❌ ተሸንፌአለሁ", callback_data=f"claim_lose_{match_id}")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(p1, f"🎉 ጨዋታው ተጀምሯል! የውርርድ መጠን፡ {amount} ብር።\nጨዋታው ሲያልቅ ውጤቱን ይምረጡ፡", reply_markup=markup)
    await context.bot.send_message(p2, f"🎉 ጨዋታው ተጀምሯል! የውርርድ መጠን፡ {amount} ብር።\nጨዋታው ሲያልቅ ውጤቱን ይምረጡ፡", reply_markup=markup)

async def handle_claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    action, match_id = data.split("_")[1], data.split("_")[2]

    if match_id not in active_matches:
        await query.edit_message_text("ይህ ጨዋታ ተጠናቋል ወይም አልተገኘም።")
        return

    match = active_matches[match_id]
    match['claims'][user_id] = action

    p1, p2, amount = match['p1'], match['p2'], match['amount']

    if len(match['claims']) == 2:
        c1, c2 = match['claims'][p1], match['claims'][p2]

        if c1 == "win" and c2 == "win":
            msg = "⚠️ ሁለታችሁም አሸንፌአለሁ ብላችኋል! እባክዎን የጨዋታውን ውጤት የሚያሳይ Screenshot በዚህ ቦት ላይ ይላኩ።"
            await context.bot.send_message(p1, msg)
            await context.bot.send_message(p2, msg)
        elif c1 == "win" and c2 == "lose":
            prize = amount * 2
            user_balances[p1] += prize
            await context.bot.send_message(p1, f"🎉 እንኳን ደስ አለዎት! {prize} ብር አሸንፈዋል።")
            await context.bot.send_message(p2, f"❌ በጨዋታው ተሸንፈዋል።")
            del active_matches[match_id]
        elif c2 == "win" and c1 == "lose":
            prize = amount * 2
            user_balances[p2] += prize
            await context.bot.send_message(p2, f"🎉 እንኳን ደስ አለዎት! {prize} ብር አሸንፈዋል።")
            await context.bot.send_message(p1, f"❌ በጨዋታው ተሸንፈዋል።")
            del active_matches[match_id]

async def handle_screenshot_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1].file_id

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=f"⚠️ **የጨዋታ አለመግባባት (Dispute Screenshot)!**\nUser ID: `{user_id}`",
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ ስክሪንሻቱ ለ Admin ተልኳል። ማጣራቱ እንደተጠናቀቀ አሸናፊው ይፋ ይደረጋል!")

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
            p1 = match_queues[amount].pop(0)
            p2 = match_queues[amount].pop(0)
            await start_match(context, p1, p2, amount)
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
        user_id = update.effective_user.id

        await start_match(context, host_id, user_id, amount)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ የገባው Room ID አልተገኘም። /start ብለው እንደገና ይሞክሩ።")
        return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    recharge_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💳 Recharge$"), handle_recharge_start)],
        states={
            RECHARGE_TXID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recharge_txid)]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    withdraw_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏧 Withdraw$"), handle_withdraw_start)],
        states={
            WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)],
            WITHDRAW_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_phone)]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    join_room_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_mode_callback, pattern="^friend_join$")],
        states={
            JOIN_ROOM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_join_code)]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.Regex("^💰 Balance$"), handle_balance))
    app.add_handler(MessageHandler(filters.Regex("^(⚽ eFootball|🎮 DLS)$"), handle_game_selection))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot_photo))

    app.add_handler(recharge_conv)
    app.add_handler(withdraw_conv)
    app.add_handler(join_room_conv)

    app.add_handler(CallbackQueryHandler(handle_claim_callback, pattern="^claim_"))
    app.add_handler(CallbackQueryHandler(handle_admin_callbacks, pattern="^(app_|rej_|dispute_)"))
    app.add_handler(CallbackQueryHandler(handle_mode_callback))

    print("Bot is running on Render...")
    app.run_polling()
