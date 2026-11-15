#!/usr/bin/env python3
"""The brief for a helper: the task, plus the kit's rules for that kind of task, quoted from the references as they
stand today (Python 3 stdlib). A helper starts cold and reads nothing on its own; what is not in its brief does not
exist for it, so the rules travel inside the brief.

  python3 tools/brief.py predict --task "<the user's first message, quoted>" --out logs/brief-predict.md
  python3 tools/brief.py overlap --task "<the user's first message, quoted>" --out logs/brief-overlap.md   # also writes research/past-designs.md
  python3 tools/brief.py review --task "draft v2 of <one line>" --out logs/brief-review.md
  python3 tools/brief.py sourcing --task "…" --writes "research/<x>/*" --reads "STATE.md" --done "…"
  python3 tools/brief.py list
  python3 tools/brief.py wait research/predict.md                     # wait for a file another helper writes

Pass the whole file as the helper's prompt (Claude Code: the Agent tool, with the model it prints). Use --out, not >:
PowerShell 5.1's > writes UTF-16.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_kit():
    """The kit this script came from, or, for the copy in a design's tools/, the kit its STATE.md names."""
    here = os.path.dirname(HERE)
    if os.path.isdir(os.path.join(here, "references")):
        return here
    state = os.path.join(here, "STATE.md")
    if os.path.isfile(state):
        import re
        m = re.search(r"Kit:\s*(\S+)", open(state, encoding="utf-8").read())
        if m and os.path.isdir(os.path.join(m.group(1), "references")):
            return m.group(1)
    if os.environ.get("GRAPHIC_BASE_KIT"):
        return os.environ["GRAPHIC_BASE_KIT"]
    default = os.path.join(os.path.expanduser("~"), ".claude", "skills", "graphic-base")
    if os.path.isdir(os.path.join(default, "references")):
        return default
    sys.exit("brief: the kit is not found; set GRAPHIC_BASE_KIT to the kit folder")


KIT = find_kit()


def design_folder():
    for d in (os.getcwd(), os.path.dirname(HERE)):
        if os.path.isfile(os.path.join(d, "STATE.md")):
            return d
    return None


PREDICT = ("references/ideas.md", "**The prediction test (independent).**", "**The overlap check (independent).**")
OVERLAP = ("references/ideas.md", "**The overlap check (independent).**", "**After the check.**")
SOURCES = ("references/sources.md", "## 1. Which need, which source", "")
NEVER = ("references/sources.md", "## 7. What is never used", "")
CLICHES = ("references/craft.md", "## 6. AI-overused choices and clichés", "")
HIER = ("references/craft.md", "## 2. Hierarchy and the first read", "")

KINDS = {
    "predict": ("the prediction test: the designs the user's first message makes anyone expect, five lines, from that message alone", [PREDICT], "sonnet", "low"),
    "overlap": ("the overlap check: each candidate idea against the expected designs and this user's own designs, judged by someone who did not write them", [OVERLAP], "sonnet", "low"),
    "review": ("the independent viewer: a delivered draft, judged cold", [HIER, CLICHES], "inherit", ""),
    "sourcing": ("finding open material and logging its licence", [SOURCES, NEVER], "sonnet", "medium"),
}
MARK = "<!-- graphic-base brief: {} -->"
DEFAULTS = {
    "predict": {"writes": "research/predict.md",
                "reads": "nothing: the user's first message is quoted in the task, and it is all you get",
                "done": "research/predict.md holds five lines, one expected design each: its subject, key image, layout "
                        "and look"},
    "overlap": {"writes": "research/overlap.md",
                "reads": "research/candidates.md (the ideas to judge), research/predict.md (the designs anyone would "
                         "expect; not there yet: python3 tools/brief.py wait research/predict.md), research/past-designs.md "
                         "(this user's own designs)",
                "done": "research/overlap.md holds one line per candidate: its number, then CLEAR, SHARES (one element "
                        "repeats: which, and with what) or OVERLAP (the idea itself repeats: with what); a prediction by "
                        "its number, a design by its title"},
    "review": {"writes": "review/critique-vN.md",
               "reads": "renders/draft-vN/*.png, renders/draft-vN/*-thumb.jpg, review/draft-vN.jpg, logs/check-draft-vN.txt; "
                        "NOT design.html, STATE.md, notes/ or the chat",
               "done": "review/critique-vN.md holds the three biggest problems and the verdict lines"},
}
SHARED = ("STATE.md", "design.html", "LICENSES.csv")
VERDICT = ("End your report with these lines, exactly:\nVerdict: APPROVE | FIX | UNVERIFIABLE\nRed items: none, or one "
           "\"- \" line each (broken, must not reach a final)\nPolish: what would make it better (never a reason for "
           "another round)\nEvidence: the files you looked at")


