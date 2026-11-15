#!/usr/bin/env python3
"""Deal 3 options from a bank so proposals vary from design to design, and log every pick (Python 3 stdlib).

  python3 tools/deal.py deal angle                    # 3 idea angles for the diverge step
  python3 tools/deal.py deal spark                    # 3 sparks: a seed from outside, a device, a form, a medium, two more
  python3 tools/deal.py deal seed --n <pieces>        # one seed from outside for each piece of a set
  python3 tools/deal.py deal look --n 6               # 6 references for the style board from about 130 looks
  python3 tools/deal.py pick spark s2 --reason "<the user's idea, crossed with this hand's seed and device>"
  python3 tools/deal.py pick angle own --reason "<the user's own angle>"
  python3 tools/deal.py redeal look --reason "<why none of these serves this piece>"
  python3 tools/deal.py show
  python3 tools/deal.py past --scan <folder>          # remember the designs made before under a folder (once)
  python3 tools/deal.py deal type --purpose event --look <recipe id> --mood "<tone>" --title "<the headline>"
  python3 tools/deal.py pick type <id> --reason "<why this pairing fits this piece>"
  python3 tools/deal.py redeal type --reason "<the user's reason>"
  python3 tools/deal.py taste type <font id> --verdict reject --reason "<the user's reason>"

A spark's seed is a real thing drawn by chance from outside (dice.py: a museum object, a species, something in space,
an invention, a heritage site, a craft or custom), each from another pool, within a few seconds. The random seed is
the date plus the project folder name (--seed overrides), so the same project on the same day gets the same hand.
Options picked earlier in this project, and cards the user's last designs were dealt, are left out. Asking again while
a hand is open shows the same hand: a new one needs `redeal` with a written reason. `pick` needs a one-line reason
built on this design's facts; `own` records the user's own answer. Everything is logged in history.json.

The type bank (type_deal.py) deals font pairings from type-library.json, filtered by purpose, look, mood and extended Latin
coverage and weighted by the taste log, and writes the specimen cards' data into type/. KIT/references/ideas.md.
"""
import argparse
import datetime
import hashlib
import json
import os
import random
import sys

import dice
import type_deal

BANKS = {
    "angle": {
        "smallest-witness": "seen through the smallest thing in the subject's world",
        "object-speaks": "an object connected to the subject carries the whole message",
        "one-detail": "one detail, enlarged, stands for the whole",
        "scale-flip": "a scale flip: the tiny made vast, or the vast made tiny",
        "the-count": "a number or a count tells it",
        "before-after": "the change: before and after on one page",
        "the-map": "where it happens, drawn as a map",
        "the-tool": "the tool or instrument of the subject, not the subject",
        "the-trace": "the trace the subject leaves (a footprint, a stain, a crumb, a shadow)",
        "opposite-premise": "the opposite of what the idea first suggests",
        "the-ritual": "an everyday ritual shown as a ceremony",
        "the-instruction": "an instruction, a recipe or a manual as the format",
        "the-label": "a label, a tag or a ticket as the whole design",
        "type-is-image": "the words themselves become the picture",
        "the-archive": "an old document or object from the subject's past, made new",
        "the-gap": "the words say one thing, the picture another; the gap is the message",
    },
}


SPARKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sparks.json")
SPARK_AXES = ("device", "form", "medium")
SPARK_EXTRA = ("tone", "era", "colour", "material")


def seen_path():
    return os.environ.get("GRAPHIC_BASE_SPARKS") or os.path.join(os.path.expanduser("~"), ".graphic-base", "sparks-seen.json")


def load_seen():
    try:
        with open(seen_path(), encoding="utf-8") as fh:
            return set(json.load(fh))
    except (OSError, ValueError):
        return set()


def save_seen(seen, cards):
    try:
        os.makedirs(os.path.dirname(seen_path()), exist_ok=True)
        with open(seen_path(), "w", encoding="utf-8") as fh:
            json.dump((list(seen - set(cards)) + list(cards))[-300:], fh, ensure_ascii=False)
    except OSError:
        pass


def spark_hand(seed, n, out=()):
    """n sparks, each a seed from outside (every one from another pool), one card from every core axis and two of the
    others; no card twice in a deal, and none the user's last designs were dealt (sparks-seen.json) while the axis has
    others left. Returns the hands' lines and their seeds in full."""
    with open(SPARKS, encoding="utf-8") as fh:
        data = json.load(fh)
    seen = load_seen()
    rng = random.Random(int(hashlib.sha256(f"{seed}|spark".encode()).hexdigest(), 16))
    used, hands = set(out) | seen, {}
    seeds = {f"s{i}": s for i, s in enumerate(dice.draw(f"{seed}|spark", n, avoid=used), 1)}
    for i in range(1, n + 1):
        parts = [f"seed: {seeds[f's{i}']['name']}"]
        for axis in SPARK_AXES + tuple(rng.sample(SPARK_EXTRA, 2)):
            pool = [x for x in data[axis] if x not in used] or data[axis]
            card = rng.choice(pool)
            used.add(card)
            parts.append(f"{axis}: {card}")
        hands[f"s{i}"] = " · ".join(parts)
    save_seen(seen, [p.split(": ", 1)[1] for h in hands.values() for p in h.split(" · ")])
    return hands, seeds


