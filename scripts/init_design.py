#!/usr/bin/env python3
"""Make a design's project folder (Python 3 standard library).

  python3 KIT/scripts/init_design.py <short-name> --quick --designs-folder Designs
  python3 KIT/scripts/init_design.py <short-name> --studio --designs-folder Designs
  python3 KIT/scripts/init_design.py <design-folder> --update-tools       # a design begun with an older kit gets the new tools

Where it goes: a chat whose folder already holds only designs (or is the designs folder) makes it right there;
otherwise inside <designs folder>/ under the chat's folder. A short name is lowercase ASCII with hyphens. It never
makes a design inside a design, and never steps into one that exists: EXISTS (made earlier) or IN USE (its files
changed in the last 15 minutes: another chat may be working there); then ask the user.

The folder: design.html · STATE.md · Studio also ROADMAP.md, COPY.md, research/facts.md · tools/ (the kit's scripts) · refs/ (the user's references) · assets/
(fetched or supplied files) · research/ · review/ · renders/ · exports/ (what is delivered) · notes/ · LICENSES.csv ·
a local git history for silent snapshots (nothing is uploaded).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
TOOLS = ["make.py", "render.mjs", "asset_search.py", "fonts.py", "keys.py", "snapshot.py", "words_check.py",
         "deal.py", "dice.py", "type_deal.py", "brief.py", "styles.py", "direction.py", "type_refs.py",
         "print.py", "formats.py", "guard.py", "sparks.json", "seeds.json"]
DATA = [("references", "type-library.json"), ("templates", "type-specimen.html")]
FIELDS = "file,title,author,source_url,licence,licence_url,attribution_text,modifications,downloaded_at,used_in,notes\n"
GITIGNORE = "renders/\nreview/*.jpg\nreview/*.png\nresearch/.cache/\nresearch/**/thumbs/\nexports/\nassets/\nfonts/\n.env\n*.part\nlogs/\n"


def is_design(d):
    return (d / "STATE.md").exists() and (d / "tools" / "make.py").exists()


def recently_changed(d, minutes=15):
    cutoff = time.time() - minutes * 60
    for p in d.rglob("*"):
        if ".git" in p.parts or "research" in p.parts:
            continue
        try:
            if p.is_file() and p.stat().st_mtime > cutoff:
                return True
        except OSError:
            pass
    return False


def copy_tools(dest):
    (dest / "tools").mkdir(exist_ok=True)
    for t in TOOLS:
        src = KIT / "scripts" / t
        if src.exists():
            shutil.copy2(src, dest / "tools" / t)
    for folder, name in DATA:
        if (KIT / folder / name).exists():
            shutil.copy2(KIT / folder / name, dest / "tools" / name)
    import json                                      # the style index, pointing at the kit's recipes
    idx = json.loads((KIT / "styles" / "index.json").read_text(encoding="utf-8"))
    idx["dir"] = str(KIT / "styles")
    (dest / "tools" / "styles-index.json").write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")


def where(name, designs_folder):
    cwd = Path.cwd()
    if is_design(cwd):
        sys.exit(f"STOP: this chat is inside a design ({cwd.name}). Ask the user: a new design beside it, in "
                 f"{cwd.parent}? Never a design inside a design.")
    kids = [p for p in cwd.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if cwd.name.lower() == designs_folder.lower() or (kids and all(is_design(k) for k in kids)):
        return cwd / name
    return cwd / designs_folder / name


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--studio", action="store_true")
    ap.add_argument("--designs-folder", default="Designs", help="the folder that holds the designs (default Designs; the user's word for it when they prefer)")
    ap.add_argument("--update-tools", action="store_true")
    ap.add_argument("--format", help="start from a saved format (formats.py list)")
    a = ap.parse_args()

    if a.update_tools:
        d = Path(a.name).resolve()
        if not is_design(d):
            sys.exit(f"{d} is not a design folder (no STATE.md and tools/make.py)")
        copy_tools(d)
        mark = "<!-- ============================== ENGINE (do not edit) ============================== -->"
        page, kit_page = d / "design.html", (KIT / "templates" / "design.html").read_text(encoding="utf-8")
        if page.exists() and mark in page.read_text(encoding="utf-8"):     # the engine block is the kit's, never the user's
            mine = page.read_text(encoding="utf-8")
            new = mine.split(mark)[0] + mark + kit_page.split(mark)[1]
            if new != mine:
                page.write_text(new, encoding="utf-8")
                print("engine in design.html brought up to the kit's version")
        print(f"tools refreshed in {d / 'tools'}")
        return

    name = re.sub(r"[^a-z0-9]+", "-", a.name.lower().translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))).strip("-")
    if not name:
        sys.exit("give a short name (letters, digits, hyphens)")
    dest = where(name, a.designs_folder)
    if dest.exists():
        state = "IN USE" if recently_changed(dest) else "EXISTS"
        sys.exit(f"{state}: {dest} is already there. Ask the user: continue that design, or a new name?")
    mode = "studio" if a.studio else "quick"
    dest.mkdir(parents=True)
    for sub in ("refs", "assets", "research", "review", "renders", "exports", "notes", "logs"):
        (dest / sub).mkdir()
    copy_tools(dest)
    shutil.copy2(KIT / "templates" / "design.html", dest / "design.html")
    if mode == "studio":
        for name in ("ROADMAP.md", "COPY.md"):
            shutil.copy2(KIT / "templates" / name, dest / name)
        (dest / "research" / "facts.md").write_text(
            "# Facts\n\n| Claim or number | Source | Year | Link |\n|---|---|---|---|\n", encoding="utf-8")
    shutil.copy2(KIT / "templates" / ("STATE.md" if mode == "quick" else "STATE-studio.md"), dest / "STATE.md")
    s = (dest / "STATE.md").read_text(encoding="utf-8").replace("<kit path>", str(KIT).replace("\\", "/"))
    (dest / "STATE.md").write_text(s, encoding="utf-8")
    (dest / "LICENSES.csv").write_text(FIELDS, encoding="utf-8")
    if a.format:
        sys.path.insert(0, str(KIT / "scripts"))
        import formats
        formats.use(a.format, str(dest))
        st = (dest / "STATE.md").read_text(encoding="utf-8")
        (dest / "STATE.md").write_text(st.replace("- **Purpose:**", f"- **Format:** {a.format} (FORMAT.md; the source's code: research/format-reference.html)\n- **Purpose:**", 1), encoding="utf-8")
    (dest / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    if shutil.which("git"):
        subprocess.run(["git", "init", "-q"], cwd=dest)
        subprocess.run([sys.executable, str(dest / "tools" / "snapshot.py"), "start"],
                       cwd=dest, capture_output=True)
    print(f"made {mode} design: {dest}")
    print(f"next: cd \"{dest}\" · tell the user where it is, in words they can follow, then the path")


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    main()
