"""p06_r_1.png 안의 18, 19를 쪼개기.
   - 컬럼 전체 폭에서 행별 잉크 밀도를 본 뒤
   - 본문 영역에서 가장 큰 빈 띠(즉 단락 간 공백 중 가장 큰 것)를 경계로 사용
"""
import numpy as np
from PIL import Image
from pathlib import Path

P = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\auto2\p06_r_1.png")
OUT = P.parent

img = np.array(Image.open(P).convert("RGB"))
gray = (0.299*img[...,0] + 0.587*img[...,1] + 0.114*img[...,2]).astype(np.uint8)
H, W = gray.shape
ink = (gray < 200).astype(np.uint8)
row_density = ink.sum(axis=1)
is_blank = row_density < (W * 0.005)

# 행 단위 빈 띠 찾기
gaps = []
cur = None
for y in range(H):
    if is_blank[y]:
        if cur is None: cur = y
    else:
        if cur is not None:
            gaps.append((cur, y, y - cur))
            cur = None
if cur is not None:
    gaps.append((cur, H, H - cur))

# 위/아래 너무 가까운 가장자리 빈 영역은 제외 (페이지 위/아래 여백)
inner = [g for g in gaps if 100 < g[0] and g[1] < H - 100]
inner.sort(key=lambda g: -g[2])
print("Top 10 inner gaps (start, end, height):")
for g in inner[:10]:
    print(f"  y={g[0]:4d}-{g[1]:4d}  h={g[2]}")

if not inner:
    print("내부 빈 띠 없음 — 분할 불가")
else:
    s, e, _ = inner[0]
    cut = (s + e) // 2
    Image.fromarray(img[:cut]).save(OUT / "p06_r_1.png")  # Q18로 갈음
    Image.fromarray(img[cut:]).save(OUT / "p06_r_2.png")  # Q19
    print(f"분할 완료: cut y={cut}  (위 {cut}px, 아래 {H-cut}px)")
