"""국어 PDF 모든 페이지에서 문항 번호 후보 텍스트 찾기"""
import fitz, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test_korean.pdf"
doc = fitz.open(PDF)

QNUM_PATTERNS = [
    (re.compile(r"^\s*(\d{1,2})\s*\.\s*$"), "N.단독"),
    (re.compile(r"^\s*(\d{1,2})\s*\.\s+\S"), "N. text"),
    (re.compile(r"^\s*(\d{1,2})\s*\.\s*[가-힣]"), "N.한글"),
]

for p_idx in range(len(doc)):
    page = doc[p_idx]
    p = p_idx + 1
    text = page.get_text("dict")
    finds = []
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "").strip()
                if not t: continue
                bbox = span["bbox"]
                size = span.get("size", 0)
                for pat, name in QNUM_PATTERNS:
                    m = pat.match(t)
                    if m:
                        finds.append((bbox[0], bbox[1], size, m.group(1), t[:30], name))
                        break
    if finds:
        print(f"\n=== p{p} — 문항 번호 후보 {len(finds)}개 ===")
        for x,y,sz,q,t,name in finds:
            print(f"  q{q:>3} x={x:6.1f} y={y:6.1f} sz={sz:5.2f} [{name}] {t!r}")
