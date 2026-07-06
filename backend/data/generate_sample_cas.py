"""Dev-only generator for the bundled synthetic sample CAS PDF (WEA-73).

Pure-Python, ZERO third-party dependencies — emits a valid A4 text PDF using
the built-in Helvetica fonts. Run once to (re)produce `sample_cas.pdf`; this
script is NOT imported by the running app, so it adds no runtime dependency and
cannot affect the Docker build.

    python backend/data/generate_sample_cas.py

The numbers here MUST stay in sync with SAMPLE_CAS_HOLDINGS in
backend/routers/portfolio.py — the PDF is the "look, a real statement" visual;
the holdings list is the demo source of truth for the analysis.
"""
import os

# IDBI brand-ish colours (r, g, b in 0..1)
GREEN = (0.0, 0.514, 0.424)
ORANGE = (0.953, 0.44, 0.129)
LIGHT = (0.90, 0.96, 0.94)
GRAY = (0.45, 0.45, 0.45)
WHITE = (1, 1, 1)
BLACK = (0, 0, 0)

PAGE_W, PAGE_H = 595, 842  # A4 in points


def _esc(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


class Content:
    """Accumulates PDF page-content operators."""

    def __init__(self):
        self.ops: list[str] = []

    def text(self, x, y, size, s, bold=False, color=BLACK):
        r, g, b = color
        font = "F2" if bold else "F1"
        self.ops.append(
            f"BT {r:.3f} {g:.3f} {b:.3f} rg /{font} {size} Tf "
            f"1 0 0 1 {x} {y} Tm ({_esc(s)}) Tj ET"
        )

    def rect(self, x, y, w, h, color):
        r, g, b = color
        self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x} {y} {w} {h} re f")

    def line(self, x1, y1, x2, y2, color=GRAY, width=0.6):
        r, g, b = color
        self.ops.append(
            f"{r:.3f} {g:.3f} {b:.3f} RG {width} w {x1} {y1} m {x2} {y2} l S"
        )

    def render(self) -> bytes:
        return "\n".join(self.ops).encode("latin-1")


def build_content() -> bytes:
    c = Content()

    # ---- Header band ----
    c.rect(0, PAGE_H - 62, PAGE_W, 62, GREEN)
    c.text(40, PAGE_H - 34, 18, "Consolidated Account Statement (CAS)", bold=True, color=WHITE)
    c.text(40, PAGE_H - 52, 9, "SPECIMEN / SAMPLE  -  for WealthSeva AI demonstration only. Not a real statement.", color=WHITE)

    # ---- Investor block ----
    y = PAGE_H - 84
    c.text(40, y, 11, "Investor: RAMESH KUMAR", bold=True)
    c.text(40, y - 16, 10, "PAN: ABCDE1234F   (specimen PAN - not a real PAN)")
    c.text(40, y - 32, 10, "Statement Period: 01-Apr-2025 to 31-Mar-2026")
    c.text(40, y - 48, 10, "Consolidation: NSDL / CDSL depositories + CAMS / KFintech RTAs")

    # ---- Section A: Demat equity holdings ----
    y = PAGE_H - 152
    c.text(40, y, 12, "A.  Demat Holdings - Equity Shares", bold=True, color=GREEN)
    c.line(40, y - 5, PAGE_W - 40, y - 5, GREEN, 1.0)
    y -= 20
    c.text(40, y, 9, "Company", bold=True)
    c.text(250, y, 9, "ISIN", bold=True)
    c.text(400, y, 9, "Units", bold=True)
    c.text(480, y, 9, "Value (Rs)", bold=True)
    equity_rows = [
        ("Reliance Industries Ltd", "INE002A01018", "50", "1,45,000"),
        ("HDFC Bank Ltd", "INE040A01034", "60", "96,000"),
        ("Infosys Ltd", "INE009A01021", "50", "78,000"),
    ]
    for name, isin, units, val in equity_rows:
        y -= 15
        c.text(40, y, 9, name)
        c.text(250, y, 9, isin)
        c.text(400, y, 9, units)
        c.text(480, y, 9, val)

    # ---- Section B: Mutual fund folios ----
    y -= 34
    c.text(40, y, 12, "B.  Mutual Fund Folios", bold=True, color=GREEN)
    c.line(40, y - 5, PAGE_W - 40, y - 5, GREEN, 1.0)
    y -= 20
    c.text(40, y, 9, "Scheme", bold=True)
    c.text(250, y, 9, "Folio", bold=True)
    c.text(330, y, 9, "Category", bold=True)
    c.text(420, y, 9, "Units", bold=True)
    c.text(500, y, 9, "Value (Rs)", bold=True)
    mf_rows = [
        ("SBI Bluechip Fund", "12345678", "Equity", "700.000", "62,000"),
        ("HDFC Corporate Bond Fund", "23456789", "Debt", "3,600.000", "1,10,000"),
        ("ICICI Pru Short Term Fund", "34567890", "Debt", "1,400.000", "70,000"),
        ("SBI Liquid Fund", "45678901", "Liquid", "24.000", "90,000"),
        ("Nippon India Gold Savings Fund", "56789012", "Gold", "1,800.000", "45,000"),
    ]
    for name, folio, cat, units, val in mf_rows:
        y -= 15
        c.text(40, y, 9, name)
        c.text(250, y, 9, folio)
        c.text(330, y, 9, cat)
        c.text(420, y, 9, units)
        c.text(500, y, 9, val)

    # ---- Total band ----
    y -= 30
    c.rect(40, y - 6, PAGE_W - 80, 22, LIGHT)
    c.text(48, y, 12, "Total Portfolio Value:  Rs 6,96,000", bold=True, color=GREEN)

    # ---- Asset allocation summary ----
    y -= 40
    c.text(40, y, 12, "Asset Allocation", bold=True, color=ORANGE)
    for i, (label, val, pct) in enumerate([
        ("Equity", "3,81,000", "55%"),
        ("Debt", "1,80,000", "26%"),
        ("Liquid", "90,000", "13%"),
        ("Gold", "45,000", "6%"),
    ]):
        yy = y - 18 - i * 15
        c.text(48, yy, 10, f"{label}")
        c.text(180, yy, 10, f"Rs {val}")
        c.text(300, yy, 10, pct)

    # ---- Footer disclaimer ----
    c.text(40, 48, 8,
           "This is a SPECIMEN statement generated for the WealthSeva AI demo. All names, PAN, folios and",
           color=GRAY)
    c.text(40, 38, 8,
           "holdings are fictitious. Not a financial document and not for any real transaction.",
           color=GRAY)

    return c.render()


def build_pdf() -> bytes:
    content = build_content()
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> "
            b"/Contents 6 0 R >>" % (PAGE_W, PAGE_H)
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]  # object 0 is the free head
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i
        out += obj
        out += b"\nendobj\n"

    xref_pos = len(out)
    n = len(objects) + 1
    out += b"xref\n0 %d\n" % n
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % n
    out += b"startxref\n%d\n%%%%EOF\n" % xref_pos
    return bytes(out)


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_cas.pdf")
    with open(path, "wb") as f:
        f.write(build_pdf())
    print(f"Wrote {path} ({os.path.getsize(path)} bytes)")
