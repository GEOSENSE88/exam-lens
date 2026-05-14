"""산남고 booklet PDF에 텍스트 레이어가 있는지 + 문항 번호가 추출되는지 확인"""
import fitz
import re

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test.pdf"
doc = fitz.open(PDF)

print(f"=== {len(doc)}페이지 PDF ===")
QNUM_RE = re.compile(r"^\s*(\d{1,2})\s*\.\s*")
SQ_RE = re.compile(r"\[\s*서술형\s*문항?\s*(\d+)\s*\]")

for p_idx, page in enumerate(doc):
    p = p_idx + 1
    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])
    text_blocks = [b for b in blocks if b.get("type") == 0]
    img_blocks = [b for b in blocks if b.get("type") == 1]
    total_chars = 0
    qnum_candidates = []
    for b in text_blocks:
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                total_chars += len(t)
                # 문항 번호 후보
                m = QNUM_RE.match(t.strip())
                if m and 1 <= int(m.group(1)) <= 30:
                    qnum_candidates.append({
                        "qno": int(m.group(1)),
                        "bbox": span["bbox"],
                        "size": span.get("size", 0),
                        "text": t[:40]
                    })
                m2 = SQ_RE.search(t)
                if m2:
                    qnum_candidates.append({
                        "qno": "S"+m2.group(1),
                        "bbox": span["bbox"],
                        "size": span.get("size", 0),
                        "text": t[:40]
                    })
    print(f"\n--- page {p}: {len(text_blocks)} text blocks · {len(img_blocks)} img blocks · {total_chars} chars ---")
    print(f"문항번호 후보 {len(qnum_candidates)}개:")
    for c in qnum_candidates[:30]:
        bbox = c["bbox"]
        print(f"  q={c['qno']:>3} bbox=({bbox[0]:6.1f},{bbox[1]:6.1f})-({bbox[2]:6.1f},{bbox[3]:6.1f}) size={c['size']:.1f} text={c['text']!r}")
