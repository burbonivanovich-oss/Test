#!/usr/bin/env python3
"""
Simple Telegram session setup using file-based sessions.

This creates a .session file that can be used to authenticate the bot.

Usage:
    python3 setup_session.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79991234567
"""

import asyncio
import sys
import os
from telethon import TelegramClient


async def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]
    phone = sys.argv[3]

    session_file = "telegram_session"

    print("=" * 70)
    print("Telegram Session Setup")
    print("=" * 70)
    print()
    print(f"API ID: {api_id}")
    print(f"Phone: {phone}")
    print(f"Session file: {session_file}.session")
    print()

    # Create client with file-based session
    client = TelegramClient(session_file, api_id, api_hash)

    try:
        await client.connect()

        # Check if already authenticated
        if await client.is_user_authorized():
            print("✅ Already authenticated!")
            me = await client.get_me()
            print(f"Logged in as: {me.first_name} (@{me.username or 'no username'})")
            print()
        else:
            # Send code request
            print(f"📱 Sending code to {phone}...")
            result = await client.send_code_request(phone)
            print("✅ Code sent to Telegram!")
            print()

            # Wait for user to input code
            code = input("Enter the code you received: ").strip()

            if not code:
                print("❌ No code provided")
                sys.exit(1)

            # Sign in
            print()
            print("🔐 Verifying code...")
            try:
                await client.sign_in(phone, code)
                me = await client.get_me()
                print()
                print("✅ Success! Session created and saved.")
                print()
                print(f"Authenticated as: {me.first_name} (@{me.username or 'no username'})")
                print()
                print("=" * 70)
                print("📝 Session file created: telegram_session.session")
                print("=" * 70)
                print()
                print("Copy this file to your server (e.g., bothost.ru)")
                print()

            except Exception as e:
                print(f"❌ Code verification failed: {e}")
                sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
