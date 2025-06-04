import discord
from discord.ext import tasks
import asyncio
import yaml
import os
from dotenv import load_dotenv
from utils.ptero_api import get_server_stats
from utils.discord_utils import create_embed
from utils.logger import log_info, log_error
import aiohttp
import sys

def prompt_env_var(var_name, prompt_text):
    value = os.getenv(var_name)
    if not value:
        print(f"{prompt_text}: ", end="", flush=True)
        value = input()
        with open('.env', 'a') as envfile:
            envfile.write(f'{var_name}={value}\n')
    return value

def prompt_config_var(var_name, prompt_text, default=None, is_list=False):
    if os.path.exists('config.yml'):
        with open('config.yml', 'r') as file:
            config = yaml.safe_load(file)
    else:
        config = {}
    value = config.get(var_name)
    if not value:
        if is_list:
            print(f"{prompt_text} (comma separated): ", end="", flush=True)
            value = input().split(',')
            value = [v.strip() for v in value if v.strip()]
        else:
            print(f"{prompt_text}{' ['+str(default)+']' if default else ''}: ", end="", flush=True)
            value = input() or default
        config[var_name] = value
        with open('config.yml', 'w') as file:
            yaml.dump(config, file)
    return value

if not os.path.exists('.env') or not os.path.exists('config.yml'):
    print("First run detected. Let's configure your bot.")
    prompt_env_var('DISCORD_TOKEN', 'Enter your Discord bot token')
    prompt_env_var('PTERO_API_KEY', 'Enter your Pterodactyl API key')
    prompt_env_var('PTERO_PANEL_URL', 'Enter your Pterodactyl panel URL (e.g. https://panel.example.com)')
    prompt_config_var('channel_id', 'Enter the Discord channel ID to post stats')
    prompt_config_var('server_ids', 'Enter the Pterodactyl server IDs to track', is_list=True)
    prompt_config_var('update_interval', 'Enter the update interval in seconds', default=300)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

with open("config.yml", 'r') as file:
    config = yaml.safe_load(file)

channel_id = config['channel_id']
server_ids = config['server_ids']
update_interval = config['update_interval']

@client.event
async def on_ready():
    log_info(f"Logged in as {client.user}")
    update_stats.start()

@tasks.loop(seconds=update_interval)
async def update_stats():
    channel = client.get_channel(channel_id)
    if channel is None:
        log_error("Channel not found.")
        return

    async with aiohttp.ClientSession() as session:
        for server_id in server_ids:
            try:
                stats = await get_server_stats(session, server_id)
                embed = create_embed(server_id, stats['attributes']['resources'])
                await channel.send(embed=embed)
            except Exception as e:
                log_error(f"Failed to fetch stats for {server_id}: {e}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg = message.content.lower()
    if msg.startswith("!pterostats"):
        channel = message.channel
        async with aiohttp.ClientSession() as session:
            for server_id in server_ids:
                try:
                    stats = await get_server_stats(session, server_id)
                    embed = create_embed(server_id, stats['attributes']['resources'])
                    await channel.send(embed=embed)
                except Exception as e:
                    log_error(f"Failed to fetch stats for {server_id}: {e}")
    elif msg.startswith("!addserver "):
        new_id = message.content.split(maxsplit=1)[1].strip()
        if new_id in server_ids:
            await message.channel.send(f"Server `{new_id}` is already being tracked.")
        else:
            server_ids.append(new_id)
            with open("config.yml", 'w') as file:
                yaml.dump({'channel_id': channel_id, 'server_ids': server_ids, 'update_interval': update_interval}, file)
            await message.channel.send(f"Server `{new_id}` added to tracking list.")
            log_info(f"Added server {new_id}")
    elif msg.startswith("!removeserver "):
        rem_id = message.content.split(maxsplit=1)[1].strip()
        if rem_id not in server_ids:
            await message.channel.send(f"Server `{rem_id}` is not being tracked.")
        else:
            server_ids.remove(rem_id)
            with open("config.yml", 'w') as file:
                yaml.dump({'channel_id': channel_id, 'server_ids': server_ids, 'update_interval': update_interval}, file)
            await message.channel.send(f"Server `{rem_id}` removed from tracking list.")
            log_info(f"Removed server {rem_id}")

client.run(os.getenv("DISCORD_TOKEN"))
