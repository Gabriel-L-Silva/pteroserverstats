import json
import os
import time
from colorama import Fore
from .get_server_details import get_server_details
from .get_server_stats import get_server_stats
from .promise_timeout import promise_timeout
from .send_message import send_message

async def get_stats(client, config, return_data=False):
    """Get server stats and send to Discord (optionally just return data)"""
    try:
        print(f"{Fore.CYAN}[PSS] {Fore.YELLOW}Fetching server details for server ID: {os.getenv('ServerID')}")
        details = await promise_timeout(get_server_details(), config.get('timeout', 5))
        
        if not details:
            raise Exception("Failed to get server details")
        
        print(f"{Fore.CYAN}[PSS] {Fore.YELLOW}Fetching server resources for server ID: {os.getenv('ServerID')}")
        stats = await promise_timeout(get_server_stats(config), config.get('timeout', 5))
        
        if stats and stats.get('current_state') == "missing":
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Server {details['name']} is currently down.")
        else:
            print(f"{Fore.CYAN}[PSS] {Fore.GREEN}Server {details['name']} state is normal.")
        
        data = {
            'details': details,
            'stats': stats,
            'timestamp': int(time.time() * 1000)
        }
        
        if return_data:
            return data
        
        await send_message(client, data, config)
        return data
        
    except Exception as error:
        if config.get('log_error'):
            print(f"Error: {error}")
        
        print(f"{Fore.CYAN}[PSS] {Fore.RED}Server is currently down.")
        
        # Try to load cached data
        if os.path.exists("cache.json"):
            try:
                with open("cache.json", 'r') as f:
                    data = json.load(f)
                
                # Update stats to show server as down
                data['stats'] = {
                    'current_state': 'missing',
                    'is_suspended': False,
                    'resources': {
                        'memory_bytes': 0,
                        'cpu_absolute': 0,
                        'disk_bytes': 0,
                        'network_rx_bytes': 0,
                        'network_tx_bytes': 0,
                        'uptime': 0
                    }
                }
                
                if return_data:
                    return data
                
                await send_message(client, data, config)
                return data
                
            except Exception:
                print(f"{Fore.CYAN}[PSS] {Fore.RED}Something went wrong with cache data...")
                return None
        else:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Last cache was not found!")
            return None