# 🗓️ NJIT Auto Schedule Builder

**Live demo ▶︎ [https://njitautoschedulebuilder.onrender.com/](https://njitautoschedulebuilder.onrender.com/)**

> Find every clash‑free schedule for your chosen NJIT courses in one click.

![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey?style=flat-square)
![Render](https://img.shields.io/badge/Hosted_on-Render-00c7a9?style=flat-square)

---

## ⚠️ Important Notice

**As of March 2024**: The automatic course scraping functionality is no longer active due to NJIT system changes. Course data is now updated manually to ensure reliability. The schedule builder functionality remains fully operational with the latest course data.

---

## ✨ Features

| Local | Hosted |   |
|-------|--------|---|
| 📋 **Manual catalogue updates** for reliability | ✔︎ | ✔︎ |
| 🧮 Enumerates **all valid schedules** (cap configurable) | ✔︎ | ✔︎ |
| 🌙 Free‑tier hosting — container sleeps when idle | – | ✔︎ |
| ⚡ Tiny footprint — only Flask + Gunicorn | ✔︎ | ✔︎ |

---

## 🏗 Project structure

```
AutoScheduleBuilder/
├ app.py              Flask web UI & solver
├ all_sections.json   Course catalogue data
├ requirements.txt    Flask + Gunicorn runtime deps
├ Procfile           Process file for Gunicorn
└ README.md          ← you are here
```

---

## 🚀 Quick start (local)

```bash
# 1. Clone & install deps
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Run the server
python -m flask run

# 3. Open http://127.0.0.1:5000/
```

---

## 📋 Course Data Updates

The course catalogue (`all_sections.json`) is now updated manually at the start of each registration period to ensure accuracy. This change was made to maintain reliability after NJIT's system modernization.

Last update: March 2024 (Fall 2024 courses)

---

## 🛠 Configuration

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| MAX_SOLNS | app.py | 50 | Max schedules returned to keep UI snappy. |

---

## 🙌 Credits & License

* Original concept @donovanmchenry
* Flask schedule solver @donovanmchenry
* **License** MIT — use it, fork it, improve it!

Enjoy building the perfect schedule 🎓✨