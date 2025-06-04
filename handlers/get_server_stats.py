import os
import requests
from requests.exceptions import RequestException

async def get_server_stats(config):
    """Get server stats from Pterodactyl/Pelican panel"""
    panel_url = os.getenv('PanelURL')
    server_id = os.getenv('ServerID')
    panel_key = os.getenv('PanelKEY')
    
    url = f"{panel_url}/api/client/servers/{server_id}/resources"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {panel_key}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        attributes = data['attributes']
        
        return {
            'current_state': attributes['current_state'],
            'resources': attributes['resources']
        }
        
    except Exception as error:
        if config.get('log_error'):
            print(f"Error getting server stats: {error}")
        return False 