"""HWPX 본문에서 문항 텍스트 추출"""
import zipfile
import re
from xml.etree import ElementTree as ET
from pathlib import Path

HWPX = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(공개용).hwpx"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops")

with zipfile.ZipFile(HWPX) as z:
    sec1 = z.read("Contents/section1.xml").decode("utf-8")

# namespace 정리: hp:t 가 본문 텍스트 태그 (HWPX 표준)
# 단순화 — 모든 <hp:t> 콘텐츠를 순서대로 추출
NS = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
root = ET.fromstring(sec1)

# 모든 텍스트를 paragraph 단위로 모음
paragraphs = []
for p in root.iter(f"{NS}p"):
    parts = []
    for t in p.iter(f"{NS}t"):
        if t.text:
            parts.append(t.text)
    paragraphs.append("".join(parts))

# 비어있지 않은 paragraph만 출력
non_empty = [p for p in paragraphs if p.strip()]
print(f"전체 paragraph: {len(paragraphs)}, 비어있지 않은 것: {len(non_empty)}")

# 문항 번호 패턴 찾기
QNUM = re.compile(r"^\s*(\d{1,2})\s*[.．]")
qstarts = []
for i, p in enumerate(paragraphs):
    m = QNUM.match(p)
    if m:
        qstarts.append((i, int(m.group(1)), p[:80]))

print(f"\n문항 번호 후보: {len(qstarts)}")
for i, n, txt in qstarts:
    print(f"  para#{i:>4} q={n:>2} : {txt}")

# 전체 텍스트도 저장
with open(OUT / "section1_text.txt", "w", encoding="utf-8") as f:
    for i, p in enumerate(paragraphs):
        f.write(f"[{i:>4}] {p}\n")
