import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime
import pytz
import os
from flask import Flask
from threading import Thread

# --- 1. إعداد سيرفر صغير لبقاء البوت مستيقظاً ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- 2. إعداد البوت ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ضع ID القناة هنا (يجب أن يكون رقماً)
NOTIFICATION_CHANNEL_ID = 123456789012345678 

def get_next_race_info():
    try:
        url = "http://ergast.com/api/f1/current/next.json"
        data = requests.get(url).json()
        race = data['MRData']['RaceTable']['Races'][0]
        race_time_str = f"{race['date']}T{race['time'].replace('Z', '')}"
        utc_time = datetime.strptime(race_time_str, "%Y-%m-%dT%H:%M:%S")
        utc_time = pytz.utc.localize(utc_time)
        makkah_tz = pytz.timezone('Asia/Riyadh')
        return {"name": race['raceName'], "time": utc_time.astimezone(makkah_tz)}
    except:
        return None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if not check_race_alerts.is_running():
        check_race_alerts.start()

# --- 3. مهمة التنبيه قبل السباق بيوم ---
@tasks.loop(hours=1)
async def check_race_alerts():
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel: return

    race = get_next_race_info()
    if race:
        now = datetime.now(pytz.timezone('Asia/Riyadh'))
        time_diff = race['time'] - now
        hours_until = time_diff.total_seconds() / 3600

        # التنبيه إذا كان الوقت المتبقي بين 23 و 24 ساعة
        if 23 < hours_until <= 24:
            embed = discord.Embed(title="🚨 تنبيه سباق غداً!", color=0xff0000)
            embed.add_field(name="السباق", value=race['name'], inline=False)
            embed.add_field(name="الوقت (مكة)", value=race['time'].strftime("%I:%M %p"), inline=True)
            await channel.send(content="@everyone", embed=embed)

# --- 4. الأوامر اليدوية ---
@bot.command()
async def f1(ctx):
    race = get_next_race_info()
    if race:
        await ctx.send(f"🏁 السباق القادم: **{race['name']}**\n⏰ توقيت مكة: `{race['time'].strftime('%Y-%m-%d %I:%M %p')}`")

# تشغيل السيرفر والبوت
keep_alive()
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
