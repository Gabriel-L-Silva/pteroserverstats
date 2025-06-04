import aiohttp
import os

API_KEY = os.getenv("PTERO_API_KEY")
PANEL_URL = os.getenv("PTERO_PANEL_URL")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

async def get_server_stats(session, server_id):
    url = f"{PANEL_URL}/api/client/servers/{server_id}/resources"
    async with session.get(url, headers=headers) as response:
        return await response.json()
