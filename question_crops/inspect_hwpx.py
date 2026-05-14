"""HWPX 구조 살펴보기 — 문항 번호 위치 정보가 추출 가능한지"""
import zipfile
from pathlib import Path

HWPX = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(공개용).hwpx"

with zipfile.ZipFile(HWPX) as z:
    names = z.namelist()
    print(f"파일 수: {len(names)}")
    for n in names[:50]:
        info = z.getinfo(n)
        print(f"  {info.file_size:>10}  {n}")
    print("...")
    # section 파일이 본문
    sections = [n for n in names if n.startswith("Contents/section")]
    print(f"\nsection 수: {len(sections)}")
    for s in sections:
        print(f"  {s}")
