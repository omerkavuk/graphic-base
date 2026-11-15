#!/usr/bin/env python3
"""Search open collections for a design's material (photos, artworks, illustrations, icons, textures), then fetch the
picks with a LICENSES.csv row (Python 3 stdlib; ffmpeg optional, for contact sheets). KIT/references/sources.md says
which source serves which need.

  python3 tools/asset_search.py search --q "<subject>" --out research/<subject>                 # photos and artworks
  python3 tools/asset_search.py search --q "<subject>" --sources met,cleveland --out research/<subject>
  python3 tools/asset_search.py search --q "<a plant, an animal, a machine>" --type illustration --out research/<x>
  python3 tools/asset_search.py search --q "leaf" --type icon --out research/icons             # SVG icons, open sets only
  python3 tools/asset_search.py search --q "paper" --type texture --out research/paper           # CC0 surfaces
  python3 tools/asset_search.py supply --q "<element>" --q "<element>"     # what the archives hold, nothing downloaded
  python3 tools/asset_search.py fetch --results research/<x>/results.json --pick 2,5 --dest assets/img
  python3 tools/asset_search.py board --dirs research/<a> research/<b> --per 3 --refs refs --out research/board-v1

Sources (official APIs only, no browser, no scraping):
  wikimedia    Wikimedia Commons: photos (--type image) and SVG drawings, maps and diagrams (--type illustration);
               licence per file
  openverse    Openverse: openly licensed images gathered from Flickr, museums and many sites; CC0, PDM, CC BY, CC BY-SA
               only; licence and attribution kept per item
  aic          Art Institute of Chicago: public-domain artworks (CC0 images, up to 3000 px)
  cleveland    Cleveland Museum of Art Open Access: CC0 artworks and objects (up to 3400 px)
  met          The Metropolitan Museum of Art Open Access: public-domain objects (CC0); opt-in (slow: one call per object)
  rijks        Rijksmuseum: public-domain artworks, prints and photographs; matches titles; opt-in
  nasa         NASA Image and Video Library (credit NASA, no endorsement implied)
  smithsonian  Smithsonian Open Access: CC0 objects, specimens, posters, photographs; needs a free key once:
               keys.py open SMITHSONIAN_API_KEY (api.data.gov)
  unsplash     Unsplash: contemporary photos (Unsplash License: free, no credit owed, credit given anyway; not for
               a competing stock service); key: keys.py open UNSPLASH_ACCESS_KEY
  pexels       Pexels: contemporary photos (Pexels License, like Unsplash); key: keys.py open PEXELS_API_KEY
  pixabay      Pixabay: photos, illustrations and vectors (Pixabay Content License); key: keys.py open PIXABAY_API_KEY.
               AI-generated hits are dropped.
  iconify      Iconify: 200,000+ SVG icons from about 150 open sets (Tabler, Lucide, Phosphor, Material Symbols, Remix,
               Heroicons...); only sets with an open licence (MIT, ISC, Apache 2.0, CC0, CC BY, OFL) are kept, the set's
               licence recorded per icon; --type icon. Name sets with --q "leaf prefixes:tabler,ph".
  polyhaven    Poly Haven: textures and HDRIs, all CC0
  ambientcg    ambientCG: CC0 surfaces (paper, concrete, fabric, wood, metal...); --type texture; fetch keeps the colour map
  --type typography: mood-only type references (Fonts In Use, Typewolf, Are.na) through type_refs.py when present.
Keyed sources without a key are left out of a default search quietly (the line says which key would add them).
Licences kept: cc0, pd, cc-by, cc-by-sa, nasa, unsplash, pexels, pixabay, and for icons mit, isc, apache, ofl; anything
else (NC, ND, unknown) is dropped. --licence cc0,pd keeps only those.

search writes <out>/results.json (numbered records) and, when ffmpeg is present, <out>/sheet.jpg: one small contact
sheet (look at it, not single images: cheaper). fetch downloads the picked numbers into --dest and appends a row per
file to LICENSES.csv at once (no row, no use). board merges several searches (and the user's refs/) into one numbered
sheet and prints a measured palette. Polite: a clear User-Agent, a pause between requests, results cached in
research/.cache/.
"""
import argparse
import concurrent.futures
import csv
import datetime
import hashlib
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "graphic-base-asset-search/1.0 (open-licence design research; low volume)"
CACHE = os.path.join("research", ".cache")
OPEN = {"cc0", "pd", "cc-by", "cc-by-sa", "nasa", "pixabay", "unsplash", "pexels", "mit", "isc", "apache", "ofl"}
LIC_URL = {"cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
           "pd": "https://creativecommons.org/publicdomain/mark/1.0/",
           "cc-by": "https://creativecommons.org/licenses/by/4.0/",
           "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
           "nasa": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
           "pixabay": "https://pixabay.com/service/license-summary/",
           "unsplash": "https://unsplash.com/license", "pexels": "https://www.pexels.com/license/",
           "mit": "https://opensource.org/license/mit", "isc": "https://opensource.org/license/isc-license-txt",
           "apache": "https://www.apache.org/licenses/LICENSE-2.0", "ofl": "https://openfontlicense.org"}
SOURCE_NAME = {"wikimedia": "Wikimedia Commons", "archive": "Internet Archive", "aic": "Art Institute of Chicago", "polyhaven": "Poly Haven",
               "nasa": "NASA", "met": "The Metropolitan Museum of Art", "openverse": "Openverse", "pixabay": "Pixabay",
               "cleveland": "Cleveland Museum of Art", "rijks": "Rijksmuseum", "smithsonian": "Smithsonian Open Access",
               "unsplash": "Unsplash", "pexels": "Pexels", "iconify": "Iconify", "ambientcg": "ambientCG"}
FIELDS = ["file", "title", "author", "source_url", "licence", "licence_url", "attribution_text", "modifications",
          "downloaded_at", "used_in", "notes"]
_last = {}                                    # host -> when its last request started: sources asked side by side never wait on each other
HOST_DELAY = {}           # seconds between requests; other hosts 0.5
MAX_WAIT = [None]                            # --max-wait: a short wait and no second try, for a board the user waits on
HOST_TIMEOUT = {"api.openverse.org": 60}      # its audio search can take 10-25 s on an uncached query; others 25


SHARED_PACE = {}           # a board starts its searches at once: their API calls queue across processes


