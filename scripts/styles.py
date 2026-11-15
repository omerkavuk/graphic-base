#!/usr/bin/env python3
"""The style library: the 33 styles graphic base offers, each with a recipe (KIT/styles/<id>.md) and a picture
(KIT/styles/posters/<id>.jpg, mood only, never placed). Python 3 stdlib; Chrome through render.mjs for the board.

  python3 tools/styles.py suggest "<what it is about>" --purpose editorial --content report,data --tone serious       --sector finance --board review/style-board.jpg    # every style on one numbered board, the top three marked
  python3 tools/styles.py vocab                          # the words --purpose, --content, --tone and --sector take
  python3 tools/styles.py list                           # one line per style: id · name · family · essence
  python3 tools/styles.py show swiss                     # name, fit, uses and the recipe file to read
  python3 tools/styles.py board swiss newspaper dataviz --out review/styles.jpg

The board always shows all the styles, in a fixed order (by family), so a number means the same style every time.
The top three are scored from the content profile (purpose, content kind, tone, sector) against each style's fit, plus
the content words against its tags; each comes with its reasons. Read only the chosen recipe, never all of them.
Recipes: graphic base's own, and some adapted from lemo-opuscar by LemoLab and cinecode (MIT,
KIT/styles/LICENSE-lemo-opuscar).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.expanduser("~"), ".graphic-base", "cache", "styles")
SHOWN = os.environ.get("GRAPHIC_BASE_SHOWN") or os.path.join(os.path.expanduser("~"), ".graphic-base", "shown-styles.json")


def shown_boards():
    try:
        return json.load(open(SHOWN, encoding="utf-8")).get("boards", [])
    except (OSError, ValueError):
        return []


def remember(ids):
    """Every board the user saw, so the next designs are offered something else (kept: the last 30 boards)."""
    import time
    boards = (shown_boards() + [{"t": int(time.time()), "ids": list(ids)}])[-30:]
    os.makedirs(os.path.dirname(SHOWN), exist_ok=True)
    json.dump({"boards": boards}, open(SHOWN, "w", encoding="utf-8"))


def recent(k=6):
    """Styles on the user's last k boards."""
    return {i for b in shown_boards()[-k:] for i in b.get("ids", [])}


def index():
    for p in (os.path.join(HERE, "styles-index.json"), os.path.join(HERE, "..", "styles", "index.json")):
        if os.path.exists(p):
            data = json.load(open(p, encoding="utf-8"))
            data.setdefault("dir", os.path.dirname(os.path.abspath(p)))
            return data
    raise SystemExit("styles index not found (tools/styles-index.json or KIT/styles/index.json)")


def by_id(data, sid):
    for s in data["styles"]:
        if s["id"] == sid:
            return s
    raise SystemExit(f"unknown style: {sid} (styles.py list)")


def aliases(data):
    p = os.path.join(data["dir"], "aliases.json")
    return json.load(open(p, encoding="utf-8"))["aliases"] if os.path.exists(p) else []


GENERIC = {"blockbuster", "belgesel", "documentary", "true crime", "netflix documentary", "80s", "80'ler", "vhs", "synthwave",
           "morph", "shape morph", "şekil dönüşümü", "liquid", "sıvı", "metaball", "liquid logo", "swiss", "linear", "saas",
           "saas launch", "stop motion", "stop-motion", "pixel art", "16-bit", "snes", "comic book", "slapstick", "goofy",
           "cartoon comedy", "komik çizgi", "line boil", "frame by frame", "cel animation", "kare kare çizim", "variety show",
           "kinetic captions", "komik altyazı", "efektli altyazı", "sticker explainer", "çıkartma anlatım", "whiteboard explainer",
           "video essay", "video essayi", "adult animation", "data journalism", "1930s cartoon", "30'lar çizgi design",
           "60s titles", "60'lar jenerik", "city pop", "80s anime", "80'ler anime", "ukiyo-e", "ukiyoe", "disney 3d", "apple ad",
           "apple reklamı", "matematik anlatımı", "math explainer", "görsel ispat", "visual proof"}


