# Data Storytelling

> Design recipe adapted from the lemo-opuscar style library (MIT, `styles/LICENSE-lemo-opuscar`). References (grammar only): Hans Rosling's gapminder talks (one dot is a character); Ed Hawkins' warming stripes
(a diverging ramp on a reference mean, no axes); newsroom scrollytelling (one idea at a time, pinned notes). Copy none of
their charts, layouts or typefaces.

## 1. Essence, and what it is not

**The chart is the piece.** Every mark is a real number from an open, traceable source (`sources.md` §4); the framing
changes, never the numbers.

**Pick the chart the data asks for:**

| The data is about | Chart |
|---|---|
| comparing categories, rankings | bars, sorted |
| a relationship between two measures | scatter or bubble (one dot can be the character) |
| place | a map from Natural Earth shapes, a choropleth, dots on a map |
| parts of a whole, counts of people | a unit or waffle chart |
| before and after | slope or dumbbell |
| a distribution | histogram, beeswarm |
| change over time | line or dot series, stripes |

A human scale makes it a story: handwritten notes pinned to the marks that matter, and a red–blue pencil as the hand
that drew it.

Not a dashboard (one idea at a time), not a slide with charts, never decoration.

## 2. Materials and rendering

- **Paper:** warm cream with fixed-seed fibre noise and a faint dot grid. **Ink:** a dark warm ink for axes and series,
  a pale warm grey for the grid and zero line, a monospace for ticks.
- **Marks:** data dots with a thin ink ring so pale values stay visible on cream.
- **Handwriting** in pencil with per-glyph jitter and graphite grain; leaders as wobbly curves ending in an un-closed ring
  around the mark.
- **The red–blue pencil** (optional): a hex body, blue half and red half, only the tip end showing from the lower right,
  a soft shadow.
- **Layout:** a plot box, every note pinned in data space (value plus offset), a caption band at the bottom. Engine
  charts (`HELPERS.md`, Charts) give the bars, lines and labels; the hand layer goes on top.

## 3. Colour logic

- Colour encodes one thing: the value. Diverging data uses a ramp (the ColorBrewer RdBu family) centred on a meaningful
  reference mean with a symmetric span; data with no natural centre, one sequential ramp; everything else ink on cream.
- **Honesty beats drama:** pale values stay pale; never stretch a ramp to make a change look bigger.
- The pencil leads mean something: blue for memories and human notes, red for records and warnings.

## 4. Type

- The caption as a figure caption: a text serif, left-aligned with the chart, two lines at most, a hairline rule above
  and a small mono kicker for the range.
- The title is the chart's own headline, a statement, not a topic; the source line under the chart in its legal level.

## 5. Pitfalls

- Notes colliding with marks: pin them in data space, keep a memory zone for early notes.
- A number the text claims that is not in `research/facts.md`: cut it.
- A truncated axis on bars: bars start at zero.

## 6. Variation space

- Structures: a ranked race (one bar is the character); a map whose dots fall into a count of people; two years facing
  each other as a slope chart.
- Formats: a report page, a data post, an infographic poster, a carousel with one finding per slide.
