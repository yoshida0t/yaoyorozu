import io
import sys
import argparse
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

def tex_to_image(tex,font_size):
    fig = plt.figure()
    fig.text(0, 0, f"${tex}$", fontsize=font_size)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output",  default="output.png", help="output file")
    ap.add_argument("-f", "--pngfile", help="input png")
    ap.add_argument("-t", "--text", help="text")
    ap.add_argument("--font-size", type=int, default=40, help="Fontsize of label")
    ap.add_argument("--stamp-point", default="bottom", help="place of stamp")
    args = ap.parse_args()
    
    path = Path(args.pngfile)
    
    
    
    base = Image.open(path)
    
    formula = tex_to_image(r"\text{d}_\text{xy}",args.font_size)
    formula = tex_to_image(args.text,args.font_size)
    
    if args.stamp_point=="bottom":
        bw, bh = base.size
        fw, fh = formula.size
        pos = ((bw - fw) // 2, int(bh*0.95) - fh)
    
    base.paste(formula, pos, formula)
    base.save("output.png")

if __name__ == "__main__":
    main()