def named_hits(data, query):
    """Aliases hit by a proper name (a director, design, studio, artist, brand), not by a word for a technique or genre."""
    q = f" {query.replace('İ', 'i').lower()} "
    return [al for al in aliases(data) if any((f" {n} " in q or (len(n) > 4 and n in q)) and n not in GENERIC
                                              for n in al["names"])]


def alias_hits(data, query):
    q = f" {query.replace('İ', 'i').lower()} "
    return [al for al in aliases(data) if any(f" {n} " in q or (len(n) > 4 and n in q) for n in al["names"])]


def said_name(al, query):
    """The look's name as the user said it: a group of names answers to any of them."""
    q = f" {query.replace('İ', 'i').lower()} "
    return next((n for n in al["names"] if f" {n} " in q or (len(n) > 4 and n in q)), al["names"][0])


def cmd_names(a):
    data = index()
    for al in aliases(data):
        print(f"{' / '.join(al['names'])} → {', '.join(al['styles']) or '(family only)'} · family {al['family']}"
              + (f" · {al['note']}" if al.get("note") else ""))


STOP = {"poster", "post", "banner", "cover", "flyer", "design", "graphic", "the", "a", "an", "of", "and", "for", "with",
        "about", "like", "style", "make", "piece", "our", "this", "that", "from", "into"}
DIMS = (("purpose", 3), ("content", 3), ("tone", 2), ("sector", 2))


def cmd_list(a):
    data = index()
    only = None
    for al in alias_hits(data, a.q or ""):
        picks = al["styles"] or [s["id"] for s in data["styles"] if s["base"] == al["family"]][:4]
        print(f"known name \"{said_name(al, a.q or '')}\" → {', '.join(al['styles']) or 'family ' + al['family'] + ' (no recipe; nearest in the family below)'}"
              + (f" · family {al['family']}" if al["styles"] else "") + (f" · {al['note']}" if al.get("note") else ""))
        only = (only or []) + [i for i in picks if i not in (only or [])]
    words = [w for w in (a.q or "").lower().split() if w not in STOP and len(w) > 1]
    rows = []
    for s in ([by_id(data, i) for i in only] if only is not None else data["styles"]):
        if a.base and a.base not in (s["base"], s.get("family")):
            continue
        if a.kind != "all" and s.get("kind", "design") != a.kind:
            continue
        if a.category and a.category.lower() not in s["category"].lower():
            continue
        hay = " ".join([s["id"], s["name"], s["category"], s["essence"], " ".join(s["uses"]), " ".join(s.get("tags", [])) * 2]).lower()
        score = sum(w in hay for w in words)
        if only is None and words and not score:
            continue
        rows.append((-score if only is None else 0, s))
    rows.sort(key=lambda r: r[0])                  # most matching words first; known names keep their order
    for _, s in rows[:a.n]:
        ess = s["essence"] if a.long else s["essence"][:110].rstrip() + ("…" if len(s["essence"]) > 110 else "")
        print(f"{s['id']} · {s['name']} · {s.get('kind', 'design')} · {s.get('family', s['base'])} · {ess}")
    print(f"({min(len(rows), a.n)} of {len(data['styles'])}" + (f", {len(rows)} matched)" if len(rows) > a.n else ")"))


def words_of(text):
    return [w for w in re.findall(r"[\w'-]+", (text or "").lower()) if w not in STOP and len(w) > 2]


def listed(v):
    return [w.strip().lower() for w in re.split(r"[,\s]+", v or "") if w.strip()]


def fit_reasons(s, prof, words):
    """Why a style fits: the profile values it shares, then the content words found in its tags or essence."""
    fit, out, score = s.get("fit", {}), [], 0.0
    for dim, w in DIMS:
        hit = [v for v in prof.get(dim, []) if v in fit.get(dim, [])]
        score += w * len(hit)
        out += [f"{dim} {v}" for v in hit]
    hay = " ".join([s["id"], s["name"], s["essence"], " ".join(s["uses"]), " ".join(s.get("tags", []))]).lower()
    wh = [w for w in words if w in hay]
    score += len(wh)
    return score, out + ([f"words {', '.join(wh[:4])}"] if wh else [])


