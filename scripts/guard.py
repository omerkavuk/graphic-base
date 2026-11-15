#!/usr/bin/env python3
"""Claude Code hooks that hold a design's gates (standard library only; registered by the skill's header).

  guard.py tool   PreToolUse: before a tool runs, inside a design project only:
                    - a large image read into the chat (over 1.2 megapixels): the sheets make.py writes are small
                    - the key store (~/.graphic-base/keys.env) opened, printed or searched
                    - a question asked while a picture the tools said to show has not been sent (show before you ask)
                    - the ideas question before the prediction test and the overlap check (ideas.md §1)
                    - picture code in design.html before the design card is written in STATE.md
                    - picture code in design.html before the words are approved (STATE.md: Copy approved: yes)
                    - "Copy approved: yes" written before every word was shown in the chat (quick-mode.md §2)
                    - a helper started without a brief from tools/brief.py
  guard.py stop   Stop: a delivered draft's turn ends on its question, never on plain text

Acts only inside a design project (a folder with STATE.md and tools/make.py at or above the session folder, or above
the file a tool touches); anywhere else it exits 0. Any internal error also exits 0: a guard never blocks work because
of its own fault. A block is exit 2 with the reason on stderr (PreToolUse), or a JSON decision (Stop).
"""
import json
import os
import re
import struct
import sys
from pathlib import Path

IMAGE_MAX = 1_200_000
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SHOW = re.compile(r"show the user(?: the soft proof)?: (.+?\.(?:jpg|jpeg|png))", re.I)
IDEA_HEADERS = re.compile(r"^(idea|ideas|interpretation|idée|idee|ideia|fikir|fikirler|yorum)s?$", re.I)   # the header is in the user's language
WORD = re.compile(r"[^\W\d_]{4,}", re.U)


def is_design(d):
    return (d / "STATE.md").is_file() and (d / "tools" / "make.py").is_file()


def design_near(start):
    try:
        p = Path(start).resolve()
    except (OSError, ValueError):
        return None
    for d in [p] + list(p.parents)[:4]:
        if is_design(d):
            return d
    return None


def design_for(ev, inp):
    found = design_near(ev.get("cwd") or os.getcwd())
    if found:
        return found
    for key in ("file_path", "path", "notebook_path"):
        if inp.get(key):
            found = design_near(Path(inp[key]).parent)
            if found:
                return found
    return None


