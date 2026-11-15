# Sources: where each kind of material comes from

Read the section the need names, never the whole file. The rule under every row: **a file enters a design only with a
`LICENSES.csv` row, written at download time; unknown licence = not used.** `asset_search.py fetch` writes the row by
itself; anything the user or you bring in by hand gets its row written by hand in the same columns.

Three kinds of source, never confused:

- **Searched by the kit** (`asset_search.py`, official APIs): the first stop for photos, artworks, illustrations,
  icons and textures.
- **Fetched by hand from an open library** (fonts, maps, data, patterns): a known file at a known address, its licence
  on its page. Download only with the user's OK when it is large (over about 50 MB) or needs an account.
- **Mood only** (inspiration sites, design archives, other people's work): looked at, never placed in a design. Mood
  references sit in `research/` and never reach `exports/`.

The kit never logs in, never scrapes a site against its terms and never drives a browser for research. A site that has
no API and no open download is a place to send the user ("save what you like into `refs/`"), not a place to take from.

## 1. Which need, which source

| Need | First | Then | Licence to expect |
|---|---|---|---|
| A real place, object, animal, plant | `wikimedia`, `openverse` | `smithsonian` (key), `nasa` for space and Earth | per file: CC0, PD, CC BY, CC BY-SA |
| Fine art, prints, posters, old engravings | `aic`, `cleveland` | `met`, `rijks` (opt-in), `openverse --type illustration` | CC0 / PD |
| Contemporary photos (people, food, work, cities) | `unsplash`, `pexels` (free keys) | `pixabay` (key), `openverse` | Unsplash / Pexels / Pixabay licences: free, no credit owed (give it anyway) |
| Vintage illustration, botanical and scientific plates | `openverse --type illustration` (Biodiversity Heritage Library, rawpixel PD) | `aic`, `smithsonian` | CC0 / PD |
| Diagrams, maps, flags, coats of arms as SVG | `wikimedia --type illustration` | Natural Earth (§3) | per file; flags and arms are often PD but trademarks and official emblems have their own rules |
| Icons | `iconify` (`--type icon`) | name the set: `--q "leaf prefixes:tabler,ph"` | the set's licence, recorded per icon (MIT, ISC, Apache 2.0, CC0, CC BY) |
| Paper, card, fabric, concrete, wood, metal surfaces | `ambientcg`, `polyhaven` (`--type texture`) | | CC0 |
| Fonts | `fonts.py` (Google Fonts and Fontsource, pinned) | §2 | SIL OFL 1.1 mostly; check each family |
| Data for charts | §4 | | CC BY mostly: credit on the design or in its notes |
| Type and layout inspiration | §5 (mood only) | the user's own `refs/` | never placed |

When two sources answer, prefer: **the user's own material** › **public domain / CC0** › **CC BY** › **CC BY-SA** (it
can carry its share-alike terms over to the whole design: say so to the user before using one) › stock licences.

**Choosing between search hits:** pick by what the design needs to show (the angle, the light, the part of the thing
that is seen), never the first hit; drop tourist snapshots, watermarks, another brand's product, AI-generated pictures,
and anything whose subject is cut where the layout needs it whole. A thin board is better than a weak one.

**Real people:** a photograph of a recognisable person in an advertising or brand design needs a model release, which
open archives almost never have. CC0 frees the photograph, not the person in it. For brand and marketing pieces, use
people only from the user's own material or stock that states it carries releases; say so in one line.

## 2. Fonts

Use the kit's `fonts.py` first (it ranks 2,000+ open fonts by tone and leaves out the faces AI design overuses). When a
direction asks for something it does not hold, these libraries are open:

| Library | What it holds | Licence | How |
|---|---|---|---|
| Google Fonts (fonts.google.com) | about 1,800 families, most with Latin Extended | SIL OFL 1.1, some Apache 2.0 | through Fontsource on jsDelivr, pinned: `@fontsource/<family>@<version>` |
| Fontsource (fontsource.org) | Google Fonts plus other open families as npm packages | each family's own (read its `LICENSE`) | pinned CDN, as above |
| Velvetyne (velvetyne.fr) | experimental and display faces | SIL OFL 1.1 | download by hand from its page |
| Collletttivo (collletttivo.it) | contemporary display and text faces | SIL OFL 1.1 | download by hand |
| The League of Moveable Type (theleagueofmoveabletype.com) | classic open display faces | SIL OFL 1.1 | download by hand |
| Open Foundry (open-foundry.com) | curated open faces with specimens | SIL OFL 1.1 | download by hand |
| Fontshare (fontshare.com, Indian Type Foundry) | quality grotesques and serifs | ITF Free Font License: free for commercial use, **not** OFL; the files may not be redistributed | the user downloads the files into `fonts/`; never committed or shared |
| Use & Modify (usemodify.com) | a curated list of open faces from many foundries | each face's own | read the licence on the face's own page |

