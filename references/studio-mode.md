# Studio mode

For pieces with many pages or many parts: a report, a programme booklet, a brochure, a carousel of slides, a campaign
of several pieces. The same engine as Quick mode (one `design.html`, `make.py`), with a gate at every step and two
more plans: `ROADMAP.md` (the concept and the page plan) and `COPY.md` (every word). Read with `SKILL.md` (first
questions, hard rules) and the purpose file.

## 1. Who does the work, and the context

- **This chat** talks with the user, keeps `STATE.md` and does the work it holds the context for: the roadmap, the
  copy, the style frame, every page, notes of up to five targeted edits. `design.html` has one owner: this chat.
- **Fresh helpers** take an independent part that runs beside it, each from a brief (`python3 tools/brief.py <kind>
  … --out logs/brief-<kind>.md`): the prediction test and the overlap check (`predict`, `overlap`), finding material
  and logging licences (`sourcing`), gathering the facts for a report into `research/facts.md` (`sourcing` with the
  facts table as its file), and the independent viewer on a delivered draft (`review`). One task each, at most 25
  tool calls, details in their own files, a reply of 10 lines or fewer.
- **Notes** are saved verbatim in `notes/round-N.md`, starting with `## Keep` (what the user praised; a fix or a
  re-plan never changes it), split per page; up to five targeted edits this chat makes itself; a re-plan (new pages, a
  new order) is written as a diff against the praised version (KEPT · CHANGED · NEW).
- **Handoff:** at every gate, update "Resume here" in `STATE.md` and take a silent snapshot (`tools/snapshot.py
  "gate <n>"`); after about 15 user messages, offer a new chat that continues from `STATE.md` (`SKILL.md`, Small
  context).

## 2. The steps

| # | Step | Output | Gate |
|---|---|---|---|
| 1 | Interview (one round, in calls of up to four questions) | `STATE.md` fields | answers |
| 2 | Concept | `ROADMAP.md`: the one message, the idea, the structure, the page plan, risks | **user OK** |
| 3 | Copy | `COPY.md`: every word, page by page, shown in full | **user OK** + pace |
| 4 | Style frame | the key page at final quality: `review/stills-vN.jpg` | **user OK** |
| 4b | Type | specimen cards on the style frame's palette (`quick-mode.md` §2b) | **user pick** |
| 5 | Layout sheet | every page as a grey wireframe with the real copy, in spreads (`make.py layout`) | **user OK** |
| 6 | Draft | every page and view at true size, all checks (`make.py draft`) | final, notes or jury |
| — | Final | exports: pages as PNG, one PDF per document, press PDF for print, soft proof | delivered |

**Pace** (asked with the copy gate, as a second question): **"Step by step"** (each step its own gate) or **"Make it
all, show me the draft"** (after the copy, straight to the draft: the style frame and the layout sheet go out as
progress, never as questions). ★ steps for 12 pages or more, or a print run; ★ through for a short carousel. Written
as `Pace:` in `STATE.md`; "stop, show me" brings the gates back.

A complete brief skips what it answers: a client brief that fixes the copy and the page plan goes straight to the
style frame.

## Step 1: Interview

`SKILL.md` and `quick-mode.md` §1 hold the questions; Studio asks them in this order: **call 1** = the idea's
interpretations (after the sparks, the prediction test and the overlap check: `ideas.md` §1; a set of pieces takes one
seed per piece, `ideas.md` §2), the approach, the views and their page counts (★ from the purpose: `purposes.md`;
print booklets in multiples of 4), images; the style board is built from the content profile and sent
(`quick-mode.md` §1, question 3: all 33 styles, the top three for the content marked);
**call 2** = the style alone about the board, then the facts and data the piece rests on (★ "I search open sources and show you every number with its source"
· "I give you the numbers" · both) and who writes the copy; **call 3** = the profile (Quality · ★ Balanced · Economy:
how many style-frame rounds, how much detail per page). Write the answers into `STATE.md`.

## Step 2: Concept (STOP)

Fill `ROADMAP.md`, one screen: the one message (the sentence a reader keeps), who reads it and where, the idea, the
structure, the signature, the **page plan** (one row per page or piece: kind, content, key element, words), the
style, three risks and the specificity test (`ideas.md` §3). The page plan follows the rules of rhythm:

- **Kinds:** cover, opener (a chapter's first page), text, data, image, quote, breather (a page that rests the eye:
  one image or one line), closer. Never three of one kind in a row; a data page next to an image or a breather.
- **One idea per page or spread;** a spread is read as one picture in print, so its two pages are designed together.
- **Counts:** a report's chapters get an opener each; every 3–4 pages something big (a number, a photograph, a quote)
  resets the eye; the closer answers the cover.
