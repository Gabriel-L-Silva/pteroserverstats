import os
import re
import uuid
import requests
import discord
from urllib.parse import urlparse
from colorama import Fore
from .application import Application

class Setup:
    def __init__(self):
        self.questions = [
            "Please enter your panel URL: ",
            "Please enter your panel API key: ",
            "Please enter your discord bot token: ",
            "Please enter your discord channel ID: ",
            "Please enter your panel server IDs (comma separated): "
        ]
        
        self.answers = []
    
    def run(self):
        """Run the interactive setup process"""
        print(f"{Fore.CYAN}Welcome to PteroServerStats!")
        print(f"{Fore.YELLOW}Please fill in the following credentials to set up the app.\n")
        
        self._ask_questions()
    
    def _ask_questions(self):
        """Ask setup questions interactively"""
        for i, question in enumerate(self.questions):
            while True:
                print(question)
                answer = input("> ").strip()
                
                if self._validate_answer(i, answer):
                    # Process URL to get origin only
                    if i == 0 and self._is_valid_url(answer):
                        self.answers.append(urlparse(answer).scheme + "://" + urlparse(answer).netloc)
                    else:
                        self.answers.append(answer)
                    break
        
        # Validate all credentials
        self._validate_credentials()
    
    def _validate_answer(self, question_index, answer):
        """Validate individual answers"""
        if question_index == 0:  # Panel URL
            if not self._is_valid_url(answer):
                print(f'{Fore.RED}❌ Invalid Panel URL. Please enter a valid URL. Example Correct URL: "https://panel.example.com"')
                return False
        
        elif question_index == 1:  # Panel API Key
            if not re.match(r'^(plcn_|ptlc_)', answer):
                print(f'{Fore.RED}❌ Invalid Panel API key. It must start with "plcn_" or "ptlc_".')
                return False
            
            if re.match(r'^(peli_|ptla_)', answer):
                print(f'{Fore.RED}❌ Invalid Panel API key. You cannot use Application API Keys.')
                return False
        
        elif question_index == 2:  # Discord Bot Token
            # Basic token validation (Discord tokens are usually long strings)
            if len(answer) < 50:
                print(f'{Fore.RED}❌ Invalid Discord Bot Token. Token seems too short.')
                return False
        
        elif question_index == 3:  # Channel ID
            if not re.match(r'^\d+$', answer):
                print(f'{Fore.RED}❌ Invalid Channel ID. It must be a number.')
                return False
        
        elif question_index == 4:  # Server IDs (comma separated)
            ids = [s.strip() for s in answer.split(',') if s.strip()]
            if not ids:
                print(f'{Fore.RED}❌ You must provide at least one valid Panel Server ID.')
                return False
            for sid in ids:
                try:
                    uuid.UUID(sid)
                except ValueError:
                    print(f'{Fore.RED}❌ Invalid Panel Server ID: {sid}')
                    return False
        
        return True
    
    def _is_valid_url(self, url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _validate_credentials(self):
        """Validate all credentials with their respective services"""
        panel_url, panel_key, bot_token, channel_id, server_ids = self.answers
        server_id = server_ids.split(',')[0].strip()
        
        # Test panel credentials
        try:
            response = requests.get(
                f"{panel_url}/api/client",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {panel_key}"
                },
                timeout=10
            )
            response.raise_for_status()
            print(f"\n{Fore.GREEN}✓ Valid Panel Credentials.")
            
        except Exception as error:
            print(f"\n{Fore.RED}❌ Invalid Panel Credentials.")
            self._handle_panel_error(error)
            print(f"\n{Fore.RED}Please run the setup again and fill in the correct credentials.")
            exit(1)
        
        # Test server ID
        try:
            response = requests.get(
                f"{panel_url}/api/client/servers/{server_id}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {panel_key}"
                },
                timeout=10
            )
            response.raise_for_status()
            print(f"{Fore.GREEN}✓ Valid Panel Server ID.")
            
        except Exception as error:
            print(f"\n{Fore.RED}❌ Invalid Server ID.")
            self._handle_panel_error(error)
            print(f"\n{Fore.RED}Please run the setup again and fill in the correct credentials.")
            exit(1)
        
        # Test Discord credentials
        self._validate_discord_credentials(bot_token, channel_id)
    
    def _validate_discord_credentials(self, bot_token, channel_id):
        """Validate Discord bot token and channel ID"""
        import asyncio
        
        async def test_discord():
            try:
                # Create temporary client to test credentials
                intents = discord.Intents.default()
                intents.guilds = True
                client = discord.Client(intents=intents)
                
                @client.event
                async def on_ready():
                    try:
                        print(f"{Fore.GREEN}✓ Valid Discord Bot.")
                        
                        # Test channel access
                        channel = await client.fetch_channel(int(channel_id))
                        print(f"{Fore.GREEN}✓ Valid Discord Channel.")
                        
                        # Save configuration
                        self._save_configuration()
                        
                        await client.close()
                        
                        # Start the main application
                        print(f"\n{Fore.GREEN}Configuration saved in {Fore.BLUE}.env{Fore.GREEN}.\n")
                        app = Application()
                        app.run()
                        
                    except discord.NotFound:
                        print(f"{Fore.RED}❌ Invalid Channel ID.")
                        await client.close()
                        exit(1)
                    except discord.Forbidden:
                        print(f"{Fore.RED}❌ Bot doesn't have access to the channel.")
                        await client.close()
                        exit(1)
                    except Exception as e:
                        print(f"{Fore.RED}❌ Error accessing channel: {e}")
                        await client.close()
                        exit(1)
                
                await client.start(bot_token)
                
            except discord.LoginFailure:
                print(f"{Fore.RED}❌ Invalid Discord Bot Token.")
                print(f"\n{Fore.RED}Please run the setup again and fill in the correct credentials.")
                exit(1)
            except Exception as e:
                print(f"{Fore.RED}❌ Discord Error: {e}")
                exit(1)
        
        # Run the async validation
        try:
            asyncio.run(test_discord())
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Setup interrupted by user.")
            exit(1)
    
    def _save_configuration(self):
        """Save configuration to .env file"""
        panel_url, panel_key, bot_token, channel_id, server_ids = self.answers
        
        # Create setup completion marker
        with open(".setup-complete", "w") as f:
            f.write("If you want to re-run the setup process, you can delete this file.")
        
        # Save environment variables
        env_content = f"""PanelURL={panel_url}
PanelKEY={panel_key}
DiscordBotToken={bot_token}
DiscordChannel={channel_id}
ServerID={server_ids.split(',')[0].strip()}
SERVER_IDS={server_ids}"""
        
        with open(".env", "w") as f:
            f.write(env_content)
    
    def _handle_panel_error(self, error):
        """Handle panel-related errors with appropriate messages"""
        error_str = str(error).lower()
        
        if "name or service not known" in error_str or "nodename nor servname provided" in error_str:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ENOTFOUND | DNS Error. Ensure your network connection and DNS server are functioning correctly.")
        elif "connection refused" in error_str:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ECONNREFUSED | Connection refused. Ensure the panel is running and reachable.")
        elif "timed out" in error_str:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ETIMEDOUT | Connection timed out. The panel took too long to respond.")
        elif "connection reset by peer" in error_str:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ECONNRESET | Connection reset by peer. The panel closed the connection unexpectedly.")
        elif "no route to host" in error_str:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}EHOSTUNREACH | Host unreachable. The panel is down or not reachable.")
        elif hasattr(error, 'response') and error.response:
            status_code = error.response.status_code
            if status_code == 401:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}401 | Unauthorized. Invalid Application Key or API Key doesn't have permission to perform this action.")
            elif status_code == 403:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}403 | Forbidden. Invalid Application Key or API Key doesn't have permission to perform this action.")
            elif status_code == 404:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}404 | Not Found. Invalid Panel URL or the Panel doesn't exist.")
            elif status_code == 429:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}429 | Too Many Requests. You have sent too many requests in a given amount of time.")
            elif status_code in [500, 502, 503, 504]:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}500 | Internal Server Error. This is an error with your panel, PSS is not the cause.")
            else:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}{status_code} | Unexpected error: {getattr(error.response, 'reason', 'Unknown')}")
        else:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Unexpected error: {error}")