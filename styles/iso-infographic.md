# Isometric Infographic

> Design recipe adapted from the lemo-opuscar style library (MIT, `styles/LICENSE-lemo-opuscar`). References (grammar only): true-isometric game architecture (flat colour blocks, three fixed tones per face);
cutaway city-builder dioramas (a floating board with soil strata); science explainers (one clear visual metaphor per
step); Isotype by Otto Neurath and Gerd Arntz (repeated identical icons stand for quantity). Use none of their
characters, buildings, icons or palettes.

## 1. Essence, and what it is not

- **Flat, true isometric:** no perspective, no outlines on solids; shapes separated only by the three tones of each
  face.
- **Infographic furniture is part of the picture:** leader lines, label pins, dashed cut lines, hatched section faces, a
  legend and a route line live in the world.
- **Numbers built from icons** (Isotype), and they add up.
- **A diorama:** the system on a floating board with a visible cross-section at its edges, on a pale ground.

Not low-poly 3D (no perspective or lighting beyond three tones), not a flat 2D explainer, not a blueprint.

## 2. Materials and rendering

- **Projection:** axes at 30°: `sx = (x − y)·cos30°·k`, `sy = ((x + y)·½ − z)·k`; painter depth x + y + z, everything
  sorted before drawing (SVG in that order).
- **Three tones per face** from one base: the top mixed ~20 % toward warm white, the right side ~22 % toward a cool dark
  (e.g. `#231A2C`), the left the base.
- **Ink lines** (2 px) only for leaders, pins, cut lines, routes and labels.
- **The board:** on a pale ground with a faint isometric dot lattice and a soft shadow; its front faces show strata
  (soil, water, floors, pipes).
- **People:** minimal figures (round head, tapered two-tone body, an arm stroke, a hat for identity, no faces).
- **Composites** (a terraced hill, a crane on a ship) drawn as one ordered item; generic sorting fails on them.

## 3. Colour logic

- A pale neutral ground and 5–7 flat hues, each with its three tones; one ink colour.
- Colour codes meaning, like a legend: one hue per material or role; never one hue for two meanings.
- **Focus and context:** when one thing matters, everything else desaturates toward warm grey.
- Examples: a coffee chain: coffee red, leaf green, sea blue, soil, mustard on cream; a hospital: teal, coral, lavender,
  steel on pale grey; a data centre: electric blue, amber, graphite, mint on off-white.

## 4. Type

- One geometric sans: titles in caps with ~0.12 em tracking, big numbers with units at half size, a halo in the ground
  colour behind all text.
- **Label pins:** dot, vertical leader, horizontal rule, text; up or down, left or right, never over the subject.
- The legend as an end block: title, totals, the Isotype key, sources, "not to scale".

## 5. Pitfalls

- Faces culled the wrong way: give every face an outward hint.
- A wheel touching the wrong surface reads as an accident: visible clearance.
- An object with the wrong silhouette reads as something else (a white box with a red roof is a house): give machines
  their tell-tale parts.

## 6. Variation space

- Structures: one building floor by floor in a cutaway; two boards compared; a cycle route with one number changed.
- Formats: an infographic poster, a report spread, a process carousel, a city or tech data post.
