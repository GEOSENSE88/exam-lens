"""합본 PDF — 각 페이지 첫 50자 + footer 쪽번호 + 문항 후보"""
import fitz, re, sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = r"C:\Users\이성훈\Documents\카카오톡 받은 파일\2026. 1학기 중간고사 원안지 양식(합본_재재재재수정) (1).pdf"
DST = r"C:\Users\이성훈\OneDrive\Exam_lens\test_combined.pdf"
shutil.copy(SRC, DST)
doc = fitz.open(DST)
print(f"pages: {len(doc)} rect={doc[0].rect}")

PNUM = re.compile(r"\(\s*(\d+)\s*\)\s*쪽")
QNUM_PATS = [re.compile(r"^\s*(\d{1,2})\s*\.\s+\S"), re.compile(r"^\s*(\d{1,2})\s*\.\s*[가-힣]")]

for p_idx in range(len(doc)):
    page = doc[p_idx]
    p = p_idx + 1
    W, H = page.rect.width, page.rect.height
    text = page.get_text("dict")

    all_spans = []
    footer_items = []
    qcandidates = []

    for block in text.get("blocks", []):
        if block.get("type") != 0: continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                if not t.strip(): continue
                bbox = span["bbox"]
                sz = span.get("size", 0)
                all_spans.append((bbox[0], bbox[1], sz, t))
                if bbox[1] >= H * 0.85:
                    footer_items.append((bbox[0], bbox[1], sz, t))
                # Question number candidates
                for pat in QNUM_PATS:
                    m = pat.match(t.strip())
                    if m:
                        qcandidates.append((bbox[0], bbox[1], sz, m.group(1), t.strip()[:30]))
                        break

    pnums = []
    for x,y,sz,t in footer_items:
        for m in PNUM.finditer(t):
            pnums.append((x, m.group(1)))

    sample = ' | '.join(s[3][:20] for s in all_spans[:5])
    print(f"\n=== p{p} (W={W:.0f} H={H:.0f}) — spans={len(all_spans)} ===")
    print(f"  첫 spans: {sample}")
    if pnums:
        print(f"  쪽번호: {pnums}")
    if qcandidates:
        print(f"  문항후보 ({len(qcandidates)}):")
        for x,y,sz,q,t in qcandidates[:8]:
            print(f"    q{q:>3} x={x:6.1f} y={y:6.1f} sz={sz:5.2f} {t!r}")
