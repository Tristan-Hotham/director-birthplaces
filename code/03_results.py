"""All results (data/results.json), reusable tables (data/*.csv) and page data (data/site.json, data/points.json).

Definitions
- Director: a Wikidata person who is the director of at least one film item.
- Birthplace point: coordinates of the place of birth. A birthplace that is itself a country (for example 'United States')
  gives a country but no point.
- Debut decade: the decade of the earliest dated film the director is credited with in Wikidata.
- Main film country: the country of origin with the most of the director's films, each film's weight split equally
  between its countries of origin; former states count towards their principal present-day successor.
- Worked abroad: the main film country is not the birth country (and, for a former state, the birth country is not one of
  its present-day successors). Only directors with a birth country and at least one film with a country of origin.
- Notable: {NOTABLE}+ sitelinks (Wikipedia articles and other Wikimedia pages about the person, in any language).
- Women's share: women / (women + men + another gender), among directors whose gender Wikidata records.
"""
import csv, math
from collections import Counter, defaultdict
from common import *

D0 = jload(f"{WORK}/directors_geo.json")
D = D0["directors"]
G = jload(f"{WORK}/geo.json"); META, QID, FORMER, BIG = G["meta"], G["qid"], G["former"], G["big"]
F = jload(f"{WORK}/films.json")
CN = lambda i: META[i]["name"] if i in META else i
RENAME = {"København": "Copenhagen", "Montréal": "Montreal", "Kolkata": "Kolkata", "São Paulo": "São Paulo", "Ürümqi": "Urumqi",
          "Washington, D.C.": "Washington", "Wien": "Vienna", "Köln": "Cologne", "Tel Aviv-Yafo": "Tel Aviv", "Bombay": "Mumbai"}
