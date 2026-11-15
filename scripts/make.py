#!/usr/bin/env python3
"""One call per step: render, check, answer in a few lines (Python 3 standard library; Node 22+ and Chrome for render.mjs).

  python3 tools/make.py stills [--views post,story]   # review stills of the named views (default: the first two)
  python3 tools/make.py draft                         # every view at true size (print views at 150 dpi), all checks
  python3 tools/make.py final                         # export files: true size (or the view's scale), print at its dpi + PDF
  python3 tools/make.py check                         # the checks only, on a fresh render, nothing kept
  python3 tools/make.py layout                        # Studio: every page as a grey wireframe, in spreads (the flatplan)
  python3 tools/make.py stills --views report --pages 1,5   # chosen pages of a multi-page view

Every run writes logs/last-make.txt; a draft writes logs/check-draft-vN.txt. Never print a log into the chat: read its
last lines.

A draft is HELD (exit 3, nothing to show yet) for one fix pass when a hard rule breaks: the template's example left in,
text off the edge or clipped, text over text, text below its minimum size, contrast under 4.5:1 (3:1 for large text),
a fallback or unloaded font, missing glyphs, a dash in the words, a print image under 150 ppi. The next draft delivers
whatever remains, named in plain lines for the user. NOTES never hold: taste (AI-overused fonts and palettes), clichés,
a flat hierarchy, a weak one-second read, words that read as generated. Each is fixed or answered with a reason on the
card (STATE.md: "- **Taste:** <what>: <why>", "- **Cliché:** <what>: <why>").
"""
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
LOGS = ROOT / "logs"
DESIGN = ROOT / "design.html"
STATEF = ROOT / ".make.json"

# Minimum text size by where the view is seen (the eye's size, not the file's): phone = a post seen about 390 px wide;
# screen = shown at its own pixel size; print = points on paper at arm's length; far = a poster read from 2 m or more.
MIN = {"phone": {"text": 11.0, "legal": 9.0}, "screen": {"text": 14.0, "legal": 12.0},
       "print": {"text": 8.0, "legal": 6.0}, "far": {"text": 18.0, "legal": 12.0}}
LEGAL_ROLES = {"legal", "credit", "caption", "footnote", "source", "fine", "folio", "running"}
MARGIN_ROLES = {"folio", "running"}
AI_FONTS_EXTRA = {"playfair-display", "playfair", "inter", "geist", "space-grotesk", "dm-sans", "poppins", "montserrat"}
TAILWIND_BLUES = {"#3b82f6", "#2563eb", "#1d4ed8", "#60a5fa", "#6366f1", "#4f46e5", "#8b5cf6", "#7c3aed", "#0ea5e9"}


def log(line, sink):
    print(line)
    sink.append(line)


def node():
    return shutil.which("node") or "node"


def render(out, views=None, scale=None, pdf=False, thumb=160, contrast=True, print_dpi=150, marks=False, pages=None, wire=False,
           params=None):
    """render.mjs per scale group: screen views at their scale, print views at print_dpi / 96."""
    info = design_views()
    ids = views or [v["id"] for v in info]
    groups = {}
    for v in info:
        if v["id"] not in ids:
            continue
        dpi = (v.get("dpi") or 300) if print_dpi is None else print_dpi
        k = scale or (dpi / 96 if v.get("unit") == "mm" else v.get("scale", 1))
        groups.setdefault(round(k, 4), []).append(v["id"])
    views_out = []
    for k, group in groups.items():
        rp = Path(out) / f"report-{len(views_out)}.json"
        cmd = [node(), str(HERE / "render.mjs"), "--url", str(DESIGN), "--out", str(out), "--views", ",".join(group),
               "--scale", str(k), "--report", str(rp)]
        if thumb:
            cmd += ["--thumb", str(thumb)]
        if pdf:
            cmd += ["--pdf"] + (["--marks"] if marks else [])
        if not contrast:
            cmd += ["--no-contrast"]
        if pages:
            cmd += ["--pages", pages]
        if wire:
            cmd += ["--wire"]
        if params:
            cmd += ["--params", params]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (LOGS / "render.log").open("a", encoding="utf-8").write(r.stdout + r.stderr)
        if r.returncode != 0:
            sys.exit("render failed: " + (r.stderr.strip().splitlines() or ["see logs/render.log"])[-1][:300])
        views_out += json.loads(rp.read_text(encoding="utf-8"))["views"]
        rp.unlink()
    return views_out


