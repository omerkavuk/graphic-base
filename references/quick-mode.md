# Quick mode

The whole piece lives in one file, `design.html`: the DESIGN block (title, purpose, views, palette, type), the styles,
and one `<section class="view">` per size. The main chat does everything; `make.py` renders, checks and answers in a
few lines. Learn the engine from `KIT/templates/HELPERS.md`, not from the starter's code.

Three habits carry the work: **a short, exact plan** (one card with sizes, colours and the reading order), **your own
eyes before anything is shown** (the still, compared with the card), and **notes as numbers** (what changes, by how
much). Nothing is approved unseen: the style board, every word and the card are in front of the user before each OK.

## Flow

| # | Step | Gate |
|---|---|---|
| 1 | Questions in one round, the style board between its two calls | answers |
| 1b | Research for material in the background, when chosen | shown at 2a |
| 2 | **The words:** every word as it will appear, in the message | OK or edits |
| 2a | The design card, as text, within a minute or two | OK, one note or a swap |
| 3 | The key view as a still | go on, or a note (none for a complete brief) |
| 3b | The other views; their stills go out as progress | none |
| 4 | The draft: every view at true size, all checks | final, notes or a jury check |
| 5 | Up to two revision rounds, then the final | OK |

## 1. Questions (one round)

**What the user already said is never asked again.** "You decide" settles nothing about taste: the idea's
interpretations and the style board still come, each one short question with the ★ first, since the idea and the look
are where the user's taste enters. With the question tool: **call 1** (after mode and purpose) = idea, approach, sizes,
images; then the style board is built and sent (`SendUserFile`, render); **call 2** = the style question alone about
the board, then references and the words (who writes the copy).

1. **Idea.** Three steps before the question, each catching what the maker cannot see in its own ideas
   (`ideas.md` §1): **the prediction test** (right after `init_design.py`: `python3 tools/brief.py predict --task
   "<the user's first message, quoted>" --out logs/brief-predict.md`, then a helper with that brief, in the
   background); **the sparks** meanwhile (`python3 tools/deal.py deal spark`: three hands, each led by a real thing
   drawn by chance, crossed with the user's idea into ten private angles, the first three dropped); **the overlap
   check** (the best five in `research/candidates.md`, then `brief.py overlap … --out logs/brief-overlap.md` and a
   helper, about half a minute). Then 2–3 interpretations that are not OVERLAP, each one line of what the viewer sees
   and what it does that the predictions did not, ★ the one that lands hardest; the user's literal version stays an
   option; the pick is logged (`deal.py pick spark s2 --reason "…"`). A set of pieces takes one seed per piece
   (`ideas.md` §2).
1a. **Approach,** always asked: what the piece is made of, chosen before anything is built inside it.
   The 3–4 that suit, ★ first with a few words why, each one line of what the viewer sees and its honest cost:
   typographic (type is the image) · photographic (a found or supplied photograph carries it) · illustrated (drawn in
   code: shapes, pattern, line, cut paper) · data and infographic (numbers, charts, maps that explain) · hand-made or
   collage (paper, print marks, found archive pieces). A brief that names one makes it the ★. The answer goes into
   `STATE.md` (`- **Approach:**`) before the board.
2. **Sizes.** The sizes it ships in, ★ from the purpose and where it goes (`purposes.md` §sizes): one master and
   up to three more. Each becomes a view. Print: the trim size, 3 mm bleed, 300 dpi, said in plain words ("A5, ready
   for print, with 3 mm extra at every edge for trimming").
3. **Style: the style board.** Every style graphic base offers, all 33, on one numbered board, each shown by its
   picture; the top three for this content are marked ★. A style carries to any format (a poster, a post, a report):
   its palette logic, its type, its spacing, its structure.
   - **Profile the content** (privately, then one line in `STATE.md`, `- **Content profile:**`): the purpose (brand ·
     editorial · event), what kind of content it is (report, data, explainer, announcement, invitation, product,
     story, process, quote, list, campaign, place, people), its tone in two words (serious, calm, playful, bold,
     elegant, urgent, warm, festive, nostalgic, cultural, technical) and its sector (finance, environment, culture,
     food, public, tech, …; `styles.py vocab` lists every word). Read it from the brief, the facts and the user's
     words: an energy-finance report is editorial, report and data, serious, finance.
   - **The board:** `python3 tools/styles.py suggest "<what it is about, in English words>" --purpose <p> --content
     <a,b> --tone <a,b> --sector <a,b> --board review/style-board.jpg`. It draws all 33 in a fixed order (grouped by
     family, so a number always means the same style) and marks the three that fit the profile best, each with its
     reasons. A look the user named goes in the words; a known name leads the three.
   - **Show, then ask:** send the board (`SendUserFile`, render), then the style question alone: the three ★ styles
     as options, ★ first, each with one line tied to this content ("Acid Diagram: your story is a process; one bold
     line and a five-box diagram carry it"), and **"None of these: something bolder"** last. Any other number on the
     board is a valid answer, typed in Other.
   - **"None of these: something bolder":** ask in one line what felt wrong when the answer does not say, then name
     three bolder styles from the same board (pushed tone: bold, urgent, playful) with a reason each.
   - **After the pick:** read only its recipe (`styles/<id>.md`); its Colour, Type and Pitfalls sections seed the card,
     its Variation section is where this piece departs from the picture. Write `- **Look · mood:**` with the id. The
     picture is mood only: take its grammar, never its layout.
4. **Images,** always its own question: ★ from the approach: a) drawn in code · b) searched in open
   archives (`sources.md` §1: what each archive holds) · c) their own files (in `assets/`) · d) none, type only. A real
   person, product or place the piece is about: say what open archives can and cannot give (`asset_search.py supply`
   counts it in seconds), and that a recognisable person in a brand piece needs a release (`sources.md` §1).
