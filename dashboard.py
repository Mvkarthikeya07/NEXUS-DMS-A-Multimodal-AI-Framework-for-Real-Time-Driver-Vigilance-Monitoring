"""NEXUS-DMS — Flask Analytics Dashboard.

A real-time analytics dashboard that reads event logs from CSV
and displays driver safety metrics, charts, and alert history.

Usage:
    python dashboard.py
    
Then open http://127.0.0.1:5000 in your browser.
"""

import csv
import logging
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

from config import Config
from logger import setup_logging

setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def read_events() -> list[dict]:
    """Read all events from the CSV log file.
    
    Returns:
        List of dicts with keys: Date, Time, Event.
    """
    log_file = Config.LOG_FILE
    if not log_file.exists():
        return []

    events = []
    try:
        with open(log_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append({
                    "Date": row.get("Date", ""),
                    "Time": row.get("Time", ""),
                    "Event": row.get("Event", "").strip(),
                })
    except Exception as e:
        logger.error("Error reading log file: %s", e)

    return events


def compute_metrics(events: list[dict]) -> dict:
    """Compute dashboard metrics from events.
    
    Returns:
        Dict with total_alerts, event_counts, safety_score,
        recent_events, event_distribution, timeline data.
    """
    total = len(events)
    event_types = [e["Event"] for e in events]
    counts = Counter(event_types)

    # Safety score: starts at 100, loses points per alert (min 0)
    penalty_weights = {
        "DROWSY_EMERGENCY": 10,
        "DROWSY_BUZZER_ALERT": 5,
        "DROWSY_VOICE_WARNING": 2,
        "PHONE_SMS_ALERT": 8,
        "PHONE_VOICE_WARNING": 3,
        "YAWN_DETECTED": 1,
    }
    penalty = sum(
        counts.get(evt, 0) * weight
        for evt, weight in penalty_weights.items()
    )
    # Also penalize unknown events
    for evt, count in counts.items():
        if evt not in penalty_weights:
            penalty += count * 2
    safety_score = max(0, 100 - penalty)

    # Recent events (last 20)
    recent = events[-20:][::-1]

    # Event distribution for chart
    distribution = [
        {"event": evt, "count": cnt}
        for evt, cnt in counts.most_common()
    ]

    # Timeline: group by date
    timeline = {}
    for e in events:
        date = e["Date"]
        if date not in timeline:
            timeline[date] = 0
        timeline[date] += 1
    timeline_data = [
        {"date": d, "count": c}
        for d, c in sorted(timeline.items())
    ]

    return {
        "total_alerts": total,
        "safety_score": safety_score,
        "event_counts": dict(counts),
        "recent_events": recent,
        "distribution": distribution,
        "timeline": timeline_data,
        "drowsy_count": sum(v for k, v in counts.items() if "DROWSY" in k),
        "phone_count": sum(v for k, v in counts.items() if "PHONE" in k),
        "yawn_count": counts.get("YAWN_DETECTED", 0),
        "distraction_count": sum(v for k, v in counts.items() if "DISTRACTION" in k),
    }


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("dashboard.html")


@app.route("/api/metrics")
def api_metrics():
    """JSON API endpoint for dashboard metrics."""
    events = read_events()
    metrics = compute_metrics(events)
    return jsonify(metrics)


@app.route("/api/events")
def api_events():
    """JSON API endpoint for all events."""
    events = read_events()
    return jsonify(events)


@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename):
    """Serve screenshot images."""
    return send_from_directory(str(Config.SCREENSHOT_DIR), filename)


if __name__ == "__main__":
    Config.ensure_directories()
    logger.info("Starting NEXUS-DMS Dashboard on http://%s:%s", Config.FLASK_HOST, Config.FLASK_PORT)
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )