
import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime
import pytz
import os
from flask import Flask
from threading import Thread

# --- 1. سيرفر Keep Alive لبقاء البوت مستيقظاً على ريندر ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بنجاح!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- 2. إعدادات البوت الأساسية ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ⚠️ تأكد من وضع ID القناة الصحيح هنا
NOTIFICATION_CHANNEL_ID = 123456789012345678 

def get_makkah_time(date_str, time_str):
    try:
        full_str = f"{date_str}T{time_str.replace('Z', '')}"
        utc_time = datetime.strptime(full_str, "%Y-%m-%dT%H:%M:%S")
        utc_time = pytz.utc.localize(utc_time)
        return utc_time.astimezone(pytz.timezone('Asia/Riyadh'))
    except: return None

# --- 3. الأوامر ---

@bot.command()
async def help(ctx):
    """دليل الأوامر"""
    embed = discord.Embed(title="🏎️ دليل أوامر بوت الفورميلا 1", color=0xFF0000)
    embed.add_field(name="🏁 `!next`", value="السباق القادم وتوقيت مكة.", inline=False)
    embed.add_field(name="🏁 `!last`", value="نتائج آخر سباق (الترتيب والفرق).", inline=False)
    embed.add_field(name="🏆 `!drivers`", value="ترتيب البطولة لجميع السائقين.", inline=False)
    embed.add_field(name="🏎️ `!teams`", value="ترتيب الفرق (الصانعين).", inline=False)
    embed.add_field(name="📅 `!calendar`", value="جدول السباقات القادمة وأماكنها.", inline=False)
    embed.set_footer(text="سيصلك تنبيه تلقائي قبل كل سباق بـ 24 ساعة")
    await ctx.send(embed=embed)

@bot.command()
async def last(ctx):
    """نتائج آخر سباق انتهى"""
    url = "http://ergast.com/api/f1/current/last/results.json"
    try:
        data = requests.get(url).json()['MRData']['RaceTable']['Races'][0]
        results = data['Results']
        embed = discord.Embed(title=f"🏁 نتائج: {data['raceName']}", color=0x3498db)
        content = ""
        for r in results:
            pos = r['position'].zfill(2)
            name = r['Driver']['familyName']
            team = r['Constructor']['name']
            content += f"`{pos}` **{name}** ({team})\n"
        embed.description = content
        await ctx.send(embed=embed)
    except: await ctx.send("❌ تعذر جلب النتائج.")

@bot.command()
async def drivers(ctx):
    """ترتيب جميع السائقين"""
    url = "http://ergast.com/api/f1/current/driverStandings.json"
    data = requests.get(url).json()['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    embed = discord.Embed(title="🏆 ترتيب بطولة السائقين", color=0xFFD700)
    content = ""
    for d in standings:
        pos = d['position'].zfill(2)
        name = d['Driver']['familyName']
        team = d['Constructors'][0]['name']
        pts = d['points']
        content += f"`{pos}` **{name}** ({team}) - {pts} ن\n"
    embed.description = content
    await ctx.send(embed=embed)

@bot.command()
async def teams(ctx):
    """ترتيب الفرق"""
    url = "http://ergast.com/api/f1/current/constructorStandings.json"
    data = requests.get(url).json()['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
    embed = discord.Embed(title="🏎️ ترتيب الصانعين", color=0x00BFFF)
    content = ""
    for t in data:
        pos = t['position']
        name = t['Constructor']['name']
        pts = t['points']
        content += f"`{pos}` **{name}** - {pts} ن\n"
    embed.description = content
    await ctx.send(embed=embed)

@bot.command()
async def next(ctx):
    """السباق القادم"""
    url = "http://ergast.com/api/f1/current/next.json"
    data = requests.get(url).json()['MRData']['RaceTable']['Races'][0]
    time = get_makkah_time(data['date'], data['time'])
    embed = discord.Embed(title=f"🏁 السباق القادم: {data['raceName']}", color=0x2ecc71)
    embed.add_field(name="📍 الحلبة", value=data['Circuit']['circuitName'])
    embed.add_field(name="⏰ توقيت مكة", value=time.strftime("%Y-%m-%d %I:%M %p"))
    await ctx.send(embed=embed)

@bot.command()
async def calendar(ctx):
    """جدول المواعيد"""
    url = "http://ergast.com/api/f1/current.json"
    races = requests.get(url).json()['MRData']['RaceTable']['Races']
    embed = discord.Embed(title="📅 جدول سباقات الموسم المتبقية", color=0x9b59b6)
    count = 0
    now = datetime.now(pytz.timezone('Asia/Riyadh'))
    for r in races:
        r_time = get_makkah_time(r['date'], r.get('time', '00:00:00Z'))
        if r_time and r_time > now:
            embed.add_field(name=r['raceName'], value=f"🗓️ {r_time.strftime('%d/%m')}\n📍 {r['Circuit']['Location']['country']}", inline=True)
            count += 1
        if count >= 9: break
    await ctx.send(embed=embed)

# --- 4. التنبيهات التلقائية ---
@tasks.loop(hours=1)
async def check_alerts():
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel: return
    try:
        url = "http://ergast.com/api/f1/current/next.json"
        data = requests.get(url).json()['MRData']['RaceTable']['Races'][0]
        r_time = get_makkah_time(data['date'], data['time'])
        if r_time:
            diff = (r_time - datetime.now(pytz.timezone('Asia/Riyadh'))).total_seconds() / 3600
            if 23 < diff <= 24:
                embed = discord.Embed(title="🚨 تذكير: السباق غداً!", description=f"سباق **{data['raceName']}** يبدأ غداً في تمام الساعة {r_time.strftime('%I:%M %p')} بتوقيت مكة.", color=0xe74c3c)
                await channel.send(content="@everyone", embed=embed)
    except: pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    check_alerts.start()

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
