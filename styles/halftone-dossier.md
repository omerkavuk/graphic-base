# Halftone Dossier

> Design recipe adapted from the lemo-opuscar style library (MIT, `styles/LICENSE-lemo-opuscar`). References (grammar only): Ben-Day-dot pop-art printing for dot density as shading; offset overprint zines for
multiply layers and misregistration; mugshot height charts and case-file folders for the framing; variety-show caption
bars for the keyword highlight.

## 1. Essence, and what it is not

- **Everything is paper:** a warm cream sheet with low mottling, fine grain, a vignette and a fold; dark pieces are
  printed on it too, never glowing.
- **Shading is never a gradient:** halftone dots whose size follows a density field; two or three dot layers at
  different screen angles overprint (multiply).
- **Bureaucratic apparatus:** case numbers, file chips, numbered exhibits, height charts, name plates, stamps; their
  seriousness frames the subject, grave or trivial.
- **Loud but readable:** one big headline, one exhibit or gag, one caption line per page or slide.

Not risograph (no grainy two-ink zine look as the whole), not Swiss (no clean grid on white), not a candy game-show
look. Dots, paper and stamps visible everywhere.

## 2. Materials and rendering

- **Paper layer** multiplied over everything: mottling, warm noise, a radial vignette, a faint centre fold; a few hundred
  paper and ink specks (dust on the print).
- **Halftone:** a rotated grid of circles; step 20–26 px at 1080 px; a different angle per layer; radius = density ×
  step × 0.6–0.72 (around 0.7 dots merge into solid); density fields radial (halos), edge (dots crowding the border) or
  linear (lit from above); the second layer multiplied.
- **Halftone-filled numerals and shapes:** a flat fill overprinted by a darker halftone clipped to the glyph; giant
  numerals may bleed off the page.
- **Characters:** chunky shapes with a heavy ink outline (~7 px), flat fills, glossy eyes (an ink ellipse and two
  highlights).
- **Stamps:** a double rounded rectangle and bold text through a coarse ink-grain filter, ~93 % opacity, tilted ±10°.
- **Props:** starbursts, speech bubbles, radial rays, sticky notes, folders, clocks: flat fill and ink outline.

## 3. Colour logic

- A paper ground, one dark ink and four or five flat spot inks; the dark ink (navy, black-brown or deep green) carries
  outlines, body text and the caption bar.
- One ink is the overprint shadow (misregistration offsets); one the highlight for keywords and numerals; one warm red
  for stamps and alarms. Flat inks only: tone from dot size and overprint.
- A "secret" page flips to a dark ink ground with a lighter dot layer of the same family.
- Palettes: cream / navy / cobalt / hot pink / yellow / red; manila / sepia-black / teal / mustard / vermilion; off-white
  / forest green / tomato / sky / ochre.

## 4. Type

- Headlines in a black-weight serif or slab, left near the margin, with a misregistration shadow (+8/+8 px in the
  overprint ink).
- A fat rounded display face for names, big numbers and times; a heavy monospace for case numbers, dates, rulers.
- The **caption bar:** a dark-ink rounded pill with an overprint offset shadow, paper-coloured text, the keyword in the
  highlight ink.
- Stamps in one or two words (CLOSED, APPROVED), the language's letters checked.

## 5. Pitfalls

- Dots under ~14 px step alias into moiré: keep the step up; check the export at 100 %.
- Too many inks lose the print feel: five plus paper at most.
- Clip-path ids are global: every clipped numeral needs its own id.

## 6. Variation space

- Structures: a declassified report unredacted page by page; a missing-person file worked backwards; an insurance claim
  where each exhibit contradicts the statement.
- Formats: an investigative carousel, a retro campaign poster, a news-style post, a report's chapter openers.
