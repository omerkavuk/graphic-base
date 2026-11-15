# Woodcut Print

> Design recipe adapted from the lemo-opuscar style library (MIT, `styles/LICENSE-lemo-opuscar`). References (grammar only): the wordless woodcut novels of Frans Masereel and Lynd Ward, told in self-contained
plates; Käthe Kollwitz's woodcuts, where emotion lives in the direction of the gouge; Gustave Doré's engraving, where
line spacing and direction build light and volume. Never their plates, figures, borders or titles.

## 1. Essence, and what it is not

The page is **one printed plate**: black ink on laid paper, inside a paper margin. Three rules of relief printing:

1. **Black is the wood, white is what the knife removed.** Light is carved: a bright area is many wide cuts, a dark
   area untouched wood.
2. **Cuts follow the form,** coarse gouges for big light, fine lines for detail.
3. **The block is a mirror:** carved lettering reads backwards on the block, forwards on the print.

Not copperplate engraving (no swelling burin lines on white), not linocut poster art (no flat colour areas), not a
photo through a threshold filter (the cuts must follow the form).

## 2. Materials and rendering

- **Print frame:** the image inside a paper margin, wider at the bottom for the caption; the image edge is the block
  edge: ragged ink, never a clean rectangle.
- **Knife classes** (at 1080 px wide): knife 1–2 px for contours and the white halo between a black figure and a black
  ground; V-gouge 2–8 px for hatching and hair; U-gouge 10–22 px for rays and sky; stabs (r 3–8 px) for snow and sparks.
- **Hatching:** direction follows form (arcs wrap round things, slopes follow the fall line, light radiates); width
  follows tone (bright = wide cuts, mid = thin, dark = none); far = dense and fine, near = sparse and coarse; every cut a
  separate tapered stroke (30–160 px, blunt entry, chipped edge), never a machine line.
- **Figures:** a black silhouette, a white knife halo, grazing-light hatching on the lit edge only; skin carved white,
  features left black.
- **Print character:** knife burr on edges, ±6 % ink unevenness, wood-grain streaks, specks where ink didn't take; an
  SVG filter (turbulence plus displacement) at a fixed seed.

## 3. Colour logic

- Two values carry everything: near-black ink and warm laid-paper white.
- **At most one colour plate,** printed only where white was carved, so it glows out of the cuts; reserved for the one
  thing that matters (a flame, a heart, a signal lamp): burnt copper for heat, Prussian blue for water or night,
  oxblood for a seal.

## 4. Type

- Captions in letterpress in the paper margin below the plate, an old-style face, never over the image.
- Titles carved, not typed: cut into a black panel in the same knife grammar.

## 5. Pitfalls

- White marks on white areas are invisible: stab cuts need dark masses behind them.
- Hatching every surface looks like fur or rain: grazing light, 3–6 cuts on the lit edge only.
- Black faces with white cuts don't read small: skin white, features black, a keep-line around white parts.
- Short wobbly hatches turn into zig-zags: long cuts, one broad highlight band, a thin rim light.

## 6. Variation space

- Structures: a book of hours (seven plates, one per hour); one plate with a single colour for the thing that burns;
  two places printed on one sheet.
- Formats: a book cover, a folk festival poster, a craft brand label, a report's chapter openers.
