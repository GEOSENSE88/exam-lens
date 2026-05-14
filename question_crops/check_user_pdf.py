"""사용자 원본 PDF에서 서술형 검출이 왜 실패하는지 진단"""
import fitz, re

PDF = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(260415).pdf"
doc = fitz.open(PDF)
print(f"=== {len(doc)}페이지 PDF ===")

# 검색: 서술형 관련 모든 텍스트
patterns_to_check = [
    r"서술형",
    r"서답형",
    r"\[",
    r"\]",
]

for p_idx, page in enumerate(doc):
    p = p_idx + 1
    print(f"\n--- page {p} ---")
    text_dict = page.get_text("dict")
    found_serv = []
    found_brackets = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                bbox = span["bbox"]
                if "서술" in t or "서답" in t:
                    found_serv.append({
                        "text": t,
                        "bbox": bbox,
                        "size": span.get("size", 0),
                        "font": span.get("font", ""),
                    })
                if "[" in t or "]" in t:
                    found_brackets.append({
                        "text": t,
                        "bbox": bbox,
                        "size": span.get("size", 0),
                    })
    if found_serv:
        print(f"  '서술/서답' 포함 텍스트 {len(found_serv)}개:")
        for s in found_serv[:20]:
            b = s["bbox"]
            print(f"    text={s['text']!r:40} bbox=({b[0]:6.1f},{b[1]:6.1f}) size={s['size']:.1f} font={s['font']}")
    if found_brackets:
        print(f"  '[' or ']' 포함 텍스트 {len(found_brackets)}개:")
        for s in found_brackets[:10]:
            b = s["bbox"]
            print(f"    text={s['text']!r:40} bbox=({b[0]:6.1f},{b[1]:6.1f}) size={s['size']:.1f}")
