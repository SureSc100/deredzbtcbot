import os, time, requests

def _tg_creds():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id

def tg_send(text):
    token, chat_id = _tg_creds()
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def format_signal(symbol, side, price, sl, tp, confidence, timeframe, reason):
    return (
        f"\u26A1 <b>Signal</b> | <b>{symbol}</b>\n"
        f"Side: <b>{side}</b> @ <code>{price:.4f}</code> ({timeframe})\n"
        f"SL: <code>{sl:.4f}</code> | TP: <code>{tp:.4f}</code>\n"
        f"Confidence: <b>{confidence:.1f}%</b>\n"
        f"Why: {reason}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

def format_info(msg):
    return f"\u2139\uFE0F {msg}"
