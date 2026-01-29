import os
import threading
import requests
from flask import Flask, send_from_directory
import discord
from discord.ext import commands

# --- 1. حل مشاكل السجل والمنفذ (Web Server) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>F1 Bot is Online! 🏎️</h1><p>Server is running correctly on Render.</p>"

@app.route('/favicon.ico')
def favicon():
    # حل مشكلة 404 favicon التي تظهر في السجلات
    return "", 204 

def run_web():
    # Render يحدد المنفذ تلقائياً، وإذا لم يجد يستخدم 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. إعدادات بوت F1 ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# أمر ترتيب السائقين
@bot.command(name="ترتيب")
async def standings(ctx):
    try:
        response = requests.get("https://ergast.com/api/f1/current/driverStandings.json")
        data = response.json()
        standings_list = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        
        msg = "🏆 **ترتيب سائقي F1 الحالي:**\n"
        for i, driver in enumerate(standings_list[:10], 1):
            name = driver['Driver']['familyName']
            points = driver['points']
            msg += f"**{i}.** {name} — {points} نقطة\n"
        await ctx.send(msg)
    except Exception as e:
        await ctx.send("❌ عذراً، حدث خطأ أثناء جلب البيانات.")

# أمر السباق القادم
@bot.command(name="السباق")
async def next_race(ctx):
    try:
        response = requests.get("https://ergast.com/api/f1/current/next.json")
        data = response.json()
        race = data['MRData']['RaceTable']['Races'][0]
        
        msg = (f"🏁 **السباق القادم:**\n"
               f"📌 **الجولة:** {race['raceName']}\n"
               f"🏟️ **الحلبة:** {race['Circuit']['circuitName']}\n"
               f"📅 **التاريخ:** {race['date']}\n"
               f"⏰ **الوقت:** {race['time'].replace('Z', ' GMT')}")
        await ctx.send(msg)
    except Exception as e:
        await ctx.send("❌ لا توجد معلومات عن السباق القادم حالياً.")

# --- 3. التشغيل الذكي ---
if __name__ == "__main__":
    # تشغيل سيرفر الويب في خلفية النظام (Background Thread)
    threading.Thread(target=run_web, daemon=True).start()
    
    # جلب التوكن من إعدادات Render (Environment Variables)
    token = os.getenv('DISCORD_TOKEN')
    
    if token:
        bot.run(token)
    else:
        print("❌ خطأ: التوكن 'DISCORD_TOKEN' غير موجود في إعدادات Render!")
