import os
import requests
from colorama import Fore
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException

async def get_server_details():
    """Get server details from Pterodactyl/Pelican panel"""
    panel_url = os.getenv('PanelURL')
    server_id = os.getenv('ServerID')
    panel_key = os.getenv('PanelKEY')
    
    url = f"{panel_url}/api/client/servers/{server_id}"
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
            'uuid': attributes['uuid'],
            'name': attributes['name'],
            'limits': {
                'memory': attributes['limits']['memory'],
                'swap': attributes['limits']['swap'],
                'disk': attributes['limits']['disk'],
                'io': attributes['limits']['io'],
                'cpu': attributes['limits']['cpu'],
                'threads': attributes['limits']['threads']
            }
        }
        
    except ConnectionError as e:
        if "Name or service not known" in str(e) or "nodename nor servname provided" in str(e):
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ENOTFOUND | DNS Error. Ensure your network connection and DNS server are functioning correctly.")
        elif "Connection refused" in str(e):
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ECONNREFUSED | Connection refused. Ensure the panel is running and reachable.")
        elif "Connection reset by peer" in str(e):
            print(f"{Fore.CYAN}[PSS] {Fore.RED}ECONNRESET | Connection reset by peer. The panel closed the connection unexpectedly.")
        elif "No route to host" in str(e):
            print(f"{Fore.CYAN}[PSS] {Fore.RED}EHOSTUNREACH | Host unreachable. The panel is down or not reachable.")
        else:
            print(f"{Fore.CYAN}[PSS] {Fore.RED}Connection Error: {str(e)}")
        return False
        
    except Timeout:
        print(f"{Fore.CYAN}[PSS] {Fore.RED}ETIMEDOUT | Connection timed out. The panel took too long to respond.")
        return False
        
    except HTTPError as e:
        status_code = e.response.status_code
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
            print(f"{Fore.CYAN}[PSS] {Fore.RED}{status_code} | Unexpected error: {e.response.reason}")
        return False
        
    except RequestException as e:
        print(f"{Fore.CYAN}[PSS] {Fore.RED}Unexpected error: {str(e)}")
        return False 