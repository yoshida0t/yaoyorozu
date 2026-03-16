#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
複数PNGを読み込み、各画像に対応するパス文字列を描画し、横4枚でタイル結合して1枚にマージする。

使い方例:
  python merge_pngs_with_path.py "images/**/*.png" -o merged.png
  python merge_pngs_with_path.py img1.png img2.png img3.png -o out.png --resize-mode fit --cell-w 512 --cell-h 512
"""

from __future__ import annotations

import argparse
import glob
import math
import os
from pathlib import Path
from typing import Iterable, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from natsort import natsorted
from pathlib import Path




defalut_font_path=Path(__file__).resolve().parent / "Arial.ttf"



def collect_paths(inputs: List[str], recursive: bool = True) -> List[Path]:
    paths: List[Path] = []
    for s in inputs:
        # glob を含む場合
        if any(ch in s for ch in ["*", "?", "["]):
            for p in glob.glob(s, recursive=recursive):
                paths.append(Path(p))
        else:
            paths.append(Path(s))
    # 存在＆pngのみ
    out = []
    for p in paths:
        if p.is_file() and p.suffix.lower() == ".png":
            out.append(p)
    # 重複除去（順序維持）
    seen = set()
    uniq = []
    for p in out:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def shorten_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3] + "..."


def load_font(font_path: str | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path:
        return ImageFont.truetype(font_path, font_size)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", font_size)
    except Exception:
        return ImageFont.load_default()


#def draw_path_label(
#    im: Image.Image,
#    label: str,
#    font: ImageFont.ImageFont,
#    padding: int = 8,
#    bg_alpha: int = 160,
#    text_fill: Tuple[int, int, int, int] = (255, 255, 255, 255),
#) -> Image.Image:
#    # RGBAにして描画
#    if im.mode != "RGBA":
#        im = im.convert("RGBA")
#
#    draw = ImageDraw.Draw(im)
#    # テキストサイズ測定
#    bbox = draw.textbbox((0, 0), label, font=font)
#    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
#
#    # 背景矩形（左上固定）
#    x0, y0 = padding, padding
#    x1, y1 = x0 + tw + padding * 2, y0 + th + padding * 2
#
#    # 背景（半透明黒）
#    bg = Image.new("RGBA", im.size, (0, 0, 0, 0))
#    bg_draw = ImageDraw.Draw(bg)
#    bg_draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, bg_alpha))
#
#    im = Image.alpha_composite(im, bg)
#    draw = ImageDraw.Draw(im)
#    draw.text((x0 + padding, y0 + padding), label, font=font, fill=text_fill)
#    return im

def draw_path_label(
    im,
    label,
    font,
    padding=8,
    text_fill=(0, 0, 0, 255),
):
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    draw = ImageDraw.Draw(im)

    # テキストサイズ測定
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = padding
    y = padding

    # 背景は描かない
    draw.text((x, y), label, font=font, fill=text_fill)

    return im


def fit_to_cell(im: Image.Image, cell_w: int, cell_h: int, mode: str) -> Image.Image:
    """
    mode:
      - "none": 元サイズのまま（セルサイズ指定は無視に近い。後段で最大値に合わせる）
      - "fit": アスペクト維持して枠内に収める（余白あり）
      - "pad": fitと同じだが、余白込みで必ずcellサイズにする
      - "stretch": 縦横をcellに合わせて変形（非推奨）
    """
    if mode == "none":
        return im

    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")

    if mode == "stretch":
        return im.resize((cell_w, cell_h), Image.LANCZOS)

    # fit / pad
    w, h = im.size
    scale = min(cell_w / w, cell_h / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    rim = im.resize((nw, nh), Image.LANCZOS)

    if mode == "fit":
        return rim

    # pad: cellサイズにキャンバス作って中央配置
    canvas = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    ox = (cell_w - nw) // 2
    oy = (cell_h - nh) // 2
    canvas.paste(rim, (ox, oy), rim if rim.mode == "RGBA" else None)
    return canvas


def merge_images_grid(
    images: List[Image.Image],
    cols: int = 4,
    gap: int = 8,
    bg_color: Tuple[int, int, int, int] = (30, 30, 30, 255),
    force_cell: Tuple[int, int] | None = None,
) -> Image.Image:
    if not images:
        raise ValueError("画像が0枚です。")

    cols = max(1, cols)
    rows = math.ceil(len(images) / cols)

    # セルサイズ決定
    if force_cell is not None:
        cell_w, cell_h = force_cell
    else:
        cell_w = max(im.size[0] for im in images)
        cell_h = max(im.size[1] for im in images)

    out_w = cols * cell_w + (cols - 1) * gap
    out_h = rows * cell_h + (rows - 1) * gap

    out = Image.new("RGBA", (out_w, out_h), bg_color)

    for idx, im in enumerate(images):
        r = idx // cols
        c = idx % cols
        x = c * (cell_w + gap)
        y = r * (cell_h + gap)

        # force_cellがない場合でも、セル内に中央寄せしたいのでここでパディング
        if im.mode != "RGBA":
            im_rgba = im.convert("RGBA")
        else:
            im_rgba = im

        if force_cell is None:
            # セル内中央配置
            tmp = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
            ox = (cell_w - im_rgba.size[0]) // 2
            oy = (cell_h - im_rgba.size[1]) // 2
            tmp.paste(im_rgba, (ox, oy), im_rgba)
            out.paste(tmp, (x, y), tmp)
        else:
            out.paste(im_rgba, (x, y), im_rgba)

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="pngファイル or glob（例: images/**/*.png）")
    ap.add_argument("-o", "--output", default="merged.png", help="出力ファイル名")
    ap.add_argument("--cols", type=int, default=4, help="横方向の最大枚数（デフォルト4）")
    ap.add_argument("--gap", type=int, default=8, help="画像間の余白px")
    ap.add_argument("--font-path", default=defalut_font_path, help="ttf/otfフォントへのパス（任意）")
    ap.add_argument("--font-size", type=int, default=18, help="ラベル文字サイズ")
    ap.add_argument("--max-label-chars", type=int, default=120, help="ラベルの最大文字数（長すぎる場合は省略）")
    ap.add_argument("--label", default="name", help="ラベル")
    ap.add_argument("--label-mode", choices=["abs", "rel", "name"], default="rel",
                    help="描画するパス: abs=絶対, rel=カレントからの相対, name=ファイル名のみ")
    ap.add_argument("--resize-mode", choices=["none", "fit", "pad", "stretch"], default="pad",
                    help="セルに合わせる方法: none/fit/pad/stretch（デフォルトpad）")
    ap.add_argument("--cell-w", type=int, default=512, help="セル幅（resize-modeがnone以外で有効）")
    ap.add_argument("--cell-h", type=int, default=512, help="セル高さ（resize-modeがnone以外で有効）")
    args = ap.parse_args()

    paths = collect_paths(args.inputs, recursive=True)
    if not paths:
        raise SystemExit("PNGが見つかりませんでした。入力パスやglobを確認してください。")

    font = load_font(args.font_path, args.font_size)

    processed: List[Image.Image] = []
    cwd = Path.cwd()
    
    paths = natsorted(paths)
    for p in paths:
        im = Image.open(p)

        label = p.name
        #label = label.split('.')[1]+label.split('.')[2] 
        if args.label=="name":
            label = label.split('.')[1]+label.split('.')[2]
        else:
            label = args.label
        label = shorten_text(label, args.max_label_chars)

        # 先にリサイズ（padならここでセルサイズ固定になる）→ その上にラベル描画（見やすい）
        if args.resize_mode != "none":
            im = fit_to_cell(im, args.cell_w, args.cell_h, args.resize_mode)

        im = draw_path_label(im, label, font=font)
        processed.append(im)

    force_cell = None
    if args.resize_mode != "none":
        force_cell = (args.cell_w, args.cell_h)

    merged = merge_images_grid(
        processed,
        cols=max(1, args.cols),
        gap=max(0, args.gap),
        force_cell=force_cell,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # PNGで保存（透過保持）
    merged.save(out_path, format="PNG")
    print(f"Saved: {out_path} ({merged.size[0]}x{merged.size[1]})  count={len(paths)}")


if __name__ == "__main__":
    main()
