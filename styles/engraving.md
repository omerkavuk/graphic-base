# Copperplate Engraving

> Design recipe adapted from the lemo-opuscar style library (MIT, `styles/LICENSE-lemo-opuscar`). References (grammar only): 19th-century natural-history plates (a centred subject, numbered roundels, a roman
title over an italic name, "del." and "sculp." credits, the plate mark); Hogarth and Doré for the burin line; hand-
coloured plates for washes laid after printing. Never a plate, pose, border or title.

## 1. Essence, and what it is not

An **intaglio print:** the line is ink held in a groove a burin cut into copper. Three rules:

1. **Tone is made of lines, never fills:** light is bare paper; half-tone one family of parallel lines; shadow a second
   family crossing it; the deepest dark a third, lozenge-making family.
2. **Every line swells and tapers:** fine in, deep in the middle, out to a point; thicker where the form turns from the
   light. A uniform-width line reads as pen or vector: never.
3. **Colour comes after, by hand:** transparent watercolour laid flat region by region over the black print, spilling a
  little past the lines, ink always on top; often only one part coloured.

Not a woodcut (black block, white gouges), not a pen sketch, not an engineering drawing, not a sepia filter.

## 2. Materials and rendering

- **The sheet:** laid paper (cream, around `#f1e8d2`) with fibres, laid lines and sparse foxing; a pressed, bevelled
  plate mark and a ruled border.
- **Ink:** one warm near-black (around `#1c1510`); outlines heaviest, the first hatching from a hair (~0.18 px) to ~2 px,
  crossings thinner; spacing relative to the figure (~1/180 of its height) so small figures never go grey.
- **Swell law** for every hatch: width × (0.2 + 0.8·sin(πu)^0.7), tapered over the first and last ~22 %; families switch
  on by tone (about 0.14, 0.5, 0.75 on a 0–1 tone).
- **One light direction** (upper left); tone from the shape (pillow lighting, spheres and cylinders), never from
  texture; lines stop at the shapes in front.
- **Roundels:** a double-ruled circle magnifying a detail, a ruled ground with a white halo around the subject; hairline
  leaders from a dot on the part, a small italic figure number at the root.
- **Hand colouring** multiplied over paper and under ink: a little spill, slight misregister, a tide line at the wet
  edge, granulation.

## 3. Colour logic

- Two values, paper and ink; all tone is line density.
- Colour only as transparent wash in muted earth and mineral pigments, one stronger pigment at most; never on lettering,
  rules or paper outside the figure.
- Washes: an amber insect with blue-grey wings; a sea-green coastal band on buff land; one rose organ on a black anatomy
  plate.

## 4. Type

- Roman capitals for the title (wide tracking), italics for scientific names, a script for notes; small caps for plate
  numbers and credits.
- Every label belongs to the plate: never shrunk to fit; balanced over two lines when long.

## 5. Pitfalls

- Uniform width reads as pen: swell every hatch, pinch contours between runs.
- Overlaps without occlusion: lines stop at what is in front.
- Outline-only parts beside a hatched body: hatch along each part's axis.
- Leaders hugging the subject read as crossing it: clearance.

## 6. Variation space

| Use | Order of information |
|---|---|
| Museum label or case card | title and scientific name → details with terms → where to see it |
| Textbook figure | figure → parts labelled one by one → caption |
| Craft heritage | object → 2–3 craft details → maker and edition |
| Certificate | a framed plate, a name in script, a roman title, a seal |

Formats: a certificate, a premium label, a heritage brand plate, a classic invitation, a museum poster.
