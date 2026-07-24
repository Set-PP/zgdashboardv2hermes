#!/usr/bin/env python3
"""Create a fresh Telethon session — run this ONCE on your computer, then copy the .session file."""
import asyncio
from telethon import TelegramClient

API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = "zawg_telethon_v2"

async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()
    print(f"✅ Session saved as: {SESSION}.session")
    print(f"   Copy to: C:\\Users\\user\\Downloads\\{SESSION}.session")
    await client.disconnect()

asyncio.run(main())
