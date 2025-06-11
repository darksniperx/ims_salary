import os
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

BOT_TOKEN = '7736976337:AAGjQQU2JFj1Xd2pLUqX5Ee6Rq2v-AVtRqk'
ADMIN_ID = 7730908928

BASE_URL = "http://erp.imsec.ac.in/salary_slip/print_salary_slip/"
SAVE_DIR = "salary_slips"
LOG_DIR = "logs"
blocked_users = set()
user_list = set()

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def download_pdf(emp_id):
    url = f"{BASE_URL}{emp_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if "application/pdf" in res.headers.get("Content-Type", ""):
            filename = os.path.join(SAVE_DIR, f"sniper_{emp_id}.pdf")
            with open(filename, "wb") as f:
                f.write(res.content)
            return filename
        return None
    except:
        return None

def log_usage(user, action):
    log_file = os.path.join(LOG_DIR, f"{user.id}.log")
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now()}] {user.full_name} ({user.id}) -> {action}\n")

async def notify_admin(context, user, action):
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📢 *User Alert:*\n👤 @{user.username or 'NoUsername'}\n🆔 {user.id}\n🎯 Action: `{action}`",
        parse_mode="Markdown"
    )

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_list.add(user.id)

    kb = [[KeyboardButton("/downloadone <id>(8000-9200)")],
          [KeyboardButton("/downloadall <start> <end>(9000-9200)")],
          [KeyboardButton("/menu")],
          [KeyboardButton("/contact <your message>")]]
    await update.message.reply_text(
        "💥 Welcome to SNIPER ERP Bot\n👨‍💻 Created by: Sniper\n\nUse the menu or type a command below: /start to start",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    await notify_admin(context, user, "Started Bot")

# /downloadone
async def download_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in blocked_users:
        await update.message.reply_text("🚫 You are blocked from using this bot.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗Usage: /downloadone <id>")
        return

    emp_id = int(context.args[0])
    file_path = download_pdf(emp_id)
    if file_path:
        await update.message.reply_document(document=open(file_path, "rb"), filename=f"sniper_{emp_id}.pdf")
        log_usage(user, f"Downloaded sniper_{emp_id}.pdf")
        await notify_admin(context, user, f"Downloaded sniper_{emp_id}.pdf")
    else:
        await update.message.reply_text("❌ PDF Not Found.")

# /downloadall
async def download_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in blocked_users:
        await update.message.reply_text("🚫 You are blocked.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("❗Usage: /downloadall <start> <end>")
        return

    start_id = int(context.args[0])
    end_id = int(context.args[1])

    await update.message.reply_text(f"⏬ Downloading slips from {start_id} to {end_id}...")

    for i in range(start_id, end_id + 1):
        file_path = download_pdf(i)
        if file_path:
            await update.message.reply_document(document=open(file_path, "rb"), filename=f"sniper_{i}.pdf")
            log_usage(user, f"Downloaded sniper_{i}.pdf")
            await notify_admin(context, user, f"Downloaded sniper_{i}.pdf")
        else:
            await update.message.reply_text(f"❌ ID {i} Not Found.")

# /block
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Only admin can block users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗Usage: /block <user_id>")
        return

    uid = int(context.args[0])
    blocked_users.add(uid)
    await update.message.reply_text(f"❌ User {uid} is now blocked.")

# /unblock
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Only admin can unblock users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗Usage: /unblock <user_id>")
        return

    uid = int(context.args[0])
    blocked_users.discard(uid)
    await update.message.reply_text(f"✅ User {uid} is now unblocked.")

# /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton("/downloadone <id>(8000-9200)")],
          [KeyboardButton("/downloadall <start> <end>(9000-9200)")],
          [KeyboardButton("/contact <your message>")]]
    await update.message.reply_text("📜 Choose an option:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# /help (Admin only)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("🚫 This command is only for the bot admin.")
        return

    help_text = (
        "🛠 *Admin Help Panel:*\n\n"
        "👮 Admin ID: `{}`\n\n"
        "🔧 *Admin Commands:*\n"
        "/block <user_id> - Block user\n"
        "/unblock <user_id> - Unblock user\n"
        "/menu - Show command menu\n"
        "/help - Show this help\n\n"
        "📨 *User Support:*\n"
        "/contact <msg> - User can contact you\n\n"
        "📂 Logs: saved in `logs/`\n"
        "📁 PDFs: saved in `salary_slips/`\n\n"
        "🤖 Coded by Sniper 🔥"
    ).format(ADMIN_ID)

    await update.message.reply_text(help_text, parse_mode="Markdown")

# /contact
async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("📨 Usage: /contact <your message>")
        return

    message = " ".join(context.args)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 *Message from user:*\n👤 @{user.username or 'NoUsername'}\n🆔 {user.id}\n\n📝 {message}",
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Your message has been sent to the admin.")

# MAIN
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("downloadone", download_one))
    app.add_handler(CommandHandler("downloadall", download_all))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(CommandHandler("contact", contact_admin))

    print("🤖 SNIPER BOT IS RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
