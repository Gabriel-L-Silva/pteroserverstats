#!/usr/bin/env python3
import os
import json
from colorama import Fore, Style, init
from handlers.setup import Setup
from handlers.application import Application
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Initialize colorama for colored console output
init(autoreset=True)

# Package info equivalent
PACKAGE_INFO = {
    "name": "pteroserverstats",
    "version": "1.0.0",
    "author": "HirziDevs",
    "description": "PteroServerStats is a Discord App/Bot designed to check server stats running on Pterodactyl or Pelican panel and post it to your Discord server."
}

def print_banner():
    """Print the application banner with ASCII art"""
    banner = f"""    _{Fore.BLUE + Style.BRIGHT}{'Ptero'.ljust(8, '_')}dact{'yl & P'.ljust(8, '_')}eli{'can'.ljust(8, '_')}_{'Se'.ljust(8, '_')}rver______   ______   
   /\\  ___\\  /\\__  _\\ /\\  __ \\  /\\__  _\\ /\\  ___\\  
   \\ \\___  \\ \\/_ \\ \\/ \\ \\ \\_\\ \\ \\/_/\\ \\/ \\ \\___  \\ 
    \\/\\_____\\   \\ \\_\\  \\ \\_\\ \\_\\   \\ \\_\\  \\/\\_____\\ 
     \\/_____/    \\/_/   \\/_/\\/_/    \\/_/   \\/_____/{Fore.YELLOW + Style.BRIGHT}{PACKAGE_INFO['version']}{Style.RESET_ALL}"""
    
    print(banner)

def print_info():
    """Print copyright and project information"""
    from datetime import datetime
    current_year = datetime.now().year
    
    info = f""" 
Copyright © 2024 - {current_year} HirziDevs & Contributors
 
Discord: https://discord.znproject.my.id
Source: https://github.com/HirziDevs/PteroServerStats
License: https://github.com/Hirzidevs/PteroServerStats/blob/main/LICENSE
 
{PACKAGE_INFO['description']}
 """
    print(info)

"""Main entry point for Discord bot"""
if __name__ == "__main__":
    print_banner()
    print_info()
    # Run setup if .env or .setup-complete is missing
    if not os.path.exists(".env") or not os.path.exists(".setup-complete"):
        setup = Setup()
        setup.run()
    else:
        app = Application()
        app.run()