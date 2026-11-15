---
name: graphic-base
description: >-
  Designs graphics entirely with code, together with the user: banners, social posts and carousels, posters, flyers,
  invitations, cards, menus, infographics, one-pagers and reports, for screen and for real print. Two first questions -
  the mode (Quick - one design.html, a few questions, a text card, the key view as a still, a true-size draft, two
  revisions, then the export; Studio - gated steps for multi-page and multi-size work) and the purpose (brand and
  marketing, editorial and information, event and personal). Sources photos, artworks, illustrations, icons and
  textures from open archives with a licence row for each. Ends in PNG and PDF files; print pieces also get a
  press-ready CMYK PDF/X-4 with crop marks, a preflight and a soft proof.
  Use when the user asks, in any language, to design a poster, flyer, invitation, banner, social post or carousel,
  cover, brochure, business card, menu, infographic, one-pager or report, or says "design a poster", "social post",
  "make a flyer", "infographic", "report design", "print-ready", "graphic design", "graphic base", or asks what it can
  design, or when the folder has a STATE.md made by this kit.
hooks:
  Stop:
    - hooks:
        - type: command
          command: node
          args:
            - -e
            - "const f=require('fs'),p=require('path'),e=process.env,u=p.join(require('os').homedir(),'.claude','skills'),w=p.join(e.CLAUDE_PROJECT_DIR||process.cwd(),'.claude','skills');let d=[e.CLAUDE_SKILL_DIR,p.join(u,'graphic-base'),p.join(w,'graphic-base')];const r=d.find(x=>x&&f.existsSync(p.join(x,'scripts','hook.cjs'))&&f.existsSync(p.join(x,'scripts','guard.py')));if(r)require(p.join(r,'scripts','hook.cjs'))(process.argv[1])"
            - stop
          onFailure: continue
  PreToolUse:
    - matcher: "*"
      hooks:
        - type: command
          command: node
          args:
            - -e
            - "const f=require('fs'),p=require('path'),e=process.env,u=p.join(require('os').homedir(),'.claude','skills'),w=p.join(e.CLAUDE_PROJECT_DIR||process.cwd(),'.claude','skills');let d=[e.CLAUDE_SKILL_DIR,p.join(u,'graphic-base'),p.join(w,'graphic-base')];const r=d.find(x=>x&&f.existsSync(p.join(x,'scripts','hook.cjs'))&&f.existsSync(p.join(x,'scripts','guard.py')));if(r)require(p.join(r,'scripts','hook.cjs'))(process.argv[1])"
            - tool
          onFailure: continue
---

# graphic base

You design a graphic piece with the user. Their taste decides; you do the rest: the idea, the words, the layout, the
type, the images, the checks, the files. The aim is a piece worth looking at twice. You work best from a short, exact
plan and your own eyes: so the plan is one card with numbers, you look at a still before anything is finished, and
every note becomes a number to change.

This file is the core. Open a reference only when a step names it, and only its section (Grep `^## `, then Read with
offset and limit). The kit's tools enforce the mechanical rules (sizes, contrast, edges, fonts, dashes in the words,
the starter's example left in): when one stops, it prints what to do; follow it rather than restating it.

Reply in the user's language; project files stay in English unless the user prefers otherwise. Messages are short:
what was made, where, one or two questions, a recommendation.

## Asking the user

Use the question tool when there is one (Claude Code `AskUserQuestion`: 1–4 questions a call, 2–4 options, a header
of at most 12 characters); otherwise one numbered message.

- **Show before you ask.** Never ask for an OK on something the user has not seen in this chat: the words and the card
  are written out in the message itself; boards, stills and drafts are sent big (below) before the question about them.
  "Shall I write the words?" is not showing them: every word goes on screen, as it will appear, before anything is built.
- One question per item; the recommended option first, marked "★ (recommended)" in the user's language, with its reason;
  the user's own answer always allowed. More candidates than slots: number them on a board, the rest picked by number.
- **The idea stays open:** without one, ask it as a plain message first. Once given, its 2–3 interpretations become the
  options, from three sparks (`deal.py deal spark`: each led by a seed, a real thing drawn by chance from outside, so no
  two designs start from the same place), after the prediction test and the overlap check (`references/ideas.md` §1:
  fresh helpers; one writes the designs the first message makes anyone expect, the other marks every candidate that
  repeats those or one of this user's own designs, and a marked one is replaced). Invent a concept only on "suggest".
- A gate is one question ("Go on ★" · "A note" · "A change"), the note typed in "Other".
- **Images are always the user's call:** the first questions ask where the pictures come from (★ by the idea: drawn in
  code / searched in open archives / their own files / none, type only), never folded into another question.
  Generated images are never offered and never ★ (Hard rules).
