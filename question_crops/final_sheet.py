"""final/ 안의 30개 문항을 6열 그리드로 한 장에 모음 (검수용)"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

SRC = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\final")
OUT = SRC.parent / "final_contact.png"

with open(SRC / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

THUMB_W = 360
COLS = 6
PAD = 10
LABEL_H = 26

thumbs = []
for e in idx:
    im = Image.open(SRC / e["file"])
    r = THUMB_W / im.width
    im = im.resize((THUMB_W, int(im.height * r)))
    thumbs.append((e["id"], im))

rows = (len(thumbs) + COLS - 1) // COLS
row_heights = []
for r in range(rows):
    rh = max(im.height for _, im in thumbs[r*COLS:(r+1)*COLS])
    row_heights.append(rh + LABEL_H + PAD)
total_h = sum(row_heights) + PAD
total_w = COLS * (THUMB_W + PAD) + PAD

sheet = Image.new("RGB", (total_w, total_h), (245, 245, 245))
draw = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("malgunbd.ttf", 18)
except: font = ImageFont.load_default()

y = PAD
for r in range(rows):
    x = PAD
    for c in range(COLS):
        i = r * COLS + c
        if i >= len(thumbs): break
        qid, im = thumbs[i]
        draw.rectangle([x-2, y-2, x+THUMB_W+1, y+LABEL_H+im.height+1], outline=(150,150,150), width=1)
        draw.text((x+4, y+3), qid, fill=(180, 0, 0), font=font)
        sheet.paste(im, (x, y + LABEL_H))
        x += THUMB_W + PAD
    y += row_heights[r]

sheet.save(OUT)
print(f"saved {OUT} ({sheet.size[0]}x{sheet.size[1]})")
