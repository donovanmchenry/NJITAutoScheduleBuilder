#!/usr/bin/env python3
"""
Scrape NJIT Schedule-Builder catalogue → all_sections.json
--------------------------------------------------------

* **Source** : https://myhub.njit.edu/scbldr/include/datasvc.php?p=/
  (returns JavaScript, e.g. `define({data:[ … ]})`)
* **Steps**
    1.  Download the file (or a URL you supply).
    2.  Quote un-quoted identifiers so the blob is valid JSON.
    3.  Parse and transform into the tidy schema our solver expects.

Run once per term:

```bash
python scrape_njit.py                      # latest term
python scrape_njit.py <full-datasvc-url>   # specific term
```
"""
from __future__ import annotations
import json, re, sys, urllib.request, pathlib
from typing import Dict, List

DEST         = pathlib.Path("all_sections.json")
DEFAULT_URL  = "https://myhub.njit.edu/scbldr/include/datasvc.php?p=/"
DAY_MAP      = {1: "U", 2: "M", 3: "T", 4: "W", 5: "R", 6: "F", 7: "S"}

# ───────────────────────────── helper functions ──────────────────────────────

def seconds_to_hhmm(sec: int) -> str:
    h, m = divmod(sec // 60, 60)
    return f"{h:02d}:{m:02d}"


def download(url: str) -> str:
    print(f"⏬  Downloading catalogue from {url} …")
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="replace")


def js_to_json(js: str) -> str:
    """Extract JS literal inside `define( … )` and quote identifiers."""
    m = re.search(r"define\((.*)\)\s*;?\s*$", js, re.S)
    if not m:
        sys.exit("❌  Couldn’t find `define(` wrapper – site format changed.")
    obj_txt = m.group(1).strip()

    # two-stage quoting: top-level then one nested level (good enough here)
    obj_txt = re.sub(r'([{{,])\s*(\w+)\s*:', r'\1"\2":', obj_txt)
    obj_txt = re.sub(r'(\[|,)\s*(\w+)\s*:', r'\1"\2":', obj_txt)
    return obj_txt


def transform(blob: Dict) -> Dict[str, List[Dict]]:
    """Convert site’s array-heavy structure ⇒ neat dict-of-lists."""
    cleaned: Dict[str, List[Dict]] = {}

    for course_arr in blob["data"]:
        course_code = course_arr[0]

        # each element after index 2 is a section record
        for raw_sec in course_arr[3:]:
            (
                _course,
                section_id,
                crn,
                _units,
                instructor,
                *_rest,   # a few numeric flags we ignore
                title,
                meetings,
            ) = raw_sec

            # some sections (e.g. online) have no meetings – skip them
            if not meetings:
                continue

            days, starts, ends, room = set(), [], [], ""
            for meeting in meetings:
                if len(meeting) < 4:
                    continue  # malformed row
                day_num, s_sec, e_sec, rm = meeting
                days.add(DAY_MAP.get(day_num, "?"))
                starts.append(s_sec)
                ends.append(e_sec)
                room = rm or room

            if not starts:  # still empty ⇒ no real time slots
                continue

            cleaned.setdefault(course_code, []).append({
                "crn": crn,
                "days": "".join(sorted(days)),
                "start": seconds_to_hhmm(min(starts)),
                "end": seconds_to_hhmm(max(ends)),
                "location": room,
                "section": section_id,
                "instructor": instructor,
                "title": title,
            })

    return cleaned

# ─────────────────────────────────── main ─────────────────────────────────────
if __name__ == "__main__":
    catalogue_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    raw_js   = download(catalogue_url)
    json_txt = js_to_json(raw_js)
    parsed   = json.loads(json_txt)  # now valid JSON

    catalog  = transform(parsed)
    DEST.write_text(json.dumps(catalog, indent=1))

    total = sum(len(v) for v in catalog.values())
    print(f"✅  Saved {total:,} sections → {DEST}")