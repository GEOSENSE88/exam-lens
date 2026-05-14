"""국어 PDF — 모든 문항 번호와 선지 ⑤ 위치를 페이지별로 정리"""
import fitz, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test_korean.pdf"
doc = fitz.open(PDF)

QNUM = re.compile(r"^\s*(\d{1,2})\s*[.．]\s*$")
QNUM_INLINE = re.compile(r"^\s*(\d{1,2})\s*[.．]\s+\S")
SQ = re.compile(r"\[\s*서술형\s*문항?\s*(\d+)\s*\]")

# 컬럼 x 위치 추정 (4 컬럼 booklet 가정)
# page width 842, 4컬럼이면 약 0, 210, 420, 630 근처에서 시작

print("=== 페이지별 문항 번호 + ⑤ 위치 ===")
for p_idx in range(len(doc)):
    page = doc[p_idx]
    p = p_idx + 1
    text = page.get_text("dict")
    qnums = []
    fives = []  # ⑤ 위치들
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                bbox = span["bbox"]
                size = span.get("size", 0)
                m = QNUM.match(t) or QNUM_INLINE.match(t)
                if m and 10 <= size <= 30:
                    qnums.append({"q": int(m.group(1)), "x": bbox[0], "y": bbox[1], "size": size})
                m2 = SQ.search(t)
                if m2:
                    qnums.append({"q": "S"+m2.group(1), "x": bbox[0], "y": bbox[1], "size": size})
                if "⑤" in t and 8 <= size <= 20:
                    fives.append({"x": bbox[0], "y": bbox[1], "text": t[:25]})
    if not qnums and not fives:
        continue
    print(f"\n--- p{p} ---")
    # 컬럼별로 묶기 (x ± 40)
    cols = {}
    for q in qnums + fives:
        key = round(q["x"] / 40) * 40
        cols.setdefault(key, []).append(q)
    for kx in sorted(cols.keys()):
        items = sorted(cols[kx], key=lambda i: i["y"])
        print(f"  컬럼 x~={kx}:")
        for it in items:
            if "q" in it:
                print(f"    문항 {str(it['q']):>4} y={it['y']:6.1f}")
            else:
                print(f"    ⑤    y={it['y']:6.1f}  text={it['text']!r}")