def shared_pace(url):
    """Searches started side by side share one queue per rate-limited host, so six at once never meet a 429."""
    host = urllib.parse.urlparse(url).hostname or ""
    if host not in SHARED_PACE or "/wp-json/" not in url:
        return
    try:
        import fcntl
    except ImportError:                          # Windows: each process keeps its own pace
        return
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, f".pace-{host}"), "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            last = float(f.read().strip() or 0)
        except ValueError:
            last = 0.0
        wait = last + SHARED_PACE[host] - time.time()
        if wait > 0:
            time.sleep(wait)
        f.seek(0)
        f.truncate()
        f.write(str(time.time()))


import threading
BUDGET = threading.local()                       # one deadline (and search: one wait) per source job, set in its thread
PACE = threading.Lock()


def wait_cap():
    """This thread's wait on one source (a search asks its sources side by side), else the run's --max-wait."""
    return getattr(BUDGET, "max_wait", None) or MAX_WAIT[0]


DOWN_FOR = 1800                                  # a source that did not answer sits out this project's searches this long


def down_until():
    try:
        with open(os.path.join(CACHE, "down.json")) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def mark_down(name):
    d = down_until()
    d[name] = time.time() + DOWN_FOR
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, "down.json"), "w") as fh:
        json.dump(d, fh)


def get(url, as_json=True):
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        with open(path, "rb") as fh:
            data = fh.read()
    else:
        host = urllib.parse.urlparse(url).hostname or ""
        with PACE:
            wait = _last.get(host, 0.0) + HOST_DELAY.get(host, 0.5) - time.time()
            _last[host] = time.time() + max(0.0, wait)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "AIC-User-Agent": UA})
        timeout = wait_cap() or HOST_TIMEOUT.get(host, 25)
        deadline = getattr(BUDGET, "deadline", None)
        if deadline is not None:
            left = deadline - time.time()
            if left <= 0:
                raise TimeoutError("over its time")
            timeout = min(timeout, left)
        for attempt in ((0,) if deadline is not None else (0, 1)):   # a budgeted probe never sleeps on a retry
            shared_pace(url)
            _last[host] = time.time()
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = r.read()
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt or deadline is not None:
                    raise
                after = int(e.headers.get("Retry-After") or 15) if str(e.headers.get("Retry-After") or 15).isdigit() else 15   # rate limited: wait once, then retry
                time.sleep(min(4, after) if wait_cap() else min(30, after))
            except (TimeoutError, socket.timeout, urllib.error.URLError) as e:
                timed_out = isinstance(e, (TimeoutError, socket.timeout)) or isinstance(getattr(e, "reason", None), (TimeoutError, socket.timeout))
                if not timed_out:
                    raise                                                      # a real connection error (refused, DNS, SSL): not a timeout
                if attempt or wait_cap():
                    raise TimeoutError("over its time") from e                 # normalise a stall to TimeoutError so callers keep the hits already collected
                # else: a slow search with no budget gets one more try (the loop continues)
        os.makedirs(CACHE, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
    return json.loads(data) if as_json else data


def clean(s, n=80):
    s = re.sub(r"<[^>]+>", "", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()[:n]


def norm_licence(text):
    t = (text or "").lower()
    if "cc0" in t or "zero" in t:
        return "cc0"
    if "public domain" in t or t.startswith("pd"):
        return "pd"
    if "nc" in t.replace("-", " ").split() or "nd" in t.replace("-", " ").split():
        return None
    if "by-sa" in t or "by sa" in t:
        return "cc-by-sa"
    if "cc by" in t or "cc-by" in t:
        return "cc-by"
    return None


def rec(source, sid, title, creator, licence, page, file_url, thumb, kind):
    return {"source": source, "id": str(sid), "title": clean(title), "creator": clean(creator, 60) or "unknown",
            "licence": licence, "page": page, "file": file_url, "thumb": thumb, "type": kind}


def src_wikimedia(q, n, kind):
    ft = "drawing" if kind == "illustration" else "bitmap"
    p = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} filetype:{ft}",
         "gsrnamespace": "6", "gsrlimit": n * 3, "prop": "imageinfo", "iiprop": "url|extmetadata",
         "iiurlwidth": "480", "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist"}
    s = get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p))
    out = []
    for page in sorted((s.get("query") or {}).get("pages", {}).values(), key=lambda x: x.get("index", 0)):
        ii = (page.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata") or {}
        short = (md.get("LicenseShortName") or {}).get("value") or ""
        lic = norm_licence(short)
        if lic:
            r = rec("wikimedia", page.get("pageid"), page.get("title", "").replace("File:", ""),
                    (md.get("Artist") or {}).get("value"), lic, ii.get("descriptionurl"), ii.get("url"),
                    ii.get("thumburl"), kind)
            url = ((md.get("LicenseUrl") or {}).get("value") or "").strip()
            ver = re.search(r"(\d\.\d)", short)            # keep the file's own licence version (CC BY 2.0 is not 4.0)
            if url.startswith("http"):
                r["licence_url"] = url
            elif ver and lic in ("cc-by", "cc-by-sa"):
                r["licence_url"] = f"https://creativecommons.org/licenses/{lic[3:]}/{ver.group(1)}/"
            if short:
                r["licence_name"] = short
            out.append(r)
    return out[:n]


def src_aic(q, n, kind):
    s = get("https://api.artic.edu/api/v1/artworks/search?" + urllib.parse.urlencode(
        {"q": q, "query[term][is_public_domain]": "true", "limit": n,
         "fields": "id,title,artist_display,image_id,is_public_domain,thumbnail"}))
    base = (s.get("config") or {}).get("iiif_url", "https://www.artic.edu/iiif/2")

    def size(d):          # the original's own width up to 3000 px; its IIIF server honours only a width ("max" and boxes are not)
        w = (d.get("thumbnail") or {}).get("width")
        return f"{min(3000, w)}," if isinstance(w, int) and w > 0 else "843,"
    return [rec("aic", d["id"], d.get("title"), (d.get("artist_display") or "").split("\n")[0], "cc0",
                f"https://www.artic.edu/artworks/{d['id']}", f"{base}/{d['image_id']}/full/{size(d)}/0/default.jpg",
                f"{base}/{d['image_id']}/full/200,/0/default.jpg", "image")
            for d in s.get("data", []) if d.get("image_id") and d.get("is_public_domain")]


def src_polyhaven(q, n, kind):
    t = {"hdri": "hdris", "texture": "textures"}.get(kind, "all")
    s = get(f"https://api.polyhaven.com/assets?type={t}")
    words = [w.lower() for w in q.split()]
    scored = []
    for aid, a in s.items():
        hay = " ".join([aid, a.get("name", "")] + a.get("tags", []) + a.get("categories", [])).lower()
        score = sum(w in hay for w in words)
        if score:
            scored.append((-score, -a.get("download_count", 0), aid, a))
    return [rec("polyhaven", aid, a.get("name"), ", ".join(a.get("authors", {}).keys()), "cc0",
                f"https://polyhaven.com/a/{aid}", f"https://api.polyhaven.com/files/{aid}",
                f"https://cdn.polyhaven.com/asset_img/thumbs/{aid}.png?width=256",
                {0: "hdri", 1: "texture", 2: "model"}.get(a.get("type"), kind))
            for _, _, aid, a in sorted(scored)[:n]]


def src_nasa(q, n, kind):
    s = get("https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": q, "media_type": "image", "page_size": n}))
    out = []
    for it in s.get("collection", {}).get("items", [])[:n]:
        d = (it.get("data") or [{}])[0]
        nid = urllib.parse.quote(d.get("nasa_id") or "")
        out.append(rec("nasa", d.get("nasa_id"), d.get("title"), d.get("photographer") or d.get("center") or "NASA", "nasa",
                       f"https://images.nasa.gov/details/{nid}", f"https://images-api.nasa.gov/asset/{nid}",
                       (it.get("links") or [{}])[0].get("href"), "image"))
    return out