Every family gets a `LICENSES.csv` row (family, version, licence, URL). Print PDFs embed the fonts: OFL allows it.
Test every text box with the language's special letters (a check string such as `ÀÉÎÕÜ àéîõü ŁŘŐ ĞİŞ ğış`) before
a draft; a family without them is not a choice for those words, however good it looks.

## 3. Maps and geography

| Source | Use | Licence |
|---|---|---|
| Natural Earth (naturalearthdata.com) | country, coast, river and city shapes at 1:10m, 1:50m, 1:110m, for drawn maps | public domain |
| OpenStreetMap (openstreetmap.org) | street-level data | ODbL: the design must carry "© OpenStreetMap contributors" |
| Wikimedia Commons maps (`--type illustration`) | ready SVG locator and historical maps | per file |
| NASA Visible Earth / Earth Observatory (`nasa`) | satellite images, night lights, relief | NASA media guidelines |
| USGS (usgs.gov) | US topography, imagery | mostly public domain (US government work) |

Draw maps in code from Natural Earth shapes (an SVG path per country) rather than placing a screenshot of a map
service: tiles from Google, Apple or Mapbox are not open and are never placed.

## 4. Data for charts and infographics

| Source | Holds | Licence |
|---|---|---|
| Our World in Data (ourworldindata.org) | charts and datasets on health, energy, climate, economy | CC BY 4.0 |
| World Bank Open Data (data.worldbank.org) | development indicators by country and year | CC BY 4.0 |
| UN Data (data.un.org), UNDP Human Development Reports (hdr.undp.org) | population, development indices | open with attribution: read the terms page |
| Eurostat (ec.europa.eu/eurostat) | EU statistics | reuse allowed with acknowledgement |
| National statistics offices (ONS, INSEE, Destatis, TÜİK, …) | official statistics of one country | credit the source |

A chart's numbers come from a named source with its year; the source line is on the design (small, in the legal
line) or in the delivery notes. Every number on a design traces to a row in `research/facts.md`. Chart colours come
from the design's palette; for a sequential or diverging scale that must stay readable, ColorBrewer's schemes
(colorbrewer2.org, Apache-style licence) are a sound start.

## 5. Inspiration: mood only, never placed

Look here to decide how a piece should look; take its grammar (grid, scale, colour logic, type behaviour), never its
images, layout or words.

| Site | Good for |
|---|---|
| Fonts In Use (fontsinuse.com) | real type in real work, by format (posters, branding, editorial, packaging) and by face |
| Typewolf (typewolf.com) | pairings, the faces sites use now |
| Are.na (are.na) | curated channels (Swiss posters, risograph, editorial grids); its public API allows reference use |
| Letterform Archive online (oa.letterformarchive.org) | lettering, posters and print history, high-resolution |
| Museum für Gestaltung eMuseum (emuseum.ch) | the Swiss poster collection |
| Cooper Hewitt collection (collection.cooperhewitt.org) | design objects, posters, wallcoverings; its metadata is CC0 (images vary) |
| Poster House (posterhouse.org), International Poster Gallery (internationalposter.com) | posters by era and movement |
| Typographic Posters (typographicposters.com) | contemporary type-led posters |
| Behance, Dribbble, Pinterest | trends only: much of it is the AI-average look itself; never a reference for "fresh" |

The user's own references outrank all of these: ask for 3–8 images in `refs/` (screenshots, photos, saved posts).

## 6. Generated pictures

Never offered and never ★. A connected image generator is used only when the user asks for it, after the kit's own
route (open archives, drawing in code, type-led design) was tried; its output gets a `LICENSES.csv` row naming the
service and its terms.

## 7. What is never used

- Anything marked NC (non-commercial) or ND (no derivatives), whatever the purpose: a design is changed and often
  used commercially.
- Images found through a general web search with no licence on the page.
- Logos, trademarks and product photos of other brands, unless the design is for that brand and the user supplies them.
- Stills from films, screenshots of other people's designs, and Behance or Dribbble work: mood only.
- Map tiles from commercial services.
