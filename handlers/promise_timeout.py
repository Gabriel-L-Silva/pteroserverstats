import asyncio
from asyncio import timeout

async def promise_timeout(coroutine, timeout_seconds):
    """Execute a coroutine with a timeout"""
    try:
        async with timeout(timeout_seconds):
            return await coroutine
    except asyncio.TimeoutError:
        return False 