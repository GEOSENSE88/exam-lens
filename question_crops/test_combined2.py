"""합본 PDF — Q1, Q2가 어디에 있나? 페이지 2,3 상세 텍스트"""
import fitz, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

doc = fitz.open(r"C:\Users\이성훈\OneDrive\Exam_lens\test_combined.pdf")

QNUM_PATS = [
    (re.compile(r"^\s*(\d{1,2})\s*\.\s+\S"), "N. text"),
    (re.compile(r"^\s*(\d{1,2})\s*\.\s*[가-힣]"), "N.한글"),
    (re.compile(r"^\s*(\d{1,2})\s*\.\s*$"), "N.단독"),
]

for p_idx in [1, 2, 3]:  # PDF 페이지 2, 3, 4 (0-index 1,2,3)
    page = doc[p_idx]
    p = p_idx + 1
    W, H = page.rect.width, page.rect.height
    text = page.get_text("dict")
    print(f"\n{'='*60}\n=== PDF p{p} 모든 span (sz, x, y, text) ===")
    spans = []
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                if not t.strip(): continue
                bbox = span["bbox"]
                sz = span.get("size", 0)
                spans.append((bbox[1], bbox[0], sz, t.strip()))
    spans.sort(key=lambda s: (s[0], s[1]))  # y, x 순
    for y,x,sz,t in spans:
        marker = ""
        for pat,name in QNUM_PATS:
            if pat.match(t):
                marker = f"  ★문항후보({name})"
                break
        # Look for digit. patterns
        if re.search(r"^\d+\.", t):
            marker = marker or "  →숫자.시작"
        print(f"  y={y:6.1f} x={x:6.1f} sz={sz:5.2f} {t[:60]!r}{marker}")
