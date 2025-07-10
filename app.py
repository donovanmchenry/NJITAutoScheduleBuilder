#!/usr/bin/env python3
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

# ─────────────────────────────────────── HTML (updated for NJIT branding) ─────────────────────────────────────────────
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>NJIT Auto Schedule Builder</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root{
      --njit-red:#cc0033;   /* primary brand color */
      --njit-dark:#262626;  /* dark neutral for text */
      --gray-100:#f5f5f5;
      --gray-300:#e0e0e0;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family:'Open Sans',Helvetica,Arial,sans-serif;
      background:var(--gray-100);
      color:var(--njit-dark);
    }
    header{
      background:var(--njit-red);
      padding:0.75rem 1rem;
      display:flex;
      align-items:center;
    }
    header img{
      height:40px;
    }
    main{
      max-width:900px;
      margin:2rem auto;
      padding:0 1rem;
    }
    .card{
      background:#fff;
      padding:2rem;
      border-radius:0.75rem;
      box-shadow:0 2px 8px rgba(0,0,0,.05);
    }
    h1{
      margin-top:0;
      font-size:1.75rem;
      font-weight:600;
      color:var(--njit-dark);
    }
    label{
      display:block;
      margin-top:1rem;
      font-weight:600;
    }
    input,button{
      width:100%;
      padding:0.6rem 0.75rem;
      font-size:1rem;
      border:1px solid var(--gray-300);
      border-radius:0.5rem;
    }
    button{
      margin-top:1.5rem;
      background:var(--njit-red);
      border:none;
      color:#fff;
      font-weight:600;
      transition:background .2s;
      cursor:pointer;
    }
    button:hover{
      background:#a60027;
    }
    .schedules{
      margin-top:2rem;
    }
    .schedule{
      background:var(--gray-100);
      border-left:4px solid var(--njit-red);
      padding:1rem;
      border-radius:0.5rem;
      margin-bottom:1.25rem;
      white-space:pre-line;
      font-family:monospace;
    }
  </style>
</head>
<body>
  <header>
    <img src="https://www.njit.edu/sites/all/themes/corporate2018dev/logo.svg" alt="NJIT logo">
  </header>
  <main>
    <div class="card">
      <h1>Auto Schedule Builder</h1>
      <form method="post">
        <label for="courses">Courses (space-separated)</label>
        <input id="courses" name="courses" placeholder="CS280 CS241 MATH333" required>

        <label for="start">Earliest start (HH:MM)</label>
        <input id="start" type="time" name="start" value="09:00" required>

        <label for="end">Latest finish (HH:MM)</label>
        <input id="end" type="time" name="end" value="16:00" required>

        <label for="days">Days allowed (e.g. MTWRF)</label>
        <input id="days" name="days" value="MTWRF" required>

        <button type="submit">Find schedules</button>
      </form>

      {% if schedules is not none %}
        <h2>{{ schedules|length }} schedule{{ 's' if schedules|length!=1 else '' }} found{% if schedules|length == max_solns %} (showing first {{ max_solns }}){% endif %}</h2>
        <div class="schedules">
          {% if schedules %}
            {% for sched in schedules %}
              <pre class="schedule"><strong>Schedule #{{ loop.index }}</strong>\n{{ sched }}</pre>
            {% endfor %}
          {% else %}
            <p><em>No schedule fits those constraints.</em></p>
          {% endif %}
        </div>
      {% endif %}
    </div>
  </main>
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
            rendered_schedules = [str(ve)]
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