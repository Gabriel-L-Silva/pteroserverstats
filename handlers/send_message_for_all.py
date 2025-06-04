import os
import discord
from datetime import datetime, timezone
from colorama import Fore
from humanize import naturalsize
from .uptime_formatter import format_uptime

def build_server_embed_fields(server_data, config):
    details = server_data['details']
    stats = server_data['stats']
    resources = stats['resources']
    is_online = stats.get('current_state') in ["starting", "running"]
    fields = []
    # Status
    status_text = config.get('status.online') if is_online else config.get('status.offline')
    fields.append(("Status", status_text, False))
    # Details
    if config.get('server.details') and is_online:
        if config.get('server.memory'):
            memory_used = naturalsize(resources['memory_bytes'])
            memory_limit = "∞" if details['limits']['memory'] == 0 else naturalsize(details['limits']['memory'] * 1000000)
            fields.append(("Memory Usage", f"`{memory_used}` / `{memory_limit}`", config.get('embed.fields.inline', False)))
        if config.get('server.disk'):
            disk_used = naturalsize(resources['disk_bytes'])
            disk_limit = "∞" if details['limits']['disk'] == 0 else naturalsize(details['limits']['disk'] * 1000000)
            fields.append(("Disk Usage", f"`{disk_used}` / `{disk_limit}`", config.get('embed.fields.inline', False)))
        if config.get('server.cpu'):
            cpu_usage = f"{resources['cpu_absolute']:.2f}%"
            fields.append(("CPU Load", f"`{cpu_usage}`", config.get('embed.fields.inline', False)))
        if config.get('server.network'):
            network_rx = naturalsize(resources['network_rx_bytes'])
            network_tx = naturalsize(resources['network_tx_bytes'])
            fields.append(("Network", f"Upload: `{network_rx}`\nDownload: `{network_tx}`", config.get('embed.fields.inline', False)))
        if config.get('server.uptime'):
            uptime = format_uptime(resources['uptime'])
            fields.append(("Uptime", f"`{uptime}`", config.get('embed.fields.inline', False)))
    return fields

async def send_message_for_all(client, all_stats, config):
    channel_id = int(os.getenv('DiscordChannel'))
    channel = await client.fetch_channel(channel_id)
    # Find existing messages from bot (one per server)
    messages = []
    async for message in channel.history(limit=20):
        if message.author.id == client.user.id:
            messages.append(message)
    
    embeds = []
    for server_data in all_stats:
        name = server_data['details']['name']
        uuid = server_data['details']['uuid']
        server_id = uuid # Using the actual server ID
        
        panel_url = os.getenv('PanelURL').rstrip('/')
        manage_url = f"{panel_url}/server/{uuid}"
        
        embed = discord.Embed()
        embed.title = f"{name} - {config.get('embed.title', 'Server Stats')}"
        embed.description = f"Last update: <t:{int(datetime.now(timezone.utc).timestamp())}:R>"
        embed.color = int(config.get('embed.color', '5865F2'), 16)
        embed.timestamp = datetime.now(timezone.utc)
        
        # Add server fields
        for fname, fval, finline in build_server_embed_fields(server_data, config):
            embed.add_field(name=fname, value=fval, inline=finline)
            
        # Set footer with server ID
        footer_text = config.get('embed.footer.text', 'PteroServerStats')
        embed.set_footer(text=f"{footer_text} • ID: {server_id[:8]}...{server_id[-4:]}", 
                        icon_url=config.get('embed.footer.icon', ''))
        
        # Add manage button as a view (discord.py 2.0+)
        try:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Manage Server", url=manage_url, style=discord.ButtonStyle.link))
            embeds.append((embed, view))
        except Exception:
            embeds.append((embed, None))
    # Edit or send messages (one per server)
    try:
        for i, (embed, view) in enumerate(embeds):
            if i < len(messages):
                await messages[i].edit(embed=embed, view=view)
            else:
                await channel.send(embed=embed, view=view)
        # Delete extra old messages if any
        for j in range(len(embeds), len(messages)):
            await messages[j].delete()
        print(f"{Fore.CYAN}[PSS] {Fore.GREEN}One embed per server posted to {Fore.BLUE}{channel.name}{Fore.GREEN}!")
    except Exception as error:
        print(f"{Fore.CYAN}[PSS] {Fore.RED}Error posting server stats: {error}")