def src_met(q, n, kind):
    s = get("https://collectionapi.metmuseum.org/public/collection/v1.1/search?" + urllib.parse.urlencode(
        {"q": q, "hasImages": "true", "limit": n * 4}))
    out = []
    for oid in (s.get("objectIDs") or [])[: n * 4]:
        try:
            o = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        except urllib.error.HTTPError as e:      # withdrawn object ids answer 404: skip them; a timeout or a 429 is not "none"
            if e.code == 404:
                continue
            raise
        except (TimeoutError, socket.timeout):   # out of time: keep what was found, else let the caller (supply) see the timeout
            if out:
                break
            raise
        if o.get("isPublicDomain") and o.get("primaryImageSmall"):
            out.append(rec("met", oid, o.get("title"), o.get("artistDisplayName") or o.get("culture"), "cc0",
                           o.get("objectURL"), o.get("primaryImage"), o.get("primaryImageSmall"), "image"))
        if len(out) >= n:
            break
    return out


def src_cleveland(q, n, kind):
    s = get("https://openaccess-api.clevelandart.org/api/artworks/?" + urllib.parse.urlencode(
        {"q": q, "has_image": 1, "cc0": 1, "limit": n}))
    out = []
    for d in s.get("data") or []:
        im = d.get("images") or {}
        big, small = (im.get("print") or im.get("web") or {}).get("url"), (im.get("web") or {}).get("url")
        if d.get("share_license_status") == "CC0" and big and small:
            out.append(rec("cleveland", d.get("id"), d.get("title"), ((d.get("creators") or [{}])[0] or {}).get("description"),
                           "cc0", d.get("url"), big, small, "image"))
    return out[:n]


RIJKS_EN = "http://vocab.getty.edu/aat/300388277"                 # Linked Art's tag for English text
RIJKS_LIC = {"publicdomain/zero": "cc0", "publicdomain/mark": "pd"}


def rijks_record(o):
    def text(items):                                              # the English wording when there is one
        items = [i for i in items if i.get("content")]
        pick = next((i for i in items if any(l.get("id") == RIJKS_EN for l in i.get("language") or [])), None)
        return (pick or (items[0] if items else {})).get("content")
    ids = o.get("identified_by") or []
    number = next((i.get("content") for i in ids if i.get("type") == "Identifier" and i.get("content")), None)
    for s in o.get("subject_of") or []:
        for dc in s.get("digitally_carried_by") or []:
            terms = " ".join(str(r.get("content")) for r in dc.get("referred_to_by") or [])
            lic = next((v for k, v in RIJKS_LIC.items() if k in terms), None)
            img = next((a.get("id") for a in dc.get("access_point") or []
                        if str(a.get("id")).startswith("https://iiif.micr.io/")), None)
            if lic and img and number:
                base = img.split("/full/")[0]
                return rec("rijks", number, text([i for i in ids if i.get("type") == "Name"]),
                           text((o.get("produced_by") or {}).get("referred_to_by") or []), lic,
                           f"https://www.rijksmuseum.nl/en/collection/{urllib.parse.quote(number)}",
                           f"{base}/full/!3400,3400/0/default.jpg", f"{base}/full/400,/0/default.jpg", "image")
    return None


def src_rijks(q, n, kind):
    s = get("https://data.rijksmuseum.nl/search/collection?" + urllib.parse.urlencode({"title": q, "imageAvailable": "true"}))
    out = []
    for it in (s.get("orderedItems") or [])[: n * 3]:
        oid = str(it.get("id") or "")
        if not oid.startswith("https://id.rijksmuseum.nl/"):      # follow only the museum's own object ids
            continue
        try:
            o = get(oid)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
        except (TimeoutError, socket.timeout):   # out of time: keep what was found, else let the caller (supply) see the timeout
            if out:
                break
            raise
        r = rijks_record(o)
        if r:
            out.append(r)
        if len(out) >= n:
            break
    return out


OV_ALLOWED = set()                                # set by search(): the licences this run keeps
OV_LIC = {"cc0": "cc0", "pdm": "pd", "by": "cc-by", "by-sa": "cc-by-sa"}


def src_openverse(q, n, kind):
    params = {"q": q, "license": ",".join(OV_LIC), "page_size": n, "mature": "false"}
    if kind == "illustration":
        params["category"] = "illustration,digitized_artwork"
    found = get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(params)).get("results", [])
    if not found and " " in q.strip():           # every word must match (no OR syntax): try the words one by one
        for w in sorted(set(q.split()), key=len, reverse=True)[:3]:
            try:
                found += [d for d in get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(dict(params, q=w))).get(
                    "results", []) if d.get("id") not in {x.get("id") for x in found}]
            except (TimeoutError, socket.timeout):
                if found:
                    break
                raise
            if len(found) >= n:
                break
    out = []
    for d in found:
        lic = OV_LIC.get(d.get("license"))
        if not lic:
            continue
        r = rec("openverse", d.get("id"), d.get("title"), d.get("creator"), lic, d.get("foreign_landing_url"),
                d.get("url"), d.get("thumbnail"), kind)
        r.update({"licence_url": d.get("license_url"), "attribution": d.get("attribution"),
                  "provider": d.get("source") or d.get("provider")})
        out.append(r)
    return out[:n]


