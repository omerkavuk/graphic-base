# Risograph Print

> Design recipe adapted from the lemo-opuscar style library (MIT, `styles/LICENSE-lemo-opuscar`). References (grammar only): Tom Haugomat's riso illustrations (colour fields and silhouettes, a small figure in a
large world, extra colours made by overprinting); real riso prints (translucent inks, misregistration, pinholes, feed
streaks). Copy none of their characters, compositions or palettes.

## 1. Essence, and what it is not

A risograph prints **one colour at a time:** each colour its own stencil ("plate") with its own drum of translucent ink.
That one fact makes the look:

- **A tiny palette:** 2–3 spot inks on warm off-white paper.
- **Overprint mixing:** inks multiply, so two inks make a third and all three approach black; a tint of one ink over a
  solid of another gives the brightest mixes.
- **Misregistration:** every plate lands a few px off; edges show slivers of paper or a coloured halo.
- **Halftone dots** for mid-tones, each plate on its own screen angle; **imperfect ink:** pinholes in solids, streaks
  along the feed direction, blotchy density.
- **Flat shapes, no outlines.**

Not flat vector art with a noise overlay (every colour comes from the plates), not CMYK pop-art halftone (no process
colours, no keyline), not screen print (riso ink is translucent and grainy). Never the RISO brand or machine; ink names
are colour references only.

## 2. Materials and rendering

- **Plates as layers:** draw each ink as its own layer (an SVG group or a canvas), each in the ink colour with
  `mix-blend-mode: multiply` over paper, so overlaps overprint for real; knockouts as paper-coloured shapes on a plate.
- **Per plate:** a fixed offset of a few px and a tiny rotation (misregistration, seeded); a halftone screen for tints
  (a dot pattern at ~6–8 px period at 1080 px wide, plates ≥ 15° apart in angle; ≥ 90 % prints solid); grain on the dot
  edge, pinholes in solids, a faint feed-direction streak.
- **Composition rules:** every area uses at most two plates, one of them as a tint (three halftones = mud); big flat
  shapes, lots of solid paper and solid ink; tints in a few stepped bands (20 / 40 / 60 / 100 %).
- **A paper-white halo** (4–5 px) around figures, so plates misregister around them like a real trap.
- **Design for one plate:** every main colour contains some of the first plate, so a one-ink version still reads.

## 3. Colour logic

- **2–3 spot inks, never more,** plus paper; every other colour is an overprint or a tint; no gradients except stepped
  halftone.
- Pick inks whose pairs mix into useful colours; at least one must carry a silhouette alone.
- Paper warm off-white (around `#F4EEE2`), never pure white; paper white is a colour (knockouts, highlights).
- Skin as a light tint of the palest ink: dots of a saturated ink on skin look like a rash.
- Ink sets: Blue `#0078BF` + Yellow `#FFE800` + Fluorescent Pink `#FF48B0`; Teal `#00838A` + Fluorescent Orange
  `#FF7477`; Federal Blue `#3D5588` + Red `#FF665E` + Sunflower `#FFB511`.
- Print note: fluorescent inks have no CMYK equivalent; a press file loses them (say so, or print real riso).

## 4. Type

- Type is printed: on one plate, so it misregisters and grains with it; a title on two plates with a visible offset is
  the riso double-hit.
- A heavy grotesque for titles, a geometric sans for text; text on a paper-white knockout strip catches the fringes.

## 5. Pitfalls

- Three halftoned plates in one area = mud: two plates, one tint.
- JPEG smears saturated dots: export PNG, check at 100 % and 50 % for moiré.
- A main colour without the first plate floats loose: build colours up from the one-ink silhouette.

## 6. Variation space

- Structures: two inks in dialogue, overlapping only at the climax; one subject per plate; a zine of two-plate pairings.
- Formats: a gig or zine poster, a festival flyer, an art print, an indie brand post set.