def cmd_vocab(a):
    data = index()
    for dim, _ in DIMS:
        vals = sorted({v for s in data["styles"] if s.get("kind", "design") == "design" for v in s.get("fit", {}).get(dim, [])})
        print(f"--{dim}: {', '.join(vals)}")
    fams = sorted({s.get("family", s["base"]) for s in data["styles"] if s.get("kind", "design") == "design"})
    print(f"design families: {', '.join(fams)}")


FAMILY_ORDER = ("modernist", "editorial", "expressive", "information", "photographic", "heritage", "print-craft", "retro")


def board_order(styles):
    """Every style in a fixed order (by family, then name), so a number means the same style on every board."""
    rank = {f: n for n, f in enumerate(FAMILY_ORDER)}
    return sorted(styles, key=lambda s: (rank.get(s.get("family", s["base"]), 99), s["name"]))


def cmd_suggest(a):
    """The style board: all the styles at once, numbered, with the top three for this content marked."""
    data = index()
    pool = board_order([s for s in data["styles"] if s.get("kind", "design") == "design"])
    prof = {"purpose": listed(a.purpose), "content": listed(a.content), "tone": listed(a.tone), "sector": listed(a.sector)}
    words = words_of(a.idea)
    named = [i for al in alias_hits(data, a.idea or "") for i in al["styles"]]
    scored = {s["id"]: fit_reasons(s, prof, words) for s in pool}
    top = sorted(pool, key=lambda s: (-(scored[s["id"]][0] + (10 if s["id"] in named else 0)), pool.index(s)))[:3]
    if not any(prof.values()):
        print("no content profile given: pass --purpose, --content, --tone and --sector (styles.py vocab) so the top three fit")
    print("top three for this content:")
    for s in top:
        n = pool.index(s) + 1
        why = "named" if s["id"] in named else "; ".join(scored[s["id"]][1]) or "closest overall"
        print(f"  ★ {n}. {s['id']} · {s['name']} · fits: {why}")
    print(f"all {len(pool)} styles on the board:")
    for n, s in enumerate(pool, 1):
        print(f"  {n}. {s['id']} · {s['name']} · {s.get('family', s['base'])}{'  ★' if s in top else ''}")
    if a.board:
        cmd_board(argparse.Namespace(ids=[s["id"] for s in pool], out=a.board, width=320, star=[s["id"] for s in top]))


def cmd_show(a):
    data = index()
    s = by_id(data, a.id)
    recipe = os.path.normpath(os.path.join(data["dir"], s["id"] + ".md"))
    print(f"{s['name']} ({s['id']}) · {s['category']}")
    print(f"essence: {s['essence']}")
    print(f"kind: {s.get('kind', 'design')} · family: {s.get('family', s['base'])}")
    if s.get("fit"):
        print("fit: " + " · ".join(f"{k} {', '.join(v)}" for k, v in s["fit"].items()))
    print(f"uses: {', '.join(s['uses'])}")
    print(f"recipe: {recipe}")
    print(("poster: a sample made with the kit: " + os.path.join(data["dir"], s["poster"])) if str(s.get("poster", "")).startswith("posters/")
          else "poster: a still from the source project's demo (mood only)" if s.get("poster") else "no poster")


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "graphic-base-styles/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest + ".part", "wb") as f:
        shutil.copyfileobj(r, f)
    os.replace(dest + ".part", dest)
    return dest


