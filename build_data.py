"""Turns the raw Comic Vine collection (raw.json) into the app's compact catalog-data.json.

raw.json shape: {"collected": "2026-11-25", "out": {"jubilee": [volume, ...], "venom": [...]}}
where volume = {name, year, cv, deck, count, issues: [[number, "Month YYYY", title, cover_url], ...]}.
In the output, cover_url is shortened to the part after IMG_BASE (the app adds it back).
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


IMG_BASE = "https://comicvine.gamespot.com/a/uploads/scale_small/"


def issue_sort_key(issue):
    num, date = issue[0], issue[1]
    m = re.match(r"-?\d+(\.\d+)?", num or "")
    d = re.match(r"([A-Za-z]+)\s+(\d{4})", date or "")
    dk = (int(d.group(2)), MONTHS.get(d.group(1), 0)) if d else (9999, 0)
    return (float(m.group(0)) if m else 1e9, dk, num)


out = {"collected": raw.get("collected", ""), "source": "Comic Vine", "characters": {}}
for key, vols in raw["out"].items():
    seen = {}
    for v in vols:
        issues = []
        for it in v["issues"]:
            n, d, t = (str(x).strip() for x in it[:3])
            if not n:
                continue
            row = [n, d, t]
            img = it[3] if len(it) > 3 else ""
            if img and "/img/" not in img and "blank" not in img.rsplit("/", 1)[-1]:   # skip the "no cover" placeholder
                row.append(img.replace(IMG_BASE, ""))
            issues.append(row)
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
