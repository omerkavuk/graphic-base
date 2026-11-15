# Ideas: past the obvious, on target

The first ideas that come to mind are the ones everyone has, and the maker cannot see that in its own ideas. So the
idea goes through three steps before the user sees it: the sparks, the prediction test and the overlap check. Then
2–3 interpretations reach the user, ★ the one that lands.

## 1. Diverge, then converge (private)

1. **Deal the sparks:** `python3 tools/deal.py deal spark` deals three hands in a few seconds, each led by a seed (a
   real thing drawn by chance from outside: a museum object, a species, something in space, an invention, a heritage
   site, a craft or custom; each from another pool) with a design device, a page form, a medium and two more cards (a
   tone, an era, a colour, a material). The cards of the user's last designs are left out.
2. **Write ten angles,** one line each, crossing the user's idea with the hands: the idea stays at the centre and takes
   what a seed holds (its shape, its material, its pattern, its colour, its story), never a copy of it. Vary the point
   of view (whose piece is it?), the scale (a detail, the whole), the device (one image, a count, a map, a list, a pun in
   the type), the tone. `deal.py deal angle` deals three more angles when the ten feel narrow.
3. **Discard the first three.** They are the obvious ones, whatever they are.
4. **Keep the most surprising-yet-true:** *surprising:* a viewer would not predict it from the brief, the prediction
   test did not predict it, the overlap check found it in none of this user's designs; *true:* it follows from the
   subject; nothing is bent; the viewer says "of course" afterwards.
5. **Write the best five** into `research/candidates.md`, numbered, each with: the idea in one line, the key image,
   the layout, the look, the seed it grew from.

A seed is never dropped for being unfamiliar; a card that fights the idea is swapped for another of its axis, and a
whole hand goes only by `deal.py redeal spark --reason "…"`. The pick is logged: `deal.py pick spark s2 --reason "…"`.

**The prediction test (independent).** The maker cannot judge its own surprise. As soon as the design's folder exists,
a fresh helper gets only the user's first message, quoted, and nothing else: `python3 tools/brief.py predict --task
"<the message>" --out logs/brief-predict.md`, then the Agent tool with that file as its prompt and the model it prints.
It writes `research/predict.md`: the five designs it would expect from that message, one line each (subject, key
image, layout, look). Write the angles while it runs. A kept angle that shares its subject, key image or layout with a
predicted line is replaced by the next one on the list; each interpretation offered then says in a few words what it
does that the predictions did not.

**The overlap check (independent).** The maker cannot judge its own repeats either. After `research/candidates.md` is
written: `python3 tools/brief.py overlap --task "<the message>" --out logs/brief-overlap.md` writes this user's past
designs into `research/past-designs.md` and the brief for a fresh helper, which reads the candidates beside the
predictions and the past designs and writes `research/overlap.md`: one line per candidate, CLEAR; SHARES, when one
element repeats while the idea is new (a key image, a layout, a look: which one, and with what); or OVERLAP, when the
idea itself repeats. What the message itself names (a brand, a product, a person, a place, an event) is the user's and
never an overlap on its own. About half a minute.

**After the check.** The three strongest that are not OVERLAP are offered, a SHARES one with its shared element
changed; an OVERLAP is dropped, never argued with, unless the user's message asks for that design again (a series,
the same subject on purpose). Each offered interpretation is one line of what the viewer sees, and the user's literal
version stays an option.

The ten angles stay private (they cost the user attention). The user sees the three and the ★'s reason.

## 2. A set of pieces

A carousel, a campaign of several pieces or a report's chapters takes each piece from its own seed:
`python3 tools/deal.py deal seed --n <pieces>` deals one real thing per piece, each from another pool; each piece is
built from what its seed holds, never a copy; the pieces the user named stay theirs; the pick is logged
(`deal.py pick seed all --reason "…"`). One visual language holds the set together; the seeds keep each piece alive.

## 3. The specificity test (brand and editorial)

Before the card, write 6–10 facts only this subject has: its shape, its place, its people, its numbers, its history,
its materials. The headline or the image uses at least one. **Swap test:** put a competitor's name on the draft; if it
still works, the piece is generic: go back to the idea.

## 4. The memory

Every draft records the design's title, idea and approach in `~/.graphic-base/designs.json` (`make.py` does it). The
overlap check reads it, so the user is never offered the same design twice. Designs made before the kit was installed
join with `python3 tools/deal.py past --scan <folder>`.
