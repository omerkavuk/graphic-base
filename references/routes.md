# Routes: starting from something that already exists

Read the section of the route `SKILL.md` sent you to. Each route still goes through the mode and purpose questions,
the card, the still and the draft; it only changes where the idea and the look come from.

## 1. "Like this one": a reference design

The user sends a design they like (a poster, a post, a page, a screenshot) and wants a new piece in its spirit.

1. Save it in `refs/` and write `- **Reference:** refs/<file>` in `STATE.md`. Ask once whose it is when it could be
   the user's own brand work (then it may be followed closely: say so in one line and skip the closeness check by
   leaving the Reference line out).
2. **Measure it:** `python3 tools/direction.py measure --dirs refs --out research/reference` (palette, contrast,
   warmth), and read it yourself at a small size: the grid (columns, margins), the hierarchy (what reads first, the size
   ratios), the type's character (serif or grotesque, weight, case, tracking), the image treatment, the texture, the
   signature. Write that **grammar** into the card in plain lines.
3. **Ask what changes:** the user's words ("ama bizim renklerimizle", "daha sade") are the brief; the rest comes from
   the grammar. The idea is still the user's subject: the sparks and checks of `ideas.md` run as usual, so the new piece
   is about something, not a re-skin.
4. **Never a copy:** the subject, every word, every image, the layout's masses and crops are new; a library's or a
   designer's look is taken as grammar only (`sources.md` §5). `make.py draft` holds a view that is more than 90 % like
   the reference image (TOO CLOSE) and says what to move.

## 2. "Resize this": the user's own design to new sizes

The user sends their own finished design (PNG, PDF or SVG) and needs it in other sizes: a post as a story, a banner,
an A4 flyer.

1. Their file is the master: `assets/master.<ext>`. Ask only the sizes (★ from the purpose: `purposes.md`) and
   whether the words change.
2. **Rebuild, never stretch:** the master is rebuilt in `design.html` as the first view at its own size, with the real
   type (identify the faces or the nearest open ones: `fonts.py search`), the real colours (measured:
   `direction.py measure --dirs assets`), the logo and images as separate files from the user (ask for them; a flat
   image cannot be taken apart cleanly). Trace it: `python3 tools/make.py stills --views <master> --underlay
   assets/master.png` lays the user's file under the rebuild at 45 % (`--uo 0.6` stronger); line the edges up, then
   stills without the underlay.
3. **Each new size is composed, not squeezed:** what moves, scales and drops is the card's Views line; a story is
   re-stacked for its height, a banner re-flowed for its width, a print size gets bleed and the print floors.
4. The draft and final run as in Quick mode. No closeness check: the design is the user's own.

## 3. "Same format": a saved format

After a final the user liked, one question: "Save this design's language as a format?" (★ yes when a series is
likely: monthly posts, an event series, a report every year). On yes: one more question, what returns in every piece
(★ nothing · the logo file · a fixed element · own), then `python3 tools/formats.py save "<name>" [--keep <file or
element>]` inside the design's folder.

**Use:** `python3 tools/formats.py list`, then `python3 KIT/scripts/init_design.py <short-name> --quick --format
"<name>"`: the new folder gets `FORMAT.md` (the language), the source's code as `research/format-reference.html` (to
look up how a technique was built), and the kept files. Ask only the new piece's subject and words (and sizes when they
differ). The card writes every language line again for the new subject and says how it meets it ("palette logic:
<the rule>, here <how this piece meets it>"); the type is the same face or a sibling. `make.py draft` holds a draft
whose lines repeat the source's words (FORMAT COPY) and names reused images that FORMAT.md does not keep.

## 4. Browse styles

Profile what the user wants to make (purpose, content kind, tone, sector; ask one plain line when the message gives
nothing), then `python3 tools/styles.py suggest "<their words>" --purpose … --content … --tone … --sector … --board
review/style-board.jpg` (`quick-mode.md` §1, question 3): all 33 styles, the top three marked. Sent, then the first
questions with the picked style as the look (`styles/<id>.md`, read only that one).
