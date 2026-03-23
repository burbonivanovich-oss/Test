#!/usr/bin/env python3
"""
Telethon session setup с автоматическим вводом кода через stdin.

Решение проблемы "The confirmation code has expired":
- Меньше времени между Stage 1 и Stage 2
- Автоматический ввод кода (нет ручного копирования)

Usage:
    # Stage 1: Запросить код
    python setup_session_auto.py <api_id> <api_hash> <phone>

    # Когда код придет:
    # Скопируйте код в одну строку и введите
    # Например: 62190

    # Сессия сохранится в telegram_session.session
"""

import asyncio
import sys
import os
from telethon import TelegramClient


async def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    try:
        api_id = int(sys.argv[1])
    except ValueError:
        print("ERROR: api_id must be a number")
        sys.exit(1)

    api_hash = sys.argv[2]
    phone = sys.argv[3]
    session_file = "telegram_session"

    print("=" * 70)
    print("Telegram Session Setup (Auto)")
    print("=" * 70)
    print()
    print(f"API ID: {api_id}")
    print(f"Phone: {phone}")
    print()

    client = TelegramClient(session_file, api_id, api_hash)

    try:
        await client.connect()

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
            print("⏳ Waiting for code input...")
            print("Enter the code when you receive it (and press Enter):")
            print()

            # Read code from stdin (allows piping: echo "12345" | python script.py)
            code = sys.stdin.readline().strip()

            if not code:
                print("❌ No code provided")
                sys.exit(1)

            print(f"Using code: {code}")
            print()

            try:
                await client.sign_in(phone, code)
                print("✅ Code accepted!")
                print()

            except Exception as e:
                error_str = str(e).lower()

                # Check for 2FA
                if "password" in error_str:
                    print("⚠️  Two-factor authentication enabled")
                    password = sys.stdin.readline().strip()
                    if not password:
                        print("❌ No password provided")
                        sys.exit(1)
                    try:
                        await client.sign_in(password=password)
                        print("✅ Password accepted!")
                        print()
                    except Exception as e2:
                        print(f"❌ Password failed: {e2}")
                        sys.exit(1)
                else:
                    print(f"❌ Code verification failed: {e}")
                    sys.exit(1)

            # Get user info
            me = await client.get_me()
            print("=" * 70)
            print("✅ Success! Session created and saved.")
            print("=" * 70)
            print()
            print(f"Authenticated as: {me.first_name} (@{me.username or 'no username'})")
            print()
            print(f"Session file: {session_file}.session")
            print()
            print("Save session string (for bothost.ru or .env):")
            print()

            # Get session string
            session_str = client.session.save()
            print(session_str)
            print()
            print("To use in your bot, set environment variables:")
            print(f"  export TELETHON_API_ID={api_id}")
            print(f"  export TELETHON_API_HASH={api_hash}")
            print(f'  export TELETHON_SESSION_STRING="{session_str}"')
            print()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
