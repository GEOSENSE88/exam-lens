"""PDF 9페이지를 고해상도 PNG로 렌더링 (먼저 어떻게 생겼는지 확인용)"""
import fitz
from pathlib import Path

PDF_PATH = r"D:\03. 담당 업무\평가 관련\2026-1학기 1차지필평가\[04]2026. 1학기 중간고사 원안지(3학년 한국지리)(260415).pdf"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\pages")
OUT.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF_PATH)
ZOOM = 2.0  # 144 DPI 정도 (미리보기용)
mat = fitz.Matrix(ZOOM, ZOOM)
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=mat, alpha=False)
    out = OUT / f"page_{i+1:02d}.png"
    pix.save(str(out))
    print(f"saved {out.name} ({pix.width}x{pix.height})")
