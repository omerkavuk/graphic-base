#!/usr/bin/env python3
"""Press-ready print files from a design's PDF, with Ghostscript (Python 3 stdlib + Ghostscript 9.53 or newer).

  python3 tools/print.py where                                   # is Ghostscript here, which version
  python3 tools/print.py press renders/final/poster-marks.pdf --out exports/X-poster-press.pdf \
      --trim 297x420 --bleed 3 --slug 10 [--profile printer.icc --condition FOGRA39] [--outline auto|yes|no] [--rich-black]
  python3 tools/print.py preflight exports/X-poster-press.pdf --trim 297x420 --bleed 3 --slug 10 [--tac 300]
  python3 tools/print.py proof exports/X-poster-press.pdf --out review/proof-poster.png [--dpi 100]

press: RGB to CMYK through an output profile (the printer's own when given, else Ghostscript's generic CMYK profile),
written as PDF/X-4 with its output intent, MediaBox / BleedBox / TrimBox set to the sheet, the bleed and the trim.
Fonts stay embedded; a font Chrome could only embed as Type 3 (some print checkers refuse them) turns all text into
vector outlines (--outline auto). Dark neutral colours that ICC conversion makes into four-colour black (small text in
four inks smears when the plates shift) become 100 % K, unless --rich-black.

preflight: page and boxes against the trim, bleed and slug; PDF/X version and output intent; fonts embedded, outlined
or Type 3; colour spaces (RGB left = a hold); total ink coverage (TAC) measured on a 36 dpi CMYK render: the maximum
and the share of the page over the limit (300 % by default; uncoated paper often wants 260-280 %; ask the printer).

proof: the press PDF rendered back to screen colours through its output intent: how the colours dull on paper.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

PT = 72 / 25.4


def gs_path():
    for name in ("gswin64c", "gswin32c", "gs"):
        p = shutil.which(name)
        if p:
            return p
    hits = sorted(glob.glob(r"C:\Program Files\gs\gs*\bin\gswin64c.exe")) + sorted(glob.glob("/opt/homebrew/bin/gs")) + \
        sorted(glob.glob("/usr/local/bin/gs"))
    return hits[-1] if hits else None


def need_gs():
    g = gs_path()
    if not g:
        sys.exit("NO GHOSTSCRIPT: press files need it (free). Windows: an administrator PowerShell, choco install ghostscript -y "
                 "(or the installer from ghostscript.com/releases); macOS: brew install ghostscript; Linux: sudo apt install "
                 "ghostscript. Until then the RGB PDF at trim + bleed is the print file, with the line: 'for offset printing "
                 "the printer converts it; ask for their profile'.")
    return g


def gs_profile(name):
    g = gs_path()
    for p in [os.path.join(os.path.dirname(os.path.dirname(g)), "iccprofiles", name)] + \
            glob.glob(f"/usr/share/ghostscript/*/iccprofiles/{name}") + glob.glob(f"/opt/homebrew/share/ghostscript/*/iccprofiles/{name}"):
        if os.path.exists(p):
            return p
    return None


def ps_str(s):
    return "(" + s.replace("\\", "/").replace("(", "\\(").replace(")", "\\)") + ")"


def size(text):
    w, h = text.lower().split("x")
    return float(w), float(h)


def boxes(trim, bleed, slug):
    w, h = trim
    media = (0, 0, (w + 2 * bleed + 2 * slug) * PT, (h + 2 * bleed + 2 * slug) * PT)
    bl = (slug * PT, slug * PT, (slug + 2 * bleed + w) * PT, (slug + 2 * bleed + h) * PT)
    tr = ((slug + bleed) * PT, (slug + bleed) * PT, (slug + bleed + w) * PT, (slug + bleed + h) * PT)
    return media, bl, tr


def fmt(b):
    return "[" + " ".join(f"{x:.3f}" for x in b) + "]"


def cmd_where(a):
    g = gs_path()
    if not g:
        need_gs()
    v = subprocess.run([g, "--version"], capture_output=True, text=True).stdout.strip()
    print(f"Ghostscript {v}: {g}")
    print(f"generic CMYK profile: {gs_profile('default_cmyk.icc') or 'not found'}")


def cmd_press(a):
    g = need_gs()
    trim = size(a.trim)
    media, bleed_box, trim_box = boxes(trim, a.bleed, a.slug)
    src = open(a.pdf, "rb").read()
    type3 = len(re.findall(rb"/Subtype\s*/Type3", src))
    outline = a.outline == "yes" or (a.outline == "auto" and type3 > 0)
    profile = a.profile or gs_profile("default_cmyk.icc")
    if not profile or not os.path.exists(profile):
        sys.exit("no CMYK profile: pass --profile <the printer's .icc>")
    condition = a.condition or ("Custom" if a.profile else "Generic CMYK (Ghostscript default_cmyk.icc)")
    tmp = tempfile.mkdtemp(prefix="gb-press-")
    defs = os.path.join(tmp, "pdfx.ps")
    with open(defs, "w", encoding="latin-1") as f:
        f.write(f"""%!