def piece(rel, start, stop):
    lines = open(os.path.join(KIT, rel), encoding="utf-8").read().splitlines()
    at = next((i for i, l in enumerate(lines) if l.startswith(start)), None)
    if at is None:
        raise SystemExit(f"brief: '{start[:40]}' is no longer in {rel}; update brief.py")
    level = len(start) - len(start.lstrip("#")) if start.startswith("#") else 0
    out = [lines[at]]
    for l in lines[at + 1:]:
        if stop and l.startswith(stop):
            break
        if not stop and level and l.startswith("#") and len(l) - len(l.lstrip("#")) <= level:
            break
        out.append(l)
    return "\n".join(out).strip()


def wait(path, most):
    import time
    end = time.time() + most
    while time.time() < end:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            print(f"{path} is there")
            return 0
        time.sleep(3)
    print(f"{path} is not there after {most:g} s: go on without it and say so in the report")
    return 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "wait":
        ap = argparse.ArgumentParser()
        ap.add_argument("cmd")
        ap.add_argument("file")
        ap.add_argument("--max", type=float, default=90)
        a = ap.parse_args()
        return wait(a.file, a.max)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", help="list, or one of: " + ", ".join(KINDS))
    ap.add_argument("--task")
    ap.add_argument("--writes")
    ap.add_argument("--reads")
    ap.add_argument("--done")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.kind == "list":
        for k, (what, _, model, effort) in KINDS.items():
            print(f"{k:<9} {model + (' ' + effort if effort else ''):<12} {what}")
        return 0
    if a.kind not in KINDS:
        sys.exit(f"brief: unknown kind {a.kind} (brief.py list)")
    for k, v in DEFAULTS.get(a.kind, {}).items():
        if not getattr(a, k):
            setattr(a, k, v)
    missing = [f"--{k}" for k in ("task", "writes", "reads", "done") if not getattr(a, k)]
    if missing:
        sys.exit("brief: " + ", ".join(missing) + " missing")
    shared = [w for w in a.writes.split(",") if w.strip() in SHARED]
    if shared:
        sys.exit(f"brief: {', '.join(shared)} belong to the main chat")
    folder = design_folder()
    if a.kind in ("predict", "overlap") and not folder:
        sys.exit("brief: run it in the design's folder (after init_design.py), so the helper writes into it")
    if a.kind == "overlap":
        if not os.path.isfile(os.path.join(folder, "research", "candidates.md")):
            sys.exit("brief: write the candidates first: research/candidates.md, numbered, each with its idea, key image, "
                     "layout, look and seed (ideas.md, The overlap check)")
        sys.path.insert(0, HERE)
        import dice
        n = dice.write_past(folder, os.path.join("research", "past-designs.md"))
        print(f"research/past-designs.md: {n} designs of this user", file=sys.stderr)
        a.task = ("Judge each candidate in research/candidates.md against the predictions and this user's own designs. "
                  "The user's first message, quoted, so an overlap it asks for (a series, the same subject on purpose) is "
                  "known and counts as CLEAR: " + a.task)
    what, parts, model, effort = KINDS[a.kind]
    print("start it with: model " + model + (f", effort {effort}" if effort else "") + " (inherit = the chat's own model)",
          file=sys.stderr)
    body = [MARK.format(a.kind), f"# Task ({what})\n\n{a.task}\n", "# Files\n",
            (f"PROJECT: {folder} (every path below is inside it)\n" if folder else "") +
            f"WRITES: {a.writes}\nREADS: {a.reads}\nDO NOT TOUCH: {', '.join(SHARED)} and every file not under WRITES\n"
            f"DONE WHEN: {a.done}\n", "# The kit's rules for this task (quoted; they are not optional)\n"]
    body += [piece(*p) + "\n" for p in parts]
    body.append("# Report\n\nAt most 25 tool calls. Details go in the file under WRITES; reply in 10 lines or fewer."
                + ("\n\n" + VERDICT if a.kind == "review" else ""))
    text = "\n".join(body)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(text + "\n")
        print(f"brief written to {a.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        import subprocess
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    sys.exit(main())
