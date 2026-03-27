#!/usr/bin/env python3
"""Авторизация userbot для AXIS Scout"""
from pyrogram import Client
import asyncio

API_ID = 30753988
API_HASH = "834c894a81de6018616ef951f7cc404e"
PHONE = "+77713926440"

async def main():
    app = Client(
        "axis_scout",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE,
        workdir="/home/axis/openclaw/axis-system/scout-userbot"
    )
    
    async with app:
        me = await app.get_me()
        print(f"✅ Authorized as: {me.first_name} (id: {me.id})")
        print(f"Phone: {me.phone_number}")
        print("Session saved!")

asyncio.run(main())
