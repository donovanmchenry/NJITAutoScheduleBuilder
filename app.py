#! /usr/bin/env python3
"""
Tiny Flask wrapper (v2) — now returns **ALL** clash-free schedules
=================================================================

Changes from v1
---------------
* `find_schedules` enumerates *every* valid combination (up to `MAX_SOLNS`).
* Web UI lists them sequentially: "Schedule #1", "Schedule #2", …
* `/api/solve` returns JSON array of schedules (each schedule ⇒ list of sections).

Usage: `python -m flask run --reload`
"""
from __future__ import annotations
import json, itertools, sys
from pathlib import Path
from typing import List, Set, Dict, Iterable

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATA_FILE = Path("all_sections.json")
MAX_SOLNS = 50   # hard cap so a huge search doesn't hang the server

# ───────────────────────────────────────── helper fns ─────────────────────────────────────────

def _mins(t: str) -> int:
    h, m = map(int, t.split(":"))
    return 60 * h + m

class Section:
    """Minimal immutable view of a course section (extra keys ignored)."""

    def __init__(self, course: str, crn: int, days: str, start: str, end: str, **_ignored):
        self.course = course
        self.crn = crn
        self.days: Set[str] = set(days)
        self.start = _mins(start)
        self.end   = _mins(end)

    def clashes(self, other: "Section") -> bool:
        return bool((self.days & other.days) and (self.start < other.end and other.start < self.end))

    def to_dict(self):
        return {
            "course": self.course,
            "crn": self.crn,
            "days": "".join(sorted(self.days)),
            "start": f"{self.start//60:02d}:{self.start%60:02d}",
            "end":   f"{self.end//60:02d}:{self.end%60:02d}",
        }

# ───────────────────────────────────── data loading ─────────────────────────────────────────

def load_sections() -> Dict[str, List[Section]]:
    if not DATA_FILE.exists():
        sys.exit("all_sections.json missing – run scrape_njit.py first.")
    raw = json.loads(DATA_FILE.read_text())
    return {c: [Section(c, **d) for d in lst] for c, lst in raw.items()}

SECTIONS = load_sections()

# ───────────────────────────── schedule generation ──────────────────────────────────────────

def find_schedules(courses: List[str], start_ok: int, end_ok: int, days_ok: Set[str]) -> Iterable[List[Section]]:
    pools: List[List[Section]] = []
    for c in courses:
        if c not in SECTIONS:
            raise ValueError(f"Unknown course: {c}")
        pools.append(SECTIONS[c])

    count = 0
    for combo in itertools.product(*pools):
        if any(sec.days - days_ok for sec in combo):
            continue
        if any(sec.start < start_ok or sec.end > end_ok for sec in combo):
            continue
        if any(a.clashes(b) for a, b in itertools.combinations(combo, 2)):
            continue
        yield list(combo)
        count += 1
        if count >= MAX_SOLNS:
            break

# ─────────────────────────────────────── HTML ───────────────────────────────────────────────
TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>NJIT Auto Schedule Builder</title>
  <style>
    body{font-family:system-ui, sans-serif;max-width:720px;margin:40px auto;padding:0 1rem}
    label{display:block;margin-top:1rem;font-weight:600}
    input,button{width:100%;padding:.5rem;font-size:1rem}
    button{margin-top:1.25rem;cursor:pointer;border:none;border-radius:.5rem;background:#d62828;color:#fff}
    pre{background:#f7f7f7;padding:1rem;border-radius:.5rem;white-space:pre-line}
    h2{margin-top:2rem;color:#333}
  </style>
</head>
<body>
  <h1>NJIT Auto Schedule Builder</h1>
  <form method="post">
    <label>Courses (space-separated)</label>
    <input name="courses" placeholder="CS280 CS241 MATH333" required>

    <label>Earliest start (HH:MM)</label>
    <input type="time" name="start" value="09:00" required>

    <label>Latest finish (HH:MM)</label>
    <input type="time" name="end" value="16:00" required>

    <label>Days allowed (e.g. MTWRF)</label>
    <input name="days" value="MTWRF" required>

    <button type="submit">Find schedules</button>
  </form>

  {% if schedules is not none %}
    <h2>{{ schedules|length }} schedule(s) found{% if schedules|length == max_solns %} (showing first {{ max_solns }}){% endif %}</h2>
    {% if schedules %}
      {% for sched in schedules %}
        <pre><strong>Schedule #{{ loop.index }}</strong>\n{{ sched }}</pre>
      {% endfor %}
    {% else %}
      <p><em>No schedule fits those constraints.</em></p>
    {% endif %}
  {% endif %}
</body>
</html>
"""

# ───────────────────────────────────────── routes ───────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])

def index():
    rendered_schedules = None
    if request.method == "POST":
        try:
            courses = request.form["courses"].upper().split()
            s_ok = _mins(request.form["start"])
            e_ok = _mins(request.form["end"])
            days = set(request.form["days"].upper())
            sols = list(find_schedules(courses, s_ok, e_ok, days))
            rendered_schedules = [
                "\n".join(
                    f"{sec.course}  CRN:{sec.crn}  {''.join(sorted(sec.days))}  "
                    f"{sec.start//60:02d}:{sec.start%60:02d}-{sec.end//60:02d}:{sec.end%60:02d}"
                    for sec in schedule
                )
                for schedule in sols
            ]
        except ValueError as ve:
            rendered_schedules = []
            rendered_schedules.append(str(ve))
    return render_template_string(TEMPLATE, schedules=rendered_schedules, max_solns=MAX_SOLNS)


@app.route("/api/solve", methods=["POST"])

def api_solve():
    data = request.get_json(force=True)
    try:
        courses = [c.upper() for c in data["courses"]]
        s_ok = _mins(data["start"])
        e_ok = _mins(data["end"])
        days = set(data["days"].upper())
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "malformed-request"}), 400

    solutions = [ [s.to_dict() for s in sched]
                  for sched in find_schedules(courses, s_ok, e_ok, days) ]
    if solutions:
        return jsonify(solutions)
    return jsonify({"error": "no-schedule"}), 404

# ────────────────────────────────────── run app ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)