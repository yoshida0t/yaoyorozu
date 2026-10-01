from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

__all__ = ["Molecule"]


@dataclass(eq=False)  # ndarray を含むので == の自動生成は無効化(比較は同一性)
class Molecule:
    """原子の元素記号と直交座標をまとめて持つデータ型。

    coord の単位は Å。
    """

    atoms: list[str]
    coord: np.ndarray  # shape (N, 3), dtype float, 単位 Å

    def __post_init__(self) -> None:
        coord = np.asarray(self.coord, dtype=float)

        if coord.ndim != 2 or coord.shape[1] != 3:
            raise ValueError(f"coords must be (N,3), got {coord.shape}")

        if len(self.atoms) != len(coord):
            raise ValueError(
                f"Atom/coord mismatch: {len(self.atoms)} vs {len(coord)}"
            )

        # 呼び出し側の配列・リストと共有しないようコピーして保持
        self.coord = coord.copy()
        self.atoms = list(self.atoms)

    @classmethod
    def from_xyz(cls, file_path: str | Path, *, strict: bool = True) -> Molecule:
        """XYZ ファイルを読んで Molecule を作る(read_xyz の薄いラッパー)。"""
        # core は io に依存しない方針なので、呼び出し時にだけ import する
        from ..io.xyz import read_xyz

        return read_xyz(file_path, strict=strict)
