# Craft: what makes a graphic piece work

Read by section. Every rule here is a default a piece may break on purpose, named on the card with its reason, except
those marked **hard**, which `make.py` enforces.

## 1. Steering: what code draws badly, and the route that works

- **Realistic people and animals as the subject** (a face, a body in action, a pet): code draws them badly however long
  it works. Routes, ★ in this order: a found photograph (open archive, or the user's own); a stylised drawing that
  means to be drawn (silhouette, cut paper, a single line, a pictogram); the person shown through what they hold or
  touch; type instead of the picture.
- **A photographic scene that does not exist** (a product on a beach, a crowd at a concert): it cannot be photographed
  from an archive and code will not fake it. Routes: a composite of real cut-out pieces, an illustration, a type-led
  layout, or the user's own photography.
- **What reads as cheap:** clip-art icons as the hero, a stock photo with no relation to this brand, gradients and glow
  as decoration, a photo stretched or soft, many fonts, everything the same size, everything centred.
- When the idea leans on one of these, the ★ interpretation keeps the idea and changes only how it is shown; the
  original stays an option with its honest cost; if the user picks it, help fully.

## 2. Hierarchy and the first read

- **One first read (hard, measured on the thumbnail):** one element leads by size, weight, colour or isolation; at
  160 px wide the viewer still sees what the piece is about.
- **Three levels are enough** for most pieces: the hook (headline, image or number), the information (body, details),
  the action or the source (CTA, logo, legal). Each level differs from the next by a ratio of about 1.5 or more in size,
  or a clear change of weight or colour.
- **Size contrast makes design:** one element much bigger than everything else (a headline 4–8× the body) reads as
  intent; many medium sizes read as a template.
- **White space is a material:** what is left empty around the lead makes it lead. Fill a corner only for a reason.
- **The squint test:** at 96 px or with the eyes half shut, the light and dark masses still make a composition.

## 3. Grid and alignment

- A grid in `--u` (1 % of the trim width): margins 5–8 u on a post, 6–10 % of the short side on a poster; a gutter of
  2–4 u; columns as the content needs (1, 2, 3, 4, 6, 12).
- **One alignment per piece** as the default (flush left is the safe choice for reading; a centred axis for formal
  invitations and symmetry by intent; asymmetric for energy). Mixed alignment needs a reason.
- **Edges line up:** text, images and rules share left edges and baselines; an element 3 px off a line looks like a
  mistake, 30 px off looks like a choice.
- **Optical, not mathematical:** round letters and points overshoot; a headline set large is tightened (tracking −1 to
  −3 %); all caps are opened (+5 to +12 %); a hanging quote sits outside the text edge.

## 4. Type sizes by where it is seen (hard floors, measured)

| Seen | Body floor | Legal floor | Notes |
|---|---|---|---|
| phone (a post, story or carousel, shown about 390 px wide) | 11 px at phone size (about 30 px on a 1080 canvas) | 9 px (about 25 px on 1080) | headlines usually 70–160 px on a 1080 canvas |
| screen (web banner, slide, shown at its own pixels) | 14 px | 12 px | |
| print (in the hand: flyer, invitation, card, menu, report) | 8 pt | 6 pt | body text 9–11 pt; a card's name 10–14 pt |
| far (poster A3 and up, read from 2 m or more) | 18 pt | 12 pt | a headline is read from across the room: 60 pt and up on A3 |

**Story safe zones (9:16):** the top 14 % and the bottom 20 % are covered by the app's interface: nothing that matters
there; the right 12 % holds buttons. **Post grid crops:** a 4:5 post shows as a centred square in the profile grid:
the lead survives a 1:1 crop.

**Measure:** 45–75 characters a line for reading text; leading 1.3–1.5 for body, 0.9–1.1 for large headlines.
**The language's letters (hard):** every accented or special letter the words use (é ñ ø ł ř ő, Turkish İ ı Ğ Ş,
Vietnamese stacked marks) set in the face itself, never a fallback; Turkish "i" in all caps is "İ"
(`text-transform: uppercase` with `lang="tr"` does it right; check it).

## 5. Colour

- **Roles, not swatches:** ground, ink, accent, and at most two more. The accent is rare: on 5–15 % of the page it
  signals; everywhere it is noise.
- **From something real:** the references' measured palette, the subject (the product's own colour, the place's
  stone, the season), the brand, an era's print colours.
- **Contrast (hard):** text at least 4.5:1 against what is behind it, 3:1 for large display; over a photograph, put
  the text where the photo is calm, or lay a solid block behind it, never a text shadow as the fix.
- **Print reality:** a screen's bright RGB greens, blues and oranges dull on paper (they are outside what ink can
  print); a large field of pure black prints as dark grey unless it is a rich black (the printer sets it); small text
  in pure black, never in four-colour black.