5. **Words:** a) ★ I write them (from the user's facts) · b) their own text · c) a mix. Either way every word is shown
   in the message for approval before anything is built (§2). Ask for the facts that only the user knows (date, place,
   names, price, contact), never for hex codes.

**Brand and marketing:** one plain line asks what the user surely knows: the name, two or three things that make it
different, and, if they have them, a logo (SVG or large PNG), brand colours and fonts, and the call to action.

Under the questions, one line of defaults: the sizes, safe margins, the language's letters checked, no generated images.

## 1b. Research in the background (when chosen)

Start every search at once in the background (`run_in_background`) and write the words meanwhile; the user never waits
on the network. **The look comes from the style board; open archives give material only:** what a real
thing looks like (a building, a plant, a dish, an object), never how the piece looks.

- Material: the key elements the piece shows, one search each, English, the shape in the words: `asset_search.py
  search --q "<element>" --out research/<element>`; icons with `--type icon`; surfaces with `--type texture`. Drop
  off-topic hits, watermarks, other brands, AI-generated images.
- One board: `asset_search.py board --dirs research/<a> research/<b> --per 3 --refs refs --out research/board-v1`;
  read only its summary lines and the measured palette, never single images.

An image enters the design only after `asset_search.py fetch` wrote its `LICENSES.csv` row.

## 2. The words (their own gate)

Every word that will be on the piece, shown in the message and approved before the card and before any code. Asking
"shall I write the words?" is not showing them; a file path or a summary is not showing them.

Write them first, privately: the headline in five wordings that differ in verb or stance, keep the one that says the
most in the fewest words; body copy only what the reader needs to act; cut 30 %; every line read as a native speaker
would say it; no dash; no sales tells (written to `notes/copy.txt`, then `python3 tools/words_check.py notes/copy.txt`). Budget: a post or
banner headline ≤ 7 words and ≤ 25 words in all; an invitation says who, what, when, where, how to reply and nothing
else; a poster ≤ 12 words outside the details. The user's own text is laid out the same way, used as given; a cut or a
line break it needs is shown, never made silently.

Then one message, in the user's language, the words exactly as they will appear (case, line breaks, numbers):

```
HEADLINE   <the words>
SUB        <the words>
BODY       <the words>
DETAILS    <date · place · time>
CTA        <the words>
LEGAL      <credits, source line>
```

with the headline's 2–3 alternatives in one line, the word count against the budget, a fact the user did not give
marked "(to confirm)", and for several views the lines that change per view. Then one question: "Words OK ★" · "Change
something" (the change typed in Other). After the OK, write the words into `STATE.md` (`- **Copy:**`) and set
`- **Copy approved:** yes`; the guard holds picture code until then. A word changed later is shown again in the next
message that carries a still or a draft.

## 2a. The design card (one text gate)
## 2. The design card (one text gate)

Fast: within a minute or two of the words' OK, as text; nothing heavy runs before the user has seen it. The card is
written in the message itself, every line, never only saved to a file.

One message:

- **Idea:** one line: what the viewer sees and the one thing they take away.
- **First read:** what the eye lands on first, second, third (the reading order the layout must force).
- The **material board,** when research ran.
- The **design card** (below).

One question call: "Build it ★" · "A note" · "A change". Apply a note, then build; the card is kept in `STATE.md`.

**The design card** is the only place choices are made. Each line carries numbers where they exist and its reason from
this piece; "modern", "clean", "bold", "elegant" alone decide nothing.

- **Fit:** how each kind of thing on the page is shown in this approach (the subject, people, objects, the
  ground) and what would look cheap and its route (`craft.md` §1).
- **Structure:** what carries the page in one sentence (one huge word and a small photo; a grid of twelve
  numbers; a single object centred in a field of colour; a map with three marks).
- **Look:** the style picked on the board, what this piece takes from its recipe and where it departs.
- **Palette:** 4–6 hex with roles (ground, ink, accent, and any others) and how colour is laid (flat fields,
  overprint, a duotone photo, a single accent on a neutral). From the recipe's colour logic, the subject or the
  brand; the sample's palette copied untouched needs a reason.
- **Grid:** columns, margins and gutter in `--u` (screen) or mm (print); the alignment (flush left, centred
  axis, asymmetric); the safe margin per view.
- **Hierarchy:** each reading level with its element, size in `--u` (or pt for print), weight and case; the
  ratio between levels (≥ 1.5 between first and second).
- **Font:** the face or pairing and its reason (§2b); the language's letters checked.
- **Image route:** each picture: what it shows, where it comes from (drawn, which archive, the user's file),
  and its treatment (full bleed, cut out, duotone, halftone, framed).
- **Texture:** paper, grain, print marks, or none, and why.
- **Signature:** the one device that makes it this piece and no other (a cropped letter, a colour that floods
  one corner, a rule that runs off the edge, a number set huge).
- **Views:** how the master adapts to each other size (what moves, what scales, what drops).
- **Checks:** what the first still must prove, in numbers ("the headline reads on a 160 px thumbnail", "the CTA is
  clear of the bottom 20 % on the story", "the logo is at least 24 px").

### 2b. Type

The pairing is dealt, not defaulted: `python3 tools/deal.py deal type --purpose <brand|editorial|event> --look <recipe
id or a family word> --mood "<the piece's tone in a few words>" --title "<the headline as it stands>" --sub "<the
second line>"` deals three curated pairings (80 in `references/type-library.json`, extended Latin verified),
weighted by the user's taste log (what they liked and turned down before, across designs). Draw them as one image in
the card's palette:

```
node tools/render.mjs --page type/specimen.html --params "spec=specimens.js&title=…&sub=…&bg=<hex>&ink=<hex>&accent=<hex>" --shot review/type-cards.jpg --width 1500
```

Sent with the card; the type question sits beside the card question. The pick is logged with the user's reason
(`deal.py pick type <id> --reason "…"`; turned all down: `deal.py redeal type --reason "…"`, which the taste log
remembers); its roles from `type/specimens.json` go into `DESIGN.type`. **Only when none of the three carries the
tone:** `python3 tools/fonts.py search "<tone>"` over 2,000+ open fonts (the AI-overused faces left out), then
`fonts.py role <id>`, which also writes the font's `LICENSES.csv` row. A brand's own fonts go in `fonts/` as local
roles (HELPERS.md).

## 3. Build: one file

Start from `design.html`. **Delete the example first** (the `data-example` section and the `.ex-*` rules). Edit the
DESIGN block from the card (title, purpose, views, palette, type, check strings), then the STYLE block, then one
section per view. Sizes in `var(--u)` so a layout holds across sizes of one shape; colours only through the palette
variables; text elements carry `data-role` (headline, body, cta, details, legal, label) so the checks know them.

**The key view first, alone,** with every element built (the real words, the real image or drawing, the real type):
`python3 tools/make.py stills --views <master>`. Read the sheet yourself against the card's Checks line and the board:
the one-second read on the thumbnail, the hierarchy, the alignment, the palette, any `make.py` line. Could it belong to
another piece? Redo it. Write what you see as numbers and fix it before the user sees it ("headline 18 px from the edge, safe
40 px"; "the CTA reads third, not second: 3.2 → 4.4 u"). Then send the sheet (`SendUserFile`, render) with one question
(★ go on · a note · change the view); no other view is built before the answer (with a complete brief it goes out
as progress and the build runs on).

**The other views** after the OK, each adapted, never squeezed: a story is recomposed for its height, a banner for its
width; what moves, scales and drops follows the card's Views line. Their stills go out as progress.

**A drawing that still looks wrong after two attempts** (a figure, a face, a hand, an animal) changes how it is shown
(silhouette, a detail instead of the whole, a found photograph, type), with one line to the user; never a third
attempt at the same drawing.

**The user's logo** is placed as given (SVG first), never redrawn, recoloured only to the variants the brand allows,
with clear space around it of at least its own cap height.

## 4. Draft, then final after the OK

`python3 tools/make.py draft` renders every view at true size (print views at 150 dpi plus a PDF), runs every check
and answers in a few lines. A **HELD** draft (exit 3) is fixed on exactly the named lines and drafted again before the
user sees anything; the next draft delivers what remains, each left item told to the user in one plain line. Notes
(taste, cliché, hierarchy, one-second read, words) are fixed or answered with a reason on the card.

**Deliver at once:** the sheet sent first (`SendUserFile`, render), each view's file path, the weakest spot in one
line, the known items, and for print one line: "the colours you see on screen print a little duller".

**The independent viewer.** Right after delivering a draft, start one helper in the background
(`templates/REVIEWER.md`): it saw nothing of the making, looks only at the files, and writes `review/critique-vN.md`.
When the user answers, read it first: its red items are fixed before any final.

**Then always the delivery question,** with the question tool: "Export the final files ★" · "I have notes" ·
"Jury round" (six pinpoint questions and three fixes, below).

**Jury (optional, two or three minutes, from the sheet and `logs/last-make.txt` only):** six answers, each one sentence
with where on the page: 1. first read: does the eye land where the card says? 2. the hero: does it hit harder than all
around it? 3. generic: anything that could belong to any brand (a template look, an AI default)? 4. the weakest area,
and why? 5. type: anything hard to read at its real size? 6. words: anything that reads as generated? Then three fixes
at most, biggest first, each in numbers, at least one that raises the wow, and one honest score (5 student, 6
template, 7 solid professional, 8 high-end studio, 9 award shortlist). The user picks which fixes to apply.

**Final:** `python3 tools/make.py final`: every view at export size (screen at its own pixels, or the view's `scale`;
print at its dpi), into `exports/`, with a credits file when outside material is used. Each print view also gets its
RGB PDF at trim plus bleed and, with Ghostscript, its press PDF (CMYK PDF/X-4, crop marks, boxes, preflight) and a soft
proof (`craft.md` §7). Before the final of a print piece, ask once whether the printer gave a profile or a spec
(★ "not yet, a general profile", or their file: `make.py final --profile <icc> --condition <name>`). The paths lead the
message (the press PDF named as the file for offset printers, the RGB PDF for digital printers); the preflight result in
one line; the soft proof sent (`SendUserFile`) with one line on how the colours will dull; credits under them
(`SKILL.md`, Delivery). Then two questions, one at a time: "Clean up the working files?" (★ yes: `renders/` and
`review/` stills; never `exports/`, `refs/`, `assets/` or `notes/`), then "Save this design's language as a format?"
(`routes.md` §3).

## 5. Revisions (max 2 rounds)

Notes in one batch, saved verbatim in `notes/round-N.md`, which starts with `## Keep` (what the user praised, or
"none"); `make.py` refuses a new draft without it. **Each note becomes a number before it becomes an edit:** which view
and element, what changes and by how much ("headline 11 u → 14 u", "accent #c8401c → #a23312", "logo from bottom right to top
left, 6 u clear"). Then targeted edits and one `make.py draft`; the reply gives one line per note: done /
done differently, because… / open, because…. What the user praised is never changed by a fix. After the final only technical
fixes; a new creative note goes back to a draft. After the second round, offer Studio mode.

**A scope change is a re-plan,** not a revision: a new size or a new piece goes back to §2a with a still, built after
the OK; it uses no revision round.
