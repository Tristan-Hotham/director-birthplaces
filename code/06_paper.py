"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). Facts stated in words are checked here."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_Every_Film_Director_Is_From"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# ---------- facts stated in words in the paper ----------
D = {r["dec"]: r for r in R["decades"]["rows"]}
assert all(57 <= D[k]["Europe_pct"] <= 62 for k in range(1910, 1970, 10)) and all(45 <= D[k]["Europe_pct"] <= 53 for k in range(1970, 2030, 10))
na = {k: D[k]["North America_pct"] for k in range(1910, 2030, 10)}
assert max(na, key=na.get) == 1910 and sorted(na, key=na.get)[:2] == [1950, 1960]
ab = [r["pct"] for r in R["migration"]["by_dec"] if r["dec"] >= 1910]
assert 13.5 <= min(ab) and max(ab) <= 21 and 13.5 <= R["migration"]["pct"] <= 15.5      # 'about 14% to 21%', 'one in seven'
F = [(f["from"], f["to"]) for f in R["migration"]["flows"][:12]]
assert {("GBR", "USA"), ("CAN", "USA"), ("AUT", "DEU"), ("POL", "DEU"), ("CHE", "DEU"), ("CHN", "HKG"), ("DZA", "FRA")} <= set(F)
E = [e["iso"] for e in R["migration"]["emigrant"]]
assert E[:5] == ["SVK", "CHN", "AUT", "CHE", "GBR"] and R["migration"]["emigrant"][1]["top_dest"] == "Hong Kong"
tn = [c["iso"] for c in R["countries"]["top_notable"]]; ta = [c["iso"] for c in R["countries"]["top"]]
assert tn.index("FRA") < tn.index("DEU") and tn.index("GBR") < tn.index("DEU")
assert all(ta.index(i) < tn.index(i) for i in ("DEU", "CZE", "DNK"))
assert [c["name"] for c in R["areas"]["per_capita"][:5]] == ["Prague", "Copenhagen", "Munich", "Stockholm", "Rome"]
pl = {p["name"]: p["n"] for p in R["places"]["top"]}; ar = {a["name"]: a["n"] for a in R["areas"]["top"]}
assert [p["name"] for p in R["places"]["top"][:4]] == ["New York City", "Rome", "London", "Prague"]
assert ar["Paris"] - pl["Paris"] > max(ar[k] - pl[n] for k, n in (("New York", "New York City"), ("London", "London"), ("Rome", "Rome"), ("Prague", "Prague")))
cov = {c["iso"]: c["bp_pct"] for c in R["coverage"]["by_film_country"]}
assert all(cov[i] > 80 for i in ("HUN", "RUS", "ITA", "IRN")) and all(30 <= cov[i] <= 35 for i in ("CAN", "DNK", "NGA"))
cd = {r["dec"]: r["bp_pct"] for r in R["coverage"]["by_dec"]}
assert cd[2010] < cd[1950]
W = {r["dec"]: r for r in R["women"]["by_dec"]}
assert all(W[k]["pct_notable"] > W[k]["pct"] for k in (2000, 2010, 2020))
assert [p["n"] for p in R["prolific"]["top"][3:5]] == ["William Beaudine", "Richard Thorpe"]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


