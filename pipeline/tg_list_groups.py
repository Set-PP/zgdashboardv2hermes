#!/usr/bin/env python3
"""P2.1 — Verify Telegram connection and list site-engineer groups."""
import asyncio, os
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = r"C:\Users\user\Downloads\zawg_telethon_session.session"

async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("NOT AUTHORIZED — session expired, needs re-login")
        return
    me = await client.get_me()
    print(f"CONNECTED as: {me.first_name} {me.last_name or ''} (@{me.username}) id={me.id}\n")

    print("GROUPS / CHANNELS:")
    async for d in client.iter_dialogs():
        e = d.entity
        if isinstance(e, (Channel, Chat)) and getattr(e, "title", None):
            kind = "megagroup" if getattr(e, "megagroup", False) else (
                   "channel" if isinstance(e, Channel) and getattr(e, "broadcast", False) else "group")
            print(f"  [{kind:9s}] {e.title[:55]:55s} id={e.id}")
    await client.disconnect()

asyncio.run(main())
