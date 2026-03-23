#!/usr/bin/env python3
"""
Improved Telegram session setup with two-stage authentication.

Stage 1: Send code
    python3 setup_session.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79991234567

Stage 2: Verify code
    python3 setup_session.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79991234567 123456
"""

import asyncio
import sys
import json
import os
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]
    phone = sys.argv[3]

    # Check if code is provided (stage 2)
    code = sys.argv[4] if len(sys.argv) > 4 else None

    # File to store phone_code_hash
    hash_file = ".telegram_hash"

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
            print()
            result = await client.send_code_request(phone)

            # Save phone_code_hash for later use
            try:
                hash_value = result.phone_code_hash
                with open(hash_file, 'w') as f:
                    json.dump({'phone_code_hash': hash_value}, f)
                print(f"✅ Code sent! Hash saved to {hash_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not save hash - {e}")

            print()
            print("✅ Now run:")
            print()
            print(f"python3 setup_session.py {api_id} {api_hash} {phone} <CODE>")
            print()
            print("Replace <CODE> with the code you received in Telegram")

        else:
            # Stage 2: Verify code
            print(f"🔐 Verifying code for {phone}...")
            print()

            # Read phone_code_hash from file
            if not os.path.exists(hash_file):
                print(f"❌ Error: {hash_file} not found. Run Stage 1 first.")
                sys.exit(1)

            with open(hash_file, 'r') as f:
                hash_data = json.load(f)
            phone_code_hash = hash_data['phone_code_hash']

            try:
                await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
                session_string = client.session.save()

                print("✅ Success! Your session string:")
                print()
                print(session_string)
                print()
                print("=" * 70)
                print("📝 Save this for bothost.ru:")
                print("=" * 70)
                print()
                print("Environment Variables:")
                print(f"  TELETHON_API_ID={api_id}")
                print(f"  TELETHON_API_HASH={api_hash}")
                print(f"  TELETHON_SESSION_STRING={session_string}")
                print()

                me = await client.get_me()
                print(f"Authenticated as: {me.first_name} (@{me.username or 'no username'})")
                print()

                # Clean up hash file
                if os.path.exists(hash_file):
                    os.remove(hash_file)

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
