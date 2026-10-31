"""Header card (header.png), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.patches import Patch, FancyArrowPatch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
A = points()
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)


def both(fig, name):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def clean(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_facecolor(BG)


def hbar(ax, names, vals, col, labs=None, fs=11):
    y = np.arange(len(names))[::-1]
    ax.barh(y, vals, color=col, height=.72)
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=fs); ax.tick_params(length=0)
    mx = max(vals)
    for yy, v, l in zip(y, vals, labs or [f"{v:,}" for v in vals]):
        ax.text(v + mx * .01, yy, l, va="center", fontsize=fs - 1, color=FG)
    ax.set_xlim(0, mx * 1.15); ax.set_xticks([]); clean(ax); ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)


# 1. birthplace map
fig = plt.figure(figsize=(12, 6.7), facecolor=BG)
ax = fig.add_axes([0, .08, 1, .92]); world(ax, lw=.25)
hexmap(ax, A, gs=170)
legend_hex(fig, [.22, .015, .56, .05], fs=9.5)
both(fig, "map")

# 2. women only and notable only, small multiples
fig = plt.figure(figsize=(12, 3.9), facecolor=BG)
for k, (m, t) in enumerate([(A[:, 3] == 1, f"Women ({int((A[:, 3] == 1).sum()):,})"), (A[:, 2] >= NOTABLE, f"Notable, {NOTABLE}+ sitelinks ({int((A[:, 2] >= NOTABLE).sum()):,})")]):
    ax = fig.add_axes([.01 + k * .495, .12, .48, .78]); world(ax, lw=.2)
    hexmap(ax, A[m], gs=110, lw=.15)
    ax.text(.02, 1.02, t, transform=ax.transAxes, fontproperties=DISPB, fontsize=17, color=FG, va="bottom")
legend_hex(fig, [.22, .0, .56, .07], fs=9)
both(fig, "women_notable_maps")

# 3. cities
fig = plt.figure(figsize=(12, 6.4), facecolor=BG)
a1 = fig.add_axes([.14, .06, .33, .84]); a2 = fig.add_axes([.63, .06, .33, .84])
T = R["areas"]["top"][:15]; P = R["areas"]["per_capita"][:15]
hbar(a1, [t["name"] for t in T], [t["n"] for t in T], HOT)
hbar(a2, [t["name"] for t in P], [t["per100k"] for t in P], GOLD, [f"{t['per100k']:.1f}" for t in P])
a1.set_title("Directors born in each city", loc="left", fontsize=13, color=FG, pad=10)
a2.set_title("Per 100,000 people living there now", loc="left", fontsize=13, color=FG, pad=10)
both(fig, "cities")

# 4. shift by continent
D = R["decades"]["rows"]
fig = plt.figure(figsize=(12, 5.6), facecolor=BG)
ax = fig.add_axes([.07, .16, .9, .78]); clean(ax)
xs = np.arange(len(D)); bot = np.zeros(len(D))
for k, c in CONT:
    v = np.array([d[k + "_pct"] for d in D]); ax.bar(xs, v, bottom=bot, color=c, width=.86, label=k); bot += v
ax.set_xticks(xs); ax.set_xticklabels(["before\n1910" if d["dec"] == 1900 else f"{d['dec']}s" for d in D], fontsize=10)
ax.set_ylim(0, 100); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
fig.legend(handles=[Patch(fc=c, label=k) for k, c in CONT], loc="lower center", ncol=6, frameon=False, fontsize=11)
both(fig, "shift")

# 5. rising countries
Dd = [d for d in D if d["dec"] >= 1910]
fig = plt.figure(figsize=(12, 5.4), facecolor=BG)
ax = fig.add_axes([.07, .1, .78, .84]); clean(ax)
RS = [("USA", "United States", HOT), ("FRA", "France", COOL), ("ITA", "Italy", "#3E8E5E"), ("IND", "India", GOLD), ("KOR", "South Korea", "#7A4E9E"), ("IRN", "Iran", "#2A9BA8"), ("NGA", "Nigeria", "#8A6A12")]
ends = []
for i, n, c in RS:
    v = [d["c_pct"][i] for d in Dd]; ax.plot(range(len(Dd)), v, color=c, lw=2.4, marker="o", ms=4); ends.append([v[-1], n, c])
ends.sort(); prev = -9
for v, n, c in ends:
    y = max(v, prev + 1.8); prev = y; ax.text(len(Dd) - .7, y, n, color=c, fontsize=11, va="center")
ax.set_xticks(range(len(Dd))); ax.set_xticklabels([f"{d['dec']}s" for d in Dd], fontsize=10)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")); ax.set_ylim(0, 36); ax.grid(axis="y", color=RULE)
ax.set_ylabel("share of directors who debuted that decade", fontsize=10)
both(fig, "rise")

# 6. flows map: the North Atlantic, where the largest flows are
x0e, y0e = proj(-128, 2); x1e, y1e = proj(45, 64)
ext = (x0e, x1e, y0e, y1e); asp = (y1e - y0e) / (x1e - x0e)
fig = plt.figure(figsize=(12, 12 * asp + .7), facecolor=BG)
ax = fig.add_axes([0, .7 / (12 * asp + .7), 1, 12 * asp / (12 * asp + .7)]); world(ax, lw=.3, ext=ext)
inbox = lambda c: -128 <= c[0] <= 45 and 8 <= c[1] <= 64
FL = [f for f in R["migration"]["flows"] if f["from"] in SITE["cpos"] and f["to"] in SITE["cpos"] and inbox(SITE["cpos"][f["from"]]) and inbox(SITE["cpos"][f["to"]])][:20]
mx = FL[0]["n"]
POS = {"USA": (-98, 39), "CAN": (-100, 56), "GBR": (-1.5, 52.5), "FRA": (2.5, 46.8), "DEU": (10, 51)}
pos = lambda i: POS.get(i, SITE["cpos"][i][:2])
for f in FL[::-1]:
    (xa, ya), (xb, yb) = [proj(*pos(f["from"])), proj(*pos(f["to"]))]
    ax.add_patch(FancyArrowPatch((xa, ya), (xb, yb), connectionstyle="arc3,rad=-0.22", arrowstyle="-", lw=.8 + 11 * f["n"] / mx, color=COOL, alpha=.55, zorder=4, capstyle="round"))
    ax.plot([xb], [yb], "o", ms=5 + 6 * f["n"] / mx, mfc=HOT, mec="#fff", mew=1, zorder=6)
short = lambda n: n.replace("United Kingdom", "UK").replace("United States", "US")
tx, ty = proj(-127, 31)
ax.text(tx, ty, "Largest flows\n" + "\n".join(f"{short(f['from_name'])} to {short(f['to_name'])}  {f['n']}" for f in FL[:8]), fontsize=10.5, color=FG, va="top", ha="left", linespacing=1.4, zorder=8, family=MONO,
        bbox=dict(boxstyle="round,pad=.5", fc=BG, ec=RULE, alpha=.95))
fig.text(.5, .02, f"Directors born in one country whose films are mainly from another: the {len(FL)} largest flows between countries in this view.\nLine width: number of directors. Red dots: the country where they made their films.", ha="center", fontsize=9.5, color=MUT, linespacing=1.5)
both(fig, "flows")

# 7. women by decade
Wd = [w for w in R["women"]["by_dec"] if w["dec"] >= 1910]
fig = plt.figure(figsize=(12, 5), facecolor=BG)
ax = fig.add_axes([.07, .12, .82, .82]); clean(ax)
ax.plot(range(len(Wd)), [w["pct"] for w in Wd], color=WCOL, lw=3, marker="o", label="All directors")
ax.plot(range(len(Wd)), [w["pct_notable"] for w in Wd], color=GOLD, lw=2.2, ls="--", marker="o", ms=4, label=f"Notable ({NOTABLE}+ sitelinks)")
ax.set_xticks(range(len(Wd))); ax.set_xticklabels([f"{w['dec']}s" for w in Wd], fontsize=10)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")); ax.set_ylim(0, 46); ax.grid(axis="y", color=RULE)
for i in (1, len(Wd) - 1):
    ax.annotate(f"{Wd[i]['pct']:.1f}%", (i, Wd[i]["pct"]), xytext=(0, -18 if i == 1 else 8), textcoords="offset points", ha="center", fontsize=11, color=WCOL)
ax.legend(frameon=False, loc="upper left", fontsize=11)
ax.set_ylabel("women's share, by debut decade", fontsize=10)
both(fig, "women")

# 8. countries (paper)
fig = plt.figure(figsize=(12, 6), facecolor=BG)
a1 = fig.add_axes([.17, .05, .3, .86]); a2 = fig.add_axes([.66, .05, .3, .86])
T = R["countries"]["top"][:15]; N = R["countries"]["top_notable"][:15]
hbar(a1, [t["name"] for t in T], [t["n"] for t in T], [dict(CONT).get(SITE["cont"][t["iso"]], "#888") for t in T])
hbar(a2, [t["name"] for t in N], [t["n"] for t in N], [dict(CONT).get(SITE["cont"][t["iso"]], "#888") for t in N])
a1.set_title("All directors", loc="left", fontsize=13, pad=10); a2.set_title(f"Notable ({NOTABLE}+ sitelinks)", loc="left", fontsize=13, pad=10)
both(fig, "countries")

# 9. coverage
CV = sorted(R["coverage"]["by_film_country"], key=lambda c: -c["bp_pct"])
CV = CV[:10] + CV[-10:]
fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
ax = fig.add_axes([.2, .04, .75, .9])
hbar(ax, [c["name"] for c in CV], [c["bp_pct"] for c in CV], [HOT if c["iso"] == "NGA" else "#67626C" for c in CV], [f"{c['bp_pct']:.0f}%" for c in CV])
ax.axhline(9.5, color=MUT, lw=.8, ls=":")
ax.set_title("Directors with a known birthplace, by main film country: ten highest, ten lowest", loc="left", fontsize=11.5, pad=10)
both(fig, "coverage")

# header card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
fig.text(.045, .9, "Where every", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .76, "film director", fontproperties=DISP, fontsize=46, color=HOT, va="top")
fig.text(.045, .62, "is from", fontproperties=DISP, fontsize=46, color=GOLD, va="top")
fig.text(.045, .43, f"The birthplaces of {R['source']['n_iso']:,} film\ndirectors in Wikidata, from the\nsilent era to the 2020s", fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.35)
fig.text(.045, .07, "maps.tristanhotham.com/director-birthplaces", fontsize=11, color=MUT)
ax = fig.add_axes([.36, .06, .66, .9]); world(ax, lw=.2, ext=(-11.5e6, 15.6e6, -5.5e6, 8.6e6))
hexmap(ax, A, gs=120, ext=(-11.5e6, 15.6e6, -5.5e6, 8.6e6), lw=.15)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures", sorted(os.listdir(BL)))
