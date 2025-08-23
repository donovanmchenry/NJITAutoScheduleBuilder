# 🗓️  NJIT Auto Schedule Builder

**Live demo ▶︎ [https://njitautoschedulebuilder.onrender.com/](https://njitautoschedulebuilder.onrender.com/)**

> Find every clash‑free schedule for your chosen NJIT courses in one click.

![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey?style=flat-square)
![Render](https://img.shields.io/badge/Hosted_on-Render-00c7a9?style=flat-square)
![CI](https://github.com/your-user/AutoScheduleBuilder/actions/workflows/refresh.yml/badge.svg)

---

## ✨ Features

|                                                          | Local | Hosted |
| -------------------------------------------------------- | :---: | :----: |
| 🔍 **Always‑fresh catalogue** via weekly GitHub Action   |   ✔︎  |   ✔︎   |
| 🧮 Enumerates **all valid schedules** (cap configurable) |   ✔︎  |   ✔︎   |
| 🌙 Free‑tier hosting — container sleeps when idle        |   –   |   ✔︎   |
| ⚡ Tiny footprint — only Flask + Gunicorn                 |   ✔︎  |   ✔︎   |

---

## 🏗 Project structure

```text
AutoScheduleBuilder/
├ app.py              Flask web UI & solver
├ scrape_njit.py      Scrapes NJIT catalogue → all_sections.json
├ requirements.txt    Flask + Gunicorn runtime deps
├ Procfile            Process file for Gunicorn
├ .github/
│   └ workflows/
│       └ refresh.yml  ← weekly catalogue refresh
└ README.md           ← you are here
```

---

## 🚀 Quick start (local)

```bash
# 1. Clone & install deps
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Pull the latest catalogue (≈3 MB)
python scrape_njit.py

# 3. Run the server
python -m flask run

# 4. Open http://127.0.0.1:5000/
```

---

## 🤖 Automatic catalogue refresh

A GitHub Action in `.github/workflows/refresh.yml` runs **every Sunday 03:00 UTC**:

1. Checks out the repo.
2. `python scrape_njit.py` — downloads & rewrites `all_sections.json`.
3. Commits the file *(only if it changed).*
   The push triggers an automatic redeploy on Render, so the live site stays current.

Edit the cron expression to refresh more or less often, or click **“Run workflow”** for an immediate update when NJIT flips to a new term.

---

## 🛠 Configuration

| Variable      | Location         | Default                         | Description                                                             |
| ------------- | ---------------- | ------------------------------- | ----------------------------------------------------------------------- |
| `MAX_SOLNS`   | `app.py`         | `50`                            | Max schedules returned to keep UI snappy.                               |
| `CATALOG_URL` | `scrape_njit.py` | latest term (`datasvc.php?p=/`) | Override to point at a specific `&term=202630` if NJIT publishes early. |

---

## 🙌 Credits & License

* Original concept @donovanmchenry
* Flask schedule solver @donovanmchenry
* **License** MIT — use it, fork it, improve it!

Enjoy building the perfect schedule 🎓✨
