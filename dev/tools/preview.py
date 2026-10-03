"""Render a .pptx to a grid preview.jpg (dev only): soffice -> pdf -> pdftoppm -> PIL grid."""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

def preview(pptx, out=None, cols=3, width=640):
    pptx = Path(pptx); out = Path(out or pptx.with_suffix(".preview.jpg"))
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", td, str(pptx)],
                       check=True, capture_output=True, timeout=180)
        pdf = Path(td) / (pptx.stem + ".pdf")
        subprocess.run(["pdftoppm", "-jpeg", "-r", "60", str(pdf), str(Path(td) / "p")], check=True)
        imgs = [Image.open(p) for p in sorted(Path(td).glob("p-*.jpg"), key=lambda p: int(p.stem.split("-")[1]))]
        imgs = [i.resize((width, int(i.height * width / i.width))) for i in imgs]
        h = imgs[0].height; rows = -(-len(imgs) // cols)
        grid = Image.new("RGB", (cols * width + (cols + 1) * 8, rows * h + (rows + 1) * 8), "#9aa0a6")
        for n, im in enumerate(imgs):
            grid.paste(im, (8 + (n % cols) * (width + 8), 8 + (n // cols) * (h + 8)))
        grid.save(out, quality=82)
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(preview(p))
