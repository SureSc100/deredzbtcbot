import os, json
from flask import Flask, send_from_directory, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from worker import run_scan, read_state, write_state
load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

sched = BackgroundScheduler(daemon=True)
sched.add_job(run_scan, "interval", seconds=30, id="scan")
sched.start()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/status")
def status():
    s = read_state()
    return jsonify({
        "date": s["date"],
        "signals_today": s["signals_today"],
        "cooldown_until": s["cooldown_until"],
        "signals_last_hour": s["signals_last_hour"]
    })

@app.route("/api/latest")
def latest():
    fp = os.path.join("logs", "signals.csv")
    if not os.path.isfile(fp):
        return jsonify({"ok": True, "data": None})
    import csv
    with open(fp, "r") as f:
        rows = list(csv.DictReader(f))
    return jsonify({"ok": True, "data": rows[-1] if rows else None})

@app.route("/api/logs")
def logs():
    fp = os.path.join("logs", "signals.csv")
    if not os.path.isfile(fp):
        return jsonify({"ok": True, "data": []})
    import csv
    with open(fp, "r") as f:
        rows = list(csv.DictReader(f))
    return jsonify({"ok": True, "data": rows[-100:]})

@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory("static", "manifest.webmanifest")

@app.route("/service-worker.js")
def sw():
    return send_from_directory("static", "service-worker.js")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
