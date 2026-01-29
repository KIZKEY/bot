import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz

# سيرفر صغير جداً للبقاء حياً
app = Flask('')
@app.route('/')
def home(): return "F1 Bot Online"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# إعدادات البوت
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)
CH_ID = 123456789012345678 # ضع ID قناتك هنا

# --- دالة مساعدة لجلب البيانات مع معالجة الأخطاء ---
def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# --- الأمر الرئيسي الموحد !f1 ---
@bot.group(name="f1", invoke_without_command=True)
async def f1(ctx):
    help_msg = (
        "**🏁 أوامر بوت F1 المتاحة:**\n"
        "`!f1 drivers` - ترتيب السائقين\n"
        "`!f1 teams` - ترتيب الفرق\n"
        "`!f1 next` - السباق القادم\n"
        "`!f1 last` - نتائج آخر سباق\n"
        "`!f1 radio [رقم]` - راديو السائق (OpenF1)"
    )
    await ctx.send(help_msg)

@f1.command()
async def drivers(ctx):
    data = fetch_data("http://ergast.com/api/f1/current/driverStandings.json")
    if not data:
        return await ctx.send("⚠️ البيانات غير متوفرة حالياً، حاول مرة أخرى لاحقاً.")
    
    standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    msg = "**🏆 ترتيب السائقين:**\n"
    for d in standings:
        msg += f"`{d['position']}.` {d['Driver']['familyName']} - {d['points']}ن\n"
    await ctx.send(msg[:2000])

@f1.command()
async def teams(ctx):
    data = fetch_data("http://ergast.com/api/f1/current/constructorStandings.json")
    if not data:
        return await ctx.send("⚠️ تعذر جلب بيانات الفرق حالياً.")
    
    standings = data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
    msg = "**🏎️ ترتيب الفرق:**\n"
    for t in standings:
        msg += f"`{t['position']}.` {t['Constructor']['name']} - {t['points']}ن\n"
    await ctx.send(msg)

@f1.command()
async def next(ctx):
    data = fetch_data("http://ergast.com/api/f1/current/next.json")
    if not data:
        return await ctx.send("⚠️ لا توجد معلومات عن السباق القادم حالياً.")
    
    r = data['MRData']['RaceTable']['Races'][0]
    await ctx.send(f"🏁 السباق القادم: **{r['raceName']}**\n📅 التاريخ: {r['date']}")

@f1.command()
async def radio(ctx, num: int):
    res = fetch_data(f"https://api.openf1.org/v1/team_radio?driver_number={num}")
    if res:
        await ctx.send(f"🎙️ راديو السائق {num}: {res[-1]['recording_url']}")
    else:
        await ctx.send(f"❌ لم يتم العثور على تسجيلات راديو للسائق رقم {num}.")

# --- التنبيهات التلقائية ---
@tasks.loop(hours=1)
async def alert():
    channel = bot.get_channel(CH_ID)
    if not channel: return
    data = fetch_data("http://ergast.com/api/f1/current/next.json")
    if data:
        try:
            r = data['MRData']['RaceTable']['Races'][0]
            r_time = datetime.strptime(f"{r['date']}T{r['time'].replace('Z','')}", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Riyadh'))
            diff = (r_time - datetime.now(pytz.timezone('Asia/Riyadh'))).total_seconds() / 3600
            if 23 < diff <= 24:
                await channel.send(f"🚨 **تنبيه:** سباق {r['raceName']} غداً الساعة {r_time.strftime('%I:%M %p')} @everyone")
        except: pass

@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} is ready")
    if not alert.is_running(): alert.start()

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
