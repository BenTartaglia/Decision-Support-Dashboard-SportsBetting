from __future__ import annotations

import json
import math
import os
import re
import subprocess
import time
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "Flask" / "sample_dashboard_data.json"

app = Flask(__name__)

ODDS_RE = re.compile(r"(?P<away_team>[\w .'-]+) \((?P<away_team_odds>-?\d+)\) @ (?P<home_team>[\w .'-]+) \((?P<home_team_odds>-?\d+)\)")
PRED_RE = re.compile(
    r"(?P<winner>[A-Za-z0-9 .'-]+) \((?P<winner_conf>\d+(?:\.\d+)?)%\) vs (?P<loser>[A-Za-z0-9 .'-]+): (?P<ou_pick>OVER|UNDER) (?P<ou_value>\d+(?:\.\d+)?) \((?P<ou_conf>\d+(?:\.\d+)?)%\)"
)
EV_RE = re.compile(
    r"(?P<team>[A-Za-z0-9 .'-]+) EV: (?P<ev>-?\d+(?:\.\d+)?)(?: Fraction of Bankroll: (?P<bankroll>\d+(?:\.\d+)?)%)?"
)
ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def get_ttl_hash(seconds: int = 300) -> int:
    return round(time.time() / seconds)


def american_to_implied_prob(odds: int) -> float:
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)


def kelly_fraction_from_percent(percent: float, fraction: float = 1.0) -> float:
    return max(percent, 0.0) * fraction / 100.0


def risk_level(bankroll_fraction_percent: float, confidence_gap: float) -> str:
    if bankroll_fraction_percent >= 12 or confidence_gap >= 15:
        return "High"
    if bankroll_fraction_percent >= 4 or confidence_gap >= 7:
        return "Medium"
    return "Low"


def confidence_label(probability: float) -> str:
    if probability >= 0.70:
        return "High"
    if probability >= 0.58:
        return "Moderate"
    return "Cautious"


def simulate_bankroll(starting_bankroll: float, model_prob: float, market_odds: int, steps: int = 80) -> Dict[str, List[float]]:
    payout = market_odds / 100 if market_odds > 0 else 100 / abs(market_odds)
    flat = [starting_bankroll]
    full = [starting_bankroll]
    frac = [starting_bankroll]
    full_pct = max(kelly_fraction_from_percent(kelly_percent(model_prob, market_odds), 1.0), 0.0)
    frac_pct = max(kelly_fraction_from_percent(kelly_percent(model_prob, market_odds), 0.6), 0.0)
    swing = max(model_prob - 0.5, 0.02)

    for i in range(1, steps + 1):
        win = ((i * 17) % 100) / 100 < model_prob
        flat_stake = starting_bankroll * 0.02
        full_stake = full[-1] * min(full_pct, 0.25)
        frac_stake = frac[-1] * min(frac_pct, 0.15)

        flat.append(round(flat[-1] + (flat_stake * payout if win else -flat_stake), 2))
        full.append(round(full[-1] + (full_stake * payout if win else -full_stake), 2))
        frac.append(round(frac[-1] + (frac_stake * payout if win else -frac_stake), 2))

        # slight smoothing to avoid perfectly mechanical lines
        flat[-1] = round(flat[-1] * (1 + math.sin(i / 6) * swing * 0.01), 2)
        full[-1] = round(full[-1] * (1 + math.sin(i / 5) * swing * 0.015), 2)
        frac[-1] = round(frac[-1] * (1 + math.cos(i / 7) * swing * 0.012), 2)

    return {"flat": flat, "kelly": full, "fractional": frac}


