import smtplib
import json
from email.mime.text import MIMEText
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from flask import Flask
import threading
import datetime

# === TOKEN TELEGRAM ===
TELEGRAM_TOKEN = "8265910919:AAHNpn595E_cdIa4l-VZICQqmPjSCRdi3LI"

# === ADMIN ID (ID kamu) ===
ADMIN_ID = 8060543188   # ✅ ini ID kamu

# === File penyewa ===
USERS_FILE = "users.json"

# === Load akun email dari JSON ===
with open("accounts.json") as f:
    accounts = json.load(f)

EMAIL_RECEIVER = "support@support.whatsapp.com"
EMAIL_SUBJECT = "Pertanyaan mengenai WhatsApp Business untuk Android"

current_index = 0

# ------------------ Penyewa System ------------------
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def is_active(user_id):
    users = load_users()
    if str(user_id) not in users:
        return False
    expiry = datetime.datetime.fromisoformat(users[str(user_id)]["expiry"])
    return datetime.datetime.now() < expiry

# ------------------ Email Sender ------------------
def send_email(body):
    global current_index
    account = accounts[current_index]
    EMAIL_SENDER = account["EMAIL_SENDER"]
    EMAIL_PASSWORD = account["EMAIL_PASSWORD"]

    msg = MIMEText(body)
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        result = f"✅ sudah cok tunggu 30 detik ya ngentod"
    except Exception as e:
        result = f"❌ Gagal dengan {EMAIL_SENDER}: {str(e)}"

    current_index = (current_index + 1) % len(accounts)
    return result

# ------------------ Bot Handler ------------------
def start(update, context):
    user_id = update.effective_user.id
    if not is_active(user_id):
        update.message.reply_text("⚠️ Kamu tidak punya akses. Hubungi admin untuk sewa bot ini.")
        return
    update.message.reply_text("Kirimkan nomor WhatsApp kamu, nanti saya email-kan ke support WhatsApp.")

def handle_message(update, context):
    user_id = update.effective_user.id
    if not is_active(user_id):
        update.message.reply_text("⚠️ Akses kamu sudah kadaluarsa atau tidak terdaftar.")
        return

    nomor = update.message.text.strip()
    body = f"""Helo pihak WhatsApp, perkenalkan nama saya (Repzsx) saya ingin mengajukan banding tentang mendaftar nomor telefon, saat registrasi muncul teks "login tidak tersedia" mohon untuk memperbaiki masalah tersebut, nomor saya ({nomor})"""
    result = send_email(body)
    update.message.reply_text(result)

# ------------------ Admin Commands ------------------
def tambah(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id, days = context.args[0].split(":")
        days = int(days)
        users = load_users()
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        users[user_id] = {"expiry": expiry.isoformat()}
        save_users(users)
        update.message.reply_text(f"✅ User {user_id} ditambahkan, aktif {days} hari.")
    except:
        update.message.reply_text("❌ Format salah. Gunakan: /tambah <id>:<hari>")

def perpanjang(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id, days = context.args[0].split(":")
        days = int(days)
        users = load_users()
        if user_id not in users:
            update.message.reply_text("❌ User belum terdaftar.")
            return
        expiry = datetime.datetime.fromisoformat(users[user_id]["expiry"]) + datetime.timedelta(days=days)
        users[user_id]["expiry"] = expiry.isoformat()
        save_users(users)
        update.message.reply_text(f"🔄 User {user_id} diperpanjang {days} hari.")
    except:
        update.message.reply_text("❌ Format salah. Gunakan: /perpanjang <id>:<hari>")

def hapus(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        users = load_users()
        if user_id in users:
            del users[user_id]
            save_users(users)
            update.message.reply_text(f"🗑️ User {user_id} dihapus.")
        else:
            update.message.reply_text("❌ User tidak ditemukan.")
    except:
        update.message.reply_text("❌ Format salah. Gunakan: /hapus <id>")

def cekuser(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    users = load_users()
    if not users:
        update.message.reply_text("📭 Tidak ada user terdaftar.")
        return
    text = "📋 Daftar penyewa:\n"
    for uid, data in users.items():
        text += f"- {uid} | aktif sampai {data['expiry']}\n"
    update.message.reply_text(text)

# ------------------ Run Bot ------------------
def run_bot():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Admin commands
    dp.add_handler(CommandHandler("tambah", tambah, pass_args=True))
    dp.add_handler(CommandHandler("perpanjang", perpanjang, pass_args=True))
    dp.add_handler(CommandHandler("hapus", hapus, pass_args=True))
    dp.add_handler(CommandHandler("cekuser", cekuser))

    updater.start_polling()
    updater.idle()

# ------------------ Flask (UptimeRobot) ------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()