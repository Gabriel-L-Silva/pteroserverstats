import os
import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from dotenv import load_dotenv

CONFIG_FILE = '.env'

def setup_config():
    """Prompt user for configuration and save to .env"""
    print("Configuring bot for first use...")
    config = {}
    config['DISCORD_TOKEN'] = input("Enter your Discord Bot Token: ").strip()
    config['PTERO_API_KEY'] = input("Enter your Pterodactyl API Key: ").strip()
    config['PTERO_PANEL_URL'] = input("Enter your Pterodactyl Panel URL (e.g., https://panel.example.com): ").strip().rstrip('/')
    config['SERVER_IDS'] = input("Enter Server IDs separated by commas: ").strip()
    config['DISCORD_CHANNEL_ID'] = input("Enter Discord Channel ID for auto-posts: ").strip()

    with open(CONFIG_FILE, 'w') as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")

    print(f"Configuration saved to {CONFIG_FILE}")

# Check for config
if not os.path.exists(CONFIG_FILE):
    setup_config()

# Load config
load_dotenv(CONFIG_FILE)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PTERO_API_KEY = os.getenv('PTERO_API_KEY')
PTERO_PANEL_URL = os.getenv('PTERO_PANEL_URL')
SERVER_IDS = os.getenv('SERVER_IDS').split(',')
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

HEADERS = {
    'Authorization': f'Bearer {PTERO_API_KEY}',
    'Accept': 'Application/vnd.pterodactyl.v1+json',
    'Content-Type': 'application/json'
}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

async def fetch_server_stats(session, server_id):
    url = f"{PTERO_PANEL_URL}/api/client/servers/{server_id}/resources"
    async with session.get(url, headers=HEADERS) as resp:
        data = await resp.json()
        attr = data.get('attributes', {})
        res = attr.get('resources', {})
        return {
            'server_id': server_id,
            'status': attr.get('current_state', 'unknown'),
            'memory': res.get('memory_bytes', 0),
            'disk': res.get('disk_bytes', 0),
            'cpu': res.get('cpu_absolute', 0),
            'network_rx': res.get('network_rx_bytes', 0),
            'network_tx': res.get('network_tx_bytes', 0),
            'uptime': res.get('uptime', 0)
        }

def bytes_to_human(n):
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"

def create_embed(stats_list):
    embed = discord.Embed(title="Pterodactyl Server Stats", color=0x00ff00)
    for stat in stats_list:
        status = "🟢 Online" if stat['status'] == 'running' else "🔴 Offline"
        embed.add_field(
            name=f"Server: {stat['server_id']}",
            value=(
                f"Status: {status}\n"
                f"Memory: {bytes_to_human(stat['memory'])}\n"
                f"Disk: {bytes_to_human(stat['disk'])}\n"
                f"CPU: {stat['cpu']}%\n"
                f"Network: ⬆ {bytes_to_human(stat['network_tx'])} | ⬇ {bytes_to_human(stat['network_rx'])}\n"
                f"Uptime: {stat['uptime'] // 60} min"
            ),
            inline=False
        )
    return embed

@bot.command()
async def stats(ctx):
    async with aiohttp.ClientSession() as session:
        tasks_list = [fetch_server_stats(session, sid) for sid in SERVER_IDS]
        stats_list = await asyncio.gather(*tasks_list)
    embed = create_embed(stats_list)
    await ctx.send(embed=embed)

@tasks.loop(minutes=5)
async def auto_post():
    channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
    if not channel:
        print("Invalid channel ID or bot missing permissions.")
        return
    async with aiohttp.ClientSession() as session:
        tasks_list = [fetch_server_stats(session, sid) for sid in SERVER_IDS]
        stats_list = await asyncio.gather(*tasks_list)
    embed = create_embed(stats_list)
    await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    auto_post.start()

bot.run(DISCORD_TOKEN)