def series_to_svg(series_map, width=520, height=280):
    all_vals = [v for series in series_map.values() for v in series]
    min_v = min(all_vals)
    max_v = max(all_vals)
    span = max(max_v - min_v, 1)

    colors = {
        "flat": "#b04a3f",
        "kelly": "#263a9b",
        "fractional": "#4f8a3d",
    }

    labels = {
        "flat": "Flat Betting Strategy",
        "kelly": "Kelly Strategy",
        "fractional": "Fractional Kelly Strategy",
    }

    plot_left = 60
    plot_right = width - 20
    plot_top = 20
    plot_bottom = height - 50

    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    def x_pos(i, total):
        return plot_left + i * plot_width / max(total - 1, 1)

    def y_pos(v):
        return plot_bottom - ((v - min_v) / span) * plot_height

    def build_points(vals):
        return " ".join(
            f"{x_pos(i, len(vals)):.1f},{y_pos(v):.1f}"
            for i, v in enumerate(vals)
        )

    y_ticks = []
    for i in range(5):
        frac = i / 4
        val = max_v - frac * span
        y_ticks.append({
            "label": f"${val:,.0f}",
            "y": round(y_pos(val), 1)
        })

    sample_len = len(next(iter(series_map.values()))) if series_map else 0
    x_ticks = []
    for frac in [0, 0.25, 0.5, 0.75, 1]:
        idx = round(frac * max(sample_len - 1, 0))
        x_ticks.append({
            "label": str(idx),
            "x": round(x_pos(idx, sample_len), 1) if sample_len else plot_left
        })

    legend = [
        {"label": labels[name], "color": colors[name]}
        for name in ["flat", "kelly", "fractional"]
        if name in series_map
    ]

    lines = []
    for name, vals in series_map.items():
        lines.append({
            "name": name,
            "label": labels.get(name, name.title()),
            "color": colors.get(name, "#333333"),
            "points": build_points(vals)
        })

    return {
        "width": width,
        "height": height,
        "plot_left": plot_left,
        "plot_right": plot_right,
        "plot_top": plot_top,
        "plot_bottom": plot_bottom,
        "x_label": "Number of Bets or Time",
        "y_label": "Bankroll Value ($)",
        "y_ticks": y_ticks,
        "x_ticks": x_ticks,
        "legend": legend,
        "lines": lines,
    }

def kelly_percent(model_prob: float, odds: int) -> float:
    b = odds / 100 if odds > 0 else 100 / abs(odds)
    q = 1 - model_prob
    frac = max(((b * model_prob) - q) / b, 0.0) if b else 0.0
    return round(frac * 100, 2)


def clean_stdout(raw: str) -> str:
    return ANSI_RE.sub("", raw)


def parse_stdout(stdout: str, sportsbook: str) -> Dict[str, Any]:
    stdout = clean_stdout(stdout)
    odds_matches = list(ODDS_RE.finditer(stdout))
    pred_matches = list(PRED_RE.finditer(stdout))
    ev_map: Dict[str, Dict[str, float]] = {}
    for m in EV_RE.finditer(stdout):
        ev_map[m.group("team").strip()] = {
            "ev": float(m.group("ev")),
            "bankroll_fraction": float(m.group("bankroll") or 0.0),
        }

    games: List[Dict[str, Any]] = []
    for odds_m, pred_m in zip(odds_matches, pred_matches):
        away = odds_m.group("away_team").strip()
        home = odds_m.group("home_team").strip()
        away_odds = int(odds_m.group("away_team_odds"))
        home_odds = int(odds_m.group("home_team_odds"))
        winner = pred_m.group("winner").strip()
        winner_conf = float(pred_m.group("winner_conf"))
        loser = pred_m.group("loser").strip()
        loser_conf = round(100 - winner_conf, 1)
        away_prob = winner_conf / 100 if winner == away else loser_conf / 100
        home_prob = winner_conf / 100 if winner == home else loser_conf / 100

        away_ev = ev_map.get(away, {"ev": 0.0, "bankroll_fraction": 0.0})
        home_ev = ev_map.get(home, {"ev": 0.0, "bankroll_fraction": 0.0})

        featured_team = away if away_ev["ev"] >= home_ev["ev"] else home
        featured_prob = away_prob if featured_team == away else home_prob
        featured_odds = away_odds if featured_team == away else home_odds
        featured_ev = away_ev if featured_team == away else home_ev
        implied = american_to_implied_prob(featured_odds)
        conf_gap = abs(featured_prob - implied) * 100
        full_kelly = featured_ev["bankroll_fraction"] or kelly_percent(featured_prob, featured_odds)
        fractional = round(full_kelly * 0.6, 2)
        bankroll = 1000
        suggested = round(bankroll * (fractional / 100), 2)
        risk = risk_level(full_kelly, conf_gap)
        sims = simulate_bankroll(bankroll, featured_prob, featured_odds)

        games.append({
            "id": f"{away}-at-{home}".lower().replace(" ", "-"),
            "sportsbook": sportsbook,
            "away_team": away,
            "home_team": home,
            "away_odds": away_odds,
            "home_odds": home_odds,
            "away_prob": round(away_prob * 100, 1),
            "home_prob": round(home_prob * 100, 1),
            "winner": winner,
            "winner_confidence": winner_conf,
            "model_confidence": confidence_label(max(away_prob, home_prob)),
            "ou_pick": pred_m.group("ou_pick"),
            "ou_value": float(pred_m.group("ou_value")),
            "ou_confidence": float(pred_m.group("ou_conf")),
            "away_ev": away_ev["ev"],
            "home_ev": home_ev["ev"],
            "featured_team": featured_team,
            "market_odds": featured_odds,
            "implied_prob": round(implied * 100, 1),
            "model_prob": round(featured_prob * 100, 1),
            "expected_value": round(featured_ev["ev"] / 1000, 3),
            "ev_raw": round(featured_ev["ev"], 2),
            "ev_indicator": "Positive" if featured_ev["ev"] > 0 else "Negative",
            "kelly": round(full_kelly, 2),
            "fractional_kelly": fractional,
            "bankroll": bankroll,
            "suggested_wager": suggested,
            "risk_level": risk,
            "avg_return_per_bet": round((sims["fractional"][-1] - bankroll) / len(sims["fractional"]), 2),
            "volatility": round((max(sims["kelly"]) - min(sims["kelly"])) / bankroll * 100, 1),
            "max_drawdown": round((max(sims["kelly"]) - min(sims["kelly"][-15:])) / max(sims["kelly"]) * 100, 1),
            "risk_of_ruin": max(1.0, round(18 - fractional, 1)),
            "prediction_confidence_score": round(max(away_prob, home_prob) * 100, 1),
            "variance_of_prediction": round(conf_gap, 1),
            "recent_model_stability": "Strong" if conf_gap >= 10 else ("Stable" if conf_gap >= 5 else "Watch"),
            "uncertainty_warning": "Reduce stake if line moves against model" if risk != "Low" else "Current edge is manageable",
            "notes": [
                f"{featured_team} shows the strongest edge on this board.",
                ("Positive EV but high variance." if risk == "High" else "Positive EV with manageable variance."),
                ("Reduce bet size if uncertainty rises." if risk != "Low" else "Current stake size remains disciplined."),
                f"Totals lean: {pred_m.group('ou_pick')} {pred_m.group('ou_value')} at {pred_m.group('ou_conf')}% confidence.",
            ],
            "simulation": sims,
            "chart": series_to_svg(sims),
        })

    featured = max(games, key=lambda g: g["ev_raw"]) if games else None
    return {
        "sportsbook": sportsbook,
        "date": str(date.today()),
        "games": games,
        "featured_game_id": featured["id"] if featured else None,
        "source": "live",
        "stdout": stdout,
    }


