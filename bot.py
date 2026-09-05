[9/5/2026 2:30 PM] 💯💥: #!/bin/bash

echo "🚀 የቴሌግራም ቦት ዝግጅት በመጀመር ላይ..."

# 1. Update system & Install Python/pip
echo "📦 Python እና pip በመጫን ላይ..."
sudo apt update && sudo apt install -y python3 python3-pip

# 2. Install required Python packages
echo "📚 python-telegram-bot ፓኬጅ በመጫን ላይ..."
pip3 install python-telegram-bot==20.7

# 3. Create bot.py file
echo "📝 bot.py ፋይል በመፍጠር ላይ..."
cat << 'EOF' > bot.py
import logging
import random
import string
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8640582909:AAEWINflMuUocmywDZrvIMjV_up84BHDF6I"
ADMIN_ID = 5283089413
MUST_JOIN_CHANNEL = "@trust1v1"
CHANNEL_LINK = "https://t.me/trust1v1"

TELEBIRR_NUMBER = "0940472271"
TELEBIRR_NAME = "Abenezer"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# CONVERSATION STATES
WAITING_JOIN_CODE = 1
WAITING_RECHARGE_AMOUNT = 2
WAITING_RECHARGE_RECEIPT = 3
WAITING_WITHDRAW_AMOUNT = 4
WAITING_WITHDRAW_ACCOUNT = 5

# MEMORY DATA
user_balances = {}  # {user_id: balance}
queues = {"50": [], "100": [], "200": []}
private_rooms = {}

# ---------------- FORCE JOIN CHECKER ----------------
async def is_user_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=MUST_JOIN_CHANNEL, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking membership: {e}")
        return True

