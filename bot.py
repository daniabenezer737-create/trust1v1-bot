import os
import logging
import random
import string
import threading
import sqlite3
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

# --- SQLite Database Setup (ባላንስ ፈጽሞ እንዳይጠፋ) ---
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            user_id INTEGER PRIMARY KEY,
            balance REAL
        )
    ''')
    conn.commit()
    return conn, cursor

db_conn, db_cursor = init_db()

def get_user_balance(user_id: int) -> float:
    db_cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    row = db_cursor.fetchone()
    if row is None:
        return 0.0
    return row[0]

def update_user_balance(user_id: int, amount: float):
    current = get_user_balance(user_id)
    new_balance = current + amount
    db_cursor.execute('INSERT OR REPLACE INTO balances (user_id, balance) VALUES (?, ?)', (user_id, new_balance))
    db_conn.commit()
    return new_balance

# Render / Railway Health Check Server
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

private_rooms = {}
active_matches = {}

JOIN_ROOM_STATE = 1
RECHARGE_PHOTO = 2  # ስክሪንሻት መቀበያ ስቴት
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

    bal = get_user_balance(user_id)

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
        f"እዚህ ጋር ከጓደኛዎ ጋር ሩም ፈጥረው በመወዳደር የገንዘብ ሽልማቶችን ማግኘት ይችላሉ።\n\n"
        f"💳 **የአሁኑ ባላንስዎ፦** `{bal} ብር`\n\n"
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
        bal = get_user_balance(user_id)

        reply_keyboard = [
            ['⚽ eFootball', '🎮 DLS'],
            ['💳 Recharge', '🏧 Withdraw'],
            ['💰 Balance']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        welcome_text = (
            f"ሰላም {first_name}! 👋\n"
            f"እንኳን ወደ **1v1 Gaming Betting Bot** በደህና መጡ! 🎮⚽\n\n"
            f"እዚህ ጋር ከጓደኛዎ ጋር ሩም ፈጥረው በመወዳደር የገንዘብ ሽልማቶችን ማግኘት ይችላሉ።\n\n"
            f"💳 **የአሁኑ ባላንስዎ፦** `{bal} ብር`\n\n"
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
    bal = get_user_balance(user_id)
    await update.message.reply_text(f"💳 **የእርስዎ ባላንስ፦** {bal} ብር", parse_mode="Markdown")

# Recharge Handler (Screenshot based)
async def handle_recharge_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📥 **ብር ገቢ ማድረጊያ (Recharge)**\n\n"
        f"• አነስተኛ ገቢ መጠን፦ **{MIN_DEPOSIT} ብር**\n\n"
        f"📲 **Telebirr Details:**\n"
        f"• ስልክ፦ `{TELEBIRR_PHONE}`\n"
        f"• ስም፦ **{TELEBIRR_NAME}**\n\n"
        f"እባክዎን ብር ከላኩ በኋላ የከፈሉበትን **ስክሪንሻት (Screenshot ፎቶ)** እዚህ ይላኩ፦"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return RECHARGE_PHOTO

async def handle_recharge_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ እባክዎን የቴሌብር ክፍያ የፈጸሙበትን **ስክሪንሻት (Screenshot ፎቶ)** ብቻ ይላኩ!")
        return RECHARGE_PHOTO

    photo = update.message.photo[-1].file_id
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

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=f"🔔 **አዲስ የ Recharge (የገቢ) ጥያቄ!**\n\n"
                f"• User ID: `{user_id}`\n\n"
                f"እባክዎን ስክሪንሻቱን አረጋግጠው የሚፈለገውን የብር መጠን ይምረጡ፦",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ የገቢ ማረጋገጫ ፎቶዎ ለ Admin ተልኳል። ሲረጋገጥ ባላንስዎ ላይ ይጨመራል!")
    return ConversationHandler.END

# Withdraw Handler
async def handle_withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_user_balance(user_id)

    if bal < MIN_WITHDRAW:
        await update.message.reply_text(f"❌ ብር ለማውጣት በትንሹ **{MIN_WITHDRAW} ብር** ባላንስ መኖር አለበት።\nየእርስዎ ባላንስ፦ {bal} ብር", parse_mode="Markdown")
        return ConversationHandler.END

    await update.message.reply_text(f"ወጪ ማድረግ የሚፈልጉትን የብር መጠን ያስገቡ (ትንሹ {MIN_WITHDRAW} ብር)፦")
    return WITHDRAW_AMOUNT

async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = update.effective_user.id
        bal = get_user_balance(user_id)

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

    update_user_balance(user_id, -amount)

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
        new_bal = update_user_balance(user_id, amount)
        await query.edit_message_text(f"✅ ለ User `{user_id}` {amount} ብር ገቢ ተደርጓል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"🎉 የ {amount} ብር ገቢ ጥያቄዎ ጸድቋል! አዲሱ ባላንስዎ፡ {new_bal} ብር")

    elif data.startswith("rej_rec_"):
        user_id = int(data.split("_")[2])
        await query.edit_message_text(f"❌ ለ User `{user_id}` የገቢ ጥያቄ ተሰርዟል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, "❌ የገቢ ጥያቄዎ አልፀደቀም። እባክዎን የላኩትን ስክሪንሻት አረጋግጠው እንደገና ይሞክሩ።")

    elif data.startswith("app_wd_"):
        _, _, user_id, amount = data.split("_")
        user_id, amount = int(user_id), float(amount)
        await query.edit_message_text(f"✅ ለ User `{user_id}` የ {amount} ብር ወጪ ጥያቄ ተፈጽሟል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"🎉 የ {amount} ብር ወጪ ጥያቄዎ ጸድቋል! ብሩ ወደ Telebirr አካውንትዎ ተልኳል።")

    elif data.startswith("rej_wd_"):
        _, _, user_id, amount = data.split("_")
        user_id, amount = int(user_id), float(amount)
        new_bal = update_user_balance(user_id, amount)
        await query.edit_message_text(f"❌ ለ User `{user_id}` የ {amount} ብር ወጪ ጥያቄ ተሰርዟል፤ ብሩ ተመልሷል።", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"❌ የብር ማውጣት ጥያቄዎ አልፀደቀም። የተቀነሰው {amount} ብር ወደ ባላንስዎ ተመልሷል። አዲሱ ባላንስዎ: {new_bal} ብር")

# Game Selection
async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_user_balance(user_id)

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
        [InlineKeyboardButton("🏠 ሩም ፍጠር (Create Room)", callback_data="friend_create")],
        [InlineKeyboardButton("🔑 ሩም ተቀላቀል (Join Room)", callback_data="friend_join")]
    ]
    await update.message.reply_text(f"ለ {text} ከጓደኛ ጋር ለመጫወት የሚፈልጉትን ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

async def start_match(context: ContextTypes.DEFAULT_TYPE, p1: int, p2: int, amount: float):
    update_user_balance(p1, -amount)
    update_user_balance(p2, -amount)

    match_id = f"{p1}_{p2}_{amount}"
    active_matches[match_id] = {'p1': p1, 'p2': p2, 'amount': amount, 'claims': {}}

    try:
        chat_p1 = await context.bot.get_chat(p1)
        name_p1 = f"@{chat_p1.username}" if chat_p1.username else chat_p1.first_name
    except Exception:
        name_p1 = str(p1)

    try:
        chat_p2 = await context.bot.get_chat(p2)
        name_p2 = f"@{chat_p2.username}" if chat_p2.username else chat_p2.first_name
    except Exception:
        name_p2 = str(p2)

    keyboard = [
        [InlineKeyboardButton("🏆 አሸንፌአለሁ", callback_data=f"claim_win_{match_id}")],
        [InlineKeyboardButton("❌ ተሸንፌአለሁ", callback_data=f"claim_lose_{match_id}")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    msg_p1 = (
        f"🎮 **ጨዋታው ተጀምሯል!**\n\n"
        f"• ተጋጣሚ: `{name_p2}`\n"
        f"• የውርርድ መጠን: **{amount} ብር**\n"
        f"• ጠቅላላ ሽልማት: **{amount * 2} ብር**\n\n"
        f"ጨዋታው ሲያልቅ ውጤቱን ይምረጡ:"
    )
    
    msg_p2 = (
        f"🎮 **ጨዋታው ተጀምሯል!**\n\n"
        f"• ተጋጣሚ: `{name_p1}`\n"
        f"• የውርርድ መጠን: **{amount} ብር**\n"
        f"• ጠቅላላ ሽልማት: **{amount * 2} ብር**\n\n"
        f"ጨዋታው ሲያልቅ ውጤቱን ይምረጡ:"
    )

    await context.bot.send_message(p1, msg_p1, reply_markup=markup, parse_mode="Markdown")
    await context.bot.send_message(p2, msg_p2, reply_markup=markup, parse_mode="Markdown")

async def handle_claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    parts = data.split("_")
    action = parts[1]
    match_id = "_".join(parts[2:])

    if match_id not in active_matches:
        await query.edit_message_text("❌ ይህ ጨዋታ ተጠናቋል ወይም አልተገኘም።")
        return

    match = active_matches[match_id]
    p1, p2, amount = match['p1'], match['p2'], match['amount']

    match['claims'][user_id] = action
    await query.edit_message_text("✅ የጨዋታው ውጤት ምላሽዎ ተመዝግቧል። ተጋጣሚዎ ምላሽ እስኪሰጥ ይጠብቁ...")

    if len(match['claims']) == 2:
        c1, c2 = match['claims'].get(p1), match['claims'].get(p2)
        prize = amount * 2

        if c1 == "win" and c2 == "win":
            msg = "⚠️ ሁለታችሁም 'አሸንፌአለሁ' ብላችኋል! እባክዎን የጨዋታውን የማጠናቀቂያ Screenshot በዚህ ቦት ላይ ይላኩ።"
            await context.bot.send_message(p1, msg)
            await context.bot.send_message(p2, msg)
        elif c1 == "win" and c2 == "lose":
            new_p1_bal = update_user_balance(p1, prize)
            await context.bot.send_message(p1, f"🎉 እንኳን ደስ አለዎት! {prize} ብር አሸንፈዋል። አዲሱ ባላንስዎ: {new_p1_bal} ብር")
            await context.bot.send_message(p2, f"❌ በጨዋታው ተሸንፈዋል።")
            del active_matches[match_id]
        elif c2 == "win" and c1 == "lose":
            new_p2_bal = update_user_balance(p2, prize)
            await context.bot.send_message(p2, f"🎉 እንኳን ደስ አለዎት! {prize} ብር አሸንፈዋል። አዲሱ ባላንስዎ: {new_p2_bal} ብር")
            await context.bot.send_message(p1, f"❌ በጨዋታው ተሸንፈዋል።")
            del active_matches[match_id]
        elif c1 == "lose" and c2 == "lose":
            update_user_balance(p1, amount)
            update_user_balance(p2, amount)
            msg = "⚠️ ሁለታችሁም 'ተሸንፌአለሁ' ስላላችሁ የተያዘው ብር ተመልሷል።"
            await context.bot.send_message(p1, msg)
            await context.bot.send_message(p2, msg)
            del active_matches[match_id]

async def handle_screenshot_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ውጭ ላይ የሚላኩ ፎቶዎች (ለምሳሌ በጨዋታ አለመግባባት ጊዜ የሚላኩ ስክሪንሻቶች)
    user_id = update.effective_user.id
    photo = update.message.photo[-1].file_id

    found_match_id = None
    target_match = None
    for m_id, m_data in active_matches.items():
        if user_id in (m_data['p1'], m_data['p2']):
            found_match_id = m_id
            target_match = m_data
            break

    if target_match:
        p1, p2, amount = target_match['p1'], target_match['p2'], target_match['amount']
        other_id = p2 if user_id == p1 else p1

        keyboard = [
            [
                InlineKeyboardButton(f"🏆 User {user_id} አሸናፊ", callback_data=f"dwin_{found_match_id}_{user_id}"),
                InlineKeyboardButton(f"🏆 User {other_id} አሸናፊ", callback_data=f"dwin_{found_match_id}_{other_id}")
            ]
        ]

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=f"⚠️ **የጨዋታ አለመግባባት (Dispute Screenshot)!**\n\n"
                    f"• የላከው User: `{user_id}`\n"
                    f"• ተጋጣሚ User: `{other_id}`\n"
                    f"• የውርርድ መጠን: {amount} ብር",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text("✅ ስክሪንሻቱ ለ Admin ተልኳል። ማጣራቱ እንደተጠናቀቀ አሸናፊው ይፋ ይደረጋል!")
    else:
        await update.message.reply_text("❌ በአሁኑ ሰዓት አለመግባባት ውስጥ ያለ ጨዋታ አልተገኘም።")

async def handle_admin_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("dwin_"):
        _, match_id, winner_str = data.split("_", 2)
        winner_id = int(winner_str)

        if match_id not in active_matches:
            await query.edit_message_text("❌ ይህ ጨዋታ ቀድሞ ተዘግቷል ወይም አልተገኘም።")
            return

        match = active_matches[match_id]
        p1, p2, amount = match['p1'], match['p2'], match['amount']
        loser_id = p2 if winner_id == p1 else p1

        prize = amount * 2
        new_winner_bal = update_user_balance(winner_id, prize)
        
        del active_matches[match_id]

        await query.edit_message_text(f"✅ አሸናፊው User `{winner_id}` ተለይቷል። {prize} ብር ተጨምሮለታል።", parse_mode="Markdown")
        await context.bot.send_message(winner_id, f"🎉 Admin ውጤቱን አረጋግጧል! የ {prize} ብር ሽልማት ባላንስዎ ላይ ተጨምሯል። አዲሱ ባላንስዎ: {new_winner_bal} ብር")
        await context.bot.send_message(loser_id, f"❌ Admin ውጤቱን አረጋግጧል! በጨዋታው ተሸንፈዋል።")

async def handle_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "friend_create":
        keyboard = [
            [InlineKeyboardButton("100 ብር", callback_data="create_100"),
             InlineKeyboardButton("200 ብር", callback_data="create_200"),
             InlineKeyboardButton("500 ብር", callback_data="create_500")]
        ]
        await query.edit_message_text("የሩም የውርርድ መጠን ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("create_"):
        amount = int(query.data.split("_")[1])
        user_id = query.from_user.id
        bal = get_user_balance(user_id)

        if bal < amount:
            await query.edit_message_text(f"❌ በቂ ባላንስ የለዎትም! (የእርስዎ ባላንስ: {bal} ብር)")
            return

        room_code = generate_room_code()
        private_rooms[room_code] = {'host': user_id, 'amount': amount}

        await query.edit_message_text(
            f"✅ ሩም ተፈጥሯል!\n\n"
            f"📌 **የሩም ID (Code)**: `{room_code}`\n"
            f"💰 **የውርርድ መጠን**: {amount} ብር\n\n"
            f"ይህንን የሩም ID (ኮድ) ለጓደኛዎ ይላኩለት። ጓደኛዎ ቦቱ ላይ በመግባት 'ሩም ተቀላቀል' የሚለውን በመጫን ይህንን ኮድ ያስገባል።",
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

        if user_id == host_id:
            await update.message.reply_text("❌ የፈጠሩትን ሩም እርስዎራሱ መቀላቀል አይችሉም። ሌላ ኮድ ያስገቡ፦")
            return JOIN_ROOM_STATE

        bal = get_user_balance(user_id)
        if bal < amount:
            await update.message.reply_text(f"❌ በቂ ባላንስ የለዎትም! (የእርስዎ ባላንስ: {bal} ብር)")
            return ConversationHandler.END

        await start_match(context, host_id, user_id, amount)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ የገባው Room ID አልተገኘም። እባክዎን ትክክለኛውን ኮድ እንደገና ያስገቡ፦")
        return JOIN_ROOM_STATE

if __name__ == '__main__':
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Recharge Conversation Handler (አሁን ፎቶ ብቻ ይቀበላል)
    recharge_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💳 Recharge$"), handle_recharge_start)],
        states={
            RECHARGE_PHOTO: [MessageHandler(filters.PHOTO, handle_recharge_photo_input)]
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
    app.add_handler(CallbackQueryHandler(handle_admin_dispute, pattern="^dwin_"))
    app.add_handler(CallbackQueryHandler(handle_admin_callbacks, pattern="^(app_|rej_)"))
    app.add_handler(CallbackQueryHandler(handle_mode_callback))

    print("Bot is running with Screenshot Recharge mode...")
    app.run_polling()