_VIEWS = []


def design_views():
    """The views from the DESIGN block, read by Chrome so the page's own code decides (once per run)."""
    if _VIEWS:
        return _VIEWS
    r = subprocess.run([node(), str(HERE / "render.mjs"), "--url", str(DESIGN), "--info"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit("design.html does not load: " + (r.stderr.strip().splitlines() or ["?"])[-1][:300])
    try:
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        sys.exit("design.html: could not read DESIGN.views")
    if not out:
        sys.exit("design.html: the views list is empty")
    _VIEWS.extend(out)
    return _VIEWS


def seen(view, a):
    if a.get("unit") == "mm":
        return view.get("seen") or ("far" if max(view.get("w", 0), view.get("h", 0)) >= 420 else "print")
    return view.get("seen") or ("phone" if view.get("w", 0) <= 1440 else "screen")


def eye_size(t, a, where):
    """The text's size as the eye gets it: px on a phone or screen, pt on paper."""
    if a["unit"] == "mm":
        return t["pt"], "pt"
    if where == "phone":
        return t["px"] * 390 / a["size"][0], "px on a phone"
    return t["px"], "px"


def hexrgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None


def hsl(rgb):
    r, g, b = rgb
    mx, mn = max(rgb), min(rgb)
    l = (mx + mn) / 2
    if mx == mn:
        return 0, 0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    h = ((g - b) / d % 6) if mx == r else ((b - r) / d + 2) if mx == g else ((r - g) / d + 4)
    return h * 60, s, l


def card_reasons():
    st = (ROOT / "STATE.md").read_text(encoding="utf-8") if (ROOT / "STATE.md").exists() else ""
    return {k.lower(): v.lower() for k, v in re.findall(r"\*\*(Taste|Cliché|Cliche|Rule break):\*\*\s*(.+)", st)}, st.lower()


def taste_lines(reports):
    reasons, state = card_reasons()
    answered = lambda word: any(word in v for v in reasons.values())
    out = []
    a = reports[0]
    try:
        sys.path.insert(0, str(HERE))
        import fonts
        common = set(fonts.COMMON) | AI_FONTS_EXTRA
    except Exception:
        common = AI_FONTS_EXTRA
    fams = {r["family"] for r in a["roles"] if r["family"]}
    for f in fams:
        slug = re.sub(r"[^a-z0-9]+", "-", f.lower()).strip("-")
        if slug in common and not answered(slug.replace("-", " ")) and not answered(f.lower()):
            out.append(f"taste: {f} is one of the faces AI designs reach for; a reason on the card (- **Taste:** {f}: why) or another face (fonts.py search \"<tone>\")")
    pal = a.get("palette") or {}
    g = hexrgb(pal.get("ground", "")) if pal.get("ground") else None
    if g:
        h, s, l = hsl(g)
        if 215 <= h <= 290 and s > 0.25 and l < 0.6 and not answered("violet") and not answered("blue ground"):
            out.append("taste: a blue-to-violet ground is the AI-average palette; a reason on the card or a ground from this piece's own world")
        acc = hexrgb(pal.get("accent", "")) if pal.get("accent") else None
        if acc:
            ha, sa, la = hsl(acc)
            if 25 <= h <= 50 and l > 0.86 and s > 0.15 and 5 <= ha <= 28 and sa > 0.4 and not answered("terracotta") and not answered("cream"):
                out.append("taste: cream with terracotta is the 'assistant' look; a reason on the card or another pairing")
    for k, v in pal.items():
        if v.lower() in TAILWIND_BLUES and not answered(v.lower()):
            out.append(f"taste: {k} {v} is a stock framework colour; pick it from the references instead")
    return out


def cliche_lines():
    reasons, state = card_reasons()
    answered = lambda word: any(word in v for v in reasons.values())
    src = DESIGN.read_text(encoding="utf-8")
    style = "\n".join(re.findall(r"(?is)<style>(.*?)</style>", src.split("ENGINE (do not edit)")[0]))
    body = src.split("ENGINE (do not edit)")[0]
    out = []
    if "backdrop-filter" in style and not answered("glass"):
        out.append("cliché: frosted glass panels (backdrop-filter): the tech-template look; name it on the card with its reason, or drop it")
    grads = re.findall(r"linear-gradient\(([^;]+)\)", style)
    for gtxt in grads:
        hexes = [hexrgb(x) for x in re.findall(r"#[0-9a-fA-F]{3,6}\b", gtxt)]
        hues = [hsl(x)[0] for x in hexes if x and hsl(x)[1] > 0.3]
        if len(hues) >= 2 and all(180 <= x <= 320 for x in hues) and not answered("gradient"):
            out.append("cliché: a blue-violet-cyan gradient: says no colour decision was made")
            break
    shadows = len(re.findall(r"box-shadow\s*:", style))
    radii = len(re.findall(r"border-radius\s*:", style))
    if shadows >= 2 and radii >= 2 and not answered("card"):
        out.append("cliché: rounded cards with drop shadows: the floating-UI-card look; ground the content in the page instead")
    if re.search(r"text-shadow\s*:", style) and not answered("text-shadow"):
        out.append("cliché: a text shadow: usually a fix for weak contrast; fix the contrast instead")
    emoji = re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", re.sub(r"(?is)<(script|style)\b.*?</\1>", "", body))
    if emoji and not answered("emoji"):
        out.append(f"cliché: emoji in the design's words ({''.join(dict.fromkeys(emoji))[:6]}): bullets and icons come from the design's own drawing or an icon set")
    return out


def checks(reports):
    """HOLD lines (hard rules) and NOTE lines, per view."""
    views = {v["id"]: v for v in design_views()}
    hold, note = [], []
    for a in reports:
        vid, v = a.get("tag") or a["view"], views.get(a["view"], {})
        where = seen(v, a)
        if a.get("example"):
            hold.append(f"TEMPLATE {vid}: the starter's example section is still there (data-example); delete it and build the card's design")
        for e in a.get("errors") or []:
            hold.append(f"PAGE ERROR {vid}: {e[:160]}")
        for r in a["roles"]:
            if not r["family"]:
                hold.append(f"FONT {vid}: type role '{r['name']}' is the system fallback; set it from fonts.py role or the dealt pairing")
            elif not r["glyphs"]:
                hold.append(f"GLYPHS {vid}: {r['family']} does not set every check string (the language's special letters?): another face or a family with latin-ext")
        texts = a["texts"]
        for t in texts:
            label = f"'{t['text'][:28]}'"
            if not t["loaded"] and t["family"] not in ("Georgia", "Times New Roman"):
                hold.append(f"FONT {vid}: {label} is set in {t['family']}, which did not load")
            role = t.get("role") or ""
            if role == "crop":                              # display type cropped by the edge on purpose (named on the card)
                pass
            elif t["offEdge"]:
                hold.append(f"OFF EDGE {vid}: {label} runs past the edge of the page")
            elif role in MARGIN_ROLES:                      # running heads and folios live in the margin, 5 mm inside the trim
                if not t.get("insideTrimMargin", True):
                    hold.append(f"SAFE {vid}: {label} ({role}) is closer than 5 mm to the trim")
            elif t["outsideSafe"]:
                hold.append(f"SAFE {vid}: {label} sits outside the safe margin")
            if (t["clipped"] or t["overflowing"]) and role != "crop":
                hold.append(f"CLIPPED {vid}: {label} is cut off by its box")
            size, unit = eye_size(t, a, where)
            legal = (t.get("role") or "") in LEGAL_ROLES
            floor = MIN[where]["legal" if legal else "text"]
            if size < floor:
                hold.append(f"SMALL {vid}: {label} is {size:.1f} {unit}; the floor here is {floor:g} ({'legal line' if legal else 'text'}, seen: {where})")
            c = t.get("contrast")
            if c:
                large = (t["px"] * (390 / a["size"][0] if where == "phone" else 1) >= 24) or (t["px"] >= 18.66 and int(float(t["weight"] or 400)) >= 700)
                need = 3.0 if large else 4.5
                if c["median"] < need:
                    hold.append(f"CONTRAST {vid}: {label} {c['median']}:1 against its ground (needs {need}:1)")
                elif c["worst"] < need:
                    note.append(f"contrast {vid}: {label} drops to {c['worst']}:1 over part of its ground (an image or a shape behind it)")
        for i, j in a["touch"]:
            hold.append(f"TEXT OVER TEXT {vid}: '{texts[i]['text'][:22]}' and '{texts[j]['text'][:22]}' overlap")
        for im in a["imgs"]:
            if a["unit"] == "mm" and im["ppi"]:
                if im["ppi"] < 150:
                    hold.append(f"LOW-RES {vid}: {im['src']} prints at {im['ppi']} ppi (150 is the floor, 300 the aim): a larger file, or smaller on the page")
                elif im["ppi"] < 240:
                    note.append(f"resolution {vid}: {im['src']} prints at {im['ppi']} ppi; 300 is the aim for print")
            elif im["natural"][0] and im["natural"][0] < im["shown"][0] * 0.95:
                note.append(f"resolution {vid}: {im['src']} is shown larger than its pixels ({im['natural'][0]} px shown at {im['shown'][0]} px): soft")
        sizes = sorted({round(t["px"], 1) for t in texts}, reverse=True)
        if len(sizes) >= 2 and sizes[0] / sizes[1] < 1.4:
            note.append(f"hierarchy {vid}: the two largest sizes are close ({sizes[0]:.0f} and {sizes[1]:.0f} px): the first read does not lead")
        if texts and (a.get("pages", 1) == 1 or a.get("kind") == "cover"):   # the glance test is for covers and single pieces
            k = 160 / max(a["size"])
            top = max(t["px"] for t in texts) * k
            if top < 7:
                note.append(f"one-second read {vid}: on a 160 px thumbnail the largest words are {top:.1f} px tall: nothing reads at a glance")
    note += pacing(reports, views)
    return list(dict.fromkeys(hold)), list(dict.fromkeys(note))


def pacing(reports, views):
    """Multi-page views: never three pages of one kind in a row (data-kind on each section); a printed booklet needs a
    page count the binding allows."""
    out = []
    by = {}
    for a in reports:
        if a.get("pages", 1) > 1:
            by.setdefault(a["view"], []).append(a)
    for vid, pages in by.items():
        pages.sort(key=lambda a: a.get("page", 1))
        kinds = [a.get("kind") for a in pages]
        if None in kinds:
            out.append(f"pacing {vid}: give every page a data-kind (cover, opener, text, data, image, breather, quote, closer) so the rhythm can be checked")
        for i in range(len(kinds) - 2):
            if kinds[i] and kinds[i] == kinds[i + 1] == kinds[i + 2]:
                out.append(f"pacing {vid}: pages {pages[i]['page']}-{pages[i + 2]['page']} are all '{kinds[i]}': break the run with another kind of page")
        n = pages[0].get("pages", len(pages))
        v = views.get(vid, {})
        if v.get("unit") == "mm" and n > 4 and n % 4:
            out.append(f"binding {vid}: {n} pages; a stapled booklet needs a multiple of 4 ({n + (4 - n % 4)}); perfect binding is fine, ask the printer")
    return out


def words_line():
    r = subprocess.run([sys.executable, str(HERE / "words_check.py"), "--line", str(DESIGN)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip()


def sheet(images, out, title, same_height=False):
    many = len(images) > 4
    """One contact sheet page beside its images, captured by Chrome: every view big, its thumbnail small."""
    out = Path(out)
    page = out.with_suffix(".html")
    cards = "".join(
        f'<figure><img src="{html.escape(os.path.relpath(p, page.parent).replace(os.sep, "/"))}">'
        + (f'<img class="t" src="{html.escape(os.path.relpath(t, page.parent).replace(os.sep, "/"))}">' if t else "")
        + f"<figcaption>{html.escape(lbl)}</figcaption></figure>" for p, t, lbl in images)
    page.write_text(f"""<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title><style>
body{{margin:0;padding:28px;background:#1d1d1d;color:#ddd;font:15px/1.4 system-ui,sans-serif}}
h1{{font-size:16px;font-weight:600;margin:0 0 18px}}
main{{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start}}
figure{{margin:0;display:flex;flex-direction:column;gap:8px}}
figure img{{max-height:{380 if many else 620}px;max-width:{460 if many else 720}px;outline:1px solid #444}}
figure img.t{{max-height:160px;max-width:160px;outline:none}}
figcaption{{color:#aaa}}{"figure img:not(.t){height:620px;width:auto;max-width:none}" if same_height else ""}</style><h1>{html.escape(title)}</h1><main>{cards}</main>""", encoding="utf-8")
    r = subprocess.run([node(), str(HERE / "render.mjs"), "--page", str(page), "--shot", str(out), "--width", "1500"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None
    return out


def next_n(prefix, folder):
    folder.mkdir(parents=True, exist_ok=True)
    ns = [int(m.group(1)) for p in folder.iterdir() if (m := re.fullmatch(rf"{prefix}-v(\d+)", p.name))]
    return max(ns, default=0) + 1


def sha():
    return hashlib.sha1(DESIGN.read_bytes()).hexdigest()[:12]


def load_state():
    try:
        return json.loads(STATEF.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(s):
    STATEF.write_text(json.dumps(s, indent=1), encoding="utf-8")


def title_slug():
    m = re.search(r"title:\s*'([^']+)'", DESIGN.read_text(encoding="utf-8"))
    t = (m.group(1) if m else ROOT.name)
    return re.sub(r"[^A-Za-z0-9ÇĞİÖŞÜçğıöşü]+", "-", t).strip("-") or ROOT.name


def show(path, sink, what="show the user"):
    log(f"{what}: {Path(path).resolve()} (Claude Code: SendUserFile, display 'render')", sink)


def cmd_stills(a, sink):
    views = a.views.split(",") if a.views else [v["id"] for v in design_views()][:2]
    n = next_n("stills", ROOT / "review")
    out = ROOT / "review" / f"stills-v{n}"
    under = ""
    if a.underlay:                                   # the user's design under the rebuild, at the given opacity
        from urllib.parse import quote
        under = f"underlay={quote(Path(a.underlay).resolve().as_uri())}&uo={a.uo}"
    reps = render(out, views, pages=a.pages, params=under, contrast=not a.underlay)
    hold, note = checks(reps)
    sh = sheet([(r["file"], r.get("thumb") if r.get("pages", 1) == 1 or r.get("kind") == "cover" else None,
                f"{r.get('tag') or r['view']} · {r['size'][0]}×{r['size'][1]}") for r in reps],
               ROOT / "review" / f"stills-v{n}.jpg", f"{title_slug()} · stills v{n}")
    log(f"stills v{n}: {len(reps)} view(s) -> {out}", sink)
    for line in hold + note:
        log("  " + line, sink)
    for line in taste_lines(reps) + cliche_lines():
        log("  " + line, sink)
    if sh:
        log(f"sheet: {sh}  (read it yourself first; then send it)", sink)


def cmd_draft(a, sink):
    st = load_state()
    n = next_n("draft", ROOT / "renders")
    if st.get("held") and st.get("draft"):
        n = st["draft"]                                      # a held draft is redone under its own number
    elif n > 1:
        notes = ROOT / "notes" / f"round-{n - 1}.md"
        if not notes.exists() and not a.force:
            sys.exit(f"draft v{n}: the user's notes on draft v{n - 1} first, verbatim, in notes/round-{n - 1}.md "
                     "(it starts with '## Keep'); --force only for a technical re-render with no notes")
        if notes.exists() and "## Keep" not in notes.read_text(encoding="utf-8"):
            sys.exit(f"notes/round-{n - 1}.md needs its '## Keep' list first (what the user praised, or 'none')")
    code, wline = words_line()
    if code != 0:
        log(wline, sink)
        sys.exit("STOP: a dash in the design's words; replace it (comma, full stop, colon, line break), then draft again")
    out = ROOT / "renders" / f"draft-v{n}"
    if out.exists():
        shutil.rmtree(out)
    reps = render(out, None, pdf=True, print_dpi=150)
    hold, note = checks(reps)
    taste = taste_lines(reps) + cliche_lines()
    hold += closeness(reps)
    if wline:
        note.append(wline)
    second = bool(st.get("held") and st.get("draft") == n)
    sh = sheet([(r["file"], r.get("thumb") if r.get("pages", 1) == 1 or r.get("kind") == "cover" else None,
                f"{r.get('tag') or r['view']} · {r['size'][0]}×{r['size'][1]}") for r in reps],
               ROOT / "review" / f"draft-v{n}.jpg", f"{title_slug()} · draft v{n}")
    lines = [f"draft v{n}: {len(reps)} view(s) -> {out}"]
    if hold and not second:
        lines.append(f"HELD for one fix pass ({len(hold)}): fix exactly these, then make.py draft again; nothing goes to the user yet")
        lines += ["  " + h for h in hold]
    elif hold:
        lines.append(f"delivered with {len(hold)} known issue(s) left after the fix pass: tell the user each in one plain line (what, where, why)")
        lines += ["  known: " + h for h in hold]
    lines += ["  note: " + x for x in note + taste]
    for line in lines:
        log(line, sink)
    (LOGS / f"check-draft-v{n}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    save_state({"draft": n, "held": bool(hold) and not second, "sha": sha(), "time": time.time()})
    try:                                             # the memory the overlap check reads (ideas.md §4)
        sys.path.insert(0, str(HERE))
        import dice
        dice.remember(str(ROOT))
    except Exception:
        pass
    if not hold or second:
        if sh:
            show(sh, sink)
        for r in reps:
            log(f"  {r.get('tag') or r['view']}: {Path(r['file']).resolve()}" + (f" · pdf {Path(r['pdf']).resolve()}" if r.get("pdf") else ""), sink)
        log("then: the independent viewer in the background (templates/REVIEWER.md), and the delivery question", sink)


def cmd_final(a, sink):
    st = load_state()
    if not st.get("draft") or st.get("held"):
        sys.exit("final: a delivered draft first (make.py draft), and the user's OK on it")
    if st.get("sha") != sha() and not a.force:
        sys.exit("final: design.html changed since the last draft; draft again so the user sees what ships (--force only for a purely technical change)")
    code, wline = words_line()
    if code != 0:
        sys.exit("STOP: a dash in the design's words")
    tmp = ROOT / "renders" / "final"
    if tmp.exists():
        shutil.rmtree(tmp)
    reps = render(tmp, None, pdf=True, thumb=0, print_dpi=None, marks=True)
    hold, note = checks(reps)
    exp = ROOT / "exports"
    exp.mkdir(exist_ok=True)
    slug = title_slug()
    shipped, press_lines, proofs = [], [], []
    views = {v["id"]: v for v in design_views()}
    for r in reps:
        ext = Path(r["file"]).suffix
        dst = exp / f"{slug}-{r.get('tag') or r['view']}{ext}"
        shutil.copyfile(r["file"], dst)
        shipped.append(dst)
        if r.get("pdf"):
            pdst = exp / f"{slug}-{r['view']}.pdf"
            shutil.copyfile(r["pdf"], pdst)
            shipped.append(pdst)
        if r.get("pdfMarks") and not a.no_press:
            got = press(r, views[r["view"]], exp / f"{slug}-{r['view']}-press.pdf", a)
            press_lines += got[0]
            if got[1]:
                shipped.append(got[1])
                proofs.append((r["file"], got[2], r["view"]))
    credits = credits_file(exp, slug)
    log(f"final: {len(shipped)} file(s) in {exp.resolve()}", sink)
    for p in shipped:
        log(f"  {p.resolve()}", sink)
    for line in press_lines:
        log(line, sink)
    if proofs:
        sh = sheet([x for f, p, vid in proofs for x in ((f, None, f"{vid} · screen (RGB)"), (p, None, f"{vid} · press proof (CMYK, as ink on paper)"))],
                   ROOT / "review" / "proof.jpg", f"{slug} · screen against press proof", same_height=True)
        if sh:
            show(sh, sink, "show the user the soft proof")
    if credits:
        log(f"credits: {credits.resolve()} (paste into the post, the description or the printer's notes; never on the design unless asked)", sink)
    for h in hold:
        log("  CHECK " + h, sink)


def press(r, v, out, a):
    """The press PDF of one print view (print.py: CMYK, PDF/X-4, trim and bleed boxes, crop marks), its preflight and
    its soft proof. Without Ghostscript: one line saying what the user gets instead."""
    sys.path.insert(0, str(HERE))
    import print as pr
    if not pr.gs_path():
        return [f"press {r['view']}: no Ghostscript, so no CMYK press file; the RGB PDF at trim + bleed is the print file "
                "(digital printers take it as is; for offset, the printer converts it: ask for their profile). "
                "Ghostscript is free: python3 tools/print.py where"], None, None
    trim, bleed = f"{v['w']:g}x{v['h']:g}", str(v.get("bleed", 3))
    base = [sys.executable, str(HERE / "print.py")]
    prof = (["--profile", a.profile] if a.profile else []) + (["--condition", a.condition] if a.condition else [])
    r1 = subprocess.run(base + ["press", r["pdfMarks"], "--out", str(out), "--trim", trim, "--bleed", bleed, "--slug", "10",
                                "--title", f"{title_slug()} {r['view']}"] + prof, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r1.returncode != 0:
        return [f"press {r['view']}: failed: {(r1.stderr or r1.stdout).strip()[-300:]}"], None, None
    r2 = subprocess.run(base + ["preflight", str(out), "--trim", trim, "--bleed", bleed, "--slug", "10"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    proof = ROOT / "review" / f"proof-{r['view']}.png"
    subprocess.run(base + ["proof", str(out), "--out", str(proof), "--dpi", "100"], capture_output=True, text=True)
    lines = ["  " + r1.stdout.strip()] + ["  " + x for x in r2.stdout.strip().splitlines()]
    return lines, out, proof if proof.exists() else None


def credits_file(exp, slug):
    import csv
    lic = ROOT / "LICENSES.csv"
    if not lic.exists():
        return None
    src = DESIGN.read_text(encoding="utf-8")
    rows = [r for r in csv.DictReader(lic.open(encoding="utf-8")) if r.get("file") and not r["file"].startswith("font:")
            and (Path(r["file"]).name in src or (r.get("used_in") or "").strip())]   # open fonts owe no public credit
    if not rows:
        return None
    out = exp / f"{slug}-credits.txt"
    out.write_text("\n".join(r.get("attribution_text") or f"{r['title']} · {r['author']} · {r['licence']}" for r in rows) + "\n",
                   encoding="utf-8")
    return out


def tiny(path):
    """16x16 grey bytes of an image (ffmpeg); None without ffmpeg."""
    if not shutil.which("ffmpeg"):
        return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=16:16,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return raw if len(raw) == 256 else None


def structure(a, b):
    """Pearson correlation of two 16x16 grey thumbnails: 1 = the same arrangement of masses."""
    ma, mb = sum(a) / 256, sum(b) / 256
    da, db = [x - ma for x in a], [y - mb for y in b]
    na, nb = sum(x * x for x in da) ** 0.5, sum(y * y for y in db) ** 0.5
    return sum(x * y for x, y in zip(da, db)) / (na * nb) if na and nb else 0.0


def closeness(reports):
    """The two routes that start from someone else's work: a draft that is the reference again (like-this-one route:
    STATE.md '- **Reference:** refs/<file>'), or that repeats a saved format's words (FORMAT.md)."""
    out = []
    st = (ROOT / "STATE.md").read_text(encoding="utf-8") if (ROOT / "STATE.md").exists() else ""
    for ref in re.findall(r"^- \*\*Reference:\*\*\s*(\S+\.(?:png|jpe?g|webp))", st, re.M | re.I):
        rp = ROOT / ref
        a = tiny(rp) if rp.exists() else None
        if not a:
            continue
        for r in reports:
            b = tiny(r["file"])
            if b:
                same = structure(a, b)                       # where the light and dark masses sit, not how bright the page is
                if same > 0.85:
                    out.append(f"TOO CLOSE {r.get('tag') or r['view']}: {same:.0%} like {ref}; the route takes its grammar (grid, scale, "
                               "palette logic), never its layout: move the masses, change the crop, re-set the type")
    fref = ROOT / "research" / "format-reference.html"
    if fref.exists() and (ROOT / "FORMAT.md").exists():
        sys.path.insert(0, str(HERE))
        import words_check
        mine = {t.strip().lower() for _, t in words_check.html_words(str(DESIGN)) if len(t.strip()) > 12}
        theirs = {t.strip().lower() for _, t in words_check.html_words(str(fref)) if len(t.strip()) > 12}
        if mine and len(mine & theirs) / len(mine) > 0.3:
            out.append(f"FORMAT COPY: {len(mine & theirs)} of {len(mine)} lines are the source design's words again; a format "
                       "repeats the language, never the content")
        keep = (ROOT / "FORMAT.md").read_text(encoding="utf-8")
        src_imgs = set(re.findall(r'src="([^"]+)"', fref.read_text(encoding="utf-8")))
        for im in set(re.findall(r'src="([^"]+)"', DESIGN.read_text(encoding="utf-8"))) & src_imgs:
            if im not in keep:
                out.append(f"FORMAT COPY: {im} is the source design's image again and FORMAT.md does not keep it")
    return out


def cmd_layout(a, sink):
    """The flatplan: every page of every multi-page view as a grey wireframe (images as hatched boxes, colour off), in
    reading spreads: the cover alone on the right, then facing pages. For pacing and flow, before any page is finished."""
    import html as H
    n = next_n("layout", ROOT / "review")
    out = ROOT / "review" / f"layout-v{n}"
    multi = [v["id"] for v in design_views() if v.get("pages", 1) > 1] or [v["id"] for v in design_views()]
    reps = render(out, multi, scale=0.5, thumb=0, contrast=False, wire=True, print_dpi=None)
    hold, note = checks(reps)
    rows = []
    for vid in multi:
        pages = sorted([r for r in reps if r["view"] == vid], key=lambda r: r.get("page", 1))
        facing = pages and pages[0]["unit"] == "mm" and len(pages) > 2
        groups = ([[None, pages[0]]] + [pages[i:i + 2] for i in range(1, len(pages), 2)]) if facing else [[p] for p in pages]
        cells = []
        for g in groups:
            imgs = "".join('<div class="pg empty"></div>' if r is None else
                           f'<div class="pg"><img src="{H.escape(os.path.relpath(r["file"], ROOT / "review").replace(os.sep, "/"))}">'
                           f'<span>{r.get("page", 1)} · {H.escape(r.get("kind") or "?")}</span></div>' for r in g)
            cells.append(f'<div class="spread">{imgs}</div>')
        rows.append(f"<h2>{H.escape(vid)} · {len(pages)} pages</h2><div class='row'>{''.join(cells)}</div>")
    page = ROOT / "review" / f"layout-v{n}.html"
    page.write_text(f"""<!doctype html><meta charset=utf-8><style>
body{{margin:0;padding:24px;background:#1d1d1d;color:#ddd;font:14px/1.4 system-ui,sans-serif}}
h2{{font-size:15px;font-weight:600;margin:18px 0 10px}}.row{{display:flex;flex-wrap:wrap;gap:22px}}
.spread{{display:flex;gap:2px}}.pg{{position:relative}}.pg img{{height:230px;display:block;background:#fff}}
.pg.empty{{width:163px}}.pg span{{position:absolute;left:6px;bottom:6px;background:#000c;color:#fff;font-size:12px;padding:2px 6px}}
</style><h1 style="font-size:16px;margin:0">{H.escape(title_slug())} · flatplan v{n}</h1>{''.join(rows)}""", encoding="utf-8")
    r = subprocess.run([node(), str(HERE / "render.mjs"), "--page", str(page), "--shot", str(page.with_suffix(".jpg")), "--width", "1500"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log(f"layout v{n}: {len(reps)} page(s) as wireframes -> {out}", sink)
    for line in [h for h in hold if not h.startswith(("CONTRAST", "TEMPLATE"))] + note:
        log("  " + line, sink)
    if r.returncode == 0:
        show(page.with_suffix(".jpg"), sink)


def cmd_check(a, sink):
    tmp = ROOT / "renders" / "_check"
    reps = render(tmp, None)
    hold, note = checks(reps)
    for line in hold + note + taste_lines(reps) + cliche_lines():
        log(line, sink)
    if not hold and not note:
        log("check: nothing found", sink)
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["stills", "draft", "final", "check", "layout"])
    ap.add_argument("--views")
    ap.add_argument("--pages", help="stills: which pages of a multi-page view, e.g. 1,5")
    ap.add_argument("--underlay", help="stills: the user's own design laid under the rebuild (resize route), never in a draft")
    ap.add_argument("--uo", default="0.45", help="stills: the underlay's opacity")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-press", action="store_true", help="final: skip the CMYK press PDF")
    ap.add_argument("--profile", help="final: the printer's CMYK .icc for the press PDF")
    ap.add_argument("--condition", help="final: its output condition (FOGRA39, FOGRA51, GRACoL2006_Coated1v2 …)")
    a = ap.parse_args()
    if not DESIGN.exists():
        sys.exit("no design.html here: run make.py inside the design's folder")
    LOGS.mkdir(exist_ok=True)
    sink = []
    try:
        {"stills": cmd_stills, "draft": cmd_draft, "final": cmd_final, "check": cmd_check, "layout": cmd_layout}[a.cmd](a, sink)
    finally:
        (LOGS / "last-make.txt").write_text("\n".join(sink) + "\n", encoding="utf-8")
    if a.cmd == "draft" and load_state().get("held"):
        sys.exit(3)


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    main()
