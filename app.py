#! /usr/bin/env python3
"""
Tiny Flask wrapper around the minimal schedule solver.
This version tolerates extra fields (location, instructor, …) that the
latest `scrape_njit.py` now includes in all_sections.json.
"""
from __future__ import annotations
import json, itertools, subprocess, sys
from pathlib import Path
from typing import List, Set, Dict

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATA_FILE = Path("all_sections.json")

# ───────────────────────────────────────── helper functions ──────────────────────────────────────────

def _mins(t: str) -> int:
    """Convert 'HH:MM' → minutes since midnight."""
    h, m = map(int, t.split(":"))
    return 60 * h + m

class Section:
    """Lightweight record for a meeting section.

    Extra keyword arguments are accepted and ignored so we can safely
    load richer JSON produced by the scraper (location, instructor, etc.).
    """

    def __init__(self, course: str, crn: int, days: str, start: str, end: str, **_ignored) -> None:
        self.course = course
        self.crn = crn
        self.days: Set[str] = set(days)          # e.g. {"M","W"}
        self.start = _mins(start)
        self.end = _mins(end)

    def clashes(self, other: "Section") -> bool:
        same_day = self.days & other.days
        overlap = self.start < other.end and other.start < self.end
        return bool(same_day and overlap)

    def to_dict(self):
        return {
            "course": self.course,
            "crn": self.crn,
            "days": "".join(sorted(self.days)),
            "start": f"{self.start//60:02d}:{self.start%60:02d}",
            "end": f"{self.end//60:02d}:{self.end%60:02d}",
        }


def load_sections() -> Dict[str, List[Section]]:
    if not DATA_FILE.exists():
        raise SystemExit("all_sections.json not found – run scrape_njit.py first.")
    with DATA_FILE.open() as f:
        raw = json.load(f)
    out: Dict[str, List[Section]] = {}
    for course, lst in raw.items():
        out[course] = [Section(course, **d) for d in lst]
    return out

SECTIONS = load_sections()


def find_schedule(required: List[str], start_ok: int, end_ok: int, days_ok: Set[str]):
    pools = [SECTIONS[c] for c in required if c in SECTIONS]
    if len(pools) != len(required):
        missing = set(required) - set(SECTIONS)
        raise ValueError(f"Unknown course(s): {', '.join(missing)}")
    for combo in itertools.product(*pools):
        if any(sec.days - days_ok for sec in combo):
            continue
        if any(sec.start < start_ok or sec.end > end_ok for sec in combo):
            continue
        if any(a.clashes(b) for a, b in itertools.combinations(combo, 2)):
            continue
        return combo
    return None

# ───────────────────────────────────────── HTML template ───────────────────────────────────────────
TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title> NJIT Auto Schedule Builder</title>
  <style>
    body{font-family:system-ui, sans-serif;max-width:640px;margin:40px auto;padding:0 1rem}
    label{display:block;margin-top:1rem;font-weight:600}
    input,button{width:100%;padding:.5rem;font-size:1rem}
    button{margin-top:1.25rem;cursor:pointer;border:none;border-radius:.5rem;background:#d62828;color:#fff}
    pre{background:#f1f1f1;padding:1rem;border-radius:.5rem;white-space:pre-line}
  </style>
</head>
<body>
  <h1>NJIT Auto Schedule Builder</h1>
  <form method="post">
    <label>Courses (space-separated)</label>
    <input name="courses" placeholder="CS280 CS241" required>

    <label>Earliest start (HH:MM)</label>
    <input type="time" name="start" value="09:00" required>

    <label>Latest finish (HH:MM)</label>
    <input type="time" name="end" value="16:00" required>

    <label>Days allowed (e.g. MTWRF)</label>
    <input name="days" value="MTWRF" required>

    <button type="submit">Build schedule</button>
  </form>

  {% if schedule %}
    <h2>Result</h2>
    <pre>{{ schedule }}</pre>
  {% endif %}
</body>
</html>
"""

# ───────────────────────────────────────── routes ──────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    sched_txt = None
    if request.method == "POST":
        try:
            courses = request.form["courses"].upper().split()
            start = _mins(request.form["start"])
            end = _mins(request.form["end"])
            days = set(request.form["days"].upper())
            sol = find_schedule(courses, start, end, days)
            if sol:
                lines = [f"{s.course}  CRN:{s.crn}  {''.join(sorted(s.days))}  "
                         f"{s.start//60:02d}:{s.start%60:02d}-{s.end//60:02d}:{s.end%60:02d}"
                         for s in sol]
                sched_txt = "\n".join(lines)
            else:
                sched_txt = "No schedule fits those constraints."
        except ValueError as ve:
            sched_txt = str(ve)
    return render_template_string(TEMPLATE, schedule=sched_txt)


@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.get_json(force=True)
    try:
        courses = [c.upper() for c in data["courses"]]
        start = _mins(data["start"])
        end = _mins(data["end"])
        days = set(data["days"].upper())
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "malformed-request"}), 400

    sol = find_schedule(courses, start, end, days)
    if sol:
        return jsonify([s.to_dict() for s in sol])
    return jsonify({"error": "no-schedule"}), 404

# ─────────────────────────────────────────── app run ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)