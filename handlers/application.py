import os
import asyncio
import discord
from discord.ext import tasks
from discord import app_commands
from colorama import Fore
from .configuration import Configuration
from .get_stats import get_stats
from .send_message_for_all import send_message_for_all

class Application:
    def __init__(self):
        self.config = Configuration()
        # Create Discord client with minimal intents
        intents = discord.Intents.default()
        intents.message_content = False
        intents.guilds = True
        
        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)
        self._setup_commands()
    
    def _setup_commands(self):
        @self.tree.command(
            name="addserver",
            description="Add a Pterodactyl server to monitor"
        )
        @app_commands.describe(server_id="The Pterodactyl server ID to add")
        async def addserver(interaction: discord.Interaction, server_id: str):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("You need administrator permissions to use this command!", ephemeral=True)
                return
            
            server_ids = self.config.get('server_ids', [])
            if server_id in server_ids:
                await interaction.response.send_message(f"Server {server_id} is already being monitored!", ephemeral=True)
                return
            
            server_ids.append(server_id)
            self.config.set('server_ids', server_ids)
            self.config.save()
            
            await interaction.response.send_message(f"Added server {server_id} to monitoring list!", ephemeral=True)
            await self.update_all_servers()

        @self.tree.command(
            name="removeserver",
            description="Remove a Pterodactyl server from monitoring"
        )
        @app_commands.describe(server_id="The Pterodactyl server ID to remove")
        async def removeserver(interaction: discord.Interaction, server_id: str):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("You need administrator permissions to use this command!", ephemeral=True)
                return
            
            server_ids = self.config.get('server_ids', [])
            if server_id not in server_ids:
                await interaction.response.send_message(f"Server {server_id} is not in the monitoring list!", ephemeral=True)
                return
            
            server_ids.remove(server_id)
            self.config.set('server_ids', server_ids)
            self.config.save()
            
            await interaction.response.send_message(f"Removed server {server_id} from monitoring list!", ephemeral=True)
            await self.update_all_servers()

        @self.tree.command(
            name="listservers",
            description="List all monitored Pterodactyl servers"
        )
        async def listservers(interaction: discord.Interaction):
            server_ids = self.config.get('server_ids', [])
            if not server_ids:
                await interaction.response.send_message("No servers are currently being monitored!", ephemeral=True)
                return
            
            server_list = "\n".join(f"• {sid}" for sid in server_ids)
            await interaction.response.send_message(f"Currently monitored servers:\n{server_list}", ephemeral=True)
    
    def run(self):
        """Run the Discord bot application"""
        print(f"{Fore.CYAN}[PSS] {Fore.GREEN}Starting app...")
        
        @self.client.event
        async def on_ready():
            print(f"{Fore.CYAN}[PSS] {Fore.GREEN}{Fore.BLUE}{self.client.user.name}#{self.client.user.discriminator}{Fore.GREEN} is online!")
            
            # Sync slash commands
            await self.tree.sync()
            print(f"{Fore.CYAN}[PSS] {Fore.GREEN}Slash commands synced!")
            
            # Set bot presence
            if self.config.get('presence.enable'):
                await self._set_presence()
            
            # Update all servers
            await self.update_all_servers()
            self.stats_loop.start()
        
        @tasks.loop(seconds=self.config.get('refresh', 10))
        async def stats_loop():
            await self.update_all_servers()
        
        self.stats_loop = stats_loop
        
        # Start the bot
        try:
            bot_token = os.getenv('DiscordBotToken')
            if not bot_token:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}Discord Error | No Discord Bot Token found in environment!")
                exit(1)
            
            self.client.run(bot_token)
        except discord.LoginFailure:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Discord Error | Invalid Discord Bot Token! Make sure you have the correct token in the config!")
            exit(1)
        except Exception as e:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Discord Error | {str(e)}")
            exit(1)
    async def update_all_servers(self):
        """Fetch and post stats for all servers and send a single message to Discord"""
        # Get server IDs from config
        server_ids = self.config.get('server_ids', [])
        
        # If no server IDs in config, try environment variables as fallback
        if not server_ids:
            env_server_ids = os.getenv('SERVER_IDS')
            if env_server_ids:
                server_ids = [sid.strip() for sid in env_server_ids.split(',') if sid.strip()]
            
            # Legacy single server ID support
            if not server_ids:
                env_server_id = os.getenv('ServerID')
                if env_server_id:
                    server_ids = [env_server_id]
                    
            # If we found server IDs in environment, save them to config
            if server_ids:
                self.config.set('server_ids', server_ids)
                self.config.save()
        
        if not server_ids:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}No server IDs found in config or environment!")
            return
        # Gather stats for all servers
        all_stats = []
        for server_id in server_ids:
            os.environ['ServerID'] = server_id
            stats = await get_stats(self.client, self.config, return_data=True)
            if stats:
                all_stats.append(stats)
        # Send a single message for all servers
        await send_message_for_all(self.client, all_stats, self.config)
    
    async def _set_presence(self):
        """Set bot presence/status"""
        presence_text = self.config.get('presence.text')
        presence_type = self.config.get('presence.type', 'watching').lower()
        presence_status = self.config.get('presence.status', 'online').lower()
        
        if presence_text and presence_type:
            # Map presence type
            activity_type = discord.ActivityType.watching
            if presence_type == "playing":
                activity_type = discord.ActivityType.playing
            elif presence_type == "listening":
                activity_type = discord.ActivityType.listening
            elif presence_type == "competing":
                activity_type = discord.ActivityType.competing
            
            activity = discord.Activity(type=activity_type, name=presence_text)
            
            # Map status
            status = discord.Status.online
            if presence_status == "idle":
                status = discord.Status.idle
            elif presence_status == "dnd":
                status = discord.Status.dnd
            elif presence_status == "invisible":
                status = discord.Status.invisible
            
            await self.client.change_presence(activity=activity, status=status)