def src_pixabay(q, n, kind):
    """Pixabay's photos, illustrations and vectors (Pixabay Content License: free for commercial use, no credit owed,
    never resold as files). A hit's tags must name a word of the query; AI-generated pictures are left out."""
    if kind not in ("image", "illustration"):
        return []
    key = need_key("PIXABAY_API_KEY")
    s = secret_get("https://pixabay.com/api/?" + urllib.parse.urlencode(
        {"key": key, "q": q[:100], "per_page": max(3, min(200, n * 3)), "safesearch": "true",
         "image_type": "illustration" if kind == "illustration" else "photo"}), key)
    words = [w for w in re.findall(r"\w+", q.lower()) if len(w) > 2]
    out = []
    for h in s.get("hits", []):
        tags = (h.get("tags") or "").lower()
        if (words and not any(w in tags for w in words)) or re.search(r"\bai[- ]generated\b|\bgenerative\b|\bai art\b", tags):
            continue
        r = rec("pixabay", h.get("id"), tags, h.get("user"), "pixabay", h.get("pageURL"),
                h.get("largeImageURL") or h.get("webformatURL"), h.get("webformatURL") or h.get("previewURL"), kind)
        r["licence_url"], r["licence_name"] = LIC_URL["pixabay"], "Pixabay Content License"
        r["attribution"] = f'"{r["title"]}" by {r["creator"]} on Pixabay (Pixabay Content License)'
        out.append(r)
        if len(out) >= n:
            break
    return out


def need_key(name):
    import keys
    key = keys.get(name)
    if not key:
        raise RuntimeError(f"needs a free key: tools/keys.py open {name}")
    return key


