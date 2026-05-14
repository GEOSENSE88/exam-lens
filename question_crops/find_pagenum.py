"""각 PDF 페이지에서 footer 쪽번호 후보 찾기 (가상 페이지 좌/우 별로)"""
import fitz, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test_korean.pdf"
doc = fitz.open(PDF)

# 다양한 쪽번호 패턴
PATTERNS = [
    re.compile(r"\(\s*(\d+)\s*\)\s*쪽"),
    re.compile(r"(\d+)\s*/\s*\d+"),
    re.compile(r"-\s*(\d+)\s*-"),
    re.compile(r"^\s*(\d+)\s*$"),
]

print("=== 각 페이지의 footer 영역 텍스트 + 쪽번호 후보 ===")
for p_idx in range(len(doc)):
    page = doc[p_idx]
    p = p_idx + 1
    W, H = page.rect.width, page.rect.height
    text = page.get_text("dict")
    footer_items = []  # y > H * 0.85
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "").strip()
                if not t: continue
                bbox = span["bbox"]
                if bbox[1] >= H * 0.85:
                    footer_items.append((bbox[0], bbox[1], span.get("size",0), t))
    print(f"\n--- p{p} (W={W} H={H}) — footer 토큰 {len(footer_items)} ---")
    for x,y,sz,t in footer_items[:30]:
        print(f"  x={x:6.1f} y={y:6.1f} sz={sz:4.1f} {t!r}")
    # 쪽번호 추출
    for x,y,sz,t in footer_items:
        for pat in PATTERNS:
            m = pat.search(t)
            if m:
                print(f"  → 쪽 {m.group(1)} (x={x:6.1f}, pattern={pat.pattern!r}, text={t!r})")
                break
