"""
v2: 문항 번호("1.", "2." 등 굵은 큰 글자)는 컬럼의 좌측 가장자리에만 등장한다는
    레이아웃 특성을 이용해 더 정확히 분할.

알고리즘
1) 컬럼 경계 자동 감지 (v1과 동일)
2) 각 컬럼에서 좌측 띠(left strip, 폭 ~40px)만 보고 잉크 행을 찾는다.
   ① ② ③ 같은 답지 마커는 보통 한 칸 들여쓰기되어 strip 안쪽 끝에 위치.
   문항 번호 "1.", "2." 도 strip에 위치하지만, 글자 크기가 더 크다.
3) 각 잉크 덩어리(consecutive ink rows in left strip)를 후보로 삼고,
   그 중에서 "위로 큰 빈 띠(>=40px)가 있고 글자 높이가 본문보다 큰" 것만
   문항 시작으로 채택.
4) 채택된 시작 y 사이를 잘라 문항 이미지 저장.
"""
import fitz
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import json

PDF_PATH = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(260415).pdf"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\auto2")
OUT.mkdir(parents=True, exist_ok=True)
DEBUG = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\debug2")
DEBUG.mkdir(parents=True, exist_ok=True)

ZOOM = 2.5
DARK_THRESHOLD = 200
LEFT_STRIP_PX = 38         # 컬럼 좌측 띠 폭 — 문항 번호 "1.", "2." 가 들어가는 영역
PRE_GAP_MIN_PX = 35        # 문항 시작 위에 이 정도 빈 띠가 있어야 함
MIN_QSTART_HEIGHT = 14     # 문항 번호 글자 높이 최소 (작은 ① 등 무시)
HEADER_FOOTER_MARGIN = 80

def render(page, zoom=ZOOM):
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4: img = img[..., :3]
    return img

def to_gray(img):
    return (0.299*img[...,0] + 0.587*img[...,1] + 0.114*img[...,2]).astype(np.uint8)

def detect_columns(gray):
    H, W = gray.shape
    ink = (gray < DARK_THRESHOLD).astype(np.uint8)
    col_density = ink.sum(axis=0)
    mid_start, mid_end = W // 3, (2 * W) // 3
    in_gap = col_density[mid_start:mid_end] < (H * 0.01)
    best = (0, 0, 0)
    cur = None
    for i, v in enumerate(in_gap):
        if v:
            if cur is None: cur = i
        else:
            if cur is not None:
                ln = i - cur
                if ln > best[0]: best = (ln, cur + mid_start, i + mid_start)
                cur = None
    if cur is not None:
        ln = len(in_gap) - cur
        if ln > best[0]: best = (ln, cur + mid_start, len(in_gap) + mid_start)
    if best[0] < 5: return None
    nz = np.where(col_density > H * 0.01)[0]
    if len(nz) == 0: return None
    return {
        "left_col":  (max(int(nz[0])-5, 0), best[1]),
        "right_col": (best[2], min(int(nz[-1])+5, W-1)),
    }