async def send_force_join_message(update: Update):
    keyboard = [
        [InlineKeyboardButton("📢 ግሩፑን/ቻናሉን የተቀላቀሉ", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ አረጋግጥ (Check)", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "⚠️ ቦቱን ለመጠቀም መጀመሪያ የቴሌግራም ቻናላችንን መቀላቀል አለብዎት!\n\n"
        "እባክዎ ከታች ያለውን አዝራር ተጭነው ቻናሉን ከተቀላቀሉ በኋላ '✅ አረጋግጥ' የሚለውን ይጫኑ።"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ---------------- MAIN MENU ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_user_member(context, user_id):
        await send_force_join_message(update)
        return

    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    reply_keyboard = [
        ["⚽ eFootball", "⚽ DLS"],
        ["💳 Recharge", "💸 Withdraw"],
        ["💰 Balance", "ℹ️ እርዳታ"]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "እንኳን ወደ @trust1v1 eFootball & DLS የውርርድ ቦት በደህና መጡ! 👋\n\nእባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ፡",
        reply_markup=markup
    )

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_member(context, user_id):
        await query.message.delete()
        await start(update, context)
    else:
        await query.answer("❌ አሁንም ቻናሉን አልተቀላቀሉም! እባክዎ መጀመሪያ የተቀላቀሉ፤", show_alert=True)

# ---------------- BALANCE ----------------
async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(context, user_id):
        await send_force_join_message(update)
        return
[9/5/2026 2:30 PM] 💯💥: balance = user_balances.get(user_id, 0.0)
    await update.message.reply_text(
        f"💰 የእርስዎ ባላንስ: {balance:.2f} ብር\n\n"
        f"• ዝቅተኛው የማስገቢያ መጠን: 100 ብር\n"
        f"• ዝቅተኛው የማውጫ መጠን: 300 ብር",
        parse_mode="Markdown"
    )

# ---------------- GAMES ----------------
async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(context, user_id):
        await send_force_join_message(update)
        return

    game_name = update.message.text.replace("⚽ ", "")
    keyboard = [
        [
            InlineKeyboardButton("🎮 1v1 ፈልግ (Random Match)", callback_data=f"game_random_{game_name}"),
            InlineKeyboardButton("👥 ከጓደኛ ጋር (Private Room)", callback_data=f"game_friend_{game_name}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"ለ {game_name} የጨዋታ አይነት ይምረጡ፡",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ---------------- RECHARGE ----------------
async def start_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(context, user_id):
        await send_force_join_message(update)
        return ConversationHandler.END

    await update.message.reply_text(
        f"💳 ገንዘብ ማስገባት (Recharge)\n\n"
        f"• የቴሌብር ቁጥር: {TELEBIRR_NUMBER}\n"
        f"• ስም: {TELEBIRR_NAME}\n\n"
        f"• ዝቅተኛው የማስገቢያ መጠን 100 ብር ነው።\n"
        f"እባክዎ ማስገባት የሚፈልጉትን የብር መጠን ያስገቡ (ለምሳሌ፡ 100, 200, 500)፦",
        parse_mode="Markdown"
    )
    return WAITING_RECHARGE_AMOUNT

async def process_recharge_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 100:
        await update.message.reply_text("❌ እባክዎ ከ 100 ብር ያላነሰ ትክክለኛ የብር ቁጥር ብቻ ያስገቡ!")
        return WAITING_RECHARGE_AMOUNT

    context.user_data['recharge_amount'] = int(text)
    await update.message.reply_text(
        f"✅ የብር መጠን፡ {text} ብር\n\n"
        f"እባክዎ ብሩን በቴሌብር ({TELEBIRR_NUMBER}) ከከፈሉ በኋላ የክፍያውን ደረሰኝ (Screenshot) እዚህ ይላኩ።",
        parse_mode="Markdown"
    )
    return WAITING_RECHARGE_RECEIPT

async def process_recharge_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = context.user_data.get('recharge_amount')
    user = update.effective_user

    # Notify User
    await update.message.reply_text(
        f"✅ የ {amount} ብር ማስገቢያ ጥያቄዎ እና ደረሰኝዎ ደርሶናል!\n"
        f"አድሚኑ ደረሰኙን አረጋግጦ ባላንስዎ ላይ በቅርቡ ይጨምርልዎታል።"
    )

    # Forward Receipt to Admin
    admin_text = (
        f"💳 አዲስ የገንዘብ ማስገቢያ ጥያቄ!\n\n"
        f"👤 ተጠቃሚ: @{user.username} (ID: {user.id})\n"
        f"💰 የተጠየቀው መጠን: {amount} ብር"
    )
    
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_text, parse_mode="Markdown")
    
    return ConversationHandler.END

# ---------------- WITHDRAW ----------------
async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(context, user_id):
        await send_force_join_message(update)
        return ConversationHandler.END

    balance = user_balances.get(user_id, 0.0)
    if balance < 300:
        await update.message.reply_text(
            f"❌ መውጣት አይቻልም!\n\n"
            f"የእርስዎ ባላንስ {balance:.2f} ብር ነው።\n"
            f"ገንዘብ ለማውጣት ዝቅተኛው ባላንስ 300 ብር መሆን አለበት።",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"💸 ገንዘብ ማውጣት (Withdraw)\n\n"
        f"የእርስዎ ባላንስ፡ {balance:.2f} ብር\n"
        f"• ዝቅተኛው የማውጫ መጠን 300 ብር ነው።\n\n"
        f"ማውጣት የሚፈልጉትን የብር መጠን ያስገቡ፡",
        parse_mode="Markdown"
    )
    return WAITING_WITHDRAW_AMOUNT
[9/5/2026 2:30 PM] 💯💥: async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = user_balances.get(user_id, 0.0)
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ እባክዎ ትክክለኛ ቁጥር ብቻ ያስገቡ!")
        return WAITING_WITHDRAW_AMOUNT

    amount = int(text)
    if amount < 300:
        await update.message.reply_text("❌ ዝቅተኛው የማውጫ መጠን 300 ብር ነው! እባክዎ እንደገና ያስገቡ፦")
        return WAITING_WITHDRAW_AMOUNT

    if amount > balance:
        await update.message.reply_text(f"❌ የሂሳብ መጠንዎ አይበቃም! ያለዎት ባላንስ፡ {balance:.2f} ብር ነው፦")
        return WAITING_WITHDRAW_AMOUNT

    context.user_data['withdraw_amount'] = amount
    await update.message.reply_text(
        f"✅ የትራንስፈር መጠን፡ {amount} ብር\n\n"
        f"እባክዎ ብሩ የሚላክበትን የባንክ ወይም ቴሌብር አካውንት ቁጥር እና የስም ዝርዝር ያስገቡ፦",
        parse_mode="Markdown"
    )
    return WAITING_WITHDRAW_ACCOUNT

async def process_withdraw_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    amount = context.user_data.get('withdraw_amount')
    account_details = update.message.text

    # Deduct balance temporarily
    user_balances[user_id] -= amount

    await update.message.reply_text(
        f"✅ የ {amount} ብር የማውጣት ጥያቄዎ ታስዟል!\n\n"
        f"📍 የክፍያ መድረሻ፡ {account_details}\n"
        f"አድሚኑ ክፍያውን ፈጽሞ በቅርቡ ያረጋግጥልዎታል።"
    )

    # Forward Withdraw Request to Admin
    admin_text = (
        f"💸 አዲስ የማውጣት (Withdraw) ጥያቄ!\n\n"
        f"👤 ተጠቃሚ: @{user.username} (ID: {user.id})\n"
        f"💰 የሚወጣው መጠን: {amount} ብር\n"
        f"🏦 መድረሻ አካውንት: {account_details}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")

    return ConversationHandler.END

async def cancel_op(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሂደቱ ተሰርዟል።")
    return ConversationHandler.END

# ---------------- MAIN APP SETUP ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))

    app.add_handler(MessageHandler(filters.Regex("^💰 Balance$"), handle_balance))
    app.add_handler(MessageHandler(filters.Regex("^⚽ (eFootball|DLS)$"), handle_game_selection))

    recharge_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💳 Recharge$"), start_recharge)],
        states={
            WAITING_RECHARGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_recharge_amount)],
            WAITING_RECHARGE_RECEIPT: [MessageHandler(filters.PHOTO | filters.Document.ALL, process_recharge_receipt)]
        },
        fallbacks=[CommandHandler("cancel", cancel_op)]
    )
    app.add_handler(recharge_handler)

    withdraw_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 Withdraw$"), start_withdraw)],
        states={
            WAITING_WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            WAITING_WITHDRAW_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_account)]
        },
        fallbacks=[CommandHandler("cancel", cancel_op)]
    )
    app.add_handler(withdraw_handler)

    print("✅ ቦቱ ስራ ጀምሯል...")
    app.run_polling()

if name == "main":
    main()
EOF

# 4. Run the Bot
echo "▶️ ቦቱን በመቀሰቀስ ላይ..."
python3 bot.py
