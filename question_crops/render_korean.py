"""국어 원안지 PDF를 PNG로 렌더링"""
import fitz
from pathlib import Path
PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test_korean.pdf"
import shutil
SRC = r"C:\Users\이성훈\Documents\카카오톡 받은 파일\2026. 1학기 중간고사 원안지 양식(합본_재재재재수정).pdf"
shutil.copy(SRC, PDF)
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\korean_pages")
OUT.mkdir(parents=True, exist_ok=True)
doc = fitz.open(PDF)
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
    out = OUT / f"p{i+1:02d}.png"
    pix.save(str(out))
    print(f"saved {out.name} {pix.width}x{pix.height}")
