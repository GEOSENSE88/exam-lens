"""문항 번호 위치 자동 탐지 - JSON으로 저장"""
import fitz
import re
import json
from pathlib import Path

PDF_PATH = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(260415).pdf"
OUT_DIR = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops")

doc = fitz.open(PDF_PATH)

# 모든 페이지의 텍스트 span(글자 단위 박스) 수집
# span: 동일한 폰트/크기로 연결된 글자 묶음
all_data = []
for page_no, page in enumerate(doc):
    page_data = {
        "page": page_no + 1,
        "width": page.rect.width,
        "height": page.rect.height,
        "spans": []
    }
    d = page.get_text("dict")
    for block in d["blocks"]:
        if block.get("type", 0) != 0:  # text only
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                page_data["spans"].append({
                    "text": span["text"],
                    "bbox": span["bbox"],  # x0,y0,x1,y1
                    "font": span.get("font", ""),
                    "size": span.get("size", 0),
                    "flags": span.get("flags", 0),
                })
    all_data.append(page_data)

with open(OUT_DIR / "spans.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=1)

# 문항 번호 후보 탐지 — "1.", "2.", ..., "20.", "[1]", "[1번]" 등
# 한국지리 시험은 보통 객관식 1~20번 + 서술형
QNUM_RE = re.compile(r"^\s*([0-9]{1,2})\s*[.．]\s*$")
QNUM_RE2 = re.compile(r"^\s*\[\s*([0-9]{1,2})\s*\]")

candidates = []
for pd in all_data:
    for sp in pd["spans"]:
        t = sp["text"].strip()
        m = QNUM_RE.match(t) or QNUM_RE2.match(t)
        if m:
            candidates.append({
                "page": pd["page"],
                "qnum": int(m.group(1)),
                "bbox": sp["bbox"],
                "text": sp["text"],
                "font": sp["font"],
                "size": sp["size"],
            })

with open(OUT_DIR / "qnum_candidates.json", "w", encoding="utf-8") as f:
    json.dump(candidates, f, ensure_ascii=False, indent=1)

print(f"pages={len(doc)}")
print(f"total spans={sum(len(p['spans']) for p in all_data)}")
print(f"qnum candidates={len(candidates)}")
for c in candidates[:60]:
    print(f"  p{c['page']} q{c['qnum']:>2} bbox=({c['bbox'][0]:.1f},{c['bbox'][1]:.1f})-({c['bbox'][2]:.1f},{c['bbox'][3]:.1f}) font={c['font']} size={c['size']:.1f}")