def sample_payload() -> Dict[str, Any]:
    payload = json.loads(SAMPLE_PATH.read_text())

    for game in payload.get("games", []):
        sims = game.get("simulation")
        if sims:
            game["chart"] = series_to_svg(sims)

    return payload


def fetch_dashboard_data(sportsbook: str) -> Dict[str, Any]:
    cmd = ["python", "main.py", "-xgb", f"-odds={sportsbook}", "-kc"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        raise Exception("Forced failure for testing")
        completed = subprocess.run(
            cmd, cwd=ROOT, env=env, capture_output=True, text=True, check=True, timeout=120
        )
        parsed = parse_stdout(completed.stdout, sportsbook)
        if parsed.get("games"):
            return parsed
        raise RuntimeError("No games were parsed from model output.")
    except Exception as exc:
        payload = sample_payload()
        payload["sportsbook"] = sportsbook
        payload["source"] = "demo"
        payload["error_message"] = str(exc)
        return payload


@lru_cache()
def cached_dashboard_data(sportsbook: str, ttl_hash: int) -> Dict[str, Any]:
    del ttl_hash
    return fetch_dashboard_data(sportsbook)


@app.route("/")
def index():
    sportsbook = request.args.get("sportsbook", "fanduel").lower()
    data = cached_dashboard_data(sportsbook, get_ttl_hash())
    games = data.get("games", [])
    requested_game = request.args.get("game")
    selected = None
    if requested_game:
        selected = next((g for g in games if g["id"] == requested_game), None)
    if selected is None and games:
        selected = next((g for g in games if g["id"] == data.get("featured_game_id")), games[0])
    return render_template("index.html", today=date.today(), dashboard=data, selected=selected)


@app.route("/api/dashboard")
def api_dashboard():
    sportsbook = request.args.get("sportsbook", "fanduel").lower()
    return jsonify(cached_dashboard_data(sportsbook, get_ttl_hash()))


if __name__ == "__main__":
    app.run(debug=True)
