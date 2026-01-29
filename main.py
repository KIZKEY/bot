import os
import threading
from flask import Flask, send_from_directory
import discord
from discord.ext import commands

# --- 1. إعداد سيرفر الويب (Flask) لحل مشكلة المنفذ 8080 ---
app = Flask(__name__)

@app.route('/')
def index():
    return "البوت يعمل الآن ومستقر على المنفذ 8080!"

@app.route('/favicon.ico')
def favicon():
    # حل مشكلة الـ 404 التي ظهرت في السجلات
    return "", 204  # إرسال استجابة فارغة "No Content" لتجنب الخطأ

def run_flask():
    # تشغيل السيرفر على المنفذ 8080
    app.run(host='0.0.0.0', port=8080)

# --- 2. إعداد البوت (Discord Bot) ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'تم تسجيل الدخول بنجاح باسم: {bot.user.name}')
    print("السيرفر يعمل على http://127.0.0.1:8080")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓')

# --- 3. تشغيل الاثنين معاً ---
def main():
    # تشغيل سيرفر الويب في "خيط" منفصل (Thread) حتى لا يعطل البوت
    t = threading.Thread(target=run_flask)
    t.start()
    
    # تشغيل البوت (ضع التوكن الخاص بك هنا)
    # bot.run('YOUR_BOT_TOKEN_HERE')
    print("تنبيه: قم بوضع التوكن الخاص بك في الكود ليعمل البوت.")

if __name__ == '__main__':
    main()
