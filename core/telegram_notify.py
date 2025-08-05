import requests

def send_telegram_message(token: str, chat_id: str, message: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        print(f"[Telegram] Gửi message đến {chat_id}")
        print(f"[Telegram] Token: {token[:10]}...")
        print(f"[Telegram] Message length: {len(message)} chars")
        resp = requests.post(url, data=data, timeout=10)
        print(f"[Telegram] Response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[Telegram] Error response: {resp.text}")
        return resp.status_code == 200
    except Exception as e:
        print(f"[Telegram] Exception: {e}")
        return False 