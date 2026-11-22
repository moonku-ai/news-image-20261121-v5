"""Tests for the news-image-20261121 v5 entry program (pure stdlib).

TDD: written BEFORE main.py exists. Run with: python3 test_main.py
"""
import ast
import binascii
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "main.py")


def run_main(outdir):
    env = dict(os.environ)
    env["MAKEFUN_OUTPUT_DIR"] = outdir
    r = subprocess.run([sys.executable, MAIN], env=env,
                       capture_output=True, text=True, timeout=120)
    return r


def parse_png_chunks(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    chunks = []
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        payload = data[pos + 8:pos + 8 + length]
        crc_stored, = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        crc_calc = binascii.crc32(ctype + payload) & 0xFFFFFFFF
        chunks.append((ctype.decode("latin1"), payload, crc_stored, crc_calc))
        pos += 12 + length
        if ctype == b"IEND":
            break
    return chunks


class TestEntryImage(unittest.TestCase):
    def test_png_valid_dimensions_and_crc(self):
        """Output is a valid PNG, 1024x1024, all chunk CRCs correct."""
        with tempfile.TemporaryDirectory() as d:
            r = run_main(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            path = os.path.join(d, "entry.png")
            self.assertTrue(os.path.exists(path))
            data = open(path, "rb").read()
            chunks = parse_png_chunks(data)
            self.assertEqual(chunks[0][0], "IHDR")
            w, h, depth, ctype = struct.unpack(">IIBB", chunks[0][1][:10])
            self.assertEqual((w, h), (1024, 1024))
            self.assertEqual(depth, 8)
            self.assertEqual(ctype, 2)  # truecolour RGB
            for name, _payload, stored, calc in chunks:
                self.assertEqual(stored, calc, f"bad CRC in {name}")
            self.assertEqual(chunks[-1][0], "IEND")
            # IDAT decompresses to exactly 1024 rows of (1 filter + 3072 bytes)
            idat = b"".join(p for n, p, _s, _c in chunks if n == "IDAT")
            raw = zlib.decompress(idat)
            self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))

    def test_deterministic_byte_identical(self):
        """Two runs produce byte-identical output."""
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            self.assertEqual(run_main(d1).returncode, 0)
            self.assertEqual(run_main(d2).returncode, 0)
            b1 = open(os.path.join(d1, "entry.png"), "rb").read()
            b2 = open(os.path.join(d2, "entry.png"), "rb").read()
            self.assertEqual(b1, b2)

    def test_size_limit(self):
        """Output is at most 1 MiB."""
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_main(d).returncode, 0)
            size = os.path.getsize(os.path.join(d, "entry.png"))
            self.assertLessEqual(size, 1048576, f"entry.png is {size} bytes")

    def test_stdlib_only(self):
        """main.py imports only the standard library."""
        tree = ast.parse(open(MAIN).read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        extra = imported - sys.stdlib_module_names
        self.assertEqual(extra, set(), f"non-stdlib imports: {extra}")

    def test_image_is_not_blank_and_has_ink(self):
        """The picture has real content: paper background plus plenty of ink."""
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_main(d).returncode, 0)
            data = open(os.path.join(d, "entry.png"), "rb").read()
            chunks = parse_png_chunks(data)
            idat = b"".join(p for n, p, _s, _c in chunks if n == "IDAT")
            raw = zlib.decompress(idat)
            # count non-paper pixels (paper is #F7F3EA)
            paper = bytes((0xF7, 0xF3, 0xEA))
            ink = 0
            for y in range(1024):
                row = raw[y * 3073 + 1:(y + 1) * 3073]
                for x in range(0, 3072, 3):
                    if row[x:x + 3] != paper:
                        ink += 1
            self.assertGreater(ink, 100000, f"only {ink} non-paper pixels")

    def test_font_covers_all_text(self):
        """Every character drawn on the page exists in the font."""
        import main
        texts = [t for t in main.ALL_TEXT]
        missing = sorted({ch for t in texts for ch in t if ch not in main.FONT})
        self.assertEqual(missing, [], f"characters missing from font: {missing}")

    def test_no_text_overflows_its_box(self):
        """Every wrapped headline/fact line fits its allotted width."""
        import main
        for text, scale, max_w in main.TEXT_BOXES:
            for line in main.wrap_text(text, scale, max_w):
                self.assertLessEqual(main.text_width(line, scale), max_w,
                                     f"{line!r} at scale {scale} exceeds {max_w}px")

    def test_pictograms_draw_without_error(self):
        """Each pictogram function runs and inks pixels in its box."""
        import main
        for name, fn in main.PICTOGRAMS.items():
            img = main.Canvas(300, 300)
            fn(img, 20, 20, 260, 260, main.INK)
            self.assertGreater(img.ink_count(), 100, f"pictogram {name} drew nothing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