[ /GTS_PDFXVersion (PDF/X-4) /Title {ps_str(a.title or os.path.basename(a.out))} /Trapped /False /DOCINFO pdfmark
[/_objdef {{icc_PDFX}} /type /stream /OBJ pdfmark
[{{icc_PDFX}} << /N 4 >> /PUT pdfmark
[{{icc_PDFX}} {ps_str(profile)} (r) file /PUT pdfmark
[/_objdef {{OutputIntent_PDFX}} /type /dict /OBJ pdfmark
[{{OutputIntent_PDFX}} << /Type /OutputIntent /S /GTS_PDFX /OutputCondition {ps_str(condition)}
  /OutputConditionIdentifier {ps_str(a.condition or 'Custom')} /RegistryName (http://www.color.org)
  /Info {ps_str(os.path.basename(profile))} /DestOutputProfile {{icc_PDFX}} >> /PUT pdfmark
[{{Catalog}} << /OutputIntents [ {{OutputIntent_PDFX}} ] >> /PUT pdfmark
[ /TrimBox {fmt(trim_box)} /BleedBox {fmt(bleed_box)} /PAGES pdfmark
""")
    raw = os.path.join(tmp, "press.pdf")
    cmd = [g, "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", "-dPDFX=4", "-dCompatibilityLevel=1.6",
           "-sColorConversionStrategy=CMYK", "-sProcessColorModel=DeviceCMYK", f"-sOutputICCProfile={profile}",
           f"--permit-file-read={os.path.dirname(profile)}{os.sep}", f"--permit-file-read={tmp}{os.sep}",
           "-dCompressPages=false", "-dWriteObjStms=false", "-dWriteXRefStm=false", "-dFIXEDMEDIA", f"-dDEVICEWIDTHPOINTS={media[2]:.3f}",
           f"-dDEVICEHEIGHTPOINTS={media[3]:.3f}", "-dAutoRotatePages=/None", "-dDownsampleColorImages=false",
           "-dDownsampleGrayImages=false", "-dAutoFilterColorImages=false", "-sColorImageFilter=DCTEncode",
           "-dColorImageResolution=300", f"-sOutputFile={raw}"]
    if outline:
        cmd.append("-dNoOutputFonts")
    cmd += [defs, a.pdf]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(raw):
        sys.exit("press: Ghostscript failed: " + (r.stderr or r.stdout).strip()[-600:])
    data = open(raw, "rb").read()
    fixed = 0
    if not a.rich_black:
        data, fixed = pure_black(data)
    data = set_boxes(data, trim_box, bleed_box)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "wb").write(data)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"press: {a.out} · PDF/X-4 CMYK · profile {os.path.basename(profile)} ({condition}) · "
          f"sheet {media[2] / PT:.1f}×{media[3] / PT:.1f} mm, trim {trim[0]:g}×{trim[1]:g} mm, bleed {a.bleed:g} mm"
          + (f" · text outlined (the source had {type3} Type 3 font{'s' if type3 > 1 else ''})" if outline else " · fonts embedded")
          + (f" · {fixed} dark neutral fill{'s' if fixed != 1 else ''} set to 100 % K" if fixed else ""))


NUM = rb"(-?\d*\.?\d+)"
OP = re.compile(rb"(?<![\w.])" + NUM + rb"\s+" + NUM + rb"\s+" + NUM + rb"\s+" + NUM + rb"\s+(k|K)(?![\w])")


def pure_black(data):
    """Dark neutral CMYK fills and strokes in the page content become 0 0 0 1, written at the same byte length so the
    file's offsets stay valid; only uncompressed content streams are touched (never images or fonts)."""
    out, count, pos = bytearray(), 0, 0
    for m in re.finditer(rb"<<(.*?)>>\s*stream\r?\n", data, re.S):
        head = m.group(1)
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            break
        if b"/Filter" in head or b"/Subtype" in head and b"/Form" not in head or b"/Length1" in head:
            continue
        body = data[start:end]

        def swap(mm):
            nonlocal count
            c, mg, y, k = (float(x) for x in mm.groups()[:4])
            if k >= 0.6 and min(c, mg, y) >= 0.3 and max(c, mg, y) - min(c, mg, y) <= 0.15:
                count += 1
                new = b"0 0 0 1 " + mm.group(5)
                return new + b" " * (len(mm.group(0)) - len(new))
            return mm.group(0)
        body2 = OP.sub(swap, body)
        out += data[pos:start] + body2
        pos = end
    out += data[pos:]
    return bytes(out), count


def set_boxes(data, trim_box, bleed_box):
    """TrimBox and BleedBox on every page object (Ghostscript gives each page boxes equal to the sheet, and they win over
    the page tree's), then a fresh cross-reference table so every offset is right again. Needs a file written without
    object streams (-dWriteObjStms=false -dWriteXRefStm=false)."""
    def page(m):
        d = m.group(0)
        if not re.search(rb"/Type\s*/Page(?!s)", d):
            return re.sub(rb"/(TrimBox|BleedBox)\s*\[[^\]]*\]", b"", d) if re.search(rb"/Type\s*/Pages", d) else d
        d = re.sub(rb"/(TrimBox|BleedBox)\s*\[[^\]]*\]", b"", d)
        return d.replace(b"<<", b"<< /TrimBox " + fmt(trim_box).encode() + b" /BleedBox " + fmt(bleed_box).encode() + b" ", 1)
    data = re.sub(rb"\d+ 0 obj\s*<<.*?>>\s*(?=endobj|stream)", page, data, flags=re.S)
    x = data.rfind(b"\nxref")
    t = data.rfind(b"trailer")
    if x < 0 or t < x:
        return data
    trailer = data[t:data.find(b"startxref", t)]
    body = data[:x + 1]
    offs = {int(m.group(1)): m.start(1) for m in re.finditer(rb"(?:^|[\r\n])(\d+) 0 obj\b", body)}
    n = max(offs) + 1
    table = [b"xref\n", f"0 {n}\n".encode(), b"0000000000 65535 f \n"]
    table += [(f"{offs[i]:010d} 00000 n \n" if i in offs else "0000000000 65535 f \n").encode() for i in range(1, n)]
    trailer = re.sub(rb"/Size\s+\d+", f"/Size {n}".encode(), trailer)
    trailer = re.sub(rb"/Prev\s+\d+", b"", trailer)
    return body + b"".join(table) + trailer + f"startxref\n{len(body)}\n%%EOF\n".encode()


def read_box(data, name):
    m = re.search(rb"/" + name.encode() + rb"\s*\[\s*([^\]]+)\]", data)
    return [float(x) for x in m.group(1).split()] if m else None


def tac(g, pdf, dpi=36):
    """Total ink coverage on a CMYK render: the maximum C+M+Y+K in percent and the share of pixels over each limit."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([g, "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=bitcmyk", "-dGrayValues=256", f"-r{dpi}",
                            "-dUsePDFX3Profile", f"-sOutputFile={os.path.join(tmp, 'p%03d.cmyk')}", pdf],
                           capture_output=True, text=True)
        files = sorted(glob.glob(os.path.join(tmp, "p*.cmyk")))
        if r.returncode != 0 or not files:
            return None
        sums, worst = [], (0.0, 1)
        for n, f in enumerate(files, 1):                      # every page
            px = open(f, "rb").read()
            page = [(px[i] + px[i + 1] + px[i + 2] + px[i + 3]) * 100 / 255 for i in range(0, len(px) - 3, 4)]
            if page and max(page) > worst[0]:
                worst = (max(page), n)
            sums += page
    if not sums:
        return None
    return worst[0], sums, worst[1], len(files)


def cmd_preflight(a):
    g = need_gs()
    data = open(a.pdf, "rb").read()
    trim = size(a.trim)
    media_x, bleed_x, trim_x = boxes(trim, a.bleed, a.slug)
    hold, ok, note = [], [], []
    mb, tb, bb = read_box(data, "MediaBox"), read_box(data, "TrimBox"), read_box(data, "BleedBox")
    close = lambda b, x: b and all(abs(p - q) <= 1.0 for p, q in zip(b, x))      # within 1 pt (0.35 mm)
    (ok if close(mb, media_x) else hold).append(f"sheet {mb[2] / PT:.1f}×{mb[3] / PT:.1f} mm" if mb else "no MediaBox")
    (ok if close(tb, trim_x) else hold).append(f"TrimBox {'matches' if close(tb, trim_x) else 'wrong or missing'} (trim {trim[0]:g}×{trim[1]:g} mm)")
    (ok if close(bb, bleed_x) else hold).append(f"BleedBox {'matches' if close(bb, bleed_x) else 'wrong or missing'} ({a.bleed:g} mm bleed)")
    if a.bleed < 3:
        note.append(f"bleed {a.bleed:g} mm: most printers ask for 3 mm")
    pdfx = re.search(rb"/GTS_PDFXVersion\s*\(([^)]*)\)", data)
    (ok if pdfx else hold).append(f"{pdfx.group(1).decode() if pdfx else 'no PDF/X version'}")
    (ok if b"/OutputIntents" in data else hold).append("output intent " + ("present" if b"/OutputIntents" in data else "missing"))
    t3 = len(re.findall(rb"/Subtype\s*/Type3", data))
    ff = len(re.findall(rb"/FontFile[23]?\b", data))
    if t3:
        hold.append(f"{t3} Type 3 font(s): press again with --outline yes")
    else:
        ok.append(f"fonts: {ff} embedded" if ff else "fonts: text outlined (no fonts in the file)")
    rgb = len(re.findall(rb"/DeviceRGB\b", data))
    icc3 = len(re.findall(rb"/N\s+3\b", data))
    if rgb or icc3:
        hold.append(f"RGB left in the file ({rgb} DeviceRGB, {icc3} RGB ICC): press it again")
    else:
        ok.append("colour: CMYK only")
    m = tac(g, a.pdf)
    if m:
        top, sums, at, pages = m
        over = sum(1 for s in sums if s > a.tac) / len(sums) * 100
        line = (f"ink coverage: max {top:.0f} %" + (f" (page {at} of {pages})" if pages > 1 else "")
                + f", {over:.1f} % of the {'pages' if pages > 1 else 'page'} over {a.tac:g} %")
        (hold if over > 2 else note if top > a.tac else ok).append(line + (" (dark areas with all four inks: lighten them or ask the printer)" if over else ""))
    else:
        note.append("ink coverage: could not be measured")
    print("preflight " + ("HOLD" if hold else "PASS") + f": {os.path.basename(a.pdf)}")
    for x in hold:
        print("  HOLD " + x)
    for x in ok:
        print("  ok   " + x)
    for x in note:
        print("  note " + x)
    print("  always: the printer's own proof has the final word on colour; send them this file and ask for a proof")
    return 1 if hold else 0


def cmd_proof(a):
    g = need_gs()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    r = subprocess.run([g, "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=png16m", f"-r{a.dpi}", "-dUsePDFX3Profile",
                        "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", "-dFirstPage=1", "-dLastPage=1",
                        f"-sOutputFile={a.out}", a.pdf], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("proof: Ghostscript failed: " + (r.stderr or r.stdout).strip()[-400:])
    print(f"proof: {a.out} (the press file's colours on screen, as ink on paper will dull them)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where").set_defaults(fn=cmd_where)
    for name, fn in (("press", cmd_press), ("preflight", cmd_preflight)):
        p = sub.add_parser(name)
        p.add_argument("pdf")
        p.add_argument("--trim", required=True, help="trim size in mm, WxH")
        p.add_argument("--bleed", type=float, default=3)
        p.add_argument("--slug", type=float, default=10, help="the margin outside the bleed that carries the marks (0: none)")
        p.set_defaults(fn=fn)
        if name == "press":
            p.add_argument("--out", required=True)
            p.add_argument("--profile", help="the printer's CMYK .icc (default: Ghostscript's generic CMYK profile)")
            p.add_argument("--condition", help="the output condition identifier, e.g. FOGRA39, FOGRA51, GRACoL2006_Coated1v2")
            p.add_argument("--outline", choices=["auto", "yes", "no"], default="auto")
            p.add_argument("--rich-black", action="store_true", help="keep dark neutrals in four inks")
            p.add_argument("--title")
        else:
            p.add_argument("--tac", type=float, default=300)
    p = sub.add_parser("proof")
    p.add_argument("pdf")
    p.add_argument("--out", required=True)
    p.add_argument("--dpi", type=int, default=100)
    p.set_defaults(fn=cmd_proof)
    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=dict(os.environ, PYTHONUTF8="1")))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        getattr(_s, "reconfigure", lambda **k: None)(encoding="utf-8", errors="replace")
    main()
