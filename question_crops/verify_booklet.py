"""HTML과 동일한 알고리즘을 Python에서 재현하여 test.pdf에 대해 어떤 슬롯·컬럼이 나오는지 출력"""
import fitz, numpy as np
from pathlib import Path

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test.pdf"
DARK = 200

def to_gray(pix):
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n >= 3:
        gray = (0.299*img[...,0] + 0.587*img[...,1] + 0.114*img[...,2]).astype(np.uint8)
    else:
        gray = img[...,0]
    return gray

def longest_white_vertical_gap(gray, x_start, x_end):
    H, W = gray.shape
    ink_thresh = H * 0.01
    col_density = (gray[:, x_start:x_end] < DARK).sum(axis=0)
    best_len, best_s, best_e = 0, 0, 0
    cur = -1
    for i, d in enumerate(col_density):
        if d < ink_thresh:
            if cur < 0: cur = i
        else:
            if cur >= 0:
                ln = i - cur
                if ln > best_len: best_len, best_s, best_e = ln, cur, i
                cur = -1
    if cur >= 0:
        ln = len(col_density) - cur
        if ln > best_len: best_len, best_s, best_e = ln, cur, len(col_density)
    return {"len":best_len, "s":best_s+x_start, "e":best_e+x_start}

def body_edges(gray, x_start, x_end):
    H = gray.shape[0]
    ink_thresh = round(H * 0.05)
    col_density = (gray[:, x_start:x_end] < DARK).sum(axis=0)
    nz = np.where(col_density > ink_thresh)[0]
    if len(nz) == 0: return None
    return [max(int(nz[0]) + x_start - 5, x_start), min(int(nz[-1]) + x_start + 5, x_end - 1)]

def booklet_slots(page_num, total):
    N = total
    if page_num % 2 == 1:
        return {"left": 2*N - page_num + 1, "right": page_num}
    else:
        return {"left": page_num, "right": 2*N - page_num + 1}

def decompose(gray, page_num, total):
    H, W = gray.shape
    is_landscape = W > H
    if not is_landscape:
        return [{"slot": page_num, "x0":0, "x1":W, "isCover": page_num==1}]
    half_s, half_e = int(W*0.40), int(W*0.60)
    cg = longest_white_vertical_gap(gray, half_s, half_e)
    if cg["len"] < 20:
        return [{"slot": page_num, "x0":0, "x1":W, "isCover": page_num==1}]
    slots = booklet_slots(page_num, total)
    out = []
    le = body_edges(gray, 0, cg["s"])
    if le:
        out.append({"slot": slots["left"], "x0":le[0], "x1":le[1], "isCover": slots["left"]==1})
    re = body_edges(gray, cg["e"], W)
    if re:
        out.append({"slot": slots["right"], "x0":re[0], "x1":re[1], "isCover": slots["right"]==1})
    return out

doc = fitz.open(PDF)
print(f"PDF pages: {len(doc)}")
ZOOM = 1500 / min(doc[0].rect.width, doc[0].rect.height)
print(f"zoom: {ZOOM:.2f}")

all_vpages = []
for p_idx, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
    gray = to_gray(pix)
    H, W = gray.shape
    p = p_idx + 1
    print(f"\n=== p{p} W={W} H={H} ===")
    vpages = decompose(gray, p, len(doc))
    for vp in vpages:
        # ink check
        col_w = vp["x1"] - vp["x0"]
        # 잉크량을 가상페이지 안에서 측정
        sub = gray[int(H*0.05):int(H*0.95), vp["x0"]:vp["x1"]]
        ink_count = int((sub < DARK).sum())
        ink_ratio = ink_count / sub.size
        skip_reason = ""
        if vp["isCover"]: skip_reason = "COVER"
        elif ink_ratio < 0.005: skip_reason = "EMPTY"
        print(f"  vp slot={vp['slot']:>2} x=[{vp['x0']},{vp['x1']}] ink_ratio={ink_ratio:.4f} {'SKIP:'+skip_reason if skip_reason else 'KEEP'}")
        if not skip_reason:
            all_vpages.append(vp)

# 정렬
all_vpages.sort(key=lambda v: v["slot"])
print(f"\n=== 처리할 슬롯 순서 (booklet 디코딩 후) ===")
for vp in all_vpages:
    print(f"  slot {vp['slot']}: x={vp['x0']}-{vp['x1']}")
