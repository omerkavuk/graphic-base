#!/usr/bin/env python3
"""Saved formats: keep a finished design's language and start the next piece from it (Python 3 stdlib).

  python3 tools/formats.py save "<format name>" [--keep "assets/logo.svg"] [--keep "the closing line's position"]
  python3 tools/formats.py list
  python3 tools/formats.py show "<format name>"
  python3 KIT/scripts/init_design.py <short-name> --quick --format "<format name>"     # a new piece in that language

A format is the design's **language**, never its content: the look, the palette's logic, the grid, the hierarchy, the
type, the image treatment, the texture, the signature, how the sizes adapt. The next piece speaks it about its own
subject: its idea, words, images and data are new. It starts from the fresh template with FORMAT.md beside it and the
source's code only as research/format-reference.html, to look up how a technique was built. `--keep` names what
returns on purpose in every piece (a logo file, a fixed element): only those may repeat; `make.py draft` holds a draft
whose words repeat the source's (FORMAT COPY) and names reused images that FORMAT.md does not keep.

Formats live in ~/.graphic-base/formats (GRAPHIC_BASE_FORMATS overrides), never in the kit or a design folder.
"""
import argparse
import datetime
import os
import re
import shutil
import sys

ROOT = os.environ.get("GRAPHIC_BASE_FORMATS") or os.path.join(os.path.expanduser("~"), ".graphic-base", "formats")
CARD = ("Fit", "Structure", "Look", "Palette", "Grid", "Hierarchy", "Type", "Charts", "Image route", "Texture and finish",
        "Signature", "Views", "Taste", "Cliché", "Rule break")
STATE_LINES = ("Purpose", "Approach", "Piece and sizes", "Piece", "Views", "Look · mood", "Type", "Images")


def slug(name):
    s = re.sub(r"[^\w-]+", "-", name.strip().lower(), flags=re.UNICODE).strip("-")
    if not s:
        sys.exit("give the format a name")
    return s


def lines_of(text, labels):
    out = []
    for line in text.splitlines():
        m = re.match(r"- \*\*([^:*]+):\*\*\s*(.*)", line)
        if m and m.group(1).strip() in labels and not m.group(2).strip().startswith("<"):
            out.append(line)
    return out


def cmd_save(a):
    src = os.path.abspath(".")
    if not os.path.isfile(os.path.join(src, "STATE.md")) or not os.path.isfile(os.path.join(src, "design.html")):
        sys.exit("run save inside the design's folder (STATE.md and design.html)")
    dst = os.path.join(ROOT, slug(a.name))
    if os.path.exists(dst) and not a.force:
        sys.exit(f"format exists: {dst} (--force to replace)")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in ("design.html", "STATE.md", "ROADMAP.md"):
        if os.path.isfile(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, "source-" + f))
    for k in a.keep or []:                                   # kept files travel with the format
        if os.path.isfile(os.path.join(src, k)):
            os.makedirs(os.path.dirname(os.path.join(dst, "keep", k)), exist_ok=True)
            shutil.copy2(os.path.join(src, k), os.path.join(dst, "keep", k))
    state = open(os.path.join(src, "STATE.md"), encoding="utf-8").read()
    card = lines_of(state, CARD)
    base = lines_of(state, STATE_LINES)
    if not card:
        sys.exit("the design card in STATE.md is empty: a format is saved from a finished design")
    mode = "studio" if "(Studio mode)" in state else "quick"
    title = re.search(r"title:\s*'([^']+)'", open(os.path.join(src, "design.html"), encoding="utf-8").read())
    body = [f"# Format: {a.name}", "",
            f"From: {title.group(1) if title else os.path.basename(src)} · saved {datetime.date.today().isoformat()} · mode {mode}", "",
            "Write each line again for the new subject and say how it meets it (\"palette logic: <the rule>, here <how>\").",
            "The words, the idea, every image and every number are new; only what Keep names returns.", "",
            "## The piece", *base, "", "## The language (the source's design card)", *card, "",
            "## Keep (returns in every piece, on purpose)", *([f"- {k}" for k in a.keep or []] or ["- nothing"]), ""]
    open(os.path.join(dst, "FORMAT.md"), "w", encoding="utf-8").write("\n".join(body))
    print(f"format saved: {dst} ({len(card)} card lines, keep: {', '.join(a.keep or []) or 'nothing'})")


def cmd_list(a):
    if not os.path.isdir(ROOT) or not os.listdir(ROOT):
        print("no formats yet")
        return
    for name in sorted(os.listdir(ROOT)):
        f = os.path.join(ROOT, name, "FORMAT.md")
        if os.path.isfile(f):
            head = open(f, encoding="utf-8").read().splitlines()
            print(f"{name} · {head[2] if len(head) > 2 else ''}")


def cmd_show(a):
    f = os.path.join(ROOT, slug(a.name), "FORMAT.md")
    if not os.path.isfile(f):
        sys.exit(f"no format {a.name} (formats.py list)")
    print(open(f, encoding="utf-8").read())


def use(name, dest):
    """Called by init_design.py --format: FORMAT.md into the new design, the source's code as a reference, kept files."""
    src = os.path.join(ROOT, slug(name))
    if not os.path.isfile(os.path.join(src, "FORMAT.md")):
        sys.exit(f"no format {name} (formats.py list)")
    shutil.copy2(os.path.join(src, "FORMAT.md"), os.path.join(dest, "FORMAT.md"))
    os.makedirs(os.path.join(dest, "research"), exist_ok=True)
    shutil.copy2(os.path.join(src, "source-design.html"), os.path.join(dest, "research", "format-reference.html"))
    keep = os.path.join(src, "keep")
    if os.path.isdir(keep):
        for here, _, files in os.walk(keep):
            for f in files:
                rel = os.path.relpath(os.path.join(here, f), keep)
                os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
                shutil.copy2(os.path.join(here, f), os.path.join(dest, rel))
    return src


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("save")
    p.add_argument("name")
    p.add_argument("--keep", action="append", help="a file or element that returns in every piece, on purpose")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_save)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("show")
    p.add_argument("name")
    p.set_defaults(fn=cmd_show)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        import subprocess
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    main()
