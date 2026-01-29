import os
import threading
from flask import Flask
import discord
from discord.ext import commands

# --- إعداد سيرفر الويب لـ Render ---
app = Flask(__name__)

@app.route('/')
def status():
    return "Bot is Online and Healthy!"

@app.route('/favicon.ico')
def favicon():
    return '', 204

def run_web():
    # Render يمرر المنفذ عبر متغير بيئة يسمى PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- إعداد البوت ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# --- التشغيل الآلي ---
if __name__ == "__main__":
    # تشغيل خيط الويب للبقاء حياً على Render
    threading.Thread(target=run_web, daemon=True).start()
    
    # جلب التوكن آلياً من إعدادات Render (بدون كتابته يدوياً)
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: No DISCORD_TOKEN found in Render Dashboard!")