def image_pixels(path):
    try:
        with open(path, "rb") as f:
            head = f.read(64 * 1024)
    except OSError:
        return 0
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        return w * h
    if head[:2] == b"\xff\xd8":
        i = 2
        while i < len(head) - 9:
            if head[i] != 0xFF:
                i += 1
                continue
            marker = head[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return w * h
            length = struct.unpack(">H", head[i + 2:i + 4])[0]
            i += 2 + length
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP" and head[12:16] == b"VP8X":
        w = int.from_bytes(head[24:27], "little") + 1
        h = int.from_bytes(head[27:30], "little") + 1
        return w * h
    return 0


def transcript(ev):
    """The session's tool calls and results in order: ('use', name, input) and ('result', text)."""
    out = []
    path = ev.get("transcript_path")
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get("message") or {}
            content = msg.get("content")
            if rec.get("type") == "user" and isinstance(content, str):
                out.append(("user", content))
                continue
            if not isinstance(content, list):
                continue
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text" and rec.get("type") == "assistant":
                    out.append(("say", c.get("text") or ""))
                    continue
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    out.append(("use", c.get("name") or "", c.get("input") or {}))
                elif c.get("type") == "tool_result":
                    body = c.get("content")
                    if isinstance(body, list):
                        body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
                    out.append(("result", str(body or "")))
                elif c.get("type") == "text" and rec.get("type") == "user":
                    out.append(("user", c.get("text") or ""))
    return out


def norm(p):
    return os.path.normcase(os.path.normpath(p.strip().strip("'\"")))


def unshown(events):
    """The newest picture a tool said to show, when no SendUserFile has sent it since."""
    last_show, last_index = None, -1
    for i, e in enumerate(events):
        if e[0] == "result":
            for m in SHOW.finditer(e[1]):
                last_show, last_index = norm(m.group(1)), i
    if not last_show:
        return None
    for e in events[last_index + 1:]:
        if e[0] == "use" and e[1] == "SendUserFile":
            files = e[2].get("files") or []
            if any(norm(str(f)) == last_show or os.path.basename(norm(str(f))) == os.path.basename(last_show) for f in files):
                return None
    return last_show


def question_text(inp):
    parts = []
    for q in inp.get("questions") or []:
        parts += [q.get("question", ""), q.get("header", "")] + [o.get("label", "") + " " + o.get("description", "") for o in q.get("options") or []]
    return " ".join(parts)


def offers_ideas(inp):
    return any(IDEA_HEADERS.match((q.get("header") or "").strip()) and len(q.get("options") or []) >= 2
               for q in inp.get("questions") or [])


def card_unwritten(design):
    try:
        st = (design / "STATE.md").read_text(encoding="utf-8")
    except OSError:
        return False
    m = re.search(r"^- \*\*Structure:\*\*\s*(.*)$", st, re.M)
    return bool(m) and m.group(1).strip().startswith("<")


def copy_unapproved(design):
    """True when STATE.md has the Copy approved line and it is not yes (older designs without the line pass)."""
    try:
        st = (design / "STATE.md").read_text(encoding="utf-8")
    except OSError:
        return False
    m = re.search(r"^- \*\*Copy approved:\*\*\s*(.*)$", st, re.M)
    return bool(m) and not m.group(1).strip().lower().startswith("yes")


def the_copy(design):
    """The words of the piece: COPY.md when it is filled (Studio), else STATE.md's Copy line."""
    c = design / "COPY.md"
    if c.is_file():
        text = re.sub(r"<!--.*?-->|<[^>\n]*>", " ", c.read_text(encoding="utf-8"), flags=re.S)
        if len(WORD.findall(text)) >= 6:
            return text
    try:
        st = (design / "STATE.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^- \*\*Copy:\*\*\s*(.*)$", st, re.M)
    v = m.group(1).strip() if m else ""
    return "" if v.startswith("<") else v


ROLE_WORDS = {"headline", "body", "details", "legal", "label", "word", "words", "budget", "used", "role", "roles"}


def copy_unshown(design, events, extra=""):
    """The copy's words that the chat has not shown since the user's second-to-last message: the user approves only
    words they read in the message itself, never a file or a summary. Returns the missing words, or [] when shown."""
    words = [w.lower() for w in WORD.findall(the_copy(design)) if w.lower() not in ROLE_WORDS]
    if not words:
        return ["(the Copy line in STATE.md is empty: write every word there first)"]
    users = [i for i, e in enumerate(events) if e[0] == "user"]
    start = users[-2] if len(users) >= 2 else 0
    said = extra
    for e in events[start:]:
        if e[0] == "say":
            said += " " + e[1]
        elif e[0] == "use" and e[1] == "AskUserQuestion":
            said += " " + question_text(e[2])
    said = said.lower()
    missing = [w for w in dict.fromkeys(words) if w not in said]
    return missing if len(missing) > 0.2 * len(set(words)) else []


def touches_picture(name, inp):
    """An edit to design.html that builds the picture (styles or views), not only the DESIGN data block."""
    path = str(inp.get("file_path") or "")
    if not path.endswith("design.html"):
        return False
    if name == "Write":
        return True
    text = (inp.get("new_string") or "") + (inp.get("old_string") or "")
    return bool(re.search(r"<section|<style|\{[^}]*:[^}]*;|class=", text))


def block(reason):
    sys.stderr.write("graphic base: " + reason + "\n")
    sys.exit(2)


def tool(ev):
    name, inp = ev.get("tool_name") or "", ev.get("tool_input") or {}
    flat = json.dumps(inp, ensure_ascii=False)
    if re.search(r"\.graphic-base[\\/]+keys\.env", flat) and name in ("Read", "Bash", "PowerShell", "Grep", "Glob", "Edit", "Write"):
        block("the key store is never opened, printed or searched; reach a key only through tools/keys.py and the tools that use it")
    design = design_for(ev, inp)
    if not design:
        return 0
    if name == "Read":
        p = str(inp.get("file_path") or "")
        if os.path.splitext(p)[1].lower() in IMAGE_EXT and image_pixels(p) > IMAGE_MAX:
            block(f"{os.path.basename(p)} is over {IMAGE_MAX / 1e6:.1f} megapixels: read the small sheet make.py wrote "
                  "(review/*.jpg), or a thumbnail; the user sees the full file through SendUserFile")
    if name == "AskUserQuestion":
        events = transcript(ev)
        pending = unshown(events)
        if pending:
            block(f"show before you ask: send {pending} with SendUserFile (display 'render') first, then ask")
        if offers_ideas(inp):
            r = design / "research"
            missing = [f for f in ("predict.md", "candidates.md", "overlap.md") if not (r / f).is_file()]
            if not missing and (r / "overlap.md").stat().st_mtime < (r / "candidates.md").stat().st_mtime:
                missing = ["overlap.md (older than candidates.md: run the overlap check again)"]
            if missing:
                block("the ideas question waits for the prediction test and the overlap check (ideas.md §1): missing "
                      + ", ".join("research/" + m for m in missing))
    if name in ("Edit", "Write", "MultiEdit") and str(inp.get("file_path") or "").endswith("STATE.md"):
        new = str(inp.get("new_string") or inp.get("content") or "")
        if re.search(r"^- \*\*Copy approved:\*\*\s*yes", new, re.M | re.I):
            missing = copy_unshown(design, transcript(ev))
            if missing:
                block("the words are approved only after the user read every one in the chat: show the full copy in "
                      "your message (each line as it will appear, with its role), ask, then write Copy approved: yes. "
                      "Not shown yet: " + ", ".join(missing[:8]))
    if name in ("Edit", "Write", "MultiEdit") and touches_picture(name, inp) and copy_unapproved(design):
        block("picture code waits for the words: show every word in the message (quick-mode.md §2), get the user's OK, "
              "then write '- **Copy approved:** yes' in STATE.md")
    if name in ("Edit", "Write", "MultiEdit") and touches_picture(name, inp) and card_unwritten(design):
        block("picture code waits for the design card: write it in STATE.md (quick-mode.md §2, or the roadmap in Studio "
              "mode) and show it to the user first")
    if name in ("Agent", "Task"):
        prompt = str(inp.get("prompt") or "")
        if "<!-- graphic-base brief:" not in prompt:
            block("a helper starts from a brief: python3 tools/brief.py <predict|overlap|review|sourcing> --task \"…\" "
                  "--out logs/brief-<kind>.md, then pass that file's text as the prompt")
    return 0


def stop(ev):
    if ev.get("stop_hook_active"):
        return 0
    design = design_for(ev, {})
    if not design:
        return 0
    events = transcript(ev)
    last_user = max((i for i, e in enumerate(events) if e[0] == "user"), default=-1)
    turn = events[last_user + 1:]
    delivered = any(e[0] == "result" and re.search(r"^draft v\d+:", e[1], re.M) and "HELD" not in e[1]
                    and "show the user" in e[1] for e in turn)
    asked = any(e[0] == "use" and (e[1] == "AskUserQuestion" or (e[1].endswith("wrap_up") and e[2].get("ask"))) for e in turn)
    if delivered and not asked:
        print(json.dumps({"decision": "block", "reason": "a delivered draft's turn ends on its question: ask with the "
                          "question tool (Final ★ · Notes · Jury), after sending the sheet with SendUserFile"}))
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        ev = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if mode == "tool":
        return tool(ev)
    if mode == "stop":
        return stop(ev)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:                                   # never block work over the guard's own fault
        sys.exit(0)
