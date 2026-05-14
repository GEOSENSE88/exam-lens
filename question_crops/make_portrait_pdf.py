from PIL import Image
from pathlib import Path
src = Path(r"C:\Users\이성훈\OneDrive\Exam_lens\question_crops\pages")
imgs = []
for i in range(1, 10):
    p = src / f"page_{i:02d}.png"
    if p.exists():
        imgs.append(Image.open(p).convert("RGB"))
imgs[0].save(r"C:\Users\이성훈\OneDrive\Exam_lens\test_portrait.pdf", save_all=True, append_images=imgs[1:])
print(f"saved test_portrait.pdf with {len(imgs)} pages")