def seed_hand(seed, n, out=()):
    """n seeds from outside, one for each piece of a set, every pool used before one comes back."""
    seen = load_seen()
    seeds = {f"w{i}": s for i, s in enumerate(dice.draw(f"{seed}|worlds", n, avoid=set(out) | seen), 1)}
    save_seen(seen, [s["name"] for s in seeds.values()])
    return {k: s["name"] for k, s in seeds.items()}, seeds


def look_hand(seed, n, out=()):
    """n references for the style board: designers, movements, print crafts and vernacular graphics, none of those
    the user's last designs were dealt while others are left."""
    with open(SPARKS, encoding="utf-8") as fh:
        looks = json.load(fh)["look"]
    seen = load_seen()
    rng = random.Random(int(hashlib.sha256(f"{seed}|look".encode()).hexdigest(), 16))
    pool = [x for x in looks if x not in seen and x not in out]
    pool = pool if len(pool) >= n else looks
    hand = {f"l{i}": x for i, x in enumerate(rng.sample(pool, min(n, len(pool))), 1)}
    save_seen(seen, hand.values())
    return hand


def load(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"deals": []}


def save(path, h):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)   # dealt before the design's folder exists
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(h, fh, ensure_ascii=False, indent=1)


def one_line(text):
    text = " ".join((text or "").split())
    if not text:
        sys.exit("a one-line reason is required")
    return text


def open_hand(h, cat):
    for d in reversed(h["deals"]):
        if d["category"] == cat:
            return d if d["pick"] is None else None
    return None


def deal_hand(h, cat, seed, n, extra_out=()):
    picked = {d["pick"] for d in h["deals"] if d["category"] == cat and d["pick"]}
    pool = sorted(k for k in BANKS[cat] if k not in picked and k not in extra_out)
    if len(pool) < n:                          # bank nearly used up: allow earlier dealt-but-unpicked options again
        pool = sorted(k for k in BANKS[cat] if k not in picked) or sorted(BANKS[cat])
    rng = random.Random(int(hashlib.sha256(f"{seed}|{cat}".encode()).hexdigest(), 16))
    return rng.sample(pool, min(n, len(pool)))


def show_hand(d):
    print(f"{d['category']} · seed {d['seed']}" + (f" · re-deal: {d['redeal_reason']}" if d.get("redeal_reason") else ""))
    for i, k in enumerate(d["dealt"], 1):
        print(f"  {i}. {k}: {(d.get('texts') or {}).get(k) or BANKS.get(d['category'], {}).get(k, '')}")
        s = (d.get("seeds") or {}).get(k)
        if s:
            print(f"       {dice.POOLS.get(s.get('pool'), 'a seed')}: {s.get('fact') or s['name']} {s.get('link', '')}")
    if d["category"] == "look":
        print("the board's directions start here: keep the three that serve this idea and differ in kind and in tone "
              "(at least one with a colour decision); a name that fits nothing is swapped, with the reason in the pick")
    if d["category"] == "spark":
        print("springboards, not orders: cross the user's idea with each hand. The seed is a real thing drawn by chance, "
              "so the idea starts where habit would not go: take what it holds (a shape, a material, a pattern, a colour, "
              "its story), never a copy of it, and never drop it for being unfamiliar; a card that fights the idea is "
              "dropped for another of its axis, a seed only by a redeal with its reason")
    if d["category"] == "seed":
        print("one seed for each piece of a set (a carousel's slides, a campaign's pieces, a report's chapters): build "
              "each from what its seed holds (a shape, a material, a pattern, a colour, its story), never a copy of it; "
              "the pieces the user named stay theirs; a seed that fights the idea goes by a redeal with its reason")
        print("log what each piece took: deal.py pick seed all --reason \"…\" (or the ids kept: w1,w3)")
        return
    print(f"pick one from this design's facts: deal.py pick {d['category']} <id> --reason \"…\"")


def fresh(category, seed, n, out=()):
    """A new hand's lines (and its seeds from outside) for the categories dealt from the deck."""
    if category == "spark":
        return spark_hand(seed, n, out)
    if category == "seed":
        return seed_hand(seed, n, out)
    return look_hand(seed, max(n, 6), out), None


