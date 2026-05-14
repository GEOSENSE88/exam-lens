"""JS 텍스트 기반 알고리즘과 동일한 로직으로 Q10/Q11 크롭 영역을 시각화"""
import fitz, re
from PIL import Image, ImageDraw
from pathlib import Path

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test.pdf"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\sim_crops")
OUT.mkdir(parents=True, exist_ok=True)

QNUM_RE = re.compile(r"^\s*(\d{1,2})\s*\.\s*$")
QNUM_INLINE_RE = re.compile(r"^\s*(\d{1,2})\s*\.\s+\S")
SQ_RE = re.compile(r"\[\s*서술형\s*문항?\s*(\d+)\s*\]")

doc = fitz.open(PDF)
print(f"Pages: {len(doc)}")

for p_idx, page in enumerate(doc):
    if p_idx + 1 != 4:  # 페이지 4만 분석
        continue
    p = p_idx + 1
    short_side = min(page.rect.width, page.rect.height)
    scale = 1500 / short_side
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    W, H = pix.width, pix.height
    print(f"\n=== p{p}: viewport {W}x{H} (scale={scale:.3f}) ===")

    # 텍스트 아이템 추출 (PDF 좌표)
    text_dict = page.get_text("dict")
    qnums = []
    all_text = []
    for block in text_dict["blocks"]:
        if block.get("type") != 0: continue
        for line in block["lines"]:
            for span in line["spans"]:
                bbox = span["bbox"]  # x0, y0, x1, y1 in PDF top-left origin
                # 픽셀 좌표로 변환 (fitz는 top-left origin)
                px = bbox[0] * scale
                py = bbox[1] * scale
                pw = (bbox[2] - bbox[0]) * scale
                fontH = span["size"] * scale
                s = span["text"]
                if s.strip():
                    all_text.append({"x": px, "y": py, "w": pw, "fontH": fontH, "text": s[:40]})
                # 문항 번호 패턴 — JS와 같이 픽셀 단위 fontH로 필터
                m = QNUM_RE.match(s) or QNUM_INLINE_RE.match(s)
                if m and 12 <= fontH <= 40:
                    qno = int(m.group(1))
                    if 1 <= qno <= 30:
                        qnums.append({"key":"Q"+str(qno), "qno":qno, "x":px, "y":py, "fontH":fontH, "isS":False, "raw":s[:40]})
                        continue
                m2 = SQ_RE.search(s)
                if m2:
                    sno = int(m2.group(1))
                    if 1 <= sno <= 20:
                        qnums.append({"key":"S"+str(sno), "qno":sno, "x":px, "y":py, "fontH":fontH, "isS":True, "raw":s[:40]})

    print(f"문항 번호 후보: {len(qnums)}")
    for q in qnums:
        print(f"  {q['key']:>4} x={q['x']:7.1f} y={q['y']:7.1f} fontH={q['fontH']:.1f}")

    # 컬럼 그룹화 (JS와 동일)
    cols = []
    for q in qnums:
        col = None
        for c in cols:
            if abs(c["x"] - q["x"]) < 30:
                col = c
                break
        if col is None:
            col = {"x": q["x"], "items": []}
            cols.append(col)
        col["items"].append(q)
        col["x"] = (col["x"] * (len(col["items"])-1) + q["x"]) / len(col["items"])
    cols.sort(key=lambda c: c["x"])
    print(f"\n컬럼 개수: {len(cols)}")
    for ci, c in enumerate(cols):
        keys = ", ".join(q["key"] for q in c["items"])
        print(f"  col{ci}: x={c['x']:.1f} items=[{keys}]")

    # 각 컬럼의 우측 경계 계산
    print(f"\n각 컬럼 크롭 영역:")
    img_full = Image.frombytes("RGB", (W, H), pix.samples)
    overlay = img_full.copy()
    draw = ImageDraw.Draw(overlay)
    for ci, c in enumerate(cols):
        x_start = max(0, c["x"] - 8)
        tentative_end = cols[ci+1]["x"] - 8 if ci+1 < len(cols) else W - 5
        actual_right = c["x"]
        for item in all_text:
            if item["x"] >= c["x"] - 5 and item["x"] < tentative_end:
                right = item["x"] + (item["w"] or 0)
                if right > actual_right:
                    actual_right = right
        x_end = min(tentative_end, actual_right + 15)
        c["items"].sort(key=lambda q: q["y"])
        for qi, q in enumerate(c["items"]):
            next_q = c["items"][qi+1] if qi+1 < len(c["items"]) else None
            y_start = max(0, q["y"] - q["fontH"] - 4)
            if next_q:
                y_end = next_q["y"] - next_q["fontH"] - 4
            else:
                y_end = H - 25
            print(f"  {q['key']:>4} crop x=[{x_start:.0f},{x_end:.0f}] y=[{y_start:.0f},{y_end:.0f}] (W={x_end-x_start:.0f} H={y_end-y_start:.0f}) tentEnd={tentative_end:.0f} actualR={actual_right:.0f}")
            # 사각형 그리기
            color = ["red","blue","green","purple","orange"][q["qno"] % 5] if not q["isS"] else "black"
            draw.rectangle([x_start, y_start, x_end, y_end], outline=color, width=4)
            draw.text((x_start+5, y_start+2), q["key"], fill=color)
    overlay.save(OUT / f"p{p}_overlay.png")
    print(f"\n시각화: {OUT / f'p{p}_overlay.png'}")
