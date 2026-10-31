# Where every film director is from

A world map of where film directors were born: 78,729 people who directed a film in Wikidata, 43,619 of them with a known birth country and 41,753 with a birthplace on the map. By city and country, by the decade of their first film, by gender, and for directors who made their films mainly in another country.

Interactive page: https://maps.tristanhotham.com/director-birthplaces/
Paper: https://doi.org/10.5281/zenodo.23847840
Blog post: https://blog.tristanhotham.com/2026/10/31/director-birthplaces/

## Headline results

- Cities: grouping birthplaces within 30 km of a city of a million or more, New York (1,469) and Paris (1,368) lead, then London, Los Angeles and Rome. Per 100,000 present-day residents, Prague (45.1) and Copenhagen (37.6) lead; Tokyo has 1.1 and Mumbai 1.1.
- Countries: the United States is the birth country of 7,243 directors (16.6%), then Germany, France, Italy and India. Among notable directors (20+ sitelinks) the US share is 37.5%.
- The shift: of directors who debuted by the 1950s, 83% were born in Europe or North America and 12% in Asia; of those who debuted since 2000, 67% and 23%. India's share rises from 3.1% to 6.0%, South Korea's from 0.2% to 1.9%, Iran's from 0.5% to 1.9%.
- Working abroad: 14.9% of 42,950 directors made their films mainly in a country other than their birth country. The largest flows are United Kingdom to United States (416) and Canada to United States (232). 20.2% of directors of mainly American films were born abroad (23.9% of those who debuted in the 1930s).
- Women: 3.1% of directors who debuted in the 1920s, below 5% until the 1970s, 24.1% in the 2010s and 32.0% in the 2020s so far.
- Coverage: Wikidata records a birthplace for 55% of directors: 99.5% of notable ones but 25% of those with at most one sitelink, and 33% of directors whose films are mainly Nigerian. This maps the open record of film, not every film-maker.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/directors.csv` | All 78,729 directors: Wikidata ID, name, birth year, gender, birthplace (ID, name, point), birth country, city area, number of films, first and last film year, main film country, worked abroad, sitelinks (6.1 MB). |
| `data/countries.csv` | By present-day country: directors born there, notable directors, women's share, share who worked abroad, directors whose films are mainly from there, population. |
| `data/city_areas.csv` | 413 city areas: directors born within 30 km, per 100,000 people, notable, women's share. |
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
- Gender: women and trans women as women, men and trans men as men; shares among directors with a recorded gender (90%). Notable: 20+ sitelinks.
- Caveats: Wikidata is not a census of film-makers, coverage differs greatly by country and fame, the population includes people who directed one film, and borders are today's.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`): `directors.tsv` and `film_directors.tsv` (QLever query results on Wikidata, retrieved 2026) and Natural Earth countries, land and populated places. Intermediate files go to `/dev/shm/directors/work` (set `DIRTMP` to change).

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

Hotham, T. (2026) Where every film director is from: the birthplaces of 43,619 film directors in Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23847840

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