def page(img, captions=()):
    """A page beside an image that shows it at full width, with optional numbered captions above it. Its path, clicked
    in the Claude Code desktop app, opens it big in the app's own browser pane (elsewhere in the browser); the app does
    not show images inside a chat message."""
    import html as _h
    p = os.path.splitext(str(img))[0] + ".html"
    name = _h.escape(os.path.basename(str(img)))
    caps = "".join(f"<li>{_h.escape(c)}</li>" for c in captions)
    open(p, "w", encoding="utf-8").write(
        f'<!doctype html><meta charset=utf-8><title>{name}</title><style>body{{margin:0;background:#111;color:#eee;'
        f'font:18px/1.5 -apple-system,Helvetica,Arial,sans-serif}}ul{{margin:0;padding:14px 18px;list-style:none}}'
        f'img{{display:block;width:100%;height:auto}}</style>' + (f"<ul>{caps}</ul>" if caps else "") +
        f'<img src="{name}">')
    return os.path.abspath(p)


def show(path):
    """Put a board, a sheet or a design in front of the user: Preview on macOS, the default viewer elsewhere.
    GB_NO_OPEN=1 turns it off (tests, servers)."""
    if os.environ.get("GB_NO_OPEN") or not os.path.exists(str(path)):
        return False
    if not os.environ.get("GB_OPEN"):
        return False
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            os.startfile(str(path))
        elif shutil.which("xdg-open") and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return False
    except OSError:
        return False
    return True


def chrome():
    win = [os.path.join(os.environ.get(root, ""), *app) for root in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
           for app in (("Google", "Chrome", "Application", "chrome.exe"), ("Microsoft", "Edge", "Application", "msedge.exe"))
           if os.environ.get(root)]
    for c in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"] + win:
        if os.path.exists(c):
            return c
    return next((shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                                          "microsoft-edge") if shutil.which(n)), None)