def find_question_starts(col_gray, header=HEADER_FOOTER_MARGIN, footer=HEADER_FOOTER_MARGIN):
    """컬럼의 좌측 띠에서 문항 번호 시작 y를 찾는다."""
    H, W = col_gray.shape
    strip = col_gray[:, :LEFT_STRIP_PX]
    ink = (strip < DARK_THRESHOLD).astype(np.uint8)
    row_ink = ink.sum(axis=1)
    has_ink = row_ink > 1  # 행에 잉크가 1픽셀 이상

    # 좌측 띠에서의 잉크 덩어리(연속 행) 추출
    chunks = []
    cur = None
    for y in range(header, H - footer):
        if has_ink[y]:
            if cur is None: cur = y
        else:
            if cur is not None:
                chunks.append((cur, y))
                cur = None
    if cur is not None:
        chunks.append((cur, H - footer))

    # 각 chunk 사이의 위쪽 빈 띠 길이 계산
    starts = []
    prev_end = header
    for idx, (s, e) in enumerate(chunks):
        height = e - s
        gap_above = s - prev_end
        # 컬럼의 첫 잉크 chunk는 (충분히 크면) 무조건 문항 시작으로 채택
        is_first_in_col = (idx == 0)
        if is_first_in_col and height >= MIN_QSTART_HEIGHT:
            starts.append({"y": s, "h": height, "gap_above": gap_above, "first": True})
            prev_end = e
            continue
        if gap_above >= PRE_GAP_MIN_PX:
            full_strip_above = col_gray[max(prev_end, s - PRE_GAP_MIN_PX):s, :]
            full_ink_above = (full_strip_above < DARK_THRESHOLD).sum() / full_strip_above.size
            if full_ink_above < 0.005 and height >= MIN_QSTART_HEIGHT:
                starts.append({"y": s, "h": height, "gap_above": gap_above})
        prev_end = e
    return starts, chunks

def crop_with_starts(col_img, starts, header=HEADER_FOOTER_MARGIN, footer=HEADER_FOOTER_MARGIN):
    H = col_img.shape[0]
    if not starts:
        return [(header, H - footer, col_img[header:H - footer])]
    cuts = [s["y"] for s in starts] + [H - footer]
    crops = []
    # 첫 cut 이전(보통 컬럼 위쪽 여백)에 본문이 있으면 무시
    for i in range(len(cuts) - 1):
        y0, y1 = cuts[i], cuts[i+1]
        if y1 - y0 < 50: continue
        # 살짝 위로 패딩 (문항 번호 위 여백)
        y0p = max(y0 - 5, 0)
        crops.append((y0p, y1, col_img[y0p:y1]))
    return crops

# --- 메인
doc = fitz.open(PDF_PATH)
all_crops = []
qcount = 0
for page_no in range(1, len(doc)):  # 표지 제외
    page = doc[page_no]
    img = render(page)
    gray = to_gray(img)
    cols = detect_columns(gray)
    if not cols:
        print(f"page {page_no+1}: 컬럼 감지 실패")
        continue

    dbg = Image.fromarray(img.copy())
    draw = ImageDraw.Draw(dbg)
    H = img.shape[0]
    for col_name in ("left_col", "right_col"):
        x0, x1 = cols[col_name]
        col_img = img[:, x0:x1]
        col_gray = gray[:, x0:x1]
        starts, chunks = find_question_starts(col_gray)
        crops = crop_with_starts(col_img, starts)
        chunk_info = ""
        if len(chunks) <= 8:
            chunk_info = " chunks=" + str([(s, e, e-s) for s, e in chunks])
        print(f"  page{page_no+1} {col_name}: starts={len(starts)} crops={len(crops)} #chunks={len(chunks)}{chunk_info}")
        # 디버그 표시
        draw.line([(x0, 0), (x0, H)], fill="red", width=2)
        draw.line([(x1, 0), (x1, H)], fill="red", width=2)
        draw.line([(x0+LEFT_STRIP_PX, 0), (x0+LEFT_STRIP_PX, H)], fill="orange", width=1)
        for s in starts:
            draw.line([(x0, s["y"]), (x1, s["y"])], fill="green", width=2)
        # 저장
        for ci, (y0, y1, crop) in enumerate(crops):
            qcount += 1
            out = OUT / f"p{page_no+1:02d}_{col_name[0]}_{ci+1}.png"
            Image.fromarray(crop).save(out)
            all_crops.append({
                "file": out.name, "page": page_no+1, "column": col_name,
                "y_range": [int(y0), int(y1)], "x_range": [int(x0), int(x1)],
            })
    dbg.save(DEBUG / f"page_{page_no+1:02d}_dbg.png")

print(f"\n총 조각: {qcount}")
with open(OUT / "index.json", "w", encoding="utf-8") as f:
    json.dump(all_crops, f, ensure_ascii=False, indent=1)
