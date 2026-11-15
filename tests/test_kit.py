"""graphic base: automated tests (Python 3 stdlib; node and Chrome for the render tests, Ghostscript for the print test).

  python -m unittest discover -s tests -v          # from the kit folder

Each test builds what it needs in a temporary folder; nothing outside it is written except the kit's own caches.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
S = KIT / "scripts"
sys.path.insert(0, str(S))
PY = sys.executable
HAS_NODE = shutil.which("node") is not None


def run(args, cwd=None, inp=None):
    return subprocess.run(args, cwd=cwd, input=inp, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=dict(os.environ, PYTHONUTF8="1", GB_NO_OPEN="1"))


def new_design(tmp, name="test-piece", studio=False):
    r = run([PY, str(S / "init_design.py"), name, "--studio" if studio else "--quick", "--designs-folder", "Designs"], cwd=tmp)
    assert r.returncode == 0, r.stderr
    return Path(tmp) / "Designs" / name


SIMPLE = """  title: 'Test Piece',
  purpose: 'brand',
  lang: 'tr',
  views: [
    { id: 'post', label: 'Post', w: 1080, h: 1350, unit: 'px', safe: 0.06, seen: 'phone' },
    { id: 'card', label: 'A6', w: 105, h: 148, unit: 'mm', bleed: 3, safe: 6, dpi: 300, seen: 'print' },
  ],
  palette: { ground: '#f4f1ea', ink: '#1b1b1b', accent: '#2f6f8f' },
  type: { display: null, text: null },
  check: { strings: ['Test'] },"""


def fill(design, body, style=".h{font-size:calc(var(--u)*10);margin:0} .b{font-size:calc(var(--u)*3.4)}"):
    p = design / "design.html"
    s = p.read_text(encoding="utf-8")
    start = s.index("  title: 'Working title',")
    end = s.index("};", start)
    s = s[:start] + SIMPLE + "\n" + s[end:]
    s = re.sub(r"/\* EXAMPLE.*?</style>", style + "\n</style>", s, count=1, flags=re.S)
    s = re.sub(r"<!-- EXAMPLE.*?</section>", body, s, count=1, flags=re.S)
    p.write_text(s, encoding="utf-8")


class Words(unittest.TestCase):
    def test_dash_and_tells(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "design.html"
            f.write_text("<html><body><h1>Yeni sezon — kaçırma!</h1><p>14–16 Mart</p><script>var a='—'</script></body></html>", encoding="utf-8")
            r = run([PY, str(S / "words_check.py"), str(f)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("DASH", r.stdout)
            self.assertEqual(r.stdout.count("DASH "), 1)          # the range 14–16 and the script are not words
            self.assertIn("sales language", r.stdout)


class Licences(unittest.TestCase):
    def test_normalise(self):
        import asset_search as a
        self.assertEqual(a.norm_licence("CC0 1.0"), "cc0")
        self.assertEqual(a.norm_licence("Public domain"), "pd")
        self.assertEqual(a.norm_licence("CC BY-SA 4.0"), "cc-by-sa")
        self.assertIsNone(a.norm_licence("CC BY-NC 4.0"))
        self.assertIsNone(a.norm_licence("CC BY-ND 2.0"))

    def test_true_extension(self):
        import asset_search as a
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x.jpg"
            p.write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8X" + b"\x00" * 20)
            self.assertTrue(a.true_extension(str(p)).endswith(".webp"))


class Deck(unittest.TestCase):
    def test_sparks_deck(self):
        d = json.loads((S / "sparks.json").read_text(encoding="utf-8"))
        for axis in ("device", "form", "medium", "tone", "era", "colour", "material", "look"):
            self.assertGreaterEqual(len(d[axis]), 20, axis)
            self.assertEqual(len(d[axis]), len(set(d[axis])), f"duplicates in {axis}")

    def test_styles_index(self):
        idx = json.loads((KIT / "styles" / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(idx["styles"]), 33)
        for s in idx["styles"]:
            self.assertTrue((KIT / "styles" / f"{s['id']}.md").is_file(), s["id"])
            self.assertTrue(s.get("tags"), f"{s['id']} has no design tags")
            text = (KIT / "styles" / f"{s['id']}.md").read_text(encoding="utf-8")
            self.assertNotIn("## 7. Sound palette", text)
            # recipes are for still design: no camera, shot, frame-rate, subtitle or narration language
            film = re.findall(r"(?i)\b(camera|shots?|fps|subtitles?|narrat\w*|dolly|zoom\w*|DEMO\.md|beat-locked|comes alive|paints itself)\b", text)
            self.assertFalse(film, f"{s['id']}.md still speaks film: {sorted(set(w.lower() for w in film))}")
            self.assertIn(s.get("kind"), ("design", "image"), s["id"])
            self.assertEqual(s["kind"], "design", s["id"])  # every style is offered, with its picture and a fit profile
            self.assertTrue(s.get("poster") and (KIT / "styles" / s["poster"]).is_file(), f"{s['id']} has no picture")
            self.assertTrue(all(s["fit"].get(k) for k in ("purpose", "content", "tone", "sector")), f"{s['id']} fit")
            self.assertTrue(s.get("family"), s["id"])
            blurb = s["essence"] + " " + s["name"] + " " + " ".join(s["uses"])
            self.assertFalse(re.search(r"(?i)\b(animat\w*|camera|film|moves|motion|beat)\b", blurb), f"{s['id']} board text: {blurb[:80]}")

    def test_style_board_all_styles(self):
        """The board lists all 33 styles in a fixed order and marks a top three that fits the content."""
        env = dict(os.environ, GRAPHIC_BASE_SHOWN=str(Path(tempfile.mkdtemp()) / "shown.json"), PYTHONUTF8="1")
        def run_(*args):
            r = subprocess.run([PY, str(S / "styles.py"), "suggest", *args], capture_output=True, text=True, env=env, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            stars = re.findall(r"^  ★ (\d+)\. (\S+) ", r.stdout, re.M)
            board = re.findall(r"^  (\d+)\. (\S+) · ", r.stdout, re.M)
            return stars, board
        stars, board = run_("energy finance", "--purpose", "editorial", "--content", "report,data", "--tone", "serious,calm", "--sector", "finance")
        self.assertEqual(len(board), 33)
        self.assertEqual(len(stars), 3)
        self.assertTrue(set(i for _, i in stars) & {"dataviz", "minimal-corporate", "newspaper", "swiss", "acid-diagram", "technical-manual"}, stars)
        stars2, board2 = run_("jazz night", "--purpose", "event", "--content", "announcement", "--tone", "festive,bold", "--sector", "music")
        self.assertEqual(board, board2)                      # a number always means the same style
        self.assertNotEqual([i for _, i in stars], [i for _, i in stars2])

    def test_type_library_turkish(self):
        lib = json.loads((KIT / "references" / "type-library.json").read_text(encoding="utf-8"))
        self.assertTrue(all(p["turkish"] == "verified" or p.get("local_files") for p in lib["pairings"]))


class Print(unittest.TestCase):
    def test_pure_black_keeps_length(self):
        import print as pr
        stream = b"BT 0.71 0.66 0.65 0.86 k (Hi) Tj ET 0.1 0.2 0.9 0 k"
        pdf = b"%PDF-1.6\n1 0 obj\n<< /Length 52 >>\nstream\n" + stream + b"\nendstream\nendobj\n"
        out, n = pr.pure_black(pdf)
        self.assertEqual(n, 1)
        self.assertEqual(len(out), len(pdf))
        self.assertIn(b"0 0 0 1 k", out)
        self.assertIn(b"0.1 0.2 0.9 0 k", out)                # a colour stays a colour

    def test_boxes(self):
        import print as pr
        media, bleed, trim = pr.boxes((210, 297), 3, 10)
        self.assertAlmostEqual(media[2], 236 * 72 / 25.4, places=2)
        self.assertAlmostEqual(trim[0], 13 * 72 / 25.4, places=2)
        self.assertAlmostEqual(bleed[0], 10 * 72 / 25.4, places=2)


class Formats(unittest.TestCase):
    def test_structure(self):
        import make
        a = bytes(range(0, 256))
        self.assertAlmostEqual(make.structure(a, a), 1.0)
        self.assertAlmostEqual(make.structure(a, bytes(255 - x for x in a)), -1.0)

    def test_save_and_use(self):
        with tempfile.TemporaryDirectory() as t:
            env_root = Path(t) / "formats"
            d = new_design(t, "source-piece")
            st = d / "STATE.md"
            st.write_text(re.sub(r"(- \*\*Structure:\*\*) <[^\n]*", r"\1 one big word", st.read_text(encoding="utf-8")), encoding="utf-8")
            env = dict(os.environ, GRAPHIC_BASE_FORMATS=str(env_root), PYTHONUTF8="1")
            r = subprocess.run([PY, "tools/formats.py", "save", "test format"], cwd=d, capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([PY, str(S / "init_design.py"), "next-piece", "--quick", "--format", "test format", "--designs-folder", "Designs"],
                               cwd=t, capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            n = Path(t) / "Designs" / "next-piece"
            self.assertTrue((n / "FORMAT.md").is_file())
            self.assertTrue((n / "research" / "format-reference.html").is_file())
            self.assertIn("one big word", (n / "FORMAT.md").read_text(encoding="utf-8"))


class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.d = new_design(self.tmp)
        self.tr = Path(self.tmp) / "t.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def transcript(self, *recs):
        self.tr.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")

    def guard(self, mode, tool=None, inp=None, cwd=None):
        ev = {"cwd": str(cwd or self.d), "transcript_path": str(self.tr), "tool_name": tool, "tool_input": inp or {}}
        return run([PY, str(S / "guard.py"), mode], inp=json.dumps(ev))

    def test_show_before_ask(self):
        shown = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "show the user: C:\\x\\review\\stills-v1.jpg (Claude Code)"}]}}
        ask = {"questions": [{"question": "ok?", "header": "Gate", "options": [{"label": "a"}, {"label": "b"}]}]}
        self.transcript(shown)
        self.assertEqual(self.guard("tool", "AskUserQuestion", ask).returncode, 2)
        sent = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "SendUserFile", "input": {"files": ["C:\\x\\review\\stills-v1.jpg"]}}]}}
        self.transcript(shown, sent)
        self.assertEqual(self.guard("tool", "AskUserQuestion", ask).returncode, 0)

    def test_ideas_wait_for_checks(self):
        self.transcript()
        ask = {"questions": [{"question": "hangi?", "header": "Fikir", "options": [{"label": "a"}, {"label": "b"}]}]}
        self.assertEqual(self.guard("tool", "AskUserQuestion", ask).returncode, 2)
        r = self.d / "research"
        for f in ("predict.md", "candidates.md", "overlap.md"):
            (r / f).write_text("x", encoding="utf-8")
        self.assertEqual(self.guard("tool", "AskUserQuestion", ask).returncode, 0)

    def test_card_before_picture(self):
        edit = {"file_path": str(self.d / "design.html"), "old_string": "a", "new_string": "<section class='x'>"}
        self.assertEqual(self.guard("tool", "Edit", edit).returncode, 2)
        st = self.d / "STATE.md"
        st.write_text(re.sub(r"(- \*\*Structure:\*\*) <[^\n]*", r"\1 one huge number and a small photo", st.read_text(encoding="utf-8")), encoding="utf-8")
        self.assertEqual(self.guard("tool", "Edit", edit).returncode, 2)          # the words are not approved yet
        st.write_text(st.read_text(encoding="utf-8").replace("- **Copy approved:** no", "- **Copy approved:** yes"), encoding="utf-8")
        self.assertEqual(self.guard("tool", "Edit", edit).returncode, 0)

    def test_copy_shown_before_approval(self):
        st = self.d / "STATE.md"
        st.write_text(re.sub(r"(- \*\*Copy:\*\*) <[^\n]*", r"\1 headline: Rivers come home · body: Four districts dry since spring · cta: Read the report",
                             st.read_text(encoding="utf-8")), encoding="utf-8")
        approve = {"file_path": str(st), "old_string": "- **Copy approved:** no", "new_string": "- **Copy approved:** yes"}
        user = lambda t: {"type": "user", "message": {"content": t}}
        say = lambda t: {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}
        self.transcript(user("make a post"), say("Shall I write the words, or will you?"), user("you write them"))
        self.assertEqual(self.guard("tool", "Edit", approve).returncode, 2)
        self.transcript(user("make a post"), say("HEADLINE Rivers come home\nBODY Four districts dry since spring\nCTA Read the report"), user("ok"))
        self.assertEqual(self.guard("tool", "Edit", approve).returncode, 0)

    def test_helper_brief(self):
        self.assertEqual(self.guard("tool", "Agent", {"prompt": "go"}).returncode, 2)
        self.assertEqual(self.guard("tool", "Agent", {"prompt": "<!-- graphic-base brief: review --> go"}).returncode, 0)

    def test_key_store_and_outside(self):
        self.assertEqual(self.guard("tool", "Bash", {"command": "type %USERPROFILE%\\.graphic-base\\keys.env"}, cwd=self.tmp).returncode, 2)
        self.assertEqual(self.guard("tool", "Agent", {"prompt": "go"}, cwd=self.tmp).returncode, 0)   # not a design: silent

    def test_stop_after_draft(self):
        self.transcript({"type": "user", "message": {"content": "devam"}},
                        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "draft v2: 2 view(s)\nshow the user: C:\\y\\draft-v2.jpg"}]}})
        r = self.guard("stop")
        self.assertIn('"decision": "block"', r.stdout)


@unittest.skipUnless(HAS_NODE, "node and Chrome needed")
class Render(unittest.TestCase):
    def test_checks_and_final(self):
        with tempfile.TemporaryDirectory() as t:
            d = new_design(t)
            r = run([PY, "tools/make.py", "check"], cwd=d)
            self.assertIn("TEMPLATE", r.stdout)
            fill(d, """<section class="view" data-view="post"><div class="safe"><h1 class="h" data-role="headline">Test başlık</h1>
              <p class="b" data-role="body">İçerik satırı.</p></div></section>
              <section class="view" data-view="card"><div class="safe"><h1 class="h" data-role="headline">Test</h1>
              <p class="b" data-role="body">İçerik.</p><p data-role="legal" style="font-size:4px">küçük</p></div></section>""")
            r = run([PY, "tools/make.py", "draft"], cwd=d)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)   # system fonts and a 3 pt line: held
            self.assertIn("FONT", r.stdout)
            self.assertIn("SMALL card", r.stdout)

    def test_pages_and_layout(self):
        with tempfile.TemporaryDirectory() as t:
            d = new_design(t, studio=True)
            pages = "".join(f'<section class="view" data-view="card" data-page="{i}" data-kind="text"><div class="safe">'
                            f'<h1 class="h" data-role="headline">Sayfa {i}</h1></div></section>' for i in range(1, 6))
            fill(d, '<section class="view" data-view="post"><div class="safe"><h1 class="h" data-role="headline">Post</h1></div></section>' + pages)
            st = d / "STATE.md"
            st.write_text(st.read_text(encoding="utf-8").replace("- **Structure:** <", "- **Structure:** test <"), encoding="utf-8")
            r = run([PY, "tools/make.py", "layout"], cwd=d)
            self.assertIn("5 page(s)", r.stdout, r.stderr)
            self.assertIn("pacing card", r.stdout)
            self.assertIn("binding card", r.stdout)


if __name__ == "__main__":
    unittest.main()
