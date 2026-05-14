import fitz
from pathlib import Path
doc = fitz.open(r"C:\Users\이성훈\OneDrive\Exam_lens\test.pdf")
out = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\test_pdf_pages")
out.mkdir(parents=True, exist_ok=True)
for i, p in enumerate(doc):
    pix = p.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    pix.save(str(out / f"p{i+1}.png"))
    print(f"p{i+1}: {pix.width}x{pix.height}")