## 6. AI-overused choices and clichés (as of November 2026)

Generated design drifts to the same few choices; viewers now spot them at once. Any of them can still be right when
the piece asks for it: write the reason on the card and use it on purpose.

| Tell | Why it reads as generic | Do instead |
|---|---|---|
| Inter, Roboto, Montserrat, Poppins, Space Grotesk, DM Sans, Playfair Display, Geist | the defaults of every tool and template | a face chosen by tone: `fonts.py search "<tone>"` |
| Purple-to-blue or blue-to-cyan gradients | the out-of-the-box palette of countless tools | a palette from the piece's own world; flat colour fields |
| Cream ground with terracotta accent | the "assistant" look | colours from the references, the product, the place |
| Frosted glass panels, floating rounded cards with soft shadows | the app-interface look on a page that is not an app | content laid on the page itself: rules, blocks, edges |
| Bento grids with giant numbers | the 2024–26 landing-page trope | one number, set huge, with its meaning |
| Emoji or generic line icons as bullets | says "made in a hurry" | the design's own marks (a numeral, a rule, a drawn sign) or an icon set used with intent |
| Everything centred | no decision about alignment | flush left by default; centre only a formal or symmetric piece |
| 3D blobs, abstract gradient meshes, sparkles | decoration with no meaning | the subject itself, or an abstract shape with a job |
| Stock photo of smiling people at laptops | belongs to no brand | the brand's own people, places and products, or no people |
| Headline + subline + button, centred, on every format | the landing-page hero applied to a poster | a layout built for this format and this idea |
| Text shadow or outline to rescue contrast | a fix that shows | move the text, change the ground, lay a block behind it |

## 7. Print basics (screen-first pieces skip this)

- **Trim, bleed, safe:** the trim is the paper's finished size; the bleed (3 mm each side by default) is art that runs
  past the trim so no white edge shows after cutting; the safe margin (at least 5 mm inside the trim) keeps text away
  from the knife. Backgrounds and full-bleed images reach the bleed edge (`.bleed`); text stays in `.safe`.
- **Resolution:** placed photographs at 300 ppi at their printed size (`make.py` measures it: under 150 holds, under 240
  notes). A 1080 px photo printed 10 cm wide is about 275 ppi; 20 cm wide is 137 ppi: too soft.
- **Vector where possible:** type, logos, icons and drawn shapes are vector in the PDF; only photographs are pixels.
- **Fonts:** embedded in the PDF by Chrome; the licence must allow it (OFL does).
- **Two print files from every print view** (`make.py final`, with Ghostscript):
  - `<title>-<view>.pdf`: RGB, trim + bleed, fonts embedded. For digital printers and online shops that ask for "a
    PDF with 3 mm bleed".
  - `<title>-<view>-press.pdf`: CMYK PDF/X-4 on a sheet with crop marks and a job line in a 10 mm slug, TrimBox and
    BleedBox set, an output intent, dark neutrals as 100 % K so small text never smears across four plates; text turned
    to outlines when a font could only be embedded as Type 3 (variable fonts usually are). For offset printers.
- **The printer's profile:** the press file uses Ghostscript's generic CMYK profile unless the printer gives theirs:
  `make.py final --profile <their .icc> --condition FOGRA39` (Europe coated: FOGRA39 or FOGRA51; uncoated: FOGRA52;
  US: GRACoL). Ask the printer for the profile, the bleed and the ink limit; their spec wins over every default here.
- **Preflight** (printed by `make.py final`): sheet and boxes, PDF/X version and output intent, fonts, colour spaces
  and total ink coverage (300 % by default; uncoated paper often 260–280 %). A HOLD is fixed before the files go out;
  a note is told to the user in one line.
- **Soft proof** (`review/proof.jpg`): screen colours beside the press file rendered back as ink on paper. Bright RGB
  greens, blues, oranges and pinks dull; show the proof with the final and say it in one line. The printer's own proof
  has the final word on colour.
- Without Ghostscript the RGB PDF is the print file; say: "for offset printing the printer converts it; ask for their profile".
- **Not covered:** spot colours (Pantone), varnish and foil plates, folds and die lines. Ask the printer when a piece
  needs them; build them as separate layers only on their spec.

## 8. Words on a design

- A headline is a few words that make the viewer stop; the body tells only what they need; the CTA is a verb and an
  object ("Book your seat", "See the menu").
- Never explain what the image already shows; never a moral; never three adjectives in a row.
- **Hard:** no dash in the design's words (comma, full stop, colon or a line break instead).
- Read every line as a native speaker of its language would say it. Numbers, dates and times in the language's own
  form (English: 14 November 2026, 7.30 pm; German: 14. November 2026, 19.30 Uhr; Turkish: 14 Kasım 2026, 19.30).
- Every claim and number has its source in `research/facts.md`.
