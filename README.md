# Deredz BTC Bot — Web + Telegram (BTCUSDT, 15m, 1 signal/day, TP 4%, SL 2%)

Server + mobile web UI. Sends Telegram alerts with high-confidence BTC-only signals.

## What it does
- BTCUSDT only
- 15m scan, 1h trend confirmation
- Max 1 signal/day
- Min confidence 85
- TP +4%, SL −2%
- Telegram alerts

## Quick deploy (Render)
1. Create a new **Web Service** from this repo.
2. Runtime: **Python 3.11+**
3. Start command (auto from `Procfile`): `gunicorn server:app --preload --workers=1 --threads=4 --timeout=120`
4. Environment Variables:
   - `TELEGRAM_BOT_TOKEN` = (paste your token or leave in `.env` for local only)
   - `TELEGRAM_CHAT_ID` = your numeric chat id
   - `BINANCE_USE_TESTNET` = `true` (recommended first)
5. Deploy → open the URL. UI at `/`, APIs: `/api/status`, `/api/latest`, `/api/logs`.

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

**Security:** Prefer Render env vars over committing `.env` with secrets.