- **A campaign** of several pieces: one visual language (grid, type, palette logic, signature), each piece built for
  its own size and job; the page plan lists the pieces.

Facts for a report or infographic are gathered first (a `sourcing` helper or this chat), one row per claim in
`research/facts.md` with source, year and link (`sources.md` §4); an unconfirmed claim is cut. Show the roadmap in the
message itself (the page plan as a table), with the board beside it. **Wait for OK.**

## Step 3: Copy (STOP)

Write `COPY.md` in one go, never page by page: every word in reading order under its page heading, each line with
its role, the word count against the budget. Then a **cold read**: a fresh helper (`brief.py review --task "cold read
of COPY.md: what happened in order, every place you had to guess"`) gets only the copy and writes
`review/copy-cold.md`; fix every guess it found. Run `python3 tools/words_check.py COPY.md` (no dash, no generated
tells). The gate message carries the whole copy (a link to the file is not showing it) and asks two questions in one
call: the copy (OK · one note) and the pace. **Wait for OK,** then set `- **Copy approved:** yes` in `STATE.md` (the
guard holds picture code until then, and refuses the line when the copy was not in the chat).

## Step 4: Style frame (STOP)

Build the piece's most telling page at final quality (often not the cover: the page that carries the idea, or the
hardest page, such as a data spread), with the real copy, the real images, the chosen type and palette. Delete the
starter's example first. `python3 tools/make.py stills --views <view> --pages <n>`. Self-review before showing (two
rounds at most, Quality three, Economy one): the one-second read, the squint test, the hierarchy, the grid, every
`make.py` line, the picked style's recipe (its Pitfalls section) and the card. Then the still with one question (OK · one note). The approved page is the bar for every
other page. **Wait for OK.**

## Step 4b: Type (STOP)

`quick-mode.md` §2b, with the style frame's palette in the cards. **Wait for the pick.**

## Step 5: Layout sheet (STOP)

Every page built with its real copy and its layout (images may still be placeholders), then
`python3 tools/make.py layout`: each page as a grey wireframe (images as hatched boxes, colour off), in reading
spreads with the page number and kind under each. It checks the flow before any page is finished: text that does not
fit (CLIPPED, OFF EDGE), the rhythm (three of a kind in a row) and the binding (a multiple of 4). Send the sheet with
one question: "Is the order and the rhythm right? A page too full or too empty?" **Wait for OK.** With `Pace:
through` the sheet is still made and its findings fixed, without the question.

## Step 6: Draft, then final

Every page finished at full detail: `python3 tools/make.py draft` (every page and view at true size, print views at
150 dpi plus one PDF per document, all checks). A HELD draft is fixed and drafted again before the user sees it
(`quick-mode.md` §4). Deliver the sheet, the weakest page in one line, the known items; start the independent viewer
in the background (`brief.py review`); then the delivery question (Final · Notes · Jury). Notes: up to two rounds on
drafts, each note a number before an edit (`quick-mode.md` §5).

**Final:** `python3 tools/make.py final`: every page as PNG (`<title>-<view>-p01.png` …), one PDF per multi-page
view (a carousel's PDF is what LinkedIn's document posts take), and for print the RGB PDF plus the press PDF with every
page on its own sheet with crop marks, the preflight across all pages, and the soft proof (`craft.md` §7). Ask once for
the printer's profile and binding before a print final.

## Building pages

- One `<section class="view" data-view="<id>" data-page="<n>" data-kind="<kind>">` per page; every page of a view
  shares its size. A page number goes in an element with `data-folio` (the engine fills it; `data-folio="2"` pads to
  two digits).
- **Master pages** in CSS: a class per kind (`.k-opener`, `.k-data`) carrying its grid, so pages of one kind line up;
  running heads and folios in the same place on every page; the margins mirrored for facing pages when the card says so
  (`[data-page]:nth-of-type(even)` for left pages).
- **Text that does not fit is a layout problem, not a size problem:** cut words (back to `COPY.md`), give the page
  more room or split it; never shrink body text below the floor (`craft.md` §4).
- **Charts:** `<div data-chart="<key>" style="width:…;height:…;font-size:…">` drawn from `DESIGN.data[key]` (bar,
  hbar, line; one highlighted item or series in the accent, the rest muted, direct labels, values in the language's
  number format); the source line under it in its legal level, from `research/facts.md`. HELPERS.md has the format.
- **Images** per page from the sources (`sources.md`), each fetched with its licence row; a photograph that spans a
  spread is placed as two halves with the gutter in mind (nothing important in the middle 10 mm).
