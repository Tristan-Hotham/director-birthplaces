"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, a, c, d, m, w = R["source"], R["areas"], R["countries"], R["decades"], R["migration"], R["women"]
N = lambda v: f"{round(v):,}"
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
readme = f"""# Where every film director is from

A world map of where film directors were born: {N(s['n'])} people who directed a film in Wikidata, {N(s['n_iso'])} of them with a known birth country and {N(s['n_pt'])} with a birthplace on the map. By city and country, by the decade of their first film, by gender, and for directors who made their films mainly in another country.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Cities: grouping birthplaces within 30 km of a city of a million or more, New York ({N(a['top'][0]['n'])}) and Paris ({N(a['top'][1]['n'])}) lead, then London, Los Angeles and Rome. Per 100,000 present-day residents, Prague ({a['per_capita'][0]['per100k']:.1f}) and Copenhagen ({a['per_capita'][1]['per100k']:.1f}) lead; Tokyo has {a['tokyo']['per100k']:.1f} and Mumbai {a['mumbai']['per100k']:.1f}.
- Countries: the United States is the birth country of {N(c['top'][0]['n'])} directors ({c['us_pct']:.1f}%), then Germany, France, Italy and India. Among notable directors ({NOTABLE}+ sitelinks) the US share is {c['us_notable_pct']:.1f}%.
- The shift: of directors who debuted by the 1950s, {d['eu_na_early_pct']:.0f}% were born in Europe or North America and {d['asia_early_pct']:.0f}% in Asia; of those who debuted since 2000, {d['eu_na_late_pct']:.0f}% and {d['asia_late_pct']:.0f}%. India's share rises from {d['ind']['early_pct']:.1f}% to {d['ind']['late_pct']:.1f}%, South Korea's from {d['kor']['early_pct']:.1f}% to {d['kor']['late_pct']:.1f}%, Iran's from {d['irn']['early_pct']:.1f}% to {d['irn']['late_pct']:.1f}%.
- Working abroad: {m['pct']:.1f}% of {N(m['n'])} directors made their films mainly in a country other than their birth country. The largest flows are United Kingdom to United States ({m['flows'][0]['n']}) and Canada to United States ({m['flows'][1]['n']}). {m['us_pct']:.1f}% of directors of mainly American films were born abroad ({m['us_1930']['pct']:.1f}% of those who debuted in the 1930s).
- Women: {w['low_dec']['pct']:.1f}% of directors who debuted in the 1920s, below 5% until the 1970s, {w['d2010']['pct']:.1f}% in the 2010s and {w['d2020']['pct']:.1f}% in the 2020s so far.
- Coverage: Wikidata records a birthplace for {s['bp_pct']:.0f}% of directors: {s['notable_bp_pct']:.1f}% of notable ones but {s['sl1_bp_pct']:.0f}% of those with at most one sitelink, and {R['coverage']['nga_bp_pct']:.0f}% of directors whose films are mainly Nigerian. This maps the open record of film, not every film-maker.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/directors.csv` | All {N(s['n'])} directors: Wikidata ID, name, birth year, gender, birthplace (ID, name, point), birth country, city area, number of films, first and last film year, main film country, worked abroad, sitelinks ({size('directors.csv')}). |
| `data/countries.csv` | By present-day country: directors born there, notable directors, women's share, share who worked abroad, directors whose films are mainly from there, population. |
| `data/city_areas.csv` | {s['n_areas']} city areas: directors born within 30 km, per 100,000 people, notable, women's share. |
| `data/flows.csv` | Every birth country to main film country pair, with counts. |
| `data/decades.csv` | By debut decade: directors, share with a birth country, continent of birth, women's share. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data: directors with a birthplace point, country summaries, outlines, city labels. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the last check of the page at desktop and phone widths. |

## Method in brief

- Directors: every Wikidata item that is the director (P57) of an item that is an instance of film (Q11424); unknown values dropped. Birthplace (P19) and its coordinates; birth country is the present-day Natural Earth country the point falls in, else the birthplace's Wikidata country. Birthplaces that are whole countries give a country but no point.
- City areas: birthplaces within 30 km of a Natural Earth city of a million or more, nearest city wins; a city within 30 km of a bigger one is merged into it. Per-head rates use present-day population.
- Debut decade: the decade of a director's earliest dated film (publication date P577). Main film country: the country of origin (P495) of most of their films, co-productions split equally; former states (Soviet Union, Yugoslavia, Czechoslovakia, the German states, British India and others) count for all their successors when deciding whether a director worked abroad.
- Gender: women and trans women as women, men and trans men as men; shares among directors with a recorded gender ({s['gender_pct']:.0f}%). Notable: {NOTABLE}+ sitelinks.
- Caveats: Wikidata is not a census of film-makers, coverage differs greatly by country and fame, the population includes people who directed one film, and borders are today's.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`): `directors.tsv` and `film_directors.tsv` (QLever query results on Wikidata, retrieved {RETRIEVED}) and Natural Earth countries, land and populated places. Intermediate files go to `/dev/shm/directors/work` (set `DIRTMP` to change).

```
python3 code/01_parse.py        # parse the two query results
python3 code/02_geo.py          # outlines, birth countries, city areas, city labels
python3 code/03_results.py      # results.json, CSV files and page data
python3 code/04_build_site.py   # index.html (checks the facts stated in words)
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
node code/12_qa.js              # screenshots (serve the folder on port 8817 first)
```

## Sources and licences

- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- Natural Earth countries, land and populated places (public domain).
- Base map tiles on the page: © Esri.

Derived data, text and figures: CC BY 4.0. Code: MIT (see LICENSE).

## Citation

Hotham, T. (2026) Where every film director is from: the birthplaces of {N(s['n_iso'])} film directors in Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in readme, bad
assert "--" not in readme.replace("|---|---|", "")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. They are derived from Wikidata
(CC0) and Natural Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Where every film director is from: the birthplaces of {N(s['n_iso'])} film directors in Wikidata. New York ({N(a['top'][0]['n'])}) and Paris ({N(a['top'][1]['n'])}) lead; women went from {w['low_dec']['pct']:.0f}% of new directors in the 1920s to {w['d2020']['pct']:.0f}% in the 2020s

## Body

I mapped the birthplace of every film director in Wikidata that has one ({N(s['n_iso'])} of {N(s['n'])}). Grouping birthplaces within 30 km of big cities, New York and Paris lead; per head, Prague ({a['per_capita'][0]['per100k']:.0f} per 100,000) and Copenhagen ({a['per_capita'][1]['per100k']:.0f}). The United States is the birth country of {c['us_pct']:.0f}% of directors and {c['us_notable_pct']:.0f}% of the well-known ones. Asia's share of new directors rose from {d['asia_early_pct']:.0f}% (debut by the 1950s) to {d['asia_late_pct']:.0f}% (since 2000). {m['pct']:.0f}% made their films mainly in another country; the biggest flow is UK to US ({m['flows'][0]['n']} directors). Caveat: Wikidata has a birthplace for {s['notable_bp_pct']:.0f}% of famous directors but only {s['sl1_bp_pct']:.0f}% of obscure ones, and for {R['coverage']['nga_bp_pct']:.0f}% of Nigerian ones, so this maps the open record, not every film-maker. Interactive map with a decade slider, gender filter and search: {PAGE}

## Source comment

Source: Wikidata via QLever (CC0), 2026: every person who is the director (P57) of a film item, with place of birth (P19), date of birth, gender and sitelinks, and each film's release date and country of origin. Natural Earth countries and populated places (public domain). Birth countries on present-day borders; city areas are birthplaces within 30 km of a city of a million or more.

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post", len(post.split()), "words")
