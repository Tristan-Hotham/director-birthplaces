"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (site.json, world.json, cities) is embedded; data/points.json is loaded by the page.
Facts stated in words (page, blog, paper, collage) are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>."""
import csv
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
DIR = {r["wikidata"]: r for r in csv.DictReader(open(f"{DATA}/directors.csv", encoding="utf-8"))}
byname = {r["name"]: r for r in DIR.values() if r["name"]}

# ---------- facts stated in words ----------
A = [a["name"] for a in R["areas"]["top"]]
assert A[:5] == ["New York", "Paris", "London", "Los Angeles", "Rome"], A[:5]
assert [R["areas"]["per_capita"][0]["name"], R["areas"]["per_capita"][1]["name"]] == ["Prague", "Copenhagen"]
first_out = next(a for a in R["areas"]["top"] if SITE["cont"][a["iso"]] not in ("Europe", "North America", "South America"))
assert first_out["name"] == "Tehran" and R["areas"]["tehran"]["n"] > R["areas"]["tokyo"]["n"]
assert R["areas"]["tokyo"]["per100k"] < 2 and R["areas"]["mumbai"]["per100k"] < 2 and R["areas"]["newyork"]["per100k"] < R["areas"]["per_capita"][1]["per100k"] / 3
for nm in ("Brooklyn",):
    assert any(r["birthplace"] == nm and r["city_area"] == "New York" for r in DIR.values())
assert any(r["birthplace"].startswith("Neuilly") and r["city_area"] == "Paris" for r in DIR.values())
C = [c["iso"] for c in R["countries"]["top"]]
assert C[:5] == ["USA", "DEU", "FRA", "ITA", "IND"], C[:5]
assert R["countries"]["us_notable_pct"] > 2 * R["countries"]["us_pct"] and 15 <= R["countries"]["us_pct"] <= 18   # 'one in six'
assert R["countries"]["top_notable"][0]["iso"] == "USA"
d = R["decades"]
assert d["ind"]["late_pct"] >= 1.9 * d["ind"]["early_pct"]          # 'doubles'
assert d["kor"]["late_pct"] > d["kor"]["early_pct"] and d["irn"]["late_pct"] > d["irn"]["early_pct"] and d["us_late_pct"] < d["us_early_pct"]
assert d["asia_late_pct"] > d["asia_early_pct"] and d["eu_na_late_pct"] < d["eu_na_early_pct"]
assert d["nga"]["late_pct"] < 1 and R["coverage"]["nga_bp_pct"] < 40
F = [(f["from"], f["to"]) for f in R["migration"]["flows"]]
assert F[0] == ("GBR", "USA") and F[1] == ("CAN", "USA") and set(F[2:4]) == {("AUT", "DEU"), ("POL", "DEU")}, F[:4]
assert ("CHN", "HKG") in F[:10] and ("DZA", "FRA") in F[:10]
for nm in ("Charlie Chaplin", "Ridley Scott"):
    assert byname[nm]["birth_country"] == "GBR" and byname[nm]["main_film_country"] == "USA", nm
us = {r["dec"]: r["pct"] for r in R["migration"]["us_by_dec"]}
assert us[1930] == max(v for k, v in us.items() if k >= 1910) and us[1950] < us[1930] and us[1960] < us[1930] and us[2010] > us[1960]
e0 = R["migration"]["emigrant"][0]
assert e0["iso"] == "SVK" and e0["top_dest"] == "Czech Republic" and R["migration"]["austria"]["top_dest"] == "Germany"
W = {r["dec"]: r["pct"] for r in R["women"]["by_dec"]}
assert R["women"]["low_dec"]["dec"] == 1920 and all(W[k] < 5 for k in (1920, 1930, 1940, 1950, 1960)) and W[1970] > 5
early = [w["n"] for w in R["women"]["early"]]
assert early[0] == "Alice Guy-Blaché" and R["women"]["early"][0]["debut"] < 1900
for nm in ("Lois Weber", "Mabel Normand", "Gene Gauntier", "Anna Hoffman-Uddgren", "Luise Fleck"):
    assert nm in early, nm
assert byname["Luise Fleck"]["birthplace"] == "Vienna" and byname["Anna Hoffman-Uddgren"]["birth_country"] == "SWE"
assert [r["iso"] for r in R["women"]["top"][:3]] == ["CAN", "CHE", "NLD"]
assert {"IND", "JPN"} <= {r["iso"] for r in R["women"]["bottom"][-4:]}
p = R["prolific"]["top"]
assert p[0]["n"] == "Louis Feuillade" and p[1]["n"] == "Lau Lauritzen Sr." and p[1]["iso"] == "DNK" and p[2]["n"] == "Sam Newfield" and p[2]["iso"] == "USA"
assert R["prolific"]["top_w"][0]["n"] == "Alice Guy-Blaché" and R["prolific"]["median"] == 1
cov = {c["iso"]: c["bp_pct"] for c in R["coverage"]["by_film_country"]}
assert all(cov[i] >= 80 for i in ("RUS", "ITA", "IRN")) and all(cov[i] <= 35 for i in ("CAN", "DNK", "NGA"))
ts = [t["n"] for t in R["notable"]["top_sl"]]
for nm in ("Charlie Chaplin", "Alfred Hitchcock", "Thomas Edison", "Madonna", "Volodymyr Zelenskyy"):
    assert nm in ts, nm
assert 24 <= R["source"]["sl1_bp_pct"] <= 27        # 'a quarter'
assert any(r["birthplace"] == "Lviv" for r in DIR.values())


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    assert "{{" not in html.replace("10.5281/zenodo.23847840", "").replace("https://blog.tristanhotham.com/2026/10/31/director-birthplaces/", "")
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
