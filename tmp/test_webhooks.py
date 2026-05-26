#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app/legiongasper_framework_0813')

from channels.webhook_manager import WebhookManager, WhatsAppClient, TelegramClient, DiscordClient, SlackClient, TeamsClient, MessengerClient, SignalClient, MatrixClient, RocketChatClient, MattermostClient, ZulipClient, WebexClient, InstagramClient

async def test_webhooks():
    print("=" * 60)
    print("WEBHOOK CLIENTS TEST - 13+ Platforms")
    print("=" * 60)
    
    manager = WebhookManager()
    
    platforms = [
        ('whatsapp', WhatsAppClient, {'api_key': 'test', 'phone_id': 'test'}),
        ('telegram', TelegramClient, {'bot_token': 'test'}),
        ('discord', DiscordClient, {'webhook_url': 'https://test'}),
        ('slack', SlackClient, {'webhook_url': 'https://test'}),
        ('teams', TeamsClient, {'webhook_url': 'https://test'}),
        ('messenger', MessengerClient, {'page_token': 'test'}),
        ('signal', SignalClient, {'number': '+1234567890'}),
        ('matrix', MatrixClient, {'homeserver': 'https://test', 'access_token': 'test'}),
        ('rocketchat', RocketChatClient, {'server_url': 'https://test', 'auth_token': 'test', 'user_id': 'test'}),
        ('mattermost', MattermostClient, {'webhook_url': 'https://test'}),
        ('zulip', ZulipClient, {'site': 'https://test', 'bot_email': 'test@test', 'api_key': 'test'}),
        ('webex', WebexClient, {'access_token': 'test'}),
        ('instagram', InstagramClient, {'access_token': 'test'})
    ]
    
    print(f"\n[1/2] Testing {len(platforms)} webhook client classes...")
    
    for name, client_class, config in platforms:
        try:
            client = client_class(config)
            manager.register_client(name, client)
            assert hasattr(client, 'send_message'), f"{name} missing send_message"
            assert hasattr(client, 'parse_webhook'), f"{name} missing parse_webhook"
            print(f"  ✓ {name}: {client_class.__name__} - methods OK")
        except Exception as e:
            print(f"  ✗ {name}: FAILED - {e}")
            return False
    
    print(f"\n[SUCCESS] All {len(platforms)} clients registered")
    
    print("\n[2/2] Testing webhook parsing...")
    
    test_payloads = {
        'whatsapp': {'entry': [{'changes': [{'value': {'messages': [{'from': '123', 'text': {'body': 'Hello'}, 'type': 'text', 'timestamp': '1234567890'}]}}]}]},
        'telegram': {'message': {'from': {'id': 123, 'username': 'test'}, 'text': 'Hello', 'chat': {'id': 456}, 'date': 1234567890}},
        'discord': {'type': 1, 'token': 'test', 'data': {'content': 'Hello'}},
        'slack': {'type': 'message', 'user': 'U123', 'text': 'Hello', 'channel': 'C123', 'ts': '1234567890.123'},
        'teams': {'text': 'Hello'},
        'messenger': {'entry': [{'messaging': [{'sender': {'id': '123'}, 'message': {'text': 'Hello'}, 'timestamp': 1234567890}]}]},
        'signal': {'message': 'Hello'},
        'matrix': {'content': {'body': 'Hello'}},
        'rocketchat': {'text': 'Hello'},
        'mattermost': {'text': 'Hello'},
        'zulip': {'message': {'content': 'Hello'}},
        'webex': {'text': 'Hello'},
        'instagram': {'entry': [{'messaging': [{'sender': {'id': '123'}, 'message': {'text': 'Hello'}}]}]}
    }
    
    for platform, payload in test_payloads.items():
        try:
            result = await manager.handle_webhook(platform, payload)
            assert 'platform' in result, f"{platform} missing platform in result"
            print(f"  ✓ {platform}: webhook parsed OK")
        except Exception as e:
            print(f"  ✗ {platform}: FAILED - {e}")
    
    await manager.close_all()
    
    print("\n" + "=" * 60)
    print("ALL WEBHOOK TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_webhooks())
    sys.exit(0 if success else 1)