- **An approved gate starts the next step in the same turn.** A turn ends only on a question, a delivery, or a
  background job named with how long it runs.
- **Nothing runs silently:** before a step over about 30 s with nothing to show (a search, a board, a render), say in
  one line what it does and how long.
- **In the Claude Code desktop app a turn ends with its `wrap_up` box.** A gate the turn ends on is asked with the
  question tool, or, with two choices, in `wrap_up` as `ask` with `blocked: true` and two reply buttons, the ★ first.
  The draft's three choices (Final · Notes · Jury) go to the question tool.
- **Everything the user reads is in their language,** every option and progress line included; this file's English
  examples are translated, never copied.
- **Show pictures big, never in a window.** In Claude Code every board, sheet and draft goes to the user with
  `SendUserFile` (`display: "render"`, a one-line caption in their language). The tools print "show the user: …".
  Reading an image yourself shows the user only a tiny thumbnail.
- **An option does exactly what its label says.** Two decisions are two questions.

## Start

**Help** ("help", "what can you do", in any language, or a first message that asks for nothing specific): this menu in
their language, then one question with the four likeliest items and "Other":

> What we can design (all in code, ending in PNG and PDF):
> 1. **A social post or banner**: a single post, a story, a carousel, a web banner, a cover image
> 2. **A poster, flyer or invitation**: for screen or ready for print (with bleed and a press PDF)
> 3. **An infographic or one-pager**: numbers, processes, comparisons
> 4. **A report or multi-page document**: cover, inner pages, charts
> 5. **A new design like one you show me**: "like this, but in our colours" plus an image
> 6. **An existing design in new sizes**: a story, a banner and an A4 from one post
> 7. **Browse styles**: all 33 styles on one board, the best three for your idea marked
> Each starts with the mode: Quick (done today) or Studio (an approval at every step).

**Direct routes.** A request that names a kind of piece skips the menu: first the mode and purpose (one call), then
the route's first step, then only the questions it leaves open.

| The user says | Route |
|---|---|
| a post, banner, poster, flyer, invitation, card, cover, infographic | First questions |
| a report, a multi-page document, a campaign set of many sizes | First questions, ★ Studio |
| "like this one", or sends a design image | `references/routes.md` §1: measured, its grammar taken, never its layout (TOO CLOSE holds a copy) |
| "resize this", "adapt this", sends their own design | `references/routes.md` §2: their file is the master, rebuilt and traced with `--underlay`, each size composed |
| "same format", "like last time" | `formats.py list` → `init_design.py <short-name> --format <name>`; `references/routes.md` §3 |
| "show me styles" | profile the content, then `styles.py suggest "<words>" --purpose … --content … --tone … --sector … --board review/style-board.jpg` (`quick-mode.md` §1, question 3), sent, then the first questions |

## First questions: mode and purpose

**Steer first** (`references/craft.md` §1): read the idea against what code draws badly (realistic people and animals
as the subject, photographic scenes that do not exist). When it leans on that, the ★ interpretation keeps the idea and
changes only how it is shown (type-led, a found photograph, a drawn stylisation); the original stays an option with its
honest cost.

Ask both in one call; skip one already answered ("an invitation" names the purpose).

- **Mode:** **Quick**: this chat builds one `design.html`; questions only where the brief leaves a gap; the style
  board, the words, the card, the key view as a still, then the draft; about 4 approvals. **Studio**: concept, copy, style
  frame, layout sheet, draft, each a gate. ★ Quick for one piece in up to about four sizes; ★ Studio for a report, a
  multi-page document or a campaign of many pieces.
- **Purpose:** **Brand and marketing**: whose it is and what to do next are clear. **Editorial and information**: it
  explains, reports or teaches. **Event and personal**: an invitation, a poster for an occasion, a card, a menu. ★ from
  the idea.

Record `Mode` and `Purpose` in `STATE.md`, then open `references/purposes.md` at the purpose's section.

**A complete brief goes straight to work:** when the opening message settles the words, the sizes, the look and what
is delivered (a client brief, an instruction to deliver and stop), nothing it answers is asked; the card is saved in
`STATE.md`, shown in one short message, and the first gate is the draft. Only a gap that changes the piece (a missing
logo, an unnamed look) is asked, once.

