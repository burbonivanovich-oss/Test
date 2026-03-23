#!/usr/bin/env python3
"""
Telethon session setup with QR-code (Telegram Desktop style).

This method is MUCH FASTER and doesn't require SMS codes!

Usage:
    python setup_session_qr.py <api_id> <api_hash>

    Then scan the QR code with your phone's Telegram app.
"""

import asyncio
import sys
from telethon import TelegramClient
from telethon.errors import QRMigrationException


async def main():
    if len(sys.argv) < 3:
        print("Usage: python setup_session_qr.py <api_id> <api_hash>")
        print()
        print("Example:")
        print("  python setup_session_qr.py 37195258 da6a76c5c4884bceac2fa904ab029b02")
        sys.exit(1)

    try:
        api_id = int(sys.argv[1])
    except ValueError:
        print("ERROR: api_id must be a number")
        sys.exit(1)

    api_hash = sys.argv[2]
    session_file = "telegram_session_qr"

    print("=" * 70)
    print("Telegram QR Code Authentication")
    print("=" * 70)
    print()
    print("This method is MUCH faster than SMS!")
    print()
    print("Instructions:")
    print("1. A QR code will appear below")
    print("2. Open Telegram on your phone")
    print("3. Go to Settings → Devices → Link Desktop Device")
    print("4. Scan the QR code with your phone")
    print()
    print("=" * 70)
    print()

    client = TelegramClient(session_file, api_id, api_hash)

    try:
        await client.connect()

        if await client.is_user_authorized():
            print("✅ Already authenticated!")
            me = await client.get_me()
            print(f"Logged in as: {me.first_name} (@{me.username or 'no username'})")
            return

        # Try QR code auth
        print("⏳ Generating QR code...")
        print()

        qr_login = await client.qr_login()

        # The QR code should be displayed by Telethon
        # For terminal, we'll try to show it

        try:
            print("📲 Scan this QR code with Telegram:")
            print()

            # Try to render QR in terminal
            import pyqrcode
            qr_login.qr.print_ascii()
            print()

        except ImportError:
            print("⚠️  pyqrcode not installed, showing URL instead:")
            print(f"https://api.telegram.org/qr")
            print()
            print("Or use --method=ascii to see ASCII QR code")
            print()

        # Wait for authentication
        print("⏳ Waiting for you to scan the QR code on your phone...")
        print("(This may take a few seconds)")
        print()

        try:
            await qr_login.wait()
            print("✅ QR code scanned! Authenticating...")

        except QRMigrationException as e:
            print(f"⚠️  QR code expired, retrying...")
            await client.disconnect()
            await main()
            return

        # Verify authentication
        if await client.is_user_authorized():
            me = await client.get_me()
            print()
            print("=" * 70)
            print("✅ SUCCESS! Session created.")
            print("=" * 70)
            print()
            print(f"Authenticated as: {me.first_name} (@{me.username or 'no username'})")
            print()

            # Get session string
            session_str = client.session.save()

            print("Save these environment variables:")
            print()
            print(f"  export TELETHON_API_ID={api_id}")
            print(f"  export TELETHON_API_HASH={api_hash}")
            print(f'  export TELETHON_SESSION_STRING="{session_str}"')
            print()
            print("Or save to .env file:")
            print()
            print(f"  TELETHON_API_ID={api_id}")
            print(f"  TELETHON_API_HASH={api_hash}")
            print(f"  TELETHON_SESSION_STRING={session_str}")
            print()
        else:
            print("❌ Authentication failed")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
