#!/usr/bin/env python3
"""
One-time setup script for Telegram channel monitor authentication.

This script generates a Telethon session string that allows the bot to access
Telegram channels. Run this once to authenticate, then save the session string
to the TELETHON_SESSION_STRING environment variable.

Usage:
    python channel_monitor_setup.py <api_id> <api_hash>

Where:
    api_id: Your Telegram API ID from https://my.telegram.org/apps
    api_hash: Your Telegram API hash from https://my.telegram.org/apps

The script will:
1. Ask for your phone number
2. Send a code to your Telegram account
3. Generate a session string
4. Display instructions for saving it
"""

import asyncio
import os
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    if len(sys.argv) != 3:
        print("Usage: python channel_monitor_setup.py <api_id> <api_hash>")
        sys.exit(1)

    try:
        api_id = int(sys.argv[1])
    except ValueError:
        print("ERROR: api_id must be a number")
        sys.exit(1)

    api_hash = sys.argv[2]

    print("=" * 70)
    print("Telegram Channel Monitor - Authentication Setup")
    print("=" * 70)
    print()
    print("This will create a session string for channel monitoring.")
    print("You will need to authenticate with your Telegram account.")
    print()

    # Use in-memory session for setup
    client = TelegramClient(StringSession(), api_id, api_hash)

    try:
        await client.connect()

        # Check if already authorized
        if not await client.is_user_authorized():
            print("Starting authentication...")
            print()

            # Request code
            phone = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
            result = await client.send_code_request(phone)

            # Enter code
            code = input("Enter the code Telegram sent to you: ").strip()

            try:
                await client.sign_in(phone, code)
            except Exception as sign_in_err:
                print(f"Sign-in failed: {sign_in_err}")
                await client.disconnect()
                sys.exit(1)

        # Get the session string
        session_string = client.session.save()

        print()
        print("=" * 70)
        print("✅ Authentication successful!")
        print("=" * 70)
        print()
        print("Your session string is:")
        print()
        print(session_string)
        print()
        print("How to save it:")
        print()
        print("  Option 1: Set environment variable")
        print('    export TELETHON_SESSION_STRING="' + session_string + '"')
        print()
        print("  Option 2: Add to .env file")
        print(f'    TELETHON_SESSION_STRING="{session_string}"')
        print()
        print("Also set these environment variables:")
        print(f"  TELETHON_API_ID={api_id}")
        print(f"  TELETHON_API_HASH={api_hash}")
        print()

        # Verify by getting user info
        me = await client.get_me()
        print(f"Authenticated as: {me.first_name} (@{me.username or 'no username'})")
        print()

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
