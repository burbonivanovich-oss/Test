#!/usr/bin/env python3
"""
Simple Telegram session setup.

Stage 1: Send code
    python3 setup_session.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79991234567

Stage 2: Verify code (with phone_code_hash from Stage 1)
    python3 setup_session.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79991234567 123456 <HASH>
"""

import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]
    phone = sys.argv[3]
    code = sys.argv[4] if len(sys.argv) > 4 else None
    phone_code_hash = sys.argv[5] if len(sys.argv) > 5 else None

    print("=" * 70)
    print("Telegram Channel Monitor - Session Setup")
    print("=" * 70)
    print()

    client = TelegramClient(StringSession(), api_id, api_hash)

    try:
        await client.connect()

        if not code:
            # Stage 1: Send code
            print(f"📱 Sending code to {phone}...")
            result = await client.send_code_request(phone)

            # Get phone_code_hash from result
            print(f"\nDEBUG: result type = {type(result)}")
            print(f"DEBUG: result attrs = {dir(result)}\n")

            hash_val = getattr(result, 'phone_code_hash', None)
            if not hash_val:
                print("❌ Could not get phone_code_hash from result")
                sys.exit(1)
            print()
            print("✅ Code sent to your Telegram!")
            print()
            print("=" * 70)
            print("Now copy this command and run it with the CODE you receive:")
            print("=" * 70)
            print()
            print(f"python3 setup_session.py {api_id} {api_hash} {phone} <CODE> {hash_val}")
            print()
            print("Replace <CODE> with the 5-6 digit code from Telegram")
            print()

        else:
            # Stage 2: Verify code
            print(f"🔐 Verifying code for {phone}...")
            print()

            if not phone_code_hash:
                print("❌ Error: Missing phone_code_hash")
                print("Please copy the full command from Stage 1 output")
                sys.exit(1)

            try:
                await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
                session_string = client.session.save()

                print("✅ Success! Your session string:")
                print()
                print(session_string)
                print()
                print("=" * 70)
                print("📝 Environment Variables for bothost.ru:")
                print("=" * 70)
                print()
                print(f"TELETHON_API_ID={api_id}")
                print(f"TELETHON_API_HASH={api_hash}")
                print(f"TELETHON_SESSION_STRING={session_string}")
                print()

                me = await client.get_me()
                print(f"✅ Authenticated as: {me.first_name} (@{me.username or 'no username'})")
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
