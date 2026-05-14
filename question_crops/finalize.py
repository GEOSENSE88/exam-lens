"""auto2/ 의 30개 조각을 문항 번호 순으로 정리해 final/ 에 저장 + index.json"""
import json, shutil
from pathlib import Path
from PIL import Image

SRC = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\auto2")
FINAL = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\final")
FINAL.mkdir(parents=True, exist_ok=True)

# 페이지 좌→우, 위→아래 순서대로 객관식 1~22 + 서술형 1~8
mapping = [
    # (객관식 번호, 원본 파일)
    ("Q01", "p02_l_1.png"),
    ("Q02", "p02_l_2.png"),
    ("Q03", "p02_r_1.png"),
    ("Q04", "p02_r_2.png"),
    ("Q05", "p03_l_1.png"),
    ("Q06", "p03_l_2.png"),
    ("Q07", "p03_r_1.png"),
    ("Q08", "p03_r_2.png"),
    ("Q09", "p04_l_1.png"),
    ("Q10", "p04_r_1.png"),
    ("Q11", "p04_r_2.png"),
    ("Q12", "p05_l_1.png"),
    ("Q13", "p05_l_2.png"),
    ("Q14", "p05_r_1.png"),
    ("Q15", "p05_r_2.png"),
    ("Q16", "p06_l_1.png"),
    ("Q17", "p06_l_2.png"),
    ("Q18", "p06_r_1.png"),
    ("Q19", "p06_r_2.png"),
    ("Q20", "p07_l_1.png"),
    ("Q21", "p07_l_2.png"),
    ("Q22", "p07_r_1.png"),
    # 서술형 (S = 서술형)
    ("S01", "p08_l_1.png"),
    ("S02", "p08_l_2.png"),
    ("S03", "p08_l_3.png"),
    ("S04", "p08_r_1.png"),
    ("S05", "p08_r_2.png"),
    ("S06", "p09_l_1.png"),
    ("S07", "p09_l_2.png"),
    ("S08", "p09_r_1.png"),
]

index = []
for qid, src_name in mapping:
    src = SRC / src_name
    if not src.exists():
        print(f"❌ 누락: {src_name}")
        continue
    dst = FINAL / f"{qid}.png"
    shutil.copyfile(src, dst)
    im = Image.open(dst)
    index.append({"id": qid, "file": dst.name, "size": im.size, "src": src_name})
    print(f"  {qid} ← {src_name}  ({im.size[0]}x{im.size[1]})")

with open(FINAL / "index.json", "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=1)

print(f"\n총 {len(index)}개 문항이 final/ 에 저장됨")
