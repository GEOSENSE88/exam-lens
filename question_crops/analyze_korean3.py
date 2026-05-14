"""국어 PDF 페이지 2-5의 모든 텍스트 토큰을 덤프"""
import fitz, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test_korean.pdf"
doc = fitz.open(PDF)

for p_idx in [1, 2, 3, 4]:  # page 2-5
    page = doc[p_idx]
    p = p_idx + 1
    text = page.get_text("dict")
    print(f"\n=== p{p} ===")
    spans = []
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "").strip()
                if not t: continue
                bbox = span["bbox"]
                size = span.get("size", 0)
                spans.append((bbox[0], bbox[1], size, t))
    spans.sort(key=lambda s: (round(s[0]/30)*30, s[1]))
    for x, y, sz, t in spans[:60]:
        print(f"  x={x:6.1f} y={y:6.1f} sz={sz:5.1f} {t!r:.80}")