cityname = lambda i: RENAME.get(re.sub(r"\s+", " ", BIG[i][0]), re.sub(r"\s+", " ", BIG[i][0]))
CONTS = ["Europe", "North America", "Asia", "South America", "Africa", "Oceania"]
DECS = list(range(1910, 2030, 10))
dec_of = lambda y: None if y is None else max(1900, min(2020, y // 10 * 10))   # 1880s to 1900s pooled as 'before 1910'
pc = lambda a, b: round(100 * a / b, 1) if b else None

# birthplaces that are whole countries give no point
country_bp = {d["bp"] for d in D if d["bp"] in QID}
for d in D:
    if d["bp"] in QID:
        d["pt"] = None; d["area"] = None
    d["dec"] = dec_of(d["debut"])
    d["nfd"] = len(d["films"])

# main film country
def resolve(q):
    if q in QID: return QID[q], [QID[q]]
    if q in FORMER: return FORMER[q][2], FORMER[q][1]
    return None, None


for d in D:
    w = Counter(); succ = defaultdict(set)
    for f in d["films"]:
        os_ = [resolve(o) for o in F[f]["o"]]
        os_ = [o for o in os_ if o[0]]
        for p, s in os_:
            w[p] += 1 / len(os_); succ[p].update(s)
    d["fw"] = w
    if w:
        top = max(w.values()); cands = sorted(k for k, v in w.items() if abs(v - top) < 1e-9)
        main = d["iso"] if d["iso"] in cands else cands[0]
        d["main"] = main; d["main_set"] = sorted(succ[main]); d["main_share"] = top / sum(w.values())
    else:
        d["main"] = None; d["main_set"] = []; d["main_share"] = None
    d["abroad"] = None if not (d["iso"] and d["main"]) else (d["iso"] not in d["main_set"])

N = len(D)
withbp = [d for d in D if d["bp"]]
withiso = [d for d in D if d["iso"]]
withpt = [d for d in D if d["pt"]]
gk = [d for d in D if d["g"] in "wmo"]
R = {"meta": {"slug": SLUG, "page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "retrieved": RETRIEVED, "notable": NOTABLE}}
src = {"n_rows": D0["n_rows"], "n_blank_rows": D0["n_blank_rows"], "n": N, "n_films": len(F),
       "n_links": sum(d["nfd"] for d in D), "n_bp": len(withbp), "bp_pct": pc(len(withbp), N), "n_iso": len(withiso), "iso_pct": pc(len(withiso), N),
       "n_pt": len(withpt), "pt_pct": pc(len(withpt), N), "n_country_bp": sum(1 for d in D if d["bp"] in QID),
       "n_multi_bp": sum(1 for d in D if d["nbp"] > 1), "n_iso_point": D0["how"].get("point", 0), "n_iso_wd": D0["how"].get("wikidata country", 0),
       "agree_pct": pc(D0["agree"].get("same", 0), sum(D0["agree"].values())), "n_agree_checked": sum(D0["agree"].values()),
       "n_dob": sum(1 for d in D if d["by"]), "n_debut": sum(1 for d in D if d["debut"]), "debut_pct": pc(sum(1 for d in D if d["debut"]), N),
       "n_gender": len(gk), "gender_pct": pc(len(gk), N), "n_w": sum(1 for d in D if d["g"] == "w"), "n_m": sum(1 for d in D if d["g"] == "m"),
       "n_o": sum(1 for d in D if d["g"] == "o"), "n_u": sum(1 for d in D if d["g"] == "u"), "n_nolabel": sum(1 for d in D if not d["n"]),
       "n_notable": sum(1 for d in D if d["sl"] >= NOTABLE), "median_sl": sorted(d["sl"] for d in D)[N // 2],
       "n_main": sum(1 for d in D if d["main"]), "n_areas": len({d["area"] for d in D if d["area"] is not None}),
       "n_in_area": sum(1 for d in D if d["area"] is not None), "n_places": len({d["bp"] for d in withpt}),
       "n_countries": len({d["iso"] for d in withiso})}
src["notable_bp_pct"] = pc(sum(1 for d in D if d["sl"] >= NOTABLE and d["bp"]), src["n_notable"])
src["sl1_bp_pct"] = pc(sum(1 for d in D if d["sl"] <= 1 and d["bp"]), sum(1 for d in D if d["sl"] <= 1))
src["in_area_pct"] = pc(src["n_in_area"], src["n_pt"])
R["source"] = src

# countries
cc = Counter(d["iso"] for d in withiso); ccn = Counter(d["iso"] for d in withiso if d["sl"] >= NOTABLE)
nn = sum(ccn.values())
def wshare(ds):
    g = [d for d in ds if d["g"] in "wmo"]
    return pc(sum(1 for d in g if d["g"] == "w"), len(g)), len(g)
byc = defaultdict(list)
for d in withiso: byc[d["iso"]].append(d)
top = []
for iso, n in cc.most_common(30):
    ws, ng = wshare(byc[iso])
    top.append({"iso": iso, "name": CN(iso), "n": n, "pct": pc(n, len(withiso)), "notable": ccn[iso], "notable_pct": pc(ccn[iso], nn), "w_pct": ws,
                "per_m": round(n / META[iso]["pop"] * 1e6, 1) if META[iso]["pop"] else None})
R["countries"] = {"top": top, "top_notable": [{"iso": i, "name": CN(i), "n": n, "pct": pc(n, nn)} for i, n in ccn.most_common(20)],
                  "n_notable_iso": nn, "us_pct": pc(cc["USA"], len(withiso)), "us_notable_pct": pc(ccn["USA"], nn),
                  "top5_pct": pc(sum(n for _, n in cc.most_common(5)), len(withiso)),
                  "by_cont": [{"cont": k, "n": sum(1 for d in withiso if d["cont"] == k), "pct": pc(sum(1 for d in withiso if d["cont"] == k), len(withiso))} for k in CONTS]}
R["countries"]["europe_pct"] = R["countries"]["by_cont"][0]["pct"]
R["countries"]["africa_pct"] = R["countries"]["by_cont"][4]["pct"]
R["countries"]["africa_n"] = R["countries"]["by_cont"][4]["n"]

# cities: Wikidata birthplace items, and city areas
bpc = Counter(d["bp"] for d in withpt)
bpl = {d["bp"]: d["bpl"] for d in withpt}; bpiso = {d["bp"]: d["iso"] for d in withpt}
R["places"] = {"top": [{"q": q, "name": bpl[q] or q, "iso": bpiso[q], "n": n} for q, n in bpc.most_common(25)]}
ac = Counter(d["area"] for d in D if d["area"] is not None); acn = Counter(d["area"] for d in D if d["area"] is not None and d["sl"] >= NOTABLE)
byarea = defaultdict(list)
for d in D:
    if d["area"] is not None: byarea[d["area"]].append(d)
def area_row(i, n):
    ws, ng = wshare(byarea[i])
    return {"i": i, "name": cityname(i), "iso": BIG[i][4], "n": n, "pop": BIG[i][3], "per100k": round(n / BIG[i][3] * 1e5, 1), "notable": acn[i], "w_pct": ws,
            "places": len({d["bp"] for d in byarea[i]})}
atop = [area_row(i, n) for i, n in ac.most_common(30)]
byname = {cityname(i): area_row(i, n) for i, n in ac.items()}
per = sorted([area_row(i, n) for i, n in ac.items() if n >= 50], key=lambda r: -r["per100k"])
R["areas"] = {"top": atop, "per_capita": per[:20], "per_capita_min_n": 50, "top_notable": [{"name": cityname(i), "iso": BIG[i][4], "n": n} for i, n in acn.most_common(15)],
              "n_big": len(BIG), "n_with": len(ac), "top10_pct": pc(sum(r["n"] for r in atop[:10]), len(withpt)),
              "tehran": byname["Tehran"], "tokyo": byname["Tokyo"], "newyork": byname["New York"], "mumbai": byname["Mumbai"], "kolkata": byname["Kolkata"],
              "big_per": [r for r in sorted([area_row(i, n) for i, n in ac.items() if BIG[i][3] >= 10_000_000], key=lambda r: r["per100k"])]}

# decades: geography of births by debut decade
dd = defaultdict(list)
for d in withiso:
    if d["dec"]: dd[d["dec"]].append(d)
dall = defaultdict(list)
for d in D:
    if d["dec"]: dall[d["dec"]].append(d)
decs = []
WATCH = ["USA", "FRA", "DEU", "ITA", "GBR", "RUS", "IND", "JPN", "IRN", "KOR", "NGA", "TUR", "CHN", "ESP", "BRA", "MEX", "ARG", "EGY", "PHL", "CZE"]
for k in [1900] + DECS:
    L = dd[k]; n = len(L); A = dall[k]
    row = {"dec": k, "n": n, "n_all": len(A), "bp_pct": pc(sum(1 for d in A if d["iso"]), len(A))}
    for c in CONTS: row[c] = sum(1 for d in L if d["cont"] == c)
    for c in CONTS: row[c + "_pct"] = pc(row[c], n)
    row["c"] = {i: sum(1 for d in L if d["iso"] == i) for i in WATCH}
    row["c_pct"] = {i: pc(row["c"][i], n) for i in WATCH}
    tc = Counter(d["iso"] for d in L).most_common(5)
    row["top"] = [{"iso": i, "name": CN(i), "n": m, "pct": pc(m, n)} for i, m in tc]
    decs.append(row)
DX = {r["dec"]: r for r in decs}
early = [d for d in withiso if d["dec"] and d["dec"] <= 1950]; late = [d for d in withiso if d["dec"] and d["dec"] >= 2000]
ce, cl = Counter(d["iso"] for d in early), Counter(d["iso"] for d in late)
rise = sorted([{"iso": i, "name": CN(i), "early_pct": pc(ce[i], len(early)), "late_pct": pc(cl[i], len(late)), "late_n": cl[i],
                "ratio": round((cl[i] / len(late)) / max(ce[i] / len(early), 0.5 / len(early)), 1)} for i in cl if cl[i] >= 150], key=lambda r: -r["ratio"])
fall = sorted([{"iso": i, "name": CN(i), "early_pct": pc(ce[i], len(early)), "late_pct": pc(cl[i], len(late))} for i in ce if ce[i] >= 100], key=lambda r: r["late_pct"] / r["early_pct"])
R["decades"] = {"rows": decs, "n_early": len(early), "n_late": len(late), "rise": rise[:12], "fall": fall[:8],
                "eu_na_early_pct": pc(sum(1 for d in early if d["cont"] in ("Europe", "North America")), len(early)),
                "eu_na_late_pct": pc(sum(1 for d in late if d["cont"] in ("Europe", "North America")), len(late)),
                "asia_early_pct": pc(sum(1 for d in early if d["cont"] == "Asia"), len(early)), "asia_late_pct": pc(sum(1 for d in late if d["cont"] == "Asia"), len(late)),
                "africa_early_pct": pc(sum(1 for d in early if d["cont"] == "Africa"), len(early)), "africa_late_pct": pc(sum(1 for d in late if d["cont"] == "Africa"), len(late)),
                "eu_early_pct": pc(sum(1 for d in early if d["cont"] == "Europe"), len(early)), "eu_late_pct": pc(sum(1 for d in late if d["cont"] == "Europe"), len(late)),
                "us_early_pct": pc(ce["USA"], len(early)), "us_late_pct": pc(cl["USA"], len(late))}
for i in ("IND", "IRN", "KOR", "NGA", "TUR", "CHN", "USA", "FRA", "ITA", "DEU", "RUS", "GBR"):
    R["decades"][i.lower()] = {"early_pct": pc(ce[i], len(early)), "late_pct": pc(cl[i], len(late)), "late_n": cl[i], "early_n": ce[i]}

# coverage of birthplaces by film country: who gets a birthplace in Wikidata
bym = defaultdict(list)
for d in D:
    if d["main"]: bym[d["main"]].append(d)
covr = []
for i, L in sorted(bym.items(), key=lambda kv: -len(kv[1])):
    if len(L) < 350: continue
    covr.append({"iso": i, "name": CN(i), "n": len(L), "bp_pct": pc(sum(1 for d in L if d["iso"]), len(L)), "g_pct": pc(sum(1 for d in L if d["g"] in "wmo"), len(L))})
R["coverage"] = {"by_film_country": covr, "nga": next((c for c in covr if c["iso"] == "NGA"), None),
                 "by_dec": [{"dec": r["dec"], "bp_pct": r["bp_pct"], "n_all": r["n_all"]} for r in decs]}
ng = bym.get("NGA", [])
R["coverage"]["nga_n"] = len(ng); R["coverage"]["nga_bp_pct"] = pc(sum(1 for d in ng if d["iso"]), len(ng))
R["coverage"]["usa_bp_pct"] = pc(sum(1 for d in bym["USA"] if d["iso"]), len(bym["USA"]))
R["coverage"]["ind_bp_pct"] = pc(sum(1 for d in bym["IND"] if d["iso"]), len(bym["IND"]))
nng = [d for d in D if d["main"] == "NGA" and d["dec"] and d["dec"] >= 2000]
R["coverage"]["nga_late_n"] = len(nng)
R["coverage"]["film_country_late"] = []
for i in ("IND", "NGA", "KOR", "IRN", "USA"):
    L = [d for d in D if d["main"] == i and d["dec"]]
    R["coverage"]["film_country_late"].append({"iso": i, "early": sum(1 for d in L if d["dec"] <= 1950), "late": sum(1 for d in L if d["dec"] >= 2000)})

# migration
mig = [d for d in D if d["abroad"] is not None]
ab = [d for d in mig if d["abroad"]]
flows = Counter((d["iso"], d["main"]) for d in ab)
flows_n = Counter((d["iso"], d["main"]) for d in ab if d["sl"] >= NOTABLE)
dest = Counter(d["main"] for d in ab); orig = Counter(d["iso"] for d in ab)
us = [d for d in mig if d["main"] == "USA"]
usd = []
for k in [1900] + DECS:
    L = [d for d in us if d["dec"] == k]
    if L:
        usd.append({"dec": k, "n": len(L), "abroad": sum(1 for d in L if d["abroad"]), "pct": pc(sum(1 for d in L if d["abroad"]), len(L))})
usn = [d for d in us if d["sl"] >= NOTABLE]
emi = []
bo = defaultdict(list)
for d in mig: bo[d["iso"]].append(d)
for i, L in bo.items():
    if len(L) >= 150:
        a = [d for d in L if d["abroad"]]
        emi.append({"iso": i, "name": CN(i), "n": len(L), "abroad": len(a), "pct": pc(len(a), len(L)), "top_dest": CN(Counter(d["main"] for d in a).most_common(1)[0][0]) if a else None})
emi.sort(key=lambda r: -r["pct"])
ind = [d for d in us if d["abroad"]]
dec_ab = []
for k in [1900] + DECS:
    L = [d for d in mig if d["dec"] == k]
    if L: dec_ab.append({"dec": k, "n": len(L), "pct": pc(sum(1 for d in L if d["abroad"]), len(L))})
hol_top = Counter(d["iso"] for d in ind).most_common(12)
R["migration"] = {"n": len(mig), "n_abroad": len(ab), "pct": pc(len(ab), len(mig)),
                  "notable_pct": pc(sum(1 for d in mig if d["abroad"] and d["sl"] >= NOTABLE), sum(1 for d in mig if d["sl"] >= NOTABLE)),
                  "flows": [{"from": a, "to": b, "from_name": CN(a), "to_name": CN(b), "n": n} for (a, b), n in flows.most_common(30)],
                  "flows_notable": [{"from": a, "to": b, "from_name": CN(a), "to_name": CN(b), "n": n} for (a, b), n in flows_n.most_common(15)],
                  "dest": [{"iso": i, "name": CN(i), "n": n, "pct": pc(n, len(ab))} for i, n in dest.most_common(12)],
                  "orig": [{"iso": i, "name": CN(i), "n": n} for i, n in orig.most_common(12)],
                  "us_n": len(us), "us_abroad": len(ind), "us_pct": pc(len(ind), len(us)), "us_by_dec": usd,
                  "us_notable_pct": pc(sum(1 for d in usn if d["abroad"]), len(usn)), "us_notable_n": len(usn),
                  "us_sources": [{"iso": i, "name": CN(i), "n": n} for i, n in hol_top], "emigrant": emi[:15], "by_dec": dec_ab,
                  "us_famous": [{"n": d["n"], "q": d["q"], "iso": d["iso"], "sl": d["sl"], "debut": d["debut"]} for d in sorted(ind, key=lambda d: -d["sl"])[:24]]}
R["migration"]["us_1930"] = next(r for r in usd if r["dec"] == 1930)
R["migration"]["austria"] = next(e for e in emi if e["iso"] == "AUT")
R["migration"]["us_2010"] = next(r for r in usd if r["dec"] == 2010)

# women
wdec = []
for k in [1900] + DECS:
    L = [d for d in D if d["dec"] == k and d["g"] in "wmo"]
    Ln = [d for d in L if d["sl"] >= NOTABLE]
    wdec.append({"dec": k, "n": len(L), "w": sum(1 for d in L if d["g"] == "w"), "pct": pc(sum(1 for d in L if d["g"] == "w"), len(L)),
                 "n_notable": len(Ln), "pct_notable": pc(sum(1 for d in Ln if d["g"] == "w"), len(Ln))})
wc = []
for iso, L in byc.items():
    ws, ngk = wshare(L)
    if ngk >= 150: wc.append({"iso": iso, "name": CN(iso), "n": ngk, "pct": ws})
wc.sort(key=lambda r: -r["pct"])
wall, _ = wshare(D)
wnot, _ = wshare([d for d in D if d["sl"] >= NOTABLE])
WD_ = {r["dec"]: r for r in wdec}
R["women"] = {"pct": wall, "notable_pct": wnot, "by_dec": wdec, "by_country": wc, "n_countries": len(wc),
              "top": wc[:12], "bottom": wc[-10:], "d1930": WD_[1930], "d1950": WD_[1950], "d1970": WD_[1970], "d2010": WD_[2010], "d2020": WD_[2020],
              "u_pct": pc(src["n_u"], N), "o_n": src["n_o"],
              "famous": [{"n": d["n"], "q": d["q"], "iso": d["iso"], "sl": d["sl"], "debut": d["debut"]} for d in sorted([d for d in D if d["g"] == "w"], key=lambda d: -d["sl"])[:20]],
              "early": [{"n": d["n"], "q": d["q"], "iso": d["iso"], "debut": d["debut"]} for d in sorted([d for d in D if d["g"] == "w" and d["debut"] and d["debut"] < 1915 and d["n"]], key=lambda d: d["debut"])[:10]]}
mn = min((r for r in wdec if r["dec"] >= 1910 and r["n"] >= 300), key=lambda r: r["pct"])
R["women"]["low_dec"] = mn
R["women"]["d1920"] = WD_[1920]; R["women"]["min_n"] = 150
R["women"]["india"] = next(r for r in wc if r["iso"] == "IND"); R["women"]["japan"] = next(r for r in wc if r["iso"] == "JPN")

# prolific
pro = sorted(D, key=lambda d: (-d["nfd"], -d["sl"]))[:25]
R["prolific"] = {"top": [{"n": d["n"], "q": d["q"], "nf": d["nfd"], "iso": d["iso"], "name": CN(d["iso"]) if d["iso"] else "", "debut": d["debut"], "last": d["last"],
                          "sl": d["sl"], "g": d["g"], "main": CN(d["main"]) if d["main"] else ""} for d in pro],
                 "n50": sum(1 for d in D if d["nfd"] >= 50), "n1": sum(1 for d in D if d["nfd"] == 1), "n1_pct": pc(sum(1 for d in D if d["nfd"] == 1), N),
                 "median": sorted(d["nfd"] for d in D)[N // 2],
                 "top_w": [{"n": d["n"], "q": d["q"], "nf": d["nfd"], "iso": d["iso"], "name": CN(d["iso"]) if d["iso"] else ""} for d in sorted([d for d in D if d["g"] == "w"], key=lambda d: -d["nfd"])[:8]]}

# notable
nb = [d for d in D if d["sl"] >= NOTABLE]
R["notable"] = {"n": len(nb), "pct": pc(len(nb), N), "top_sl": [{"n": d["n"], "q": d["q"], "sl": d["sl"], "iso": d["iso"], "place": d["bpl"]} for d in sorted(D, key=lambda d: -d["sl"])[:15]],
                "europe_pct": pc(sum(1 for d in nb if d["cont"] == "Europe"), sum(1 for d in nb if d["iso"])),
                "asia_pct": pc(sum(1 for d in nb if d["cont"] == "Asia"), sum(1 for d in nb if d["iso"])),
                "africa_pct": pc(sum(1 for d in nb if d["cont"] == "Africa"), sum(1 for d in nb if d["iso"]))}

# ---------- CSV ----------
GL = {"w": "woman", "m": "man", "o": "another gender", "u": ""}
with open(f"{DATA}/directors.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["wikidata", "name", "birth_year", "gender", "birthplace_wikidata", "birthplace", "lon", "lat", "birth_country", "city_area",
                "n_films", "debut_year", "last_film_year", "main_film_country", "worked_abroad", "sitelinks"])
    for d in sorted(D, key=lambda d: -d["sl"]):
        w.writerow([d["q"], dash(d["n"]), d["by"] or "", GL[d["g"]], d["bp"] or "", dash(d["bpl"]), d["pt"][0] if d["pt"] else "", d["pt"][1] if d["pt"] else "",
                    d["iso"] or "", cityname(d["area"]) if d["area"] is not None else "", d["nfd"], d["debut"] or "", d["last"] or "", d["main"] or "",
                    "" if d["abroad"] is None else int(d["abroad"]), d["sl"]])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["iso3", "country", "continent", "directors_born", "notable_born", "women_pct", "worked_abroad_pct", "main_film_country_directors", "population_ne"])
    for iso in sorted(set(cc) | set(bym), key=lambda i: -cc.get(i, 0)):
        if iso not in META: continue
        ws, ngk = wshare(byc.get(iso, []))
        L = bo.get(iso, [])
        w.writerow([iso, CN(iso), META[iso]["cont"], cc.get(iso, 0), ccn.get(iso, 0), ws if ngk >= 20 else "", pc(sum(1 for d in L if d["abroad"]), len(L)) if len(L) >= 20 else "",
                    len(bym.get(iso, [])), META[iso]["pop"]])
with open(f"{DATA}/city_areas.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["city", "iso3", "lon", "lat", "population_ne", "directors_born", "per_100k", "notable_born", "women_pct", "birthplaces"])
    for i, n in ac.most_common():
        r = area_row(i, n); w.writerow([r["name"], r["iso"], BIG[i][1], BIG[i][2], r["pop"], n, r["per100k"], r["notable"], r["w_pct"] if n >= 20 else "", r["places"]])
with open(f"{DATA}/flows.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["born_in", "worked_mainly_in", "directors", "notable"])
    for (a, b), n in flows.most_common():
        w.writerow([a, b, n, flows_n[(a, b)]])
with open(f"{DATA}/decades.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["debut_decade", "directors", "with_birth_country", "birth_country_pct"] + CONTS + ["women_pct"])
    for r in decs:
        w.writerow([r["dec"], r["n_all"], r["n"], r["bp_pct"]] + [r[c] for c in CONTS] + [WD_[r["dec"]]["pct"]])

# ---------- page data ----------
places, pidx = [], {}
for d in withpt:
    if d["bp"] not in pidx:
        pidx[d["bp"]] = len(places); places.append([d["pt"][0], d["pt"][1], dash(d["bpl"]) or f"place with no English label ({d['bp']})", d["iso"] or "", d["bp"]])
GI = {"m": 0, "w": 1, "o": 2, "u": 3}
rows = [[pidx[d["bp"]], dash(d["n"]), d["q"], d["sl"], GI[d["g"]], d["debut"] or 0, d["by"] or 0, d["nfd"], d["main"] or "", 1 if d["abroad"] else 0]
        for d in sorted(withpt, key=lambda d: -d["sl"])]
jsave({"cols": ["place", "name", "q", "sitelinks", "gender", "debut", "born", "films", "main_film_country", "worked_abroad"], "places": places, "rows": rows}, f"{DATA}/points.json")
SITE = {"cname": {i: m["name"] for i, m in META.items()}, "cont": {i: m["cont"] for i, m in META.items()},
        "cpos": {i: [m["lx"], m["ly"], m["pop"]] for i, m in META.items()},
        "c": {i: {"n": cc[i], "nn": ccn[i], "w": wshare(byc[i])[0], "g": wshare(byc[i])[1], "dec": {k: sum(1 for d in byc[i] if d["dec"] == k) for k in [1900] + DECS},
                  "ab": pc(sum(1 for d in bo.get(i, []) if d["abroad"]), len(bo.get(i, []))) if len(bo.get(i, [])) >= 20 else None,
                  "dest": [[CN(k), v] for k, v in Counter(d["main"] for d in bo.get(i, []) if d["abroad"]).most_common(3)],
                  "inflow": [[CN(k), v] for k, v in Counter(d["iso"] for d in mig if d["main"] == i and d["abroad"]).most_common(3)],
                  "top": [[dash(d["n"]), d["q"], d["sl"]] for d in sorted(byc[i], key=lambda d: -d["sl"])[:8]],
                  "films": len(bym.get(i, []))} for i in cc},
        "areas": [[cityname(i), BIG[i][1], BIG[i][2], BIG[i][3], n, BIG[i][4]] for i, n in ac.most_common(120)],
        "decs": [1900] + DECS}
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("source",)}, indent=0)[:3000])
print("top countries", [(t["iso"], t["n"], t["pct"], t["w_pct"]) for t in top[:12]])
print("notable", R["countries"]["top_notable"][:8])
print("areas", [(a["name"], a["n"], a["per100k"]) for a in atop[:12]]); print("per cap", [(a["name"], a["n"], a["per100k"]) for a in per[:12]])
print("rise", [(r["iso"], r["early_pct"], r["late_pct"], r["late_n"], r["ratio"]) for r in rise[:12]]); print("fall", [(r["iso"], r["early_pct"], r["late_pct"]) for r in fall[:6]])
print("dec", [(r["dec"], r["n_all"], r["n"], r["Europe_pct"], r["North America_pct"], r["Asia_pct"], r["Africa_pct"]) for r in decs])
print("mig", R["migration"]["pct"], R["migration"]["flows"][:12], R["migration"]["us_by_dec"], R["migration"]["us_pct"], R["migration"]["us_notable_pct"])
print("emi", [(e["iso"], e["n"], e["pct"], e["top_dest"]) for e in emi[:10]])
print("women", wall, wnot, [(r["dec"], r["n"], r["pct"], r["pct_notable"]) for r in wdec]); print([(r["iso"], r["n"], r["pct"]) for r in wc[:8]], [(r["iso"], r["pct"]) for r in wc[-6:]])
print("prolific", [(p["n"], p["nf"], p["name"], p["debut"], p["last"]) for p in R["prolific"]["top"][:15]])
print("coverage", covr[:20]); print(R["coverage"]["film_country_late"])
print("topsl", [(t["n"], t["sl"]) for t in R["notable"]["top_sl"]])
print("women famous", [(w["n"], w["sl"]) for w in R["women"]["famous"][:8]], R["women"]["early"])
print("us famous", [(w["n"], w["iso"]) for w in R["migration"]["us_famous"][:15]])
for f in ("points.json", "site.json", "directors.csv"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
