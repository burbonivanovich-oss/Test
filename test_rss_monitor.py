#!/usr/bin/env python3
"""
Quick test of RSS-based channel monitoring.

Usage:
    python test_rss_monitor.py
    python test_rss_monitor.py --channel @rian_ru --keyword "тс пиот"
"""

import asyncio
import sys
from telegram_channel_monitor.rss_channel_monitor import RSSChannelMonitor


async def main():
    # Default test channels and keywords
    channels = [
        {"name": "РИА Новости", "username": "@rian_ru"},
        {"name": "ТАСС", "username": "@tass_agency"},
    ]
    keywords = ["тс пиот", "ТС ПИОТ"]
    hours_lookback = 24

    # Parse CLI args
    if len(sys.argv) > 1:
        if "--channel" in sys.argv:
            idx = sys.argv.index("--channel")
            if idx + 1 < len(sys.argv):
                channel = sys.argv[idx + 1]
                channels = [{"name": channel, "username": channel}]

        if "--keyword" in sys.argv:
            idx = sys.argv.index("--keyword")
            if idx + 1 < len(sys.argv):
                keyword = sys.argv[idx + 1]
                keywords = [keyword]

    print("=" * 70)
    print("🧪 Testing RSS-based Channel Monitor")
    print("=" * 70)
    print()
    print(f"Channels: {[c['username'] for c in channels]}")
    print(f"Keywords: {keywords}")
    print(f"Time window: last {hours_lookback} hours")
    print()

    # Initialize monitor
    monitor = RSSChannelMonitor()

    try:
        await monitor.connect()
        print("✅ Connected to RSS monitor")
        print()

        # Test each channel
        total_messages = 0
        for channel_info in channels:
            channel_name = channel_info.get("name", "Unknown")
            channel_username = channel_info.get("username", "")

            print(f"📡 Fetching from {channel_name} ({channel_username})…")

            try:
                messages = await monitor.get_messages_from_channel(
                    channel_username,
                    limit=20,
                    hours_lookback=hours_lookback,
                )

                if not messages:
                    print(f"  ℹ️  No messages in the last {hours_lookback} hours")
                    continue

                print(f"  📊 Got {len(messages)} messages")

                # Search for keywords
                matches = []
                for msg in messages:
                    msg_text = msg.get("text", "").lower()
                    for kw in keywords:
                        if kw.lower() in msg_text:
                            matches.append((msg, kw))
                            break

                if matches:
                    print(f"  🎯 Found {len(matches)} message(s) with keywords")
                    print()

                    for msg, keyword in matches[:3]:  # Show first 3
                        text_preview = msg.get("text", "")[:100]
                        date = msg.get("date", "?")
                        link = msg.get("link", "?")

                        print(f"    • Keyword: '{keyword}'")
                        print(f"      Text: {text_preview}…")
                        print(f"      Date: {date}")
                        print(f"      Link: {link}")
                        print()

                    if len(matches) > 3:
                        print(f"    … and {len(matches) - 3} more matches")
                        print()

                    total_messages += len(matches)
                else:
                    print(f"  ❌ No matches found for keywords")
                    print()

            except Exception as e:
                print(f"  ❌ Error: {e}")
                print()

        print("=" * 70)
        print(f"✅ Test complete! Total matches: {total_messages}")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