def secret_get(url, key, headers=None):
    """A request whose address or headers carry a key: never cached, never printed."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=wait_cap() or 25) as r:
            return json.loads(r.read())
    except Exception as e:
        raise RuntimeError(str(e).replace(key, "<key>").replace(urllib.parse.quote(key), "<key>")) from None


def src_unsplash(q, n, kind):
    if kind != "image":
        return []
    key = need_key("UNSPLASH_ACCESS_KEY")
    s = secret_get("https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({"query": q, "per_page": min(30, n)}),
                   key, {"Authorization": f"Client-ID {key}", "Accept-Version": "v1"})
    out = []
    for d in s.get("results", []):
        user = (d.get("user") or {}).get("name") or "unknown"
        r = rec("unsplash", d.get("id"), d.get("alt_description") or d.get("description") or q, user, "unsplash",
                (d.get("links") or {}).get("html"), (d.get("urls") or {}).get("full"), (d.get("urls") or {}).get("small"), "image")
        r["attribution"] = f"Photo by {user} on Unsplash"
        r["download_location"] = (d.get("links") or {}).get("download_location")   # Unsplash asks for a ping on use
        out.append(r)
    return out[:n]


def src_pexels(q, n, kind):
    if kind != "image":
        return []
    key = need_key("PEXELS_API_KEY")
    s = secret_get("https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": q, "per_page": min(80, n)}),
                   key, {"Authorization": key})
    out = []
    for d in s.get("photos", []):
        src = d.get("src") or {}
        r = rec("pexels", d.get("id"), d.get("alt") or q, d.get("photographer"), "pexels", d.get("url"),
                src.get("original"), src.get("medium"), "image")
        r["attribution"] = f"Photo by {d.get('photographer')} on Pexels"
        out.append(r)
    return out[:n]


def src_smithsonian(q, n, kind):
    if kind not in ("image", "illustration"):
        return []
    key = need_key("SMITHSONIAN_API_KEY")
    s = secret_get("https://api.si.edu/openaccess/api/v1.0/search?" + urllib.parse.urlencode(
        {"q": f"{q} AND online_media_type:Images", "rows": n * 3, "api_key": key}), key)
    out = []
    for row in (s.get("response") or {}).get("rows", []):
        c = row.get("content") or {}
        media = ((c.get("descriptiveNonRepeating") or {}).get("online_media") or {}).get("media") or []
        m = next((x for x in media if (x.get("usage") or {}).get("access") == "CC0" and x.get("type") == "Images"), None)
        if not m:
            continue
        names = (c.get("freetext") or {}).get("name") or [{}]
        who = names[0].get("content") or row.get("unitCode")
        page_url = (c.get("descriptiveNonRepeating") or {}).get("record_link") or f"https://www.si.edu/object/{row.get('id')}"
        out.append(rec("smithsonian", row.get("id"), row.get("title"), who, "cc0", page_url,
                       m.get("content"), m.get("thumbnail"), kind))
        if len(out) >= n:
            break
    return out


ICON_LIC = {"mit": "mit", "isc": "isc", "apache-2.0": "apache", "cc0-1.0": "cc0", "cc-by-4.0": "cc-by", "cc-by-3.0": "cc-by",
            "cc-by-sa-4.0": "cc-by-sa", "cc-by-sa-3.0": "cc-by-sa", "ofl-1.1": "ofl", "unlicense": "cc0"}


def src_iconify(q, n, kind):
    """Icons as SVG from the open sets Iconify serves; each icon keeps its set's licence."""
    if kind != "icon":
        return []
    m = re.search(r"prefixes:([\w,-]+)", q)
    words = re.sub(r"prefixes:[\w,-]+", "", q).strip()
    params = {"query": words, "limit": max(64, n * 4)}
    if m:
        params["prefixes"] = m.group(1)
    s = get("https://api.iconify.design/search?" + urllib.parse.urlencode(params))
    sets = s.get("collections") or {}
    out, per_set = [], {}
    cap = n if m else max(2, n // 4)                  # without named sets: a spread of sets, not twenty of one
    for full in s.get("icons", []):
        prefix, _, name = full.partition(":")
        info = sets.get(prefix) or {}
        lic = ICON_LIC.get(((info.get("license") or {}).get("spdx") or "").lower())
        if not lic or per_set.get(prefix, 0) >= cap:
            continue
        per_set[prefix] = per_set.get(prefix, 0) + 1
        svg = f"https://api.iconify.design/{prefix}/{name}.svg"
        r = rec("iconify", full, f"{info.get('name', prefix)}: {name}", (info.get("author") or {}).get("name"), lic,
                f"https://icon-sets.iconify.design/{prefix}/{name}/", svg, svg + "?height=96", "icon")
        r["licence_url"] = (info.get("license") or {}).get("url") or LIC_URL.get(lic)
        r["licence_name"] = (info.get("license") or {}).get("title")
        r["set"] = prefix
        out.append(r)
        if len(out) >= n:
            break
    return out


def src_ambientcg(q, n, kind):
    if kind != "texture":
        return []
    ask = lambda words: get("https://ambientcg.com/api/v2/full_json?" + urllib.parse.urlencode(
        {"q": words, "limit": n, "type": "Material", "include": "previewData,downloadData"})).get("foundAssets", [])
    found = ask(q)
    if not found and " " in q.strip():           # every word must match: try the words one by one, longest first
        for w in sorted(set(q.split()), key=len, reverse=True)[:3]:
            found += [x for x in ask(w) if x.get("assetId") not in {y.get("assetId") for y in found}]
            if len(found) >= n:
                break
    out = []
    for a in found:
        cats = (((a.get("downloadFolders") or {}).get("default") or {}).get("downloadFiletypeCategories") or {})
        dls = (cats.get("zip") or {}).get("downloads", [])
        pick = next((d for d in dls if d.get("attribute") == "2K-JPG"), dls[0] if dls else None)
        if not pick:
            continue
        prev = a.get("previewImage") or {}
        r = rec("ambientcg", a.get("assetId"), a.get("displayName") or a.get("assetId"), "ambientCG", "cc0",
                a.get("shortLink"), pick.get("downloadLink"), prev.get("256-PNG") or prev.get("128-PNG"), "texture")
        r["zip"] = True
        out.append(r)
    return out[:n]


SOURCES = {"wikimedia": src_wikimedia, "openverse": src_openverse, "aic": src_aic, "met": src_met, "cleveland": src_cleveland,
           "rijks": src_rijks, "nasa": src_nasa, "smithsonian": src_smithsonian, "unsplash": src_unsplash, "pexels": src_pexels,
           "pixabay": src_pixabay, "iconify": src_iconify, "polyhaven": src_polyhaven, "ambientcg": src_ambientcg}
KEYED = {"smithsonian": "SMITHSONIAN_API_KEY", "unsplash": "UNSPLASH_ACCESS_KEY", "pexels": "PEXELS_API_KEY", "pixabay": "PIXABAY_API_KEY"}
DEFAULT = {"image": "wikimedia,openverse,aic,cleveland,nasa,unsplash,pexels,smithsonian",
           "illustration": "wikimedia,openverse,aic,cleveland,smithsonian,pixabay",
           "icon": "iconify", "texture": "ambientcg,polyhaven", "hdri": "polyhaven"}


def has_key(name):
    try:
        import keys
        return bool(keys.get(name))
    except Exception:
        return False


def contact_sheet(results, out):
    thumbs, shown = [], []
    os.makedirs(os.path.join(out, "thumbs"), exist_ok=True)
    for r in results:
        if not r.get("thumb"):
            continue
        p = os.path.join(out, "thumbs", f"{r['n']:02d}.img")
        src = r["thumb"]
        try:
            if os.path.exists(src):                  # a local file (the user's refs/): read it, never download it
                data = None
                if os.path.abspath(src) != os.path.abspath(p):
                    with open(src, "rb") as source:
                        data = source.read()
            else:                                     # always this result's own (cached) thumb: a reused number never shows an old image
                data = get(src, as_json=False)
            if data is not None:
                with open(p + ".part", "wb") as destination:
                    destination.write(data)
                os.replace(p + ".part", p)
            thumbs.append(p)
            shown.append(r["n"])
        except Exception as e:
            print(f"thumb {r['n']}: skipped ({str(e)[:80]})")
    if not thumbs:
        return None
    try:
        cols = min(4, len(thumbs))
        rows = (len(thumbs) + cols - 1) // cols
        cmd = ["ffmpeg", "-v", "error", "-y"]
        for p in thumbs:
            cmd += ["-i", p]
        f = "".join(f"[{i}]scale=200:200:force_original_aspect_ratio=decrease,pad=200:200:(ow-iw)/2:(oh-ih)/2,setsar=1[t{i}];"
                    for i in range(len(thumbs)))
        layout = "|".join(f"{(i % cols) * 200}_{(i // cols) * 200}" for i in range(len(thumbs)))
        f += "".join(f"[t{i}]" for i in range(len(thumbs))) + \
            (f"xstack=inputs={len(thumbs)}:layout={layout}:fill=black" if len(thumbs) > 1 else "null")
        sheet = os.path.join(out, "sheet.jpg")
        subprocess.run(cmd + ["-filter_complex", f, "-frames:v", "1", "-q:v", "5", sheet], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return sheet, cols, shown
    except Exception:
        return None


def supply(a):
    """What the open archives hold for each key element, before any download: one metadata query per element and
    source, licences filtered, nothing fetched. A real person, team, event or brand often has almost nothing open; say
    so at once with the numbers and the routes, instead of searching for hours."""
    allowed = OPEN
    OV_ALLOWED.clear(); OV_ALLOWED.update(allowed)
    sources = (a.sources or "wikimedia,met,aic").split(",")
    print("supply (open licence only, metadata, nothing downloaded):")
    MAX_WAIT[0] = MAX_WAIT[0] or 10           # a probe answers in seconds: a slow source counts as skipped

    def ask(job):
        q, name = job
        BUDGET.deadline = time.time() + MAX_WAIT[0]   # the whole source, however many requests it makes
        try:
            return job, [r for r in SOURCES[name](q, a.n, "image") if r["licence"] in allowed]
        except Exception as e:
            return job, f"skipped ({str(e)[:40]})"
        finally:
            BUDGET.deadline = None

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as pool:
        found = dict(pool.map(ask, [(q, name) for q in a.q for name in sources]))
    verdicts = []
    for q in a.q:
        counts, titles = {}, set()
        for name in sources:
            hits = found[(q, name)]
            if isinstance(hits, str):
                counts[name] = hits
                continue
            fresh = [r for r in hits if r["title"].lower()[:40] not in titles]
            titles.update(r["title"].lower()[:40] for r in fresh)
            counts[name] = len(fresh)
        total = len(titles)
        slow = [k for k, v in counts.items() if isinstance(v, str)]
        verdict = "enough" if total >= 8 else ("not judged yet" if slow else "thin" if total else "none")
        verdicts.append((q, verdict, slow))
        print(f"  {q[:44]:44s} " + " · ".join(f"{k} {v}" for k, v in counts.items()) + f"  -> {verdict} ({total})")
    late = sorted({s for _, v, slow in verdicts if v == "not judged yet" for s in slow})
    if late:
        print("Not judged yet: " + "; ".join(q for q, v, _ in verdicts if v == "not judged yet") + f" ({', '.join(late)} "
              "did not answer in time). Search them patiently in the background with --patient "
              f"(asset_search.py search --patient --sources {','.join(late)} --q …), and never tell the user anything is "
              "missing before that search has answered.")
    gaps = [q for q, v, _ in verdicts if v in ("thin", "none")]
    if gaps:
        print("Tell the user now, with these numbers: the open archives are thin or empty for " + "; ".join(gaps)
              + ". Routes: their own licensed material in assets/ (an agency, a private collection, a broadcaster), a design-led piece "
              "(type, numbers, maps, drawn places), or a mix. Searching longer does not find what "
              "the archives do not hold.")


def search(a):
    if a.type == "typography":                  # mood references: type_refs.py (Fonts In Use, Typewolf, Are.na)
        try:
            import type_refs
        except ImportError:
            sys.exit("typography references: type_refs.py is not in this kit yet; browse the sites in references/sources.md")
        type_refs.search(a.q, a.n, a.sources, a.out, a.purpose)
        return
    allowed = set(a.licence.split(",")) if a.licence else OPEN
    OV_ALLOWED.clear(); OV_ALLOWED.update(allowed)
    results, seen = [], set()
    names = (a.sources or DEFAULT[a.type]).split(",")
    if not a.sources:                             # a default search leaves out keyed sources the user has no key for
        missing = [nm for nm in names if nm in KEYED and not has_key(KEYED[nm])]
        names = [nm for nm in names if nm not in missing]
        if missing:
            print("not asked (no key yet, each free): " + ", ".join(f"{nm} (keys.py open {KEYED[nm]})" for nm in missing))
    patient = getattr(a, "patient", False)        # --patient: every source in full, for a background run; the foreground never waits unbounded
    win = lambda nm: a.max_wait or (30 if nm in ("openverse", "met") else 20)   # seconds on one source
    down = {} if (a.sources or patient) else down_until()   # a source named with --sources is always asked
    asked = []
    for name in names:
        if down.get(name, 0) > time.time():
            back = time.strftime("%H:%M", time.localtime(down[name]))
            print(f"{name}: skipped (it did not answer a search here lately; asked again from {back}, or now with --sources {name})")
        else:
            asked.append(name)

    def ask(name):                                # each source in its own thread, with its own wait
        BUDGET.deadline = None if patient else time.time() + win(name)
        BUDGET.max_wait = None if patient else win(name)
        try:
            return list(SOURCES[name](a.q, a.n, a.type)), None
        except Exception as e:
            return [], e
        finally:
            BUDGET.deadline = BUDGET.max_wait = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(asked))) as pool:
        answers = dict(zip(asked, pool.map(ask, asked)))   # side by side: a search takes as long as its slowest source
    for name in asked:
        found, err = answers[name]
        if err is not None:
            print(f"{name}: skipped ({str(err)[:80]})")
            if isinstance(err, (TimeoutError, socket.timeout)) and not patient:
                mark_down(name)
        for r in found:
            key = (r["source"], r["id"])
            if (r["licence"] in allowed or r.get("use") == "mood-only") and key not in seen:
                seen.add(key)
                results.append(r)
    used = {}
    for i, r in enumerate(results, 1):
        r["n"] = i
        src = r["source"] + (f"/{r['provider']}" if r.get("provider") and r["provider"] != r["source"] else "")
        dur = ""
        key = f"{r['source']}:{r['id']}"
        mark = f" · used in {used[key]}" if key in used else ""
        print(f"{i:>2}. [{src}] {r['title'][:60]} · {r['creator'][:30]} · {r['licence']}{dur}{mark}")
    os.makedirs(a.out, exist_ok=True)
    json.dump({"query": a.q, "type": a.type, "results": results}, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    BUDGET.max_wait = None if patient else (a.max_wait or 20)   # a stalled thumbnail gets one short try, like each source
    try:
        sheet = contact_sheet(results, a.out)
    finally:
        BUDGET.max_wait = None
    print(f"{len(results)} results -> {a.out}/results.json" +
          (f"; sheet {sheet[0]} ({sheet[1]} per row, row by row = results {','.join(map(str, sheet[2]))})" if sheet else ""))


def tiny(path):
    """16x16 grey bytes of an image, to spot the same picture arriving twice (from two archives, or as two sizes)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=16:16,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return raw if len(raw) == 256 else None


def page(img, captions=()):
    """A page beside an image that shows it at full width, with optional numbered captions above it. Its path, clicked
    in the Claude Code desktop app, opens it big in the app's own browser pane (elsewhere in the browser); the app does
    not show images inside a chat message."""
    import html as _h
    p = os.path.splitext(str(img))[0] + ".html"
    name = _h.escape(os.path.basename(str(img)))
    caps = "".join(f"<li>{_h.escape(c)}</li>" for c in captions)
    open(p, "w", encoding="utf-8").write(
        f'<!doctype html><meta charset=utf-8><title>{name}</title><style>body{{margin:0;background:#111;color:#eee;'
        f'font:18px/1.5 -apple-system,Helvetica,Arial,sans-serif}}ul{{margin:0;padding:14px 18px;list-style:none}}'
        f'img{{display:block;width:100%;height:auto}}</style>' + (f"<ul>{caps}</ul>" if caps else "") +
        f'<img src="{name}">')
    return os.path.abspath(p)


def show(path):
    """Put a board, a sheet or a design in front of the user: Preview on macOS, the default viewer elsewhere.
    GB_NO_OPEN=1 turns it off (tests, servers)."""
    if os.environ.get("GB_NO_OPEN") or not os.path.exists(str(path)):
        return False
    if not os.environ.get("GB_OPEN"):
        return False                              # nothing opens a window: paths go into the message; GB_OPEN=1 opens them
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            os.startfile(str(path))
        elif shutil.which("xdg-open") and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return False
    except OSError:
        return False
    return True


def board(a):
    results, prints, dropped = [], [], []
    os.makedirs(os.path.join(a.out, "thumbs"), exist_ok=True)
    def add(r, src_thumb):
        fp = tiny(src_thumb) if src_thumb and os.path.exists(src_thumb) else None
        if fp and any(sum(abs(x - y) for x, y in zip(fp, q)) / 256 < 10 for q in prints):
            dropped.append(r.get("title", "")[:30])
            return
        if fp:
            prints.append(fp)
        r = dict(r, n=len(results) + 1)
        dst = os.path.join(a.out, "thumbs", f"{r['n']:02d}.img")
        if src_thumb and os.path.exists(src_thumb):
            shutil.copyfile(src_thumb, dst)
        results.append(r)
    drop = {}
    for item in a.drop or []:                    # "<folder>:1,4": leave out results 1 and 4 of that search
        folder, _, nums = item.partition(":")
        drop.setdefault(folder.rstrip("/").split("/")[-1], set()).update(int(x) for x in nums.split(",") if x.strip().isdigit())
    for d in a.dirs or []:
        found = json.load(open(os.path.join(d, "results.json")))["results"]
        gone = drop.get(os.path.basename(d.rstrip("/")), set())
        for r in [r for r in found if r.get("thumb") and r.get("n") not in gone][:a.per]:
            add(dict(r, element=os.path.basename(d.rstrip("/"))), os.path.join(d, "thumbs", f"{r['n']:02d}.img"))
    if a.refs and os.path.isdir(a.refs):
        for f in sorted(os.listdir(a.refs)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                p = os.path.join(a.refs, f)
                add(dict(rec("user", f, f, "user", "user", p, p, p, "image"), element="user"), p)
    for r in results:
        print(f"{r['n']:>2}. {r['element'][:14]:<14} [{r['source']}] {r['title'][:50]} · {r['licence']}")
    if dropped:
        print(f"left out as the same picture again: {', '.join(dropped)}")
    json.dump({"query": "board", "type": "image", "results": results}, open(os.path.join(a.out, "results.json"), "w"),
              separators=(",", ":"))
    sheet = contact_sheet(results, a.out)
    if not sheet:
        sys.exit("board: no thumbnails")
    print(f"{len(results)} references -> {a.out}/results.json; sheet {sheet[0]} ({sheet[1]} per row) · show the user: {os.path.abspath(sheet[0])} (Claude Code: SendUserFile with display 'render', it opens big in the side panel; elsewhere the page {page(sheet[0])} in your message)"
          + (" · opened on the user's screen" if show(sheet[0]) else ""))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sheet[0], "-vf", "scale=32:32", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    bins = {}
    for i in range(0, len(raw) - 2, 3):
        r, g, b = (raw[i] >> 5, raw[i + 1] >> 5, raw[i + 2] >> 5)
        if r + g + b > 0:                                   # leave out the black padding
            bins[(r, g, b)] = bins.get((r, g, b), 0) + 1
    top = sorted(bins, key=bins.get, reverse=True)[:6]
    print("palette: " + " ".join("#%02x%02x%02x" % tuple(c * 32 + 16 for c in k) for k in top))


def file_url(r, variant):
    if r["source"] == "polyhaven":
        files = get(r["file"])
        res, fmt = (variant or "2k:hdr").split(":")
        for k in ("hdri", "Diffuse", "diff"):
            node = (files.get(k) or {}).get(res)
            if isinstance(node, dict):
                pick = node.get(fmt) or next(iter(node.values()))
                if isinstance(pick, dict) and "url" in pick:
                    return pick["url"]
        raise RuntimeError("no file for that variant; try --variant 1k:jpg or 2k:hdr")
    if r["source"] == "nasa":
        hrefs = [i["href"] for i in get(r["file"]).get("collection", {}).get("items", [])]
        for tag in ("~large", "~orig", "~medium"):
            for h in hrefs:
                if tag in h and h.lower().endswith((".jpg", ".jpeg", ".png")):
                    return h
        return hrefs[0]
    return r["file"]


def ambientcg_colour(zip_path, dest):
    """ambientCG ships a zip of maps; a design needs the colour map only: keep it, drop the rest."""
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        name = next((m for m in z.namelist() if re.search(r"_Color\.(jpg|png)$", m, re.I)), None)
        if not name:
            raise RuntimeError("no colour map in the zip")
        out = os.path.join(dest, os.path.basename(name))
        with z.open(name) as src, open(out, "wb") as dst:
            shutil.copyfileobj(src, dst)
    os.remove(zip_path)
    return out


def true_extension(path):
    """Name a file by what it is, not by what the source called it (a WebP sent as .jpg confuses print shops)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(16)
    except OSError:
        return path
    ext = (".png" if head.startswith(b"\x89PNG") else ".jpg" if head[:3] == b"\xff\xd8\xff" else
           ".webp" if head[:4] == b"RIFF" and head[8:12] == b"WEBP" else ".gif" if head[:4] == b"GIF8" else
           ".tif" if head[:4] in (b"II*\x00", b"MM\x00*") else ".svg" if b"<svg" in head or head.lstrip().startswith(b"<?xml") else None)
    if not ext or path.lower().endswith(ext) or (ext == ".jpg" and path.lower().endswith(".jpeg")):
        return path
    new = os.path.splitext(path)[0] + ext
    os.replace(path, new)
    return new


def unsplash_ping(r):
    """Unsplash's guidelines ask for a ping to its download endpoint when a photo is used."""
    if r.get("source") == "unsplash" and r.get("download_location"):
        try:
            key = need_key("UNSPLASH_ACCESS_KEY")
            secret_get(r["download_location"], key, {"Authorization": f"Client-ID {key}"})
        except Exception:
            pass


def fetch(a):
    data = json.load(open(a.results, encoding="utf-8"))
    by_n = {r["n"]: r for r in data["results"]}
    os.makedirs(a.dest, exist_ok=True)
    new = not os.path.exists(a.licenses) or os.path.getsize(a.licenses) == 0
    rows = []
    picks = [int(x) for x in a.pick.split(",")]
    deadline = time.time() + max(90, 30 * len(picks))   # a loose total backstop so a batch of dead links never hangs
    fails, down = {}, set()                             # connection failures in a row per source; a source found down (3 in a row) is skipped
    for n in picks:
        if time.time() >= deadline:
            print(f"{n}+: not fetched (the fetch spent its time; try again or another source)")
            break
        r = by_n.get(n)
        if not r:
            print(f"{n}: not in results")
            continue
        if r["source"] in down:
            print(f"{n}: skipped ({r['source']} is unreachable right now)")
            continue
        if r.get("use") == "mood-only" or r.get("licence") == "mood-only":
            print(f"{n}: mood-only reference (link and thumbnail for study): never fetched into the design")
            continue
        try:
            url = file_url(r, a.variant)
            ext = os.path.splitext(urllib.parse.urlparse(url).path)[1][:6] or ".bin"
            slug = re.sub(r"[^a-z0-9]+", "-", r["title"].lower()).strip("-")[:40] or "asset"
            safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(r["id"]))
            path = os.path.join(a.dest, f"{r['source']}-{safe_id}-{slug}{ext}")
            if os.path.exists(path):
                print(f"{n}: already here: {path}")
                fails.pop(r["source"], None)
                continue
            if r["source"] == "iconify":
                path = os.path.splitext(path)[0] + ".svg"
            if r["source"] in ("unsplash", "pexels") and ext not in (".jpg", ".jpeg", ".png"):
                path = os.path.splitext(path)[0] + ".jpg"
            req = urllib.request.Request(url, headers={"User-Agent": UA, "AIC-User-Agent": UA})   # AIC's image server refuses a file without it
            with urllib.request.urlopen(req, timeout=90) as resp, open(path + ".part", "wb") as f:
                while chunk := resp.read(1 << 20):
                    f.write(chunk)
            os.replace(path + ".part", path)
            if r.get("zip"):
                path = ambientcg_colour(path, a.dest)
            path = true_extension(path)
            unsplash_ping(r)
            deadline = max(deadline, time.time() + max(90, 30 * len(picks)))   # a healthy fetch refreshes the budget
        except urllib.error.HTTPError as e:
            print(f"{n}: failed (the file is gone, HTTP {e.code})")       # the source answered; only this file is missing
            fails.pop(r["source"], None)
            continue
        except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
            fails[r["source"]] = fails.get(r["source"], 0) + 1
            print(f"{n}: failed ({str(getattr(e, 'reason', e))[:70]})")
            if fails[r["source"]] >= 3:
                down.add(r["source"])
                print(f"{r['source']} looks unreachable (3 failures in a row) — skipping its remaining picks; other sources continue")
            continue
        except Exception as e:
            print(f"{n}: failed ({str(e)[:80]})")
            continue
        fails.pop(r["source"], None)
        lic = r.get("licence_name") or {"cc0": "CC0", "pd": "Public domain", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA",
               "nasa": "Courtesy NASA", "pixabay": "Pixabay Content License", "unsplash": "Unsplash License",
               "pexels": "Pexels License", "mit": "MIT", "isc": "ISC", "apache": "Apache 2.0", "ofl": "SIL OFL 1.1"}[r["licence"]]
        rows.append({"file": path, "title": r["title"], "author": r["creator"], "source_url": r["page"],
                     "licence": r["licence"], "licence_url": r.get("licence_url") or LIC_URL[r["licence"]],
                     "attribution_text": r.get("attribution") or (
                         f'"{r["title"]}" by {r["creator"]}, {lic}' if r["creator"] == SOURCE_NAME[r["source"]]
                         else f'"{r["title"]}" by {r["creator"]}, {SOURCE_NAME[r["source"]]}, {lic}'),
                     "modifications": "", "downloaded_at": datetime.date.today().isoformat(), "used_in": "",
                     "notes": f"type={r['type']}; source={r['source']}" + (f"; via {r['provider']}" if r.get("provider") else "")})
        print(f"{n}: {path} · {r['licence']}")
    if rows:
        with open(a.licenses, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"logged {len(rows)} row(s) in {a.licenses}; fill 'used_in' and 'modifications' when used")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("--q", required=True)
    s.add_argument("--type", default="image", choices=["image", "illustration", "icon", "texture", "hdri", "typography"])
    s.add_argument("--purpose", default="brand", choices=["brand", "editorial", "event"], help="typography: default sources")
    s.add_argument("--sources")
    s.add_argument("--licence")
    s.add_argument("--n", type=int, default=6)
    s.add_argument("--out", required=True)
    s.add_argument("--max-wait", type=float, help="seconds on one source before moving to the next (default 20)")
    s.add_argument("--patient", action="store_true", help="search every source in full with no time limit — only for a background run, never the foreground")
    u = sub.add_parser("supply", help="count what the open archives hold per element, nothing downloaded")
    u.add_argument("--q", action="append", required=True, help="one key element per --q (English, the shape in words)")
    u.add_argument("--sources", help="default wikimedia,met,aic")
    u.add_argument("--n", type=int, default=20, help="results asked per source and element")
    u.add_argument("--max-wait", type=float, help="seconds per source, no second try (default 10)")
    f = sub.add_parser("fetch")
    f.add_argument("--results", required=True)
    f.add_argument("--pick", required=True)
    f.add_argument("--dest", required=True)
    f.add_argument("--variant", help="Poly Haven resolution:format, e.g. 2k:hdr, 1k:jpg")
    f.add_argument("--licenses", default="LICENSES.csv")
    b = sub.add_parser("board")
    b.add_argument("--dirs", nargs="*", help="search output folders, one per key element")
    b.add_argument("--per", type=int, default=3)
    b.add_argument("--drop", nargs="*", help='results to leave out, per search folder: "<folder>:1,4" "<folder>:2"')
    b.add_argument("--refs", help="the user's reference folder (images)")
    b.add_argument("--out", required=True)
    a = ap.parse_args()
    MAX_WAIT[0] = getattr(a, "max_wait", None)
    {"search": search, "fetch": fetch, "board": board, "supply": supply}[a.cmd](a)


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:   # Windows reads, writes and prints in a legacy code page
        import subprocess
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    main()
