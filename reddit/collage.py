"""r/dataisbeautiful collage for director-birthplaces: 2400 x 3400 px, light background. Numbers from data/results.json.
City labels are placed automatically on open sea: each label goes to the nearest free spot whose box does not touch
land (islands under 3,000 square km aside), another label or another leader line, and whose leader line does not cross
another label or leader. Europe, too crowded for the world map, gets its own inset."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib import patheffects as pe
from matplotlib.patches import Rectangle
from shapely.geometry import Polygon, box as sbox, LineString, Point
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.validation import make_valid

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
A = points()
BGc = "#F7F3EC"
H = 19
fig = plt.figure(figsize=(12, H), dpi=200, facecolor=BGc)
fy = lambda px: 1 - px / (H * 200)          # figure y from pixels below the top
fig.text(.045, fy(70), "Where every film director is from", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, fy(225), f"The birthplaces of {R['source']['n_pt']:,} film directors in Wikidata, from the silent era to the 2020s. Each hexagon is\n"
         f"shaded by the number of directors born inside it. Labels: directors born within 30 km of each city.",
         fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.45)

# ---- label placement on the rendered image ----
# Every label is tested against the pixels actually drawn: anything that is not plain sea or paper (land, hexagons,
# borders, frames, other text) is occupied. A label box (with a margin) must cover no occupied pixel, no other label
# and no leader line, and its leader line may not cross another label or leader.
AR = {a[0]: a for a in SITE["areas"]}
TOP = {a["name"]: a["n"] for a in R["areas"]["top"]}
HALO = [pe.withStroke(linewidth=4, foreground="#FFFFFF")]
BGRGB = np.array([int(BGc[i:i + 2], 16) for i in (1, 3, 5)])
PAD = 12                                        # pixels of clear sea or paper around every label
LABELS = []                                     # (text artist, axes) for the final check
MISSING = []
LBLMASK = None; LDRMASK = None


def render():
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(int)
    return buf, buf.shape[0]


def occupied(buf):
    return np.abs(buf - BGRGB).sum(2) > 24


def integral(m):
    return np.pad(m.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))


def rectsum(I, r0, c0, r1, c1):           # inclusive-exclusive, vectorised over arrays
    return I[r1, c1] - I[r0, c1] - I[r1, c0] + I[r0, c0]


def seg_hits(mask, p, q, skip=6):
    n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
    rr = np.linspace(p[0], q[0], n).round().astype(int); cc = np.linspace(p[1], q[1], n).round().astype(int)
    rr, cc = rr[skip:], cc[skip:]
    ok = (rr >= 0) & (rr < mask.shape[0]) & (cc >= 0) & (cc < mask.shape[1])
    return mask[rr[ok], cc[ok]].any()


def draw_seg(mask, p, q, w=3):
    n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
    for r, c in zip(np.linspace(p[0], q[0], n).round().astype(int), np.linspace(p[1], q[1], n).round().astype(int)):
        mask[max(r - w, 0):r + w + 1, max(c - w, 0):c + w + 1] = True


def place(ax, names, maxd, fs, first=()):
    """Greedy on the rendered image: at each step place the city whose nearest free spot is closest (names in 'first'
    go before the rest), so short leaders go first."""
    global LBLMASK, LDRMASK
    buf, Hp = render(); occ = occupied(buf)
    bb = ax.get_window_extent(); r0a, r1a = int(Hp - bb.y1) + 2, int(Hp - bb.y0) - 2; c0a, c1a = int(bb.x0) + 2, int(bb.x1) - 2
    allowed = np.zeros_like(occ); allowed[r0a:r1a, c0a:c1a] = True
    if LBLMASK is None:
        LBLMASK = np.zeros_like(occ); LDRMASK = np.zeros_like(occ)
    block = occ | ~allowed
    rend = fig.canvas.get_renderer(); inv = ax.transData.inverted()
    todo = {}
    for nm in names:
        a = AR[nm]; n = a[4]
        assert TOP.get(nm, n) == n, nm
        txt = f"{nm} {n:,}"
        t = ax.text(0, 0, txt, fontsize=fs, family=MONO); e = t.get_window_extent(rend); t.remove()
        x, y = ax.transData.transform(proj(a[1], a[2]))
        todo[nm] = (txt, int(e.width) + 2 * PAD, int(e.height) + 2 * PAD, Hp - y, x)
    order = list(first) + [n for n in names if n not in first]
    while todo:
        I = integral(block | LBLMASK | LDRMASK); best_all = None
        pending_first = [n for n in first if n in todo]
        for nm in (pending_first[:1] or [n for n in order if n in todo]):
            txt, w, h, cr, cc = todo[nm]
            R0 = np.arange(r0a, r1a - h, 4); C0 = np.arange(c0a, c1a - w, 4)
            RR, CC = np.meshgrid(R0, C0, indexing="ij")
            free = rectsum(I, RR, CC, RR + h, CC + w) == 0
            if not free.any():
                continue
            rr, cc_ = RR[free], CC[free]
            nr = np.clip(cr, rr + PAD, rr + h - PAD); nc = np.clip(cc, cc_ + PAD, cc_ + w - PAD)   # nearest point of each box
            d = np.hypot(nr - cr, nc - cc)
            for k in np.argsort(d)[:600]:
                if d[k] > maxd:
                    break
                if seg_hits(LBLMASK | LDRMASK, (cr, cc), (nr[k], nc[k])):
                    continue
                if best_all is None or d[k] < best_all[0]:
                    best_all = (d[k], nm, rr[k], cc_[k], nr[k], nc[k])
                break
        if best_all is None:
            MISSING.extend(todo); break
        d, nm, r, c, nr, nc = best_all
        txt, w, h, cr, cc = todo.pop(nm)
        LBLMASK[r:r + h, c:c + w] = True
        if d > PAD / 2:
            draw_seg(LDRMASK, (cr, cc), (nr, nc), 4)
            (x0, y0), (x1, y1) = inv.transform([[cc, Hp - cr], [nc, Hp - nr]])
            ax.plot([x0, x1], [y0, y1], color=FG, lw=.7, zorder=6, solid_capstyle="round")
        xc, yc = inv.transform([[c + w / 2, Hp - (r + h / 2)]])[0]
        ax.plot(*inv.transform([[cc, Hp - cr]])[0], "o", ms=3.2, mfc="#fff", mec=FG, mew=.9, zorder=7)
        t = ax.text(xc, yc, txt, fontsize=fs, family=MONO, color=FG, ha="center", va="center", zorder=8, path_effects=HALO)
        LABELS.append((t, ax))


# ---- world map ----
ext = (-13.4e6, 15.6e6, -5.6e6, 8.6e6)
mh_px = 2400 * (ext[3] - ext[2]) / (ext[1] - ext[0])
top_px = 380
ax = fig.add_axes([0, fy(top_px + mh_px), 1, mh_px / (H * 200)]); world(ax, lw=.3, ext=ext, ec=BGc, land="#E4DED0")
hexmap(ax, A, gs=175, ext=ext, lw=.12)
(ex0, ey0), (ex1, ey1) = proj(-11, 35.5), proj(40, 61.5)
ax.add_patch(Rectangle((ex0, ey0), ex1 - ex0, ey1 - ey0, fill=False, ec=FG, lw=.9, ls=(0, (3, 2)), zorder=9))
nx, ny = proj(-14, 66)
ax.text(nx, ny, "Europe: see inset", fontsize=10.5, family=MONO, color=FG, ha="right", va="center", zorder=9, path_effects=HALO)
WORLD_N = ["New York", "Los Angeles", "Tehran", "Buenos Aires", "Tokyo", "Mexico City", "Mumbai", "Seoul", "Sydney", "Lima", "Chicago", "São Paulo"]
place(ax, WORLD_N, 520, 10.5, first=("Tehran", "Los Angeles"))      # Tehran first, before Mumbai takes the Arabian Sea

# ---- legend and note ----
ly = top_px + mh_px + 40
legend_hex(fig, [.045, fy(ly + 60), .54, 26 / (H * 200)], title="Directors born in each hexagon (all debut decades)", fs=9)
fig.text(.6, fy(ly + 40), "Grey land: no director's birthplace recorded.\nPer head of today's population, Prague and\nCopenhagen lead: "
         f"{R['areas']['per_capita'][0]['per100k']:.0f} and {R['areas']['per_capita'][1]['per100k']:.0f} per 100,000 people.", fontsize=10, color=MUT, va="center", linespacing=1.4)
assert [R["areas"]["per_capita"][0]["name"], R["areas"]["per_capita"][1]["name"]] == ["Prague", "Copenhagen"]

# ---- Europe inset ----
iy = ly + 170
eext = (ex0, ex1, ey0, ey1); iw = .6; ih_px = 2400 * iw * (ey1 - ey0) / (ex1 - ex0)
ax2 = fig.add_axes([.03, fy(iy + ih_px), iw, ih_px / (H * 200)]); world(ax2, lw=.4, ext=eext, ec=BGc, land="#E4DED0")
hexmap(ax2, A, gs=520, ext=ext, lw=.1)        # smaller hexagons than the world map, about 55 km across
ax2.set_xlim(ex0, ex1); ax2.set_ylim(ey0, ey1); ax2.axis("on"); ax2.set_facecolor(BGc); ax2.set_xticks([]); ax2.set_yticks([])
for s_ in ax2.spines.values():
    s_.set_visible(True); s_.set_color(FG); s_.set_linewidth(.9); s_.set_linestyle((0, (3, 2)))
fig.text(.03, fy(iy - 10), "Europe", fontproperties=DISPB, fontsize=17, color=FG, va="bottom")
fig.text(.13, fy(iy - 12), "smaller hexagons, about 55 km across; same colour scale", family=MONO, fontsize=9.5, color=MUT, va="bottom")
EUR = ["Paris", "London", "Rome", "Prague", "Berlin", "Copenhagen", "Vienna", "Madrid"]
place(ax2, EUR, 700, 10)

# ---- big numbers, right of the inset ----
nums = [(f"{R['source']['n_iso']:,}", HOT, f"directors with a known\nbirth country, out of\n{R['source']['n']:,} in Wikidata"),
        (f"{R['countries']['us_pct']:.0f}%", COOL, f"born in the United States;\n{R['countries']['us_notable_pct']:.0f}% of the notable\nones ({NOTABLE}+ sitelinks)"),
        (f"{R['migration']['pct']:.0f}%", GOLD, "made their films mainly\nin a country other than\nthe one they were born in"),
        (f"{R['women']['d2020']['pct']:.0f}%", WCOL, f"of directors who debuted\nin the 2020s are women;\n1920s: {R['women']['d1920']['pct']:.1f}%")]
for i, (big, col, small) in enumerate(nums):
    xx = .68; yy = fy(iy - 20 + i * (ih_px + 20) / 4)
    fig.text(xx, yy, big, fontproperties=DISP, fontsize=34, color=col, va="top")
    fig.text(xx, yy - 95 / (H * 200), small, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.4)

# ---- bottom panels ----
def clean(a):
    a.set_facecolor(BGc)
    for s_ in ("top", "right"): a.spines[s_].set_visible(False)


py = iy + ih_px + 120
ph = (H * 200 - py - 300) / (H * 200)
bt = fy(py) - .012 - ph
T = R["areas"]["top"][:10]
a1 = fig.add_axes([.13, bt, .19, ph]); clean(a1)
y = np.arange(len(T))[::-1]
a1.barh(y, [t["n"] for t in T], color=HOT, height=.72)
a1.set_yticks(y); a1.set_yticklabels([t["name"] for t in T], fontsize=10); a1.tick_params(length=0); a1.set_xticks([])
a1.spines["bottom"].set_visible(False); a1.spines["left"].set_visible(False)
for yy, t in zip(y, T): a1.text(t["n"] + 25, yy, f"{t['n']:,}", va="center", fontsize=9.5)
a1.set_xlim(0, T[0]["n"] * 1.25)
fig.text(.045, fy(py - 22), "Top birth cities", family=MONO, fontsize=12.5, color=FG, va="bottom")
fig.text(.045, fy(py), "directors born within 30 km", family=MONO, fontsize=9.5, color=MUT, va="bottom")

Wd = [w for w in R["women"]["by_dec"] if w["dec"] >= 1910]
a2 = fig.add_axes([.41, bt + .012, .23, ph - .012]); clean(a2)
a2.plot(range(len(Wd)), [w["pct"] for w in Wd], color=WCOL, lw=2.6, marker="o", ms=4)
a2.set_xticks(range(0, len(Wd), 2)); a2.set_xticklabels([f"{w['dec']}s" for w in Wd][::2], fontsize=9)
a2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")); a2.set_ylim(0, 36); a2.tick_params(labelsize=9)
a2.grid(axis="y", color=RULE)
a2.annotate(f"{Wd[-1]['pct']:.0f}%", (len(Wd) - 1, Wd[-1]["pct"]), xytext=(-6, 4), textcoords="offset points", ha="right", fontsize=10, color=WCOL)
a2.annotate(f"{Wd[1]['pct']:.1f}%", (1, Wd[1]["pct"]), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=10, color=WCOL)
fig.text(.36, fy(py - 22), "Women's share of directors", family=MONO, fontsize=12.5, color=FG, va="bottom")
fig.text(.36, fy(py), "by decade of first film", family=MONO, fontsize=9.5, color=MUT, va="bottom")

FL = R["migration"]["flows"][:8]
short = lambda s: s.replace("United Kingdom", "UK").replace("United States", "US")
a3 = fig.add_axes([.86, bt, .11, ph]); clean(a3)
y = np.arange(len(FL))[::-1]
a3.barh(y, [f["n"] for f in FL], color=COOL, height=.72)
a3.set_yticks(y); a3.set_yticklabels([f"{short(f['from_name'])} to {short(f['to_name'])}" for f in FL], fontsize=9.5); a3.tick_params(length=0); a3.set_xticks([])
a3.spines["bottom"].set_visible(False); a3.spines["left"].set_visible(False)
for yy, f in zip(y, FL): a3.text(f["n"] + 8, yy, f"{f['n']}", va="center", fontsize=9.5)
a3.set_xlim(0, FL[0]["n"] * 1.35)
fig.text(.69, fy(py - 22), "Born here, made films there", family=MONO, fontsize=12.5, color=FG, va="bottom")
fig.text(.69, fy(py), "birth country to main film country", family=MONO, fontsize=9.5, color=MUT, va="bottom")

fig.text(.045, .012, "Source: Wikidata (CC0) via QLever, every person who directed a film item, 2026; Natural Earth (public domain). Birth countries on present-day\n"
         "borders. Wikidata records a birthplace for only some directors, and far more often for famous and European ones: this maps the open record,\n"
         "not every director. Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/director-birthplaces",
         family=MONO, fontsize=9, color=MUT, linespacing=1.55, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "where_film_directors_are_from.png")
assert not MISSING, MISSING
# ---- automatic check: every label box against the drawn map (without labels), other labels and leaders ----
for t, _ in LABELS: t.set_visible(False)
lines_ = [l for a_ in (ax, ax2) for l in a_.lines]
for l in lines_: l.set_visible(False)
buf, Hp = render(); occ = occupied(buf)
for l in lines_: l.set_visible(True)
for t, _ in LABELS: t.set_visible(True)
fig.canvas.draw(); rend = fig.canvas.get_renderer()
boxes = [t.get_window_extent(rend) for t, _ in LABELS]
problems = []
for i, (t, a_) in enumerate(LABELS):
    e = boxes[i]; r0, r1, c0, c1 = int(Hp - e.y1) - 3, int(Hp - e.y0) + 3, int(e.x0) - 3, int(e.x1) + 3
    if occ[r0:r1, c0:c1].any():
        problems.append(f"{t.get_text()}: over land, hexagons or other drawing ({int(occ[r0:r1, c0:c1].sum())} px)")
    ab = a_.get_window_extent()
    if e.x0 < ab.x0 or e.x1 > ab.x1 or e.y0 < ab.y0 or e.y1 > ab.y1:
        problems.append(f"{t.get_text()}: outside its map")
    for j in range(i):
        if e.overlaps(boxes[j]):
            problems.append(f"{t.get_text()}: overlaps {LABELS[j][0].get_text()}")
for l in lines_:
    if len(l.get_xdata()) != 2: continue
    pts = l.axes.transData.transform(np.column_stack([l.get_xdata(), l.get_ydata()]))
    seg = LineString(pts)
    for t, a_ in LABELS:
        e = t.get_window_extent(rend)
        if seg.crosses(sbox(e.x0, e.y0, e.x1, e.y1)) and seg.distance(Point(pts[1])) >= 0 and not sbox(e.x0 - 14, e.y0 - 14, e.x1 + 14, e.y1 + 14).contains(Point(pts[1])):
            problems.append(f"leader ending at {pts[1].round()} crosses {t.get_text()}")
print("label check:", "none" if not problems else problems)
assert not problems
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