def past_cmd(a):
    if a.scan:
        n = dice.scan(a.scan)
        print(f"remembered {n} designs under {a.scan}; the memory holds {len(dice.load_films())} (its ideas are what "
              f"brief.py overlap checks new ideas against)")
        return
    designs = dice.past(a.project)
    print(f"{len(designs)} designs of this user are remembered" + (": " + "; ".join(f["title"] for f in designs[:5]) +
                                                                (" …" if len(designs) > 5 else "") if designs else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["deal", "redeal", "pick", "show", "taste", "past"])
    ap.add_argument("category", nargs="?", choices=sorted(BANKS) + ["look", "seed", "spark", "type"])
    ap.add_argument("choice", nargs="?", help="pick: an id from the open hand, or 'own' (seed: 'all' or ids, w1,w3)")
    ap.add_argument("--reason", help="pick and redeal: one line")
    ap.add_argument("--project", default=".")
    ap.add_argument("--seed", help="default: <date>:<project folder name>")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--scan", help="past: a folder whose designs (made before) join the memory")
    type_deal.add_args(ap)
    a = ap.parse_args()
    if a.cmd == "past":
        return past_cmd(a)
    path = os.path.join(a.project, "history.json")
    h = load(path)
    base_seed = a.seed or f"{datetime.date.today().isoformat()}:{os.path.basename(os.path.abspath(a.project))}"

    if a.cmd == "show":
        for d in h["deals"]:
            if a.category in (None, d["category"]):
                print(f"{d['at']} {d['category']}: {', '.join(d['dealt'])} -> {d['pick'] or '(open)'}"
                      + (f": {d['reason']}" if d["reason"] else ""))
        return
    if not a.category:
        sys.exit("name a category: " + ", ".join(sorted(BANKS) + ["look", "seed", "spark", "type"]))
    if a.category == "type":
        return type_deal.run(a, h, path, base_seed, save, one_line)
    if a.cmd == "taste":
        sys.exit("taste works on the type category: deal.py taste type <id> --verdict like|reject --reason \"…\"")
    hand = open_hand(h, a.category)

    if a.cmd == "deal":
        if hand:
            print("a hand is already open (a new one needs: redeal --reason \"…\")")
            show_hand(hand)
            return
        rnd = sum(d["category"] == a.category for d in h["deals"]) + 1
        hand = {"category": a.category, "seed": f"{base_seed}#{rnd}", "dealt": [], "redeal_reason": None,
                "pick": None, "reason": None, "at": datetime.datetime.now().isoformat(timespec="minutes")}
        if a.category in ("spark", "seed", "look"):
            hand["texts"], seeds = fresh(a.category, hand["seed"], a.n)
            hand["dealt"] = sorted(hand["texts"], key=lambda k: int(k[1:]))
            if seeds:
                hand["seeds"] = seeds
        else:
            hand["dealt"] = deal_hand(h, a.category, hand["seed"], a.n)
        h["deals"].append(hand)
        save(path, h)
        show_hand(hand)

    elif a.cmd == "redeal":
        reason = one_line(a.reason)
        if not hand:
            sys.exit("no open hand: use deal")
        hand["pick"] = "(re-dealt)"
        hand["reason"] = reason
        shown = set()                          # every hand re-dealt since the last real pick stays out
        for d in reversed(h["deals"]):
            if d["category"] != a.category:
                continue
            if d["pick"] != "(re-dealt)":
                break
            shown |= set(d["dealt"])
        rnd = sum(d["category"] == a.category for d in h["deals"]) + 1
        new = {"category": a.category, "seed": f"{base_seed}#{rnd}", "dealt": [], "redeal_reason": reason,
               "pick": None, "reason": None, "at": datetime.datetime.now().isoformat(timespec="minutes")}
        if a.category in ("spark", "seed", "look"):
            old = [p.split(": ", 1)[1] if a.category == "spark" else p for d in h["deals"] if d["category"] == a.category
                   for x in (d.get("texts") or {}).values() for p in (x.split(" · ") if a.category == "spark" else [x])]
            new["texts"], seeds = fresh(a.category, new["seed"], a.n, out=old)
            new["dealt"] = sorted(new["texts"], key=lambda k: int(k[1:]))
            if seeds:
                new["seeds"] = seeds
        else:
            new["dealt"] = deal_hand(h, a.category, new["seed"], a.n, extra_out=shown)
        h["deals"].append(new)
        save(path, h)
        show_hand(new)

    else:
        reason = one_line(a.reason)
        if not hand:
            sys.exit("no open hand: use deal first")
        many = a.category == "seed" and (a.choice == "all" or set(str(a.choice).split(",")) <= set(hand["dealt"]))
        if a.choice not in hand["dealt"] and a.choice != "own" and not many:
            sys.exit(f"pick one of: {', '.join(hand['dealt'])} (or 'own' for the user's own answer"
                     + ("; 'all' or ids like w1,w3 for the worlds" if a.category == "seed" else "") + ")")
        hand["pick"], hand["reason"] = a.choice, reason
        save(path, h)
        print(f"logged: {a.category} = {a.choice}: {reason}")


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:   # Windows reads, writes and prints in a legacy code page
        import subprocess
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    main()
