"""한국지리 PDF 분석 — footer 쪽번호 추출 + 가상 페이지 분포"""
import fitz, re, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(공개용).pdf"
DST = r"C:\Users\이성훈\OneDrive\Exam_lens\test_geo.pdf"
shutil.copy(SRC, DST)
doc = fitz.open(DST)
print(f"pages: {len(doc)} rect={doc[0].rect}")

PNUM = re.compile(r"\(\s*(\d+)\s*\)\s*쪽")

for p_idx in range(len(doc)):
    page = doc[p_idx]
    p = p_idx + 1
    W, H = page.rect.width, page.rect.height
    text = page.get_text("dict")
    footer_items = []
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                if not t.strip(): continue
                bbox = span["bbox"]
                if bbox[1] >= H * 0.85 or bbox[1] <= H * 0.10:
                    footer_items.append((bbox[0], bbox[1], span.get("size",0), t))
    print(f"\n=== p{p} (W={W} H={H}) — header/footer 토큰 {len(footer_items)} ===")
    for x,y,sz,t in footer_items[:25]:
        print(f"  x={x:6.1f} y={y:6.1f} sz={sz:4.1f} {t!r}")
    # 페이지번호
    by_y = {}
    for x,y,sz,t in footer_items:
        yKey = round(y/4)*4
        by_y.setdefault(yKey, []).append((x, t))
    for yKey, items in by_y.items():
        items.sort(key=lambda i:i[0])
        joined = ' '.join(i[1] for i in items)
        ms = list(PNUM.finditer(joined))
        if ms:
            avgX = sum(i[0] for i in items)/len(items)
            print(f"  → y={yKey} avgX={avgX:.1f} 쪽번호: {[m.group(1) for m in ms]} (마지막={ms[-1].group(1)}) text={joined[:80]!r}")
