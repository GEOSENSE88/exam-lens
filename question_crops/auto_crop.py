"""
자동 문항 분할 — 2단 컬럼 레이아웃 가정
1) PDF를 고해상도로 렌더링
2) 페이지에서 컬럼 경계(좌/우) 자동 감지: 세로 방향 빈 픽셀 띠 찾기
3) 각 컬럼 안에서 수평 프로젝션으로 문항 사이의 흰 띠(gap) 찾기
4) gap 위치에서 잘라 별도 PNG로 저장
"""
import fitz
import numpy as np
from PIL import Image
from pathlib import Path

PDF_PATH = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(260415).pdf"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\auto")
OUT.mkdir(parents=True, exist_ok=True)
DEBUG = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\debug")
DEBUG.mkdir(parents=True, exist_ok=True)

ZOOM = 2.5  # ~180 DPI
DARK_THRESHOLD = 200  # 픽셀이 이보다 어두우면 '잉크' 픽셀
GAP_MIN_HEIGHT_PX = 25  # 이 정도 흰 띠가 있어야 문항 경계로 인정 (zoom 2.5 기준)
HEADER_FOOTER_MARGIN = 80  # 페이지 상하단 머리글/꼬리글 무시

def render_page(page, zoom=ZOOM):
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[..., :3]
    return img

def to_gray(img):
    return (0.299*img[...,0] + 0.587*img[...,1] + 0.114*img[...,2]).astype(np.uint8)

def detect_columns(gray):
    """페이지 전체에서 좌/우 컬럼의 x좌표 범위를 찾는다.
    세로 방향으로 잉크 밀도를 본 뒤, 가운데 영역의 가장 긴 흰 띠를 컬럼 사이 거터로 본다."""
    H, W = gray.shape
    ink = (gray < DARK_THRESHOLD).astype(np.uint8)
    col_density = ink.sum(axis=0)  # 각 x에서 위→아래로 잉크 픽셀 수
    # 가운데 1/3 영역에서 거터(흰 세로 띠) 찾기
    mid_start = W // 3
    mid_end = (2 * W) // 3
    in_gap = col_density[mid_start:mid_end] < (H * 0.01)  # 1% 미만이면 거의 흰색
    # 가장 긴 연속 흰 영역 찾기
    best = (0, 0, 0)  # length, start, end
    cur_start = None
    for i, v in enumerate(in_gap):
        if v:
            if cur_start is None:
                cur_start = i
        else:
            if cur_start is not None:
                length = i - cur_start
                if length > best[0]:
                    best = (length, cur_start + mid_start, i + mid_start)
                cur_start = None
    if cur_start is not None:
        length = len(in_gap) - cur_start
        if length > best[0]:
            best = (length, cur_start + mid_start, len(in_gap) + mid_start)
    if best[0] < 5:
        return None
    gutter_left = best[1]
    gutter_right = best[2]
    # 본문 좌/우 끝(첫/마지막 잉크 x) 도 찾자
    nonzero = np.where(col_density > H * 0.01)[0]
    if len(nonzero) == 0:
        return None
    body_left = max(int(nonzero[0]) - 5, 0)
    body_right = min(int(nonzero[-1]) + 5, W - 1)
    return {
        "left_col": (body_left, gutter_left),
        "right_col": (gutter_right, body_right),
    }

def find_horizontal_gaps(col_img_gray, min_gap=GAP_MIN_HEIGHT_PX):
    """컬럼 이미지에서 가로 방향 흰 띠(문항 사이 공백) y좌표 범위 리스트 반환."""
    ink = (col_img_gray < DARK_THRESHOLD).astype(np.uint8)
    row_density = ink.sum(axis=1)
    W = col_img_gray.shape[1]
    is_blank = row_density < (W * 0.005)  # 0.5% 미만이면 비었다고 봄
    gaps = []
    cur_start = None
    for y, v in enumerate(is_blank):
        if v:
            if cur_start is None:
                cur_start = y
        else:
            if cur_start is not None:
                if (y - cur_start) >= min_gap:
                    gaps.append((cur_start, y))
                cur_start = None
    if cur_start is not None and (len(is_blank) - cur_start) >= min_gap:
        gaps.append((cur_start, len(is_blank)))
    return gaps

def crop_questions_in_column(col_img, gaps, top_offset=HEADER_FOOTER_MARGIN, bottom_offset=HEADER_FOOTER_MARGIN):
    """gap을 경계로 컬럼을 여러 문항 이미지로 자른다."""
    H = col_img.shape[0]
    # 본문 영역 = top_offset ~ H-bottom_offset
    # 본문 시작 후의 gap만 사용
    valid_gaps = [(s, e) for s, e in gaps if s > top_offset and e < H - bottom_offset]
    cuts = [top_offset]
    for s, e in valid_gaps:
        cuts.append((s + e) // 2)
    cuts.append(H - bottom_offset)
    crops = []
    for i in range(len(cuts) - 1):
        y0, y1 = cuts[i], cuts[i+1]
        if y1 - y0 < 60:  # 너무 작으면 스킵
            continue
        crops.append((y0, y1, col_img[y0:y1]))
    return crops

# 메인
doc = fitz.open(PDF_PATH)
question_index = []
qcount = 0
# 표지(1페이지) 건너뛰기, 마지막 서술형 페이지(8~9)도 일단 따로 처리
for page_no in range(1, len(doc)):  # 0=표지 제외
    page = doc[page_no]
    img = render_page(page)
    gray = to_gray(img)
    cols = detect_columns(gray)
    if not cols:
        print(f"page {page_no+1}: 컬럼 감지 실패")
        continue
    print(f"page {page_no+1}: cols={cols}")
    for col_name in ("left_col", "right_col"):
        x0, x1 = cols[col_name]
        col_img = img[:, x0:x1]
        col_gray = gray[:, x0:x1]
        gaps = find_horizontal_gaps(col_gray)
        crops = crop_questions_in_column(col_img, gaps)
        for ci, (y0, y1, crop) in enumerate(crops):
            qcount += 1
            out = OUT / f"p{page_no+1:02d}_{col_name[0]}_{ci+1}.png"
            Image.fromarray(crop).save(out)
            question_index.append({
                "file": out.name,
                "page": page_no + 1,
                "column": col_name,
                "y_range": [int(y0), int(y1)],
                "x_range": [int(x0), int(x1)],
            })
        print(f"  {col_name}: x={x0}-{x1} crops={len(crops)} gaps={len(gaps)}")
    # 디버그용: 컬럼 경계와 gap을 그린 이미지 저장
    dbg = img.copy()
    for col_name in ("left_col", "right_col"):
        x0, x1 = cols[col_name]
        dbg[:, x0:x0+2] = [255, 0, 0]
        dbg[:, x1-2:x1] = [255, 0, 0]
        col_gray = gray[:, x0:x1]
        for s, e in find_horizontal_gaps(col_gray):
            mid = (s + e) // 2
            dbg[mid:mid+2, x0:x1] = [0, 200, 0]
    Image.fromarray(dbg).save(DEBUG / f"page_{page_no+1:02d}_dbg.png")

print(f"\n총 자른 조각 수: {qcount}")
import json
with open(OUT / "index.json", "w", encoding="utf-8") as f:
    json.dump(question_index, f, ensure_ascii=False, indent=1)
