import os, csv, json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from exchange import fetch_klines
from strategy import generate_signal
from notifier import tg_send, format_signal

load_dotenv()

INTERVAL = os.getenv("INTERVAL", "15m")
SYMBOLS = ["BTCUSDT"]
PRIMARY_SYMBOL = "BTCUSDT"
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "4"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "85"))
REQUIRE_HTF_TREND = os.getenv("REQUIRE_HTF_TREND", "true").lower() == "true"

SIGNAL_COOLDOWN_MIN = int(os.getenv("SIGNAL_COOLDOWN_MIN", "120"))
MAX_SIGNALS_PER_HOUR = int(os.getenv("MAX_SIGNALS_PER_HOUR", "1"))
MAX_SIGNALS_PER_DAY = int(os.getenv("MAX_SIGNALS_PER_DAY", "1"))
DAILY_RESET_HOUR_UTC = int(os.getenv("DAILY_RESET_HOUR_UTC", "0"))

LOG_PATH = os.getenv("LOG_PATH", "logs")
os.makedirs(LOG_PATH, exist_ok=True)

state_file = os.path.join(LOG_PATH, "state.json")
if not os.path.isfile(state_file):
    with open(state_file, "w") as f:
        json.dump({"date": datetime.utcnow().date().isoformat(),
                   "signals_today": 0,
                   "cooldown_until": {},
                   "signals_last_hour": []}, f)

def read_state():
    with open(state_file, "r") as f:
        return json.load(f)

def write_state(s):
    with open(state_file, "w") as f:
        json.dump(s, f)

def maybe_reset_daily(state):
    now = datetime.utcnow()
    last_date = datetime.fromisoformat(state["date"]).date()
    if (now.hour >= DAILY_RESET_HOUR_UTC) and (last_date < now.date()):
        state["date"] = now.date().isoformat()
        state["signals_today"] = 0
        state["signals_last_hour"] = []

def calc_tp_sl(entry: float):
    tp = entry * (1 + TAKE_PROFIT_PCT/100)
    sl = entry * (1 - STOP_LOSS_PCT/100)
    return round(tp, 6), round(sl, 6)

def log_signal(row):
    fp = os.path.join(LOG_PATH, "signals.csv")
    file_exists = os.path.isfile(fp)
    with open(fp, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            w.writeheader()
        w.writerow(row)

def should_throttle(state):
    now = datetime.utcnow()
    # cooldown for BTC only
    cd = state["cooldown_until"].get("BTCUSDT")
    if cd and now < datetime.fromisoformat(cd):
        return True, "In cooldown"
    # per-hour
    state["signals_last_hour"] = [t for t in state["signals_last_hour"] if datetime.fromisoformat(t) > now - timedelta(hours=1)]
    if len(state["signals_last_hour"]) >= MAX_SIGNALS_PER_HOUR:
        return True, "Hit MAX_SIGNALS_PER_HOUR"
    # per-day
    if state["signals_today"] >= MAX_SIGNALS_PER_DAY:
        return True, "Hit MAX_SIGNALS_PER_DAY"
    return False, ""

def set_cooldown(state):
    until = datetime.utcnow() + timedelta(minutes=SIGNAL_COOLDOWN_MIN)
    state["cooldown_until"]["BTCUSDT"] = until.isoformat()

def run_scan():
    state = read_state()
    maybe_reset_daily(state)

    throt, why = should_throttle(state)
    if throt:
        write_state(state); return

    df_15 = fetch_klines("BTCUSDT", interval=INTERVAL, limit=500)
    df_1h = fetch_klines("BTCUSDT", interval="1h", limit=500) if REQUIRE_HTF_TREND else None

    sig = generate_signal(df_15, df_1h, min_conf=MIN_CONFIDENCE, require_htf=REQUIRE_HTF_TREND)
    if sig.side is None:
        write_state(state); return

    entry = float(df_15['close'].iloc[-1])
    tp, sl = calc_tp_sl(entry)
    row = {
        "time": datetime.utcnow().isoformat(),
        "symbol": "BTCUSDT",
        "side": sig.side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "confidence": round(sig.confidence, 2),
        "interval": INTERVAL,
        "reason": sig.reason
    }
    log_signal(row)

    state["signals_last_hour"].append(datetime.utcnow().isoformat())
    state["signals_today"] += 1
    set_cooldown(state)
    write_state(state)

    tg_send(format_signal("BTCUSDT", sig.side, entry, sl, tp, sig.confidence, INTERVAL, sig.reason))
    print("Signal sent:", row)
