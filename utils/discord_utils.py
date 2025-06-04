import discord

def create_embed(server_name, stats):
    status = "🟢 Online" if stats.get('current_state', '') == "running" else "🔴 Offline"
    color = 0x00ff00 if status == "🟢 Online" else 0xff0000
    embed = discord.Embed(title=f"Stats for {server_name}", color=color)
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="CPU Usage", value=f"{stats['cpu']}%", inline=True)
    embed.add_field(name="Memory Usage", value=f"{stats['memory']['current'] / 1024 / 1024:.2f} MB", inline=True)
    embed.add_field(name="Disk Usage", value=f"{stats['disk']['current'] / 1024 / 1024:.2f} MB", inline=True)
    embed.set_footer(text="PteroStats Bot")
    return embed