s = R["source"]
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{From query to data.}\\label{tab:pipe}"
      "\\begin{tabular}{p{10cm}r}\\toprule Step & Directors\\\\\\midrule\n"
      f"Rows returned by the director query & {s['n_rows']:,}\\\\\n"
      f"Directors (after dropping unknown values) & {s['n']:,}\\\\\n"
      f"\\quad with a birthplace & {s['n_bp']:,}\\\\\n"
      f"\\quad with a birth country & {s['n_iso']:,}\\\\\n"
      f"\\quad with a birthplace point (on the map) & {s['n_pt']:,}\\\\\n"
      f"\\quad\\quad of which in a city area of a million or more & {s['n_in_area']:,}\\\\\n"
      f"\\quad with a year of birth & {s['n_dob']:,}\\\\\n"
      f"\\quad with a recorded gender & {s['n_gender']:,}\\\\\n"
      f"\\quad with a dated film (debut decade) & {s['n_debut']:,}\\\\\n"
      f"\\quad with a main film country & {s['n_main']:,}\\\\\n"
      f"\\quad notable ({NOTABLE}+ sitelinks) & {s['n_notable']:,}\\\\\n"
      f"Film items linked to these directors & {s['n_films']:,}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for a, p in zip(R["areas"]["top"][:15], R["areas"]["per_capita"][:15]):
    rows += f"{tex(a['name'])} & {a['n']:,} & {a['notable']:,} & {a['w_pct']:.0f}\\% & {tex(p['name'])} & {p['n']:,} & {p['per100k']:.1f}\\\\\n"
TCI = ("\\begin{table}[tbp]\\centering\\small\\caption{City areas: most directors (with notable directors and the share of women), and most directors per 100,000 present-day residents.}\\label{tab:cities}\\setlength{\\tabcolsep}{5pt}"
       "\\begin{tabular}{lrrr@{\\hspace{18pt}}lrr}\\toprule City & Directors & Notable & Women & City & Directors & Per 100,000\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for c in R["countries"]["top"][:20]:
    rows += f"{tex(c['name'])} & {c['n']:,} & {c['pct']:.1f}\\% & {c['notable']:,} & {c['w_pct']:.1f}\\% & {c['per_m']:.1f}\\\\\n"
TCO = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty countries of birth with most directors: share of all directors with a birth country, notable directors, women's share, and directors per million present-day population.}\\label{tab:countries}"
       "\\begin{tabular}{lrrrrr}\\toprule Country & Directors & Share & Notable & Women & Per million\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for f in R["migration"]["flows"][:15]:
    rows += f"{tex(f['from_name'])} & {tex(f['to_name'])} & {f['n']:,}\\\\\n"
TFL = ("\\begin{table}[tbp]\\centering\\small\\caption{The largest flows from birth country to main film country.}\\label{tab:flows}"
       "\\begin{tabular}{llr}\\toprule Born in & Films mainly from & Directors\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for w in R["women"]["by_dec"]:
    lab = "before 1910" if w["dec"] == 1900 else f"{w['dec']}s"
    cov_ = next(c for c in R["coverage"]["by_dec"] if c["dec"] == w["dec"])
    rows += f"{lab} & {w['n']:,} & {w['w']:,} & {w['pct']:.1f}\\% & {w['n_notable']:,} & {w['pct_notable']:.1f}\\% & {cov_['bp_pct']:.0f}\\%\\\\\n"
TW = ("\\begin{table}[tbp]\\centering\\small\\caption{By debut decade: directors with a recorded gender, women, women's share among all and among notable directors, and the share of all directors with a birth country.}\\label{tab:women}"
      "\\begin{tabular}{lrrrrrr}\\toprule Debut & With gender & Women & Share & Notable & Share & Birth country known\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw") if m.group(1) != "DOI" else m.group(0), t)
t = t.replace("{{TABLE_PIPELINE}}", TP).replace("{{TABLE_CITIES}}", TCI).replace("{{TABLE_COUNTRIES}}", TCO).replace("{{TABLE_FLOWS}}", TFL).replace("{{TABLE_WOMEN}}", TW)
assert "{{" not in t.replace("10.5281/zenodo.23847840", "") and "--" not in t and "\u2014" not in t and "\u2013" not in t
for bad in ("DSIT", "DCMS"):
    assert bad not in t
# the DOI placeholder stays literal for the publisher; LaTeX needs its braces escaped
t = t.replace("10.5281/zenodo.23847840", "\\{\\{DOI\\}\\}")
t = t.replace("\\href{https://doi.org/\\{\\{DOI\\}\\}}", "\\href{https://doi.org/}").replace("\\url{https://doi.org/\\{\\{DOI\\}\\}}", "https://doi.org/\\{\\{DOI\\}\\}")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