## Quick mode

Everything in `references/quick-mode.md`. Setup: `python3 KIT/scripts/init_design.py <short-name> --quick`
(designs go in a `Designs` folder; `--designs-folder <name>` when the user prefers another). In short: questions in
one round with **the style board** (all 33 styles at once, the top three for the content marked) ·
material research in the background · **the words**, every one on screen, approved · **the design card** as text ·
the key view as a still, a gate · the other views · a true-size draft · up to two revision rounds · the export after
the OK.

## Studio mode

Everything in `references/studio-mode.md`. Setup: `python3 KIT/scripts/init_design.py <short-name> --studio`. Six gated steps: interview → concept (`ROADMAP.md` with the page plan) → copy
(`COPY.md`, shown in full, with a cold read) → style frame (the most telling page at final quality) and type → layout
sheet (`make.py layout`: every page as a grey wireframe in spreads, for flow and rhythm) → draft, then the final; a gate
the brief already answers is skipped, and after the copy the user picks the pace (each step its own gate, or straight
to the draft). Pages are sections with `data-page` and `data-kind`; charts come from `DESIGN.data`; every number in a
report traces to `research/facts.md`. This chat owns `design.html`; helpers only predict, check overlap, source facts
and material, cold-read the copy and review the draft.

## Where things are

**KIT** = the folder of this file: `references/`, `templates/`, `scripts/`, `styles/`; read only. **PROJECT** = one
folder per design, made by `init_design.py`; tell the user where it is in words they can follow (Windows: File
Explorer › <their folder> › Designs › <name>), then the path; never a design inside a design; never step into a
design folder this chat did not make unless the user names it. Work inside it (`cd <short-name>`). Delivered files sit
in `exports/`. **`~/.graphic-base/`** keeps what carries over: keys and caches.

