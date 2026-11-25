"""Turns the raw Comic Vine collection (raw.json) into the app's compact catalog-data.json.

raw.json shape: {"collected": "2026-11-25", "out": {"jubilee": [volume, ...], "venom": [...]}}
where volume = {name, year, cv, deck, count, issues: [[number, "Month YYYY", title], ...]}.
Run:  py build_data.py path/to/raw.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

NAMES = {"jubilee": "Jubilee", "venom": "Venom"}
CV_PAGES = {"jubilee": "https://comicvine.gamespot.com/jubilee/4005-4562/", "venom": "https://comicvine.gamespot.com/venom/4005-1486/"}
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], 1)}


def issue_sort_key(issue):
    num, date, _ = issue
    m = re.match(r"-?\d+(\.\d+)?", num or "")
    d = re.match(r"([A-Za-z]+)\s+(\d{4})", date or "")
    dk = (int(d.group(2)), MONTHS.get(d.group(1), 0)) if d else (9999, 0)
    return (float(m.group(0)) if m else 1e9, dk, num)


out = {"collected": raw.get("collected", ""), "source": "Comic Vine", "characters": {}}
for key, vols in raw["out"].items():
    seen = {}
    for v in vols:
        issues = [[str(n).strip(), str(d).strip(), str(t).strip()] for n, d, t in v["issues"] if str(n).strip()]
        if not issues:
            continue
        # de-duplicate issues within a volume
        uniq = list({(i[0], i[1]): i for i in issues}.values())
        uniq.sort(key=issue_sort_key)
        vol = {"n": v["name"].strip(), "y": int(v["year"]), "cv": v["cv"], "i": uniq}
        if v.get("deck"):
            vol["d"] = v["deck"][:180]
        if v["cv"] not in seen or len(uniq) > len(seen[v["cv"]]["i"]):
            seen[v["cv"]] = vol
    vols_out = sorted(seen.values(), key=lambda x: (-len(x["i"]), x["y"], x["n"]))
    out["characters"][key] = {"name": NAMES.get(key, key.title()), "cv": CV_PAGES.get(key, ""), "volumes": vols_out}
    print(f"{key}: {len(vols_out)} series, {sum(len(x['i']) for x in vols_out)} issues")

dest = ROOT / "catalog-data.json"
dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("Wrote", dest.name, dest.stat().st_size, "bytes")
