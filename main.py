import os, sqlite3, random, string, asyncio, nest_asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Thread

# --- CONFIGURATION KOYEB (VOLUME) ---
# On utilise le chemin du Volume qu'on va créer
DB_FOLDER = "/workspace/db"
DB_NAME = os.path.join(DB_FOLDER, "rapitor_vault.db")

# --- 💾 DB INIT ---
def init_db():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, plan TEXT, hwid TEXT, created_at TEXT, status TEXT)')
    conn.commit()
    conn.close()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "🦅 RAPITOR TITAN BACKEND v15.0 - ACTIVE"

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key, hwid = data.get('key'), data.get('hwid')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM keys WHERE key=?", (key,)).fetchone()
    
    if not row or row['status'] == 'REVOKED':
        return jsonify({"status": "error", "message": "REVOKED"})
    
    if row['hwid'] is None:
        conn.execute("UPDATE keys SET hwid=?, status='ACTIVE' WHERE key=?", (hwid, key))
        conn.commit()
        return jsonify({"status": "success", "plan": row['plan']})
    
    return jsonify({"status": "success"}) if row['hwid'] == hwid else jsonify({"status": "error", "message": "HWID_MISMATCH"})

# --- 🤖 TELEGRAM ADMIN ---
BOT_TOKEN = "8372739692:AAHD-Mb92L69Ku0Mq4NWlKV3lq7W_GDPdCQ"
ADMIN_ID = 7516367607

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN_ID: return
    kb = [[InlineKeyboardButton("💎 GEN VIP", callback_data='gen_vip'), InlineKeyboardButton("🔥 GEN PREM", callback_data='gen_prem')]]
    await u.message.reply_text("🦅 RAPITOR COMMAND", reply_markup=InlineKeyboardMarkup(kb))

async def handle_btns(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    plan = "VIP" if "vip" in q.data else "PREMIUM"
    key = f"RAPITOR-{ ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)) }"
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO keys VALUES (?, ?, NULL, ?, 'PENDING')", (key, plan, datetime.now()))
    conn.commit()
    await q.edit_message_text(f"✅ NEW KEY: {key}\nPlan: {plan}")

if __name__ == "__main__":
    init_db()
    nest_asyncio.apply()
    
    # Port 8000 par défaut sur Koyeb
    port = int(os.environ.get("PORT", 8000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(handle_btns))
    bot.run_polling()