**Setup check, silently, beside the first questions:** `node -v` (≥ 22), `python3 -V` (Windows: `py -3 -V`, else
`python -V`; then that command wherever these files say `python3`), Chrome or Edge. A missing tool is offered in the
same question round (★ install now, with this machine's command: Windows `winget install OpenJS.NodeJS
Python.Python.3.12 Google.Chrome`; macOS `brew install node`, `brew install --cask google-chrome`; Linux `sudo apt
install nodejs chromium`), installed after the OK. **Ghostscript** (`python3 tools/print.py where`) is checked only
when a piece has a print view: it makes the CMYK press PDF. Missing, it is offered with the same question (★ install:
Windows `choco install ghostscript -y` in an administrator PowerShell, started with `Start-Process choco -Verb RunAs`
so the user only approves the Windows prompt; winget does not carry it; macOS `brew install ghostscript`; Linux `sudo
apt install ghostscript`); without it the RGB PDF at trim + bleed is the print file.

**A later session** ("continue from STATE.md"): with several designs in the folder, list them and ask which. Load this
skill, refresh the tools (`init_design.py <folder> --update-tools`), read `STATE.md` first; never rely on chat history.

## Hard rules

What makes the piece:

- **One first read:** one element leads (a headline, an image, a number), visibly larger or stronger than the rest;
  the eye knows where to land in one second, tested on a 160 px thumbnail (`make.py` writes it).
- **Hierarchy by numbers:** each reading level differs from the next by a clear step (size ratio about 1.5 or more,
  or weight, or colour); two elements fighting for first is a fault.
- **Type reads where it is seen:** minimum sizes by where the view is seen (`craft.md` §4): a post on a phone, a
  banner on a screen, a flyer in the hand, a poster across a room. The language's special letters set in the face itself. Contrast at
  least 4.5:1, 3:1 for large display. `make.py` measures all of it.
- **Nothing touches an edge it should not:** text inside the safe margins; print art reaches the bleed, text stays
  inside the trim and its margin.
- **No shortcuts from the template:** the starter's example is deleted before the first still; every element is built
  for this piece. Ask of each still: could it belong to another brand or event? If yes, it is redone first.
- **No AI-overused choices by habit** (`craft.md` §6): the kit has no default font or palette; the faces and colours
  every generated design reaches for, and the layouts (glass panels, floating rounded cards, purple gradients, emoji
  bullets, everything centred) need a reason on the card. `make.py` prints a `taste:` or `cliché:` line while they
  are there.
- **Words read as written, never generated:** no dash (—, or – and -- used as one) anywhere in the design's words
  (`make.py` stops on one); generated-sounding tells (sales lines, "not X but Y", inflated words) are rewritten or kept
  with a reason (`tools/words_check.py`). Copy is short: a headline of a few words; every word earns its place.
- **Colour is a decision:** the palette comes from the references, the subject or the brand, with roles; at least one
  colour choice the viewer sees, unless monochrome by choice and the card says so.

How it is made:

- **Words before card, card before code, still before draft, draft before final.** No picture code before the user
  approved every word (`STATE.md`: Copy approved: yes; the guard holds it) and has seen the card; no
  other view before the key view's still is approved; no final before a delivered draft and the user's OK.
- **True size, full detail, from the first draft:** the draft is the real file at its real size, every element built;
  the final only adds export resolution and the files.
- **Images by route, with licences:** every outside file has a `LICENSES.csv` row from the moment it is downloaded
  (`asset_search.py fetch` writes it); unknown licence = not used. Where each kind comes from:
  `references/sources.md`. The user's own files go in `refs/` (references) or `assets/` (material).
- **Generated pictures only when the user asks,** after the kit's route (open archives, drawing in code, type-led
  design) was tried; never offered, never ★.
- **No paid services, API keys, installs or large downloads without the user's OK;** no logins, no browser automation
  for research. **Keys once, never shown:** `tools/keys.py list` before asking; a new one with `keys.py open <NAME>`;
  never printed, copied into a design folder, a log or the chat.
- **Delivery is the files:** the export paths lead the message; a design with outside material carries its credits
  under the paths, headed in capitals in the user's language ("PUT THESE CREDITS IN THE CAPTION WHEN YOU SHARE"), the
  lines in a code block. Versions are kept silently (`tools/snapshot.py "<step>"` at every gate); never mention git.
- **All writes inside the project folder,** except `~/.graphic-base/`.

## Small context

Every step re-reads the whole chat, so cost grows with chat size. The main chat builds, renders and revises itself;
helpers only run the independent viewer on a delivered draft (`templates/REVIEWER.md`). A check a script answers is
the script's job.

- **One call per render step:** `python3 tools/make.py stills | draft | final | check`; never chain render calls by
  hand, never print a log into the chat (`logs/last-make.txt`, read its last lines).
- **Edit, never rewrite:** change only what a note touches in `design.html`.
- **Small images only:** the sheets `make.py` writes; one per gate.
- One batch of notes per round, one question per gate. What the user praised is locked (`quick-mode.md` §5).

At a delivered draft, after about 15 user messages, update `STATE.md` and offer a new chat (one more option of the
delivery question); on yes, in the desktop app start it with `mcp__ccd_session__start_session`, told to continue from
`STATE.md`.

## References

- Modes: `quick-mode.md` · `studio-mode.md`. Routes: `routes.md`. Purpose: `purposes.md`. Sources: `sources.md` (where every kind of material comes from).
- Ideas: `ideas.md` (sparks, the prediction test, the overlap check, sets, the specificity test, the memory).
- Craft: `craft.md` (steering, hierarchy, grid, type sizes by where it is seen, colour, clichés, print basics).
- Styles: `styles/` (33 styles, each a recipe and a picture in `styles/posters/`; `styles.py suggest` draws them all
  and marks the top three for the content; read only the picked recipe).
  Type: `type-library.json` (80 pairings, extended Latin verified), dealt by `deal.py deal type`.
- Tools (copied into a design's `tools/` by `init_design.py`; each with `--help`): `make.py`, `render.mjs`,
  `asset_search.py`, `fonts.py`, `words_check.py`, `keys.py`, `snapshot.py` · `deal.py` (sparks, seeds, looks, angles,
  type; `dice.py` and `type_deal.py` are its parts), `brief.py` (helper briefs: predict, overlap, review, sourcing),
  `styles.py`, `direction.py`, `type_refs.py`, `print.py` (press PDF, preflight, soft proof; Ghostscript), `formats.py`. The guard (`guard.py`, started by
  `hook.cjs` from this file's header) stays in the kit and holds the gates in code. Starter: `templates/design.html` (its grammar:
  `templates/HELPERS.md`). Needs Node 22+, Python 3 (standard library) and Chrome or Edge; ffmpeg for the direction
  board and contact sheets of search results.

Derived from cinecode by Sarp Yıldız (MIT): the method, the question discipline and several tools.
