# design.html: the engine's grammar

One HTML file per design. Edit three blocks: **DESIGN** (data), **STYLE** (CSS), **VIEWS** (one `<section>` per size).
Never edit the ENGINE block at the bottom; `init_design.py --update-tools` never touches `design.html`.

## DESIGN block

```js
const DESIGN = {
  title: 'Winter Concert',         // export names: exports/Winter-Concert-<view>.png
  purpose: 'event',                 // brand · editorial · event
  lang: 'en',
  views: [
    { id: 'poster', label: 'A3 poster', w: 297, h: 420, unit: 'mm', bleed: 3, safe: 8, dpi: 300, seen: 'far' },
    { id: 'post', label: 'Post 4:5', w: 1080, h: 1350, unit: 'px', safe: 0.06, seen: 'phone' },
    { id: 'story', label: 'Story', w: 1080, h: 1920, unit: 'px', safe: { top: 0.14, right: 0.12, bottom: 0.2, left: 0.06 } },
  ],
  palette: { ground: '#…', ink: '#…', accent: '#…', muted: '#…' },
  type: {
    display: { family: 'Fraunces', pkg: 'fraunces', version: '5.2.9', weights: [400, 700, 900], subsets: ['latin', 'latin-ext'] },
    text: { family: 'Literata', pkg: 'literata', version: '5.2.8', weights: [400, 700], subsets: ['latin', 'latin-ext'] },
  },
  check: { strings: ['Winter Concert', 'ÀÉÎÕÜ àéîõü ŁŘŐ ĞİŞ ğış'] },
};
```

- **views:** `unit: 'px'` sizes are the file's pixels (`scale: 2` on a view exports it at double density).
  `unit: 'mm'` is the trim; `bleed` (mm) is added on every side; `dpi` sets the final PNG's resolution (default 300);
  the PDF is vector at trim + bleed. `safe`: one number or per side; a share of the width for px views, mm for print.
  `seen`: phone · screen · print · far (the type-size floors, `craft.md` §4); default phone for px views up to 1440
  wide, screen above; print for mm views, far from A3 up.
- **type roles** come from `python3 tools/fonts.py role <id>` (a JSON line to paste) or from a dealt pairing. Local
  or brand files: `{ family: 'Brand Sans', files: { 400: 'fonts/BrandSans-Regular.woff2', 700: 'fonts/BrandSans-Bold.woff2' } }`.
  A role left `null` uses the system fallback and holds the draft.
- **check.strings:** every role must set these with real glyphs: the headline and a line of the language's special letters at least.

## Variables and classes the engine gives each view

| Name | What |
|---|---|
| `var(--u)` | 1 % of the trim width: every size in the layout is a multiple of it (`calc(var(--u) * 8)`) |
| `var(--ground)`, `var(--ink)`, `var(--accent)`, `var(--<role>)` | the palette roles |
| `var(--display)`, `var(--text)` | the font stacks of the type roles |
| `var(--trim-w)`, `var(--trim-h)`, `var(--bleed)` | the trim size and the bleed, in CSS px |
| `var(--safe-t)` … `var(--safe-l)` | the safe margins from the outer edge (bleed included) |
| `.safe` | an absolute box inside the safe margins: put text here |
| `.trim` | an absolute box at the trim line |
| `.bleed` | an absolute box to the outer edge: backgrounds and full-bleed images |

Each section is `position: relative; overflow: hidden` at its full size (trim + bleed for print). Style per view with
`[data-view="story"] .headline { … }` when a size needs its own layout.

## Pages (reports, booklets, carousels)

One section per page, all sharing the view's size:

```html
<section class="view k-cover" data-view="report" data-page="1" data-kind="cover">…</section>
<section class="view k-text" data-view="report" data-page="2" data-kind="opener">… <span data-folio="2"></span></section>
```

- `data-kind`: cover · opener · text · data · image · quote · breather · closer (make.py checks the rhythm: never three
  of one kind in a row).
- `data-folio`: the engine writes the page number into it (`data-folio="2"` pads to 2 digits).
- Renders: `report-p01.png`, `report-p02.png` …; one `report.pdf` with every page; for print, `report-marks.pdf` with
  every page on its own sheet with crop marks. `make.py stills --views report --pages 1,5` renders chosen pages;
  `make.py layout` draws every page as a grey wireframe in spreads.
- A screen view with pages (a carousel: 1080×1350 slides) also gets a PDF of all slides (LinkedIn document posts).

## Charts

```js
data: {
  growth: { type: 'bar', unit: '%', decimals: 0, highlight: '2025',
            items: [{ label: '2022', value: 12 }, { label: '2023', value: 18 }, { label: '2025', value: 31 }] },
  regions: { type: 'hbar', highlight: 'Ege', items: [{ label: 'Marmara', value: 41 }, { label: 'Ege', value: 23 }] },
  trend: { type: 'line', unit: ' mt', labels: ['2019', '2020', '2021', '2022'], highlight: 'Porto',
           series: [{ name: 'Porto', values: [3, 4, 6, 9] }, { name: 'Lyon', values: [2, 3, 3, 4] }] },
},
```

`data` sits in the DESIGN block beside `palette`. Markup: `<div data-chart="growth" style="width: calc(var(--u)*60);
height: calc(var(--u)*40); font-size: calc(var(--u)*2.6)"></div>`. The box's size and font size set the chart's; the
highlighted item or series takes `var(--accent)`, the rest `var(--chart-muted)` (falls back to `var(--rule)`); labels
sit on the marks, numbers in the design's language format. Put the source line under it (`data-role="source"`).

## Rules the checks rely on

- Text elements carry `data-role`: `headline`, `body`, `cta`, `details`, `label`, `legal` (`legal`, `credit`,
  `caption`, `source`, `footnote` get the legal floor).
- Colours only through the palette variables; images as `<img src="assets/…">` (or a CSS `background-image`) so the
  engine waits for them and measures their resolution.
- SVG drawn in the page (inline `<svg>`) for shapes, icons and charts: it stays vector in the PDF.
- Nothing random: a pattern or texture made in code uses a fixed seed (a small hash of the index), so every render is
  the same.
- No external scripts or stylesheets besides the pinned font files the engine loads.

## Opening it in a browser

Double-click `design.html` (or open it in the browser pane): every view side by side, scaled to fit, labelled.
`design.html?guides=1` draws the safe area (dashed) and the trim line (print views).
