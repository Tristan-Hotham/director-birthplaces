"""Shared paths and helpers for the director-birthplaces project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw3/directors.tsv   QLever query result on Wikidata (CC0), retrieved 2026: every person who is the
      director (P57) of at least one item that is an instance of film (P31 Q11424), with columns
      ?dir item, ?dirL English label, ?bp place of birth (P19), ?bpL its English label, ?coord its coordinates (P625),
      ?bpcountry the country (P17) of the birthplace, ?dob date of birth (P569), ?nfilms number of films directed,
      ?sl number of sitelinks, ?gender sex or gender (P21). One row per combination, so a director can repeat.
      Blank nodes (Wikidata 'unknown value') appear as .well-known/genid IRIs and are dropped.
  /home/claude/newdata/raw3/film_directors.tsv   QLever result: ?film, ?dir, ?date publication date (P577),
      ?origin country of origin (P495), one row per combination.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson,
      ne_10m_populated_places_simple.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("DIR_RAW", "/home/claude/newdata/raw3")
GEO = os.environ.get("DIR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("DIR_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("DIRTMP", "/dev/shm/directors"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "director-birthplaces"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23847840"            # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/director-birthplaces/"      # filled in by the publisher
RETRIEVED = "2026"
NOTABLE = 20               # sitelinks threshold for the 'notable directors' view
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
WD = "http://www.wikidata.org/entity/"


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikidata (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    raise ValueError(f)
