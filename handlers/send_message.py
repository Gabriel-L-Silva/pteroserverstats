import json
import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
from colorama import Fore
from humanize import naturalsize
from .uptime_formatter import format_uptime
from .webhook import send_webhook_notification

async def send_message(client, server_data, config):
    """Send Discord message with server stats"""
    # Load cache to compare states
    cache = None
    cache_path = "cache.json"
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
        except:
            cache = None
    
    # Send webhook notifications for state changes
    current_state = server_data['stats']['current_state']
    cached_state = cache['stats']['current_state'] if cache and 'stats' in cache else None
    
    if current_state == "missing" and cached_state != "missing":
        # Server went down
        embed = discord.Embed(
            title="Server down",
            description=f"Server `{server_data['details']['name']}` is down.",
            color=0xED4245
        )
        send_webhook_notification(embed, config)
    elif current_state != "missing" and cached_state == "missing":
        # Server came back online
        embed = discord.Embed(
            title="Server online",
            description=f"Server `{server_data['details']['name']}` is back online.",
            color=0x57F287
        )
        send_webhook_notification(embed, config)
    
    # Save current data to cache
    with open(cache_path, 'w') as f:
        json.dump(server_data, f, indent=2)
    
    # Get Discord channel
    channel_id = int(os.getenv('DiscordChannel'))
    channel = await client.fetch_channel(channel_id)
    
    # Find existing message from bot
    message_to_edit = None
    async for message in channel.history(limit=10):
        if message.author.id == client.user.id:
            message_to_edit = message
            break
    
    # Create embed
    embed = discord.Embed()
    
    # Set embed properties from config
    if config.get('embed.author.name'):
        embed.set_author(
            name=config.get('embed.author.name'),
            icon_url=config.get('embed.author.icon') or None
        )
    
    if config.get('embed.title'):
        embed.title = config.get('embed.title')
    
    if config.get('embed.description'):
        # Calculate next update time
        next_update = datetime.now(timezone.utc).timestamp() + config.get('refresh', 10)
        next_update_discord = f"<t:{int(next_update)}:R>"
        description = config.get('embed.description').replace('{{time}}', next_update_discord)
        embed.description = description
    
    # Set embed color
    embed_color = config.get('embed.color', '5865F2')
    try:
        embed.color = int(embed_color, 16) if isinstance(embed_color, str) else embed_color
    except ValueError:
        embed.color = 0x5865F2
    
    # Set image and thumbnail
    if config.get('embed.image'):
        embed.set_image(url=config.get('embed.image'))
    
    if config.get('embed.thumbnail'):
        embed.set_thumbnail(url=config.get('embed.thumbnail'))
    
    # Set timestamp
    if config.get('embed.timestamp'):
        embed.timestamp = datetime.now(timezone.utc)
    
    # Set footer
    if config.get('embed.footer.text'):
        embed.set_footer(
            text=config.get('embed.footer.text'),
            icon_url=config.get('embed.footer.icon') or None
        )
    
    # Add status field
    is_online = current_state in ["starting", "running"]
    status_text = config.get('status.online') if is_online else config.get('status.offline')
    embed.add_field(name="Status", value=status_text, inline=False)
    
    # Add server details if enabled and server is online
    if config.get('server.details') and is_online:
        details = server_data['details']
        stats = server_data['stats']
        resources = stats['resources']
        
        field_inline = config.get('embed.fields.inline', False)
        
        # Memory usage
        if config.get('server.memory'):
            memory_used = naturalsize(resources['memory_bytes'])
            memory_limit = "∞" if details['limits']['memory'] == 0 else naturalsize(details['limits']['memory'] * 1000000)
            embed.add_field(
                name="Memory Usage",
                value=f"`{memory_used}` / `{memory_limit}`",
                inline=field_inline
            )
        
        # Disk usage
        if config.get('server.disk'):
            disk_used = naturalsize(resources['disk_bytes'])
            disk_limit = "∞" if details['limits']['disk'] == 0 else naturalsize(details['limits']['disk'] * 1000000)
            embed.add_field(
                name="Disk Usage",
                value=f"`{disk_used}` / `{disk_limit}`",
                inline=field_inline
            )
        
        # CPU usage
        if config.get('server.cpu'):
            cpu_usage = f"{resources['cpu_absolute']:.2f}%"
            embed.add_field(
                name="CPU Load",
                value=f"`{cpu_usage}`",
                inline=field_inline
            )
        
        # Network usage
        if config.get('server.network'):
            network_rx = naturalsize(resources['network_rx_bytes'])
            network_tx = naturalsize(resources['network_tx_bytes'])
            embed.add_field(
                name="Network",
                value=f"Upload: `{network_rx}`\nDownload: `{network_tx}`",
                inline=field_inline
            )
        
        # Uptime
        if config.get('server.uptime'):
            uptime = format_uptime(resources['uptime'])
            embed.add_field(
                name="Uptime",
                value=f"`{uptime}`",
                inline=field_inline
            )
    
    try:
        # Send or edit message
        if message_to_edit:
            await message_to_edit.edit(embed=embed)
        else:
            content = config.get('message.content') or None
            await channel.send(content=content, embed=embed)
        
        print(f"{Fore.CYAN}[PSS] {Fore.GREEN}Server stats successfully posted to the {Fore.BLUE}{channel.name}{Fore.GREEN} channel!")
        
    except discord.HTTPException as error:
        if error.code == 429:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Error 429 | Your IP has been rate limited by Discord. You must wait.")
        elif error.code == 403:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}FORBIDDEN | The channel ID you provided is incorrect or bot lacks permissions.")
        elif error.code == 50001:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Discord Error | Your discord bot doesn't have access to see/send message/edit message in the channel!")
        elif error.code == 50035 and "embed" in str(error):
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Discord Error | Embed message limit exceeded!")
        else:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Discord Error: {error}")
        
        if config.get('log_error'):
            print(f"Full error: {error}")
        exit(1)
        
    except Exception as error:
        print(f"{Fore.CYAN}[PSS] {Fore.RED}Unexpected Discord Error: {error}")
        if config.get('log_error'):
            print(f"Full error: {error}")
        exit(1)