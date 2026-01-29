import os
import threading
import requests
from flask import Flask
import discord
from discord.ext import commands

# --- Web Server for Render Health Checks ---
app = Flask(__name__)
@app.route('/')
def home(): return "F1 Bot Status: Active ✅"
@app.route('/favicon.ico')
def favicon(): return '', 204

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 1. Driver Standings Command
@bot.command(name="drivers")
async def drivers(ctx):
    data = requests.get("https://ergast.com/api/f1/current/driverStandings.json").json()
    standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    msg = "🏎️ **Current Driver Standings:**\n"
    for i, d in enumerate(standings[:10], 1):
        msg += f"**{i}.** {d['Driver']['familyName']} — {d['points']} pts\n"
    await ctx.send(msg)

# 2. Constructor (Team) Standings Command
@bot.command(name="teams")
async def teams(ctx):
    data = requests.get("https://ergast.com/api/f1/current/constructorStandings.json").json()
    standings = data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
    msg = "🛠️ **Current Constructor Standings:**\n"
    for i, t in enumerate(standings, 1):
        msg += f"**{i}.** {t['Constructor']['name']} — {t['points']} pts\n"
    await ctx.send(msg)

# 3. Next Race Schedule Command
@bot.command(name="next")
async def next_race(ctx):
    data = requests.get("https://ergast.com/api/f1/current/next.json").json()
    r = data['MRData']['RaceTable']['Races'][0]
    msg = (f"🏁 **Next Grand Prix:** {r['raceName']}\n"
           f"📅 Date: {r['date']}\n"
           f"⏰ Time: {r['time']}\n"
           f"🏟️ Circuit: {r['Circuit']['circuitName']}")
    await ctx.send(msg)

# 4. Last Race Results Command
@bot.command(name="last")
async def last_race(ctx):
    data = requests.get("https://ergast.com/api/f1/current/last/results.json").json()
    r = data['MRData']['RaceTable']['Races'][0]
    results = r['Results'][:3]
    msg = f"🏆 **Results of {r['raceName']}:**\n"
    for res in results:
        msg += f"🥇 P{res['position']}: {res['Driver']['familyName']}\n"
    await ctx.send(msg)

# --- Start Everything ---
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: DISCORD_TOKEN not found!")
