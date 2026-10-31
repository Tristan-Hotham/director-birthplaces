"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23847840, https://doi.org/10.5281/zenodo.23847840 and https://blog.tristanhotham.com/2026/10/31/director-birthplaces/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Where_Every_Film_Director_Is_From"

# facts stated in words in the blog (alt text included); the page build checks the rest
import importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
A = R["areas"]
assert [a["name"] for a in A["top"][5:10]] == ["Prague", "Berlin", "Moscow", "Tehran", "Buenos Aires"]
assert [round(p["per100k"], 1) for p in A["per_capita"][:5]] == [45.1, 37.6, 23.1, 22.1, 19.0]
assert [a["n"] for a in A["top"][:5]] == [1469, 1368, 756, 642, 636]
assert [f["n"] for f in R["migration"]["flows"][:4]] == [416, 232, 124, 117]
F = [(f["from"], f["to"]) for f in R["migration"]["flows"][:10]]
assert {("DEU", "USA"), ("FRA", "USA"), ("DZA", "FRA")} <= set(F)
W = {r["dec"]: r for r in R["women"]["by_dec"]}
assert all(3 <= W[k]["pct"] <= 5 for k in range(1910, 1970, 10)) and round(W[2020]["pct"]) == 32 and round(W[2020]["pct_notable"]) == 43
cov = {c["iso"]: round(c["bp_pct"]) for c in R["coverage"]["by_film_country"]}
assert [cov[i] for i in ("HUN", "RUS", "ITA", "IRN", "POL")] == [88, 84, 82, 81, 80]
assert [cov[i] for i in ("CHN", "KOR", "AUS", "NGA", "DNK", "CAN", "PER")] == [39, 37, 34, 33, 32, 31, 29]
D = {r["dec"]: r for r in R["decades"]["rows"]}
assert 22 <= D[2000]["Asia_pct"] <= 26 and 22 <= D[2010]["Asia_pct"] <= 26
assert abs(R["decades"]["kor"]["late_pct"] - R["decades"]["irn"]["late_pct"]) < .3 and R["decades"]["kor"]["early_pct"] < .6 and R["decades"]["irn"]["early_pct"] < .6
assert R["women"]["early"][0]["n"] == "Alice Guy-Blaché"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln[:60]
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Where every film director is from",
        "slug": "director-birthplaces",
        "excerpt": f"I mapped the birthplaces of {s['n_iso']:,} film directors in Wikidata: New York and Paris lead, Prague and Copenhagen lead per head, Asia's share has grown since the 1950s, one in seven made their films abroad, and women went from {R['women']['low_dec']['pct']:.0f}% of new directors in the 1920s to {R['women']['d2020']['pct']:.0f}% in the 2020s.",
        "seo_description": "A map of where film directors were born: top cities and countries, the shift towards Asia, directors who worked abroad and the rise of women.",
        "tags": ["film", "cinema", "film directors", "maps", "data visualisation", "Wikidata", "migration", "women in film"],
        "header_alt": f"Title card reading 'Where every film director is from' in black, red and amber on cream, beside a world map of hexagons shaded from pale yellow to dark red by the number of film directors born there, darkest in Europe, the eastern United States and India. Text: the birthplaces of {s['n_iso']:,} film directors in Wikidata, from the silent era to the 2020s."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/director-birthplaces_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"director-birthplaces/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"director-birthplaces/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Where Every Film Director Is From: The Birthplaces of Film Directors in Wikidata, by City, Country, Debut Decade, Gender and Country of Work",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["film directors", "cinema history", "birthplaces", "migration", "gender", "Wikidata", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
st = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in st, bad
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
