"""Parse the two QLever TSVs into one record per director, with their films.

Rules
- One record per Wikidata item (?dir). Rows that are blank nodes (Wikidata 'unknown value') are dropped, as are
  unknown-value birthplaces and dates.
- Birthplace: the first named birthplace (P19) in the result; a director with two or more different birthplaces is
  counted and keeps the first. Point: the coordinates of that birthplace (the first if it has several).
- Birth year: the earliest parsable year of P569 from 1800 to 2015 (earlier or later values are treated as errors).
- Gender: woman (female, trans woman), man (male, trans man), another gender (non-binary and other values), or unknown.
- Films: one record per film item, with its earliest publication year (1880 to 2026) and its countries of origin.
  Debut year: the earliest film year. One line of the films file is missing its line break; it is repaired here.
"""
import csv, sys
from collections import defaultdict, Counter
from common import *

csv.field_size_limit(sys.maxsize)
POINT = re.compile(r"POINT\(([-\d.eE+]+) ([-\d.eE+]+)\)")
YEAR = re.compile(r'^"?(-?\d{1,4})-\d\d-\d\dT')
WOMAN = {"Q6581072", "Q1052281", "Q43445"}
MAN = {"Q6581097", "Q2449503", "Q44148"}


def val(v):
    v = (v or "").strip()
    if "/.well-known/genid/" in v:
        return ""
    if v.startswith("<" + WD):
        return v[len(WD) + 1:-1]
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    return v


def year(v, lo, hi):
    m = YEAR.match(v or "")
    if not m:
        return None
    y = int(m.group(1))
    return y if lo <= y <= hi else None


rows = list(csv.reader(open(f"{RAW}/directors.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
head = [h.lstrip("?") for h in rows[0]]
D = {}
n_blank = 0
for r in rows[1:]:
    raw_id = r[0]
    if "/.well-known/genid/" in raw_id:
        n_blank += 1
        continue
    r = dict(zip(head, [val(x) for x in r + [""] * (len(head) - len(r))]))
    d = D.setdefault(r["dir"], {"q": r["dir"], "n": "", "bps": [], "bpl": {}, "pt": {}, "bpc": set(), "dob": [], "nf": 0, "sl": 0, "g": set()})
    if r["dirL"] and not d["n"]:
        d["n"] = r["dirL"]
    if r["bp"]:
        if r["bp"] not in d["bps"]:
            d["bps"].append(r["bp"])
        if r["bpL"]:
            d["bpl"].setdefault(r["bp"], r["bpL"])
        m = POINT.search(r["coord"])
        if m and r["bp"] not in d["pt"]:
            lon, lat = float(m.group(1)), float(m.group(2))
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                d["pt"][r["bp"]] = (round(lon, 4), round(lat, 4))
        if r["bpcountry"]:
            d["bpc"].add((r["bp"], r["bpcountry"]))
    y = year(r["dob"], 1800, 2015)
    if y:
        d["dob"].append(y)
    d["nf"] = max(d["nf"], int(r["nfilms"] or 0))
    d["sl"] = max(d["sl"], int(r["sl"] or 0))
    if r["gender"]:
        d["g"].add(r["gender"])
print("rows", len(rows) - 1, "blank-node rows", n_blank, "directors", len(D))

# films
txt = open(f"{RAW}/film_directors.tsv", encoding="utf-8").read()
txt, nfix = re.subn(r"\t(Q\d+)(Q\d+\t)", r"\t\1\n\2", txt)
F = {}
FD = defaultdict(set)
for ln in txt.split("\n")[1:]:
    p = ln.split("\t")
    if len(p) < 2 or not p[0].startswith("Q") or not p[1].startswith("Q"):
        continue
    p += [""] * (4 - len(p))
    f = F.setdefault(p[0], {"y": None, "o": set()})
    y = year(p[2], 1880, 2026)
    if y and (f["y"] is None or y < f["y"]):
        f["y"] = y
    if p[3].startswith("Q"):
        f["o"].add(p[3])
    FD[p[1]].add(p[0])
print("films", len(F), "line repairs", nfix, "film-director links", sum(len(v) for v in FD.values()))

out = []
gc = Counter()
for q, d in D.items():
    bp = d["bps"][0] if d["bps"] else None
    g = "w" if d["g"] & WOMAN and not d["g"] & MAN else "m" if d["g"] & MAN and not d["g"] & WOMAN else ("o" if d["g"] else "u")
    gc[g] += 1
    fl = FD.get(q, set())
    yrs = [F[f]["y"] for f in fl if F[f]["y"]]
    out.append({"q": q, "n": d["n"], "bp": bp, "bpl": d["bpl"].get(bp, "") if bp else "", "pt": d["pt"].get(bp) if bp else None,
                "bpc": sorted({c for b, c in d["bpc"] if b == bp}), "nbp": len(d["bps"]), "by": min(d["dob"]) if d["dob"] else None,
                "nf": d["nf"], "sl": d["sl"], "g": g, "gq": sorted(d["g"]),
                "films": sorted(fl), "debut": min(yrs) if yrs else None, "last": max(yrs) if yrs else None})
print("gender", dict(gc), "other values", Counter(x for d in D.values() for x in d["g"] if x not in WOMAN | MAN).most_common(8))
films = {k: {"y": v["y"], "o": sorted(v["o"])} for k, v in F.items()}
jsave({"n_rows": len(rows) - 1, "n_blank_rows": n_blank, "n_line_repairs": nfix, "directors": out}, f"{WORK}/directors_raw.json")
jsave(films, f"{WORK}/films.json")