def short(text, n):
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def html_board(picks, files, cols, w, h, out, star=()):
    """The board as a page captured by render.mjs: a big number on each tile, the style's name under it, and a text
    card for a recipe without a poster."""
    import html as H
    cap = 46
    tiles = []
    for i, (st, f) in enumerate(zip(picks, files), 1):
        body = (f'<img src="{H.escape(Path(f).resolve().as_uri())}">' if f else
                f'<div class="card"><b>{H.escape(st["name"])}</b><span>{H.escape(short(st["essence"], 220))}</span></div>')
        mark = ' <b class="s">★</b>' if st.get("id") in star else ""
        tiles.append(f'<div class="t{" on" if mark else ""}">{body}<p><i>{i}</i>{H.escape(st["name"])}{mark}</p></div>')   # the number sits under the picture, never over it
    page_html = (f"<!doctype html><meta charset=utf-8><style>body{{margin:0;padding:8px;background:#000;display:grid;"
                 f"grid-template-columns:repeat({cols},{w}px);gap:8px;font-family:system-ui,Helvetica,Arial,sans-serif}}"
                 f".t{{position:relative;width:{w}px;height:{h + cap}px;background:#111}}"
                 f"img{{width:{w}px;height:{h}px;object-fit:contain;display:block;background:#000}}"
                 f".card{{width:{w}px;height:{h}px;box-sizing:border-box;padding:56px 26px 18px;background:#2a2620;color:#f1e6d0;"
                 f"display:flex;flex-direction:column;gap:10px}}.card b{{font-size:26px}}.card span{{font-size:15px;line-height:1.4;opacity:.88}}"
                 f"i{{display:inline-block;width:32px;height:32px;margin-right:10px;border-radius:16px;background:#f2c230;color:#111;"
                 f"font:700 20px/32px system-ui,Helvetica,Arial,sans-serif;text-align:center;font-style:normal;vertical-align:middle}}"
                 f"p{{margin:0;height:{cap}px;line-height:{cap}px;padding:0 12px;color:#eee;font-size:17px;white-space:nowrap;"
                 f"overflow:hidden;text-overflow:ellipsis}}.s{{color:#f2c230}}.on{{outline:4px solid #f2c230;outline-offset:-4px}}"
                 f"</style>{''.join(tiles)}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    src = os.path.splitext(os.path.abspath(out))[0] + "-board.html"
    open(src, "w", encoding="utf-8").write(page_html)
    W = cols * (w + 8) + 8
    r = subprocess.run(["node", os.path.join(HERE, "render.mjs"), "--page", src, "--shot", out, "--width", str(W), "--full"],
                       capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out)


def cmd_board(a):
    if len(a.ids) < 2:
        raise SystemExit("board takes 2 or more style ids")
    data = index()
    picks = [by_id(data, i) for i in a.ids]
    files = []
    for st in picks:
        f = None
        if st.get("poster") and not str(st["poster"]).startswith("http"):     # a picture kept in the kit (styles/posters)
            local = os.path.join(data["dir"], st["poster"])
            f = local if os.path.exists(local) else None
        elif st.get("poster"):
            try:
                f = fetch(st["poster"], os.path.join(CACHE, data.get("commit", "x")[:12] or "x", st["id"] + ".jpg"))
            except Exception:
                f = None                          # offline or moved: the text card stands in
        files.append(f)
    w = a.width
    h = round(w * 9 / 16 / 2) * 2
    cols = {4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 3}.get(len(files), 6 if len(files) > 9 else len(files))
    rows = (len(files) + cols - 1) // cols
    remember([st["id"] for st in picks])
    if not html_board(picks, files, cols, w, h, a.out, star=set(getattr(a, "star", None) or [])):
        raise SystemExit("board: render.mjs could not draw it (Chrome and Node needed)")
    print(f"board: {a.out} ({cols}x{rows}, left to right, top to bottom) · show the user: {os.path.abspath(a.out)} (Claude Code: SendUserFile with display 'render'; elsewhere the page {page(a.out)} in your message)"
          + (" · opened on the user's screen" if show(a.out) else ""))
    for i, st in enumerate(picks, 1):
        print(f"  {i}. {st['name']} ({st['id']}) · {st.get('family', st['base'])} · {short(st['essence'], 90)}")
    print("ask after showing it, in the user's language: the three ★ styles as options, each with its reason tied to "
          "the content, and \"None of these: something bolder\" last; any other number on the board goes in Other. "
          "On that answer: KIT/references/quick-mode.md §1, question 3.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("suggest", help="the style board: every style, numbered, the top three for the content marked")
    g.add_argument("idea", nargs="?", default="", help="what the piece is about, in English words (optional)")
    g.add_argument("--purpose", help="brand | editorial | event")
    g.add_argument("--content", help="comma list: report, data, explainer, announcement, invitation, product, story ... (vocab)")
    g.add_argument("--tone", help="comma list: serious, calm, playful, bold, elegant, urgent, warm ... (vocab)")
    g.add_argument("--sector", help="comma list: finance, environment, culture, food, public, tech ... (vocab)")

    g.add_argument("--board", help="also draw the numbered board to this path (opens on the user's screen)")
    g.set_defaults(fn=cmd_suggest)
    sub.add_parser("vocab", help="the words the content profile takes").set_defaults(fn=cmd_vocab)
    p = sub.add_parser("list")
    p.add_argument("--kind", default="all", choices=["design", "image", "all"])
    p.add_argument("--base", help="a family (modernist, editorial, retro, print-craft, expressive, information, heritage …)")
    p.add_argument("--category")
    p.add_argument("--q", help="words; a style matches when any word appears")
    p.add_argument("--long", action="store_true", help="the whole essence line")
    p.add_argument("--n", type=int, default=8, help="at most this many lines (best matches first)")
    p.set_defaults(fn=cmd_list)
    sub.add_parser("names").set_defaults(fn=cmd_names)
    sub.add_parser("recent", help="styles on the user's last boards (never offered again soon)").set_defaults(
        fn=lambda a: print("\n".join(sorted(recent())) or "(none yet)"))
    p = sub.add_parser("show")
    p.add_argument("id")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("board")
    p.add_argument("ids", nargs="+")
    p.add_argument("--out", default="review/styles.jpg")
    p.add_argument("--width", type=int, default=480, help="width of each poster in the board")
    p.set_defaults(fn=cmd_board)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:   # Windows reads, writes and prints in a legacy code page
        import subprocess
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    sys.exit(main())
