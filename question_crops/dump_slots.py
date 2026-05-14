"""각 슬롯을 PNG로 떼어서 어떤 원본 페이지인지 시각 확인"""
import fitz, numpy as np
from PIL import Image
from pathlib import Path
import sys, importlib.util
spec = importlib.util.spec_from_file_location("vb", r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\verify_booklet.py")
vb = importlib.util.module_from_spec(spec); spec.loader.exec_module(vb)

PDF = r"C:\Users\이성훈\OneDrive\Exam_lens\test.pdf"
OUT = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\slots")
OUT.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
ZOOM = 1500 / min(doc[0].rect.width, doc[0].rect.height)
slots_img = []
for p_idx, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
    gray = vb.to_gray(pix)
    H, W = gray.shape
    img_full = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:,:,:3]
    p = p_idx + 1
    vpages = vb.decompose(gray, p, len(doc))
    for vp in vpages:
        if vp["isCover"]: continue
        sub_img = img_full[:, vp["x0"]:vp["x1"]]
        # 잉크 검사
        sub_gray = gray[int(H*0.05):int(H*0.95), vp["x0"]:vp["x1"]]
        if (sub_gray < 200).sum() / sub_gray.size < 0.005: continue
        slots_img.append((vp["slot"], sub_img))

slots_img.sort(key=lambda t: t[0])
for slot, img in slots_img:
    Image.fromarray(img).save(OUT / f"slot_{slot:02d}.png")
print(f"저장한 슬롯: {[s for s,_ in slots_img]}")
