import os
import os, random, string, asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Thread
from supabase import create_client

# --- CONFIGURATION (À REMPLIR) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# Connexion Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home(): 
    return "🦅 RAPITOR TITAN BACKEND ACTIVE"

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key, hwid = data.get('key'), data.get('hwid')
    
    # Vérification dans Supabase
    res = supabase.table("keys").select("*").eq("key", key).execute()
    if not res.data or res.data[0]['status'] == 'REVOKED':
        return jsonify({"status": "error", "message": "REVOKED"})
    
    row = res.data[0]
    if row['hwid'] is None:
        supabase.table("keys").update({"hwid": hwid, "status": "ACTIVE"}).eq("key", key).execute()
        return jsonify({"status": "success", "plan": row['plan']})
    
    return jsonify({"status": "success"}) if row['hwid'] == hwid else jsonify({"status": "error", "message": "HWID_MISMATCH"})

# --- BOT TELEGRAM ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN_ID: return
    kb = [[InlineKeyboardButton("💎 GEN VIP", callback_data='gen_vip'), InlineKeyboardButton("🔥 GEN PREM", callback_data='gen_prem')]]
    await u.message.reply_text("🐍 RAPTOR COMMAND", reply_markup=InlineKeyboardMarkup(kb))

async def handle_btns(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    plan = "VIP" if "vip" in q.data else "PREMIUM"
    new_key = f"RAPTOR-{ ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)) }"
    
    # Insertion dans Supabase
    supabase.table("keys").insert({
        "key": new_key, 
        "plan": plan, 
        "status": "PENDING", 
        "created_at": str(datetime.now())
    }).execute()
    
    await q.edit_message_text(f"✅ NEW KEY: {new_key}\nPlan: {plan}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(handle_btns))
    bot.run_polling()
