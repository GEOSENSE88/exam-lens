"""국어 원안지 PDF 구조 분석 — 단 넘어가는 문항 파악"""
import fitz, re
from pathlib import Path

PDF = r"C:\Users\이성훈\Documents\카카오톡 받은 파일\2026. 1학기 중간고사 원안지 양식(합본_재재재재수정).pdf"
doc = fitz.open(PDF)
print(f"pages: {len(doc)}")
for i,p in enumerate(doc):
    print(f"  page {i+1}: {p.rect} rot={p.rotation}")

QNUM = re.compile(r"^\s*(\d{1,2})\s*[.．]\s*$")
QNUM_INLINE = re.compile(r"^\s*(\d{1,2})\s*[.．]\s+\S")
SQ = re.compile(r"\[\s*서술형\s*문항?\s*(\d+)\s*\]")
CHOICE = re.compile(r"^[①②③④⑤]\s")
CHOICE_ANY = re.compile(r"[①②③④⑤]")

print("\n=== 각 페이지의 문항/선지 분포 ===")
for p_idx in range(min(3, len(doc))):
    page = doc[p_idx]
    p = p_idx + 1
    print(f"\n--- page {p} ---")
    text = page.get_text("dict")
    qnums = []
    choices = []
    sqs = []
    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                bbox = span["bbox"]
                size = span.get("size", 0)
                font = span.get("font", "")
                # 문항 번호
                m = QNUM.match(t) or QNUM_INLINE.match(t)
                if m and 10 <= size <= 30:
                    qnums.append({"q": int(m.group(1)), "bbox": bbox, "size": size, "text": t[:30]})
                m2 = SQ.search(t)
                if m2:
                    sqs.append({"q": m2.group(1), "bbox": bbox, "size": size, "text": t[:30]})
                # 선지 ①~⑤
                for ch in "①②③④⑤":
                    if ch in t:
                        choices.append({"ch": ch, "bbox": bbox, "size": size, "text": t[:20]})
                        break  # 같은 줄에 여러 선지 있으면 하나만
    print(f"문항 번호 {len(qnums)}개:")
    for q in qnums:
        print(f"  q{q['q']:>2} bbox=({q['bbox'][0]:6.1f},{q['bbox'][1]:6.1f}) size={q['size']:.1f}")
    print(f"서술형 {len(sqs)}개:")
    for q in sqs:
        print(f"  {q['q']:>3} bbox=({q['bbox'][0]:6.1f},{q['bbox'][1]:6.1f})")
    print(f"선지 {len(choices)}개 (앞 15개만):")
    for c in choices[:15]:
        print(f"  {c['ch']} bbox=({c['bbox'][0]:6.1f},{c['bbox'][1]:6.1f}) size={c['size']:.1f} text={c['text']!r}")
