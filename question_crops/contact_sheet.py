"""29개 조각을 한 장의 컨택트 시트로 모아서 검수"""
from PIL import Image
from pathlib import Path
import json

SRC = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\auto2")
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\contact.png")

with open(SRC / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

THUMB_W = 320
imgs = []
for entry in idx:
    p = SRC / entry["file"]
    im = Image.open(p)
    ratio = THUMB_W / im.width
    new_h = int(im.height * ratio)
    im = im.resize((THUMB_W, new_h))
    imgs.append((entry["file"], im))

# 5열 그리드
COLS = 5
PAD = 8
LABEL_H = 22
rows = (len(imgs) + COLS - 1) // COLS
# 각 행 높이는 그 행의 최대 height
row_heights = []
for r in range(rows):
    rh = max(im.height for _, im in imgs[r*COLS:(r+1)*COLS])
    row_heights.append(rh + LABEL_H + PAD)
total_h = sum(row_heights) + PAD
total_w = COLS * (THUMB_W + PAD) + PAD
sheet = Image.new("RGB", (total_w, total_h), (255, 255, 255))
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("malgun.ttf", 14)
except:
    font = ImageFont.load_default()

y_cursor = PAD
for r in range(rows):
    x_cursor = PAD
    for c in range(COLS):
        i = r * COLS + c
        if i >= len(imgs): break
        name, im = imgs[i]
        draw.text((x_cursor, y_cursor), name, fill=(0,0,0), font=font)
        sheet.paste(im, (x_cursor, y_cursor + LABEL_H))
        x_cursor += THUMB_W + PAD
    y_cursor += row_heights[r]

sheet.save(OUT)
print(f"saved {OUT}  ({sheet.size})")
