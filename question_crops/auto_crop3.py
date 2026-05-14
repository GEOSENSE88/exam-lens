"""
v3: 좌측 띠 잉크를 세로로 팽창(dilate)해서 줄 → 단락 단위 chunk 화
    + 첫 chunk는 무조건 문항 시작 + 컬럼 전체 폭 검증
"""
import fitz
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import json

PDF_PATH = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(260415).pdf"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\auto3")
OUT.mkdir(parents=True, exist_ok=True)
DEBUG = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\debug3")
DEBUG.mkdir(parents=True, exist_ok=True)

ZOOM = 2.5
DARK_THRESHOLD = 200
LEFT_STRIP_PX = 40
DILATE_PX = 12             # 줄 사이를 메워 단락 단위로 만들기
PRE_GAP_MIN_PX = 18        # 단락 간 최소 빈 띠
MIN_QSTART_HEIGHT = 14
HEADER_FOOTER_MARGIN = 90

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
    best = (0, 0, 0); cur = None
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

def dilate_1d(arr, k):
    """1D bool/int 배열을 위/아래로 k픽셀 팽창"""
    out = arr.copy().astype(np.uint8)
    for shift in range(1, k+1):
        out[:-shift] |= arr[shift:]
        out[shift:]  |= arr[:-shift]
    return out

def find_question_starts(col_gray, header=HEADER_FOOTER_MARGIN, footer=HEADER_FOOTER_MARGIN):
    H, W = col_gray.shape
    strip = col_gray[:, :LEFT_STRIP_PX]
    has_ink = (strip < DARK_THRESHOLD).sum(axis=1) > 1  # 행별 잉크 유무
    has_ink_dilated = dilate_1d(has_ink.astype(np.uint8), DILATE_PX).astype(bool)

    # 단락 chunks
    chunks = []
    cur = None
    for y in range(header, H - footer):
        if has_ink_dilated[y]:
            if cur is None: cur = y
        else:
            if cur is not None:
                chunks.append((cur, y)); cur = None
    if cur is not None:
        chunks.append((cur, H - footer))

    starts = []
    prev_end = header
    for idx, (s, e) in enumerate(chunks):
        height = e - s
        gap_above = s - prev_end
        if idx == 0 and height >= MIN_QSTART_HEIGHT:
            starts.append({"y": s, "h": height, "gap_above": gap_above, "first": True})
        elif gap_above >= PRE_GAP_MIN_PX:
            full_strip_above = col_gray[max(prev_end, s - PRE_GAP_MIN_PX):s, :]
            full_ink_above = (full_strip_above < DARK_THRESHOLD).sum() / max(full_strip_above.size, 1)
            if full_ink_above < 0.005 and height >= MIN_QSTART_HEIGHT:
                starts.append({"y": s, "h": height, "gap_above": gap_above})
        prev_end = e
    return starts, chunks

def crop_with_starts(col_img, starts, header=HEADER_FOOTER_MARGIN, footer=HEADER_FOOTER_MARGIN):
    H = col_img.shape[0]
    if not starts:
        return [(header, H - footer, col_img[header:H - footer])]
    ys = [s["y"] for s in starts] + [H - footer]
    crops = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i+1]
        if y1 - y0 < 50: continue
        y0p = max(y0 - 8, 0)
        crops.append((y0p, y1, col_img[y0p:y1]))
    return crops

doc = fitz.open(PDF_PATH)
all_crops = []
qcount = 0
for page_no in range(1, len(doc)):
    page = doc[page_no]
    img = render(page); gray = to_gray(img)
    cols = detect_columns(gray)
    if not cols:
        print(f"page {page_no+1}: 컬럼 감지 실패"); continue
    dbg = Image.fromarray(img.copy()); draw = ImageDraw.Draw(dbg)
    H = img.shape[0]
    for col_name in ("left_col", "right_col"):
        x0, x1 = cols[col_name]
        col_img = img[:, x0:x1]
        col_gray = gray[:, x0:x1]
        starts, chunks = find_question_starts(col_gray)
        crops = crop_with_starts(col_img, starts)
        print(f"  page{page_no+1} {col_name}: starts={len(starts)} crops={len(crops)} #chunks={len(chunks)}")
        draw.line([(x0, 0), (x0, H)], fill="red", width=2)
        draw.line([(x1, 0), (x1, H)], fill="red", width=2)
        draw.line([(x0+LEFT_STRIP_PX, 0), (x0+LEFT_STRIP_PX, H)], fill="orange", width=1)
        for s in starts:
            draw.line([(x0, s["y"]), (x1, s["y"])], fill="green", width=2)
        for ci, (y0, y1, crop) in enumerate(crops):
            qcount += 1
            out = OUT / f"p{page_no+1:02d}_{col_name[0]}_{ci+1}.png"
            Image.fromarray(crop).save(out)
            all_crops.append({"file": out.name, "page": page_no+1, "column": col_name,
                              "y_range": [int(y0), int(y1)], "x_range": [int(x0), int(x1)]})
    dbg.save(DEBUG / f"page_{page_no+1:02d}_dbg.png")

print(f"\n총 조각: {qcount}")
with open(OUT / "index.json", "w", encoding="utf-8") as f:
    json.dump(all_crops, f, ensure_ascii=False, indent=1)
