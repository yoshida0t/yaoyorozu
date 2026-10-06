"""直交座標の数値微分(中心差分)のための変位構造の生成と命名ルール。

変位構造ごとの勾配を差分すれば Hessian、双極子モーメントを差分すれば
双極子微分が得られる。ここでは微分する量に依存しない部分を扱う。

命名ルール
----------
座標インデックス i(1始まり, 4桁ゼロ埋め)は直交座標に次のように対応する。

    i = 3 * atom + axis + 1      (atom, axis は 0 始まり, axis: 0=x, 1=y, 2=z)

    0001, 0002, 0003 -> 原子1 の x, y, z
    0004, 0005, 0006 -> 原子2 の x, y, z

ファイル名(拡張子なし)は

    {prefix}_0000        参照構造(変位なし)
    {prefix}_{i:04d}_p   座標 i を +step だけ変位
    {prefix}_{i:04d}_m   座標 i を -step だけ変位

このルールは displacement_name / parse_displacement_name の対で定義し、
生成側と回収側の両方がこの2関数を使うこと。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .core.molecule import Molecule
from .core.units import BOHR_TO_ANG

__all__ = [
    "Displacement",
    "make_displacements",
    "displacement_name",
    "parse_displacement_name",
    "index_from_coordinate",
    "coordinate_from_index",
]

_WIDTH = 4
_MAX_INDEX = 10**_WIDTH - 1
_SIGN_TO_SUFFIX = {1: "p", -1: "m"}
_SUFFIX_TO_SIGN = {"p": 1, "m": -1}
_NAME_RE = re.compile(rf"^(?P<prefix>.+)_(?P<index>\d{{{_WIDTH}}})(?:_(?P<sign>[pm]))?$")


@dataclass(eq=False)
class Displacement:
    """変位構造 1 つ分。

    index : 座標インデックス(1始まり)。参照構造は 0
    sign  : +1 / -1。参照構造は 0
    """

    name: str
    index: int
    sign: int
    molecule: Molecule


def index_from_coordinate(atom: int, axis: int) -> int:
    """(atom, axis)(どちらも 0 始まり)→ 座標インデックス(1 始まり)。"""
    if atom < 0 or axis not in (0, 1, 2):
        raise ValueError(f"invalid coordinate: atom={atom}, axis={axis}")
    return 3 * atom + axis + 1


def coordinate_from_index(index: int) -> tuple[int, int]:
    """座標インデックス(1 始まり)→ (atom, axis)(どちらも 0 始まり)。"""
    if index < 1:
        raise ValueError(f"coordinate index must be >= 1, got {index}")
    return divmod(index - 1, 3)


def displacement_name(prefix: str, index: int, sign: int = 0) -> str:
    """命名ルールに従った名前(拡張子なし)を返す。参照構造は index=0, sign=0。"""
    if not prefix:
        raise ValueError("prefix must not be empty")
    if not 0 <= index <= _MAX_INDEX:
        raise ValueError(f"index must be in 0..{_MAX_INDEX}, got {index}")

    if index == 0:
        if sign != 0:
            raise ValueError("reference structure (index 0) must have sign 0")
        return f"{prefix}_{index:0{_WIDTH}d}"

    if sign not in _SIGN_TO_SUFFIX:
        raise ValueError(f"sign must be +1 or -1 for index {index}, got {sign}")
    return f"{prefix}_{index:0{_WIDTH}d}_{_SIGN_TO_SUFFIX[sign]}"


def parse_displacement_name(name: str) -> tuple[str, int, int]:
    """displacement_name の逆。名前(拡張子なし)→ (prefix, index, sign)。"""
    m = _NAME_RE.match(name)
    if m is None:
        raise ValueError(f"not a displacement name: {name!r}")

    prefix = m["prefix"]
    index = int(m["index"])
    suffix = m["sign"]

    if index == 0:
        if suffix is not None:
            raise ValueError(f"reference structure must not have a sign: {name!r}")
        return prefix, 0, 0

    if suffix is None:
        raise ValueError(f"displaced structure must have _p or _m: {name!r}")
    return prefix, index, _SUFFIX_TO_SIGN[suffix]


def make_displacements(
    mol: Molecule,
    *,
    prefix: str,
    step: float = 0.005,
    include_reference: bool = True,
) -> list[Displacement]:
    """
    中心差分用の変位構造を作る。

    Parameters
    ----------
    mol               : 参照構造(coord は Å)
    prefix            : 名前の接頭辞
    step              : 変位幅(Bohr)。ORCA の NumFreq の既定値と同じ 0.005
    include_reference : True なら先頭に参照構造 {prefix}_0000 を含める

    Returns
    -------
    [参照構造,] 0001_p, 0001_m, 0002_p, 0002_m, ... の順のリスト(計 6N(+1) 個)
    """
    if step <= 0:
        raise ValueError(f"step must be positive, got {step}")

    n_coord = 3 * len(mol.atoms)
    if n_coord == 0:
        raise ValueError("molecule has no atoms")
    if n_coord > _MAX_INDEX:
        raise ValueError(
            f"too many coordinates for {_WIDTH}-digit indices: 3N = {n_coord}"
        )

    step_ang = step * BOHR_TO_ANG
    result: list[Displacement] = []

    if include_reference:
        result.append(
            Displacement(
                name=displacement_name(prefix, 0),
                index=0,
                sign=0,
                molecule=Molecule(atoms=mol.atoms, coord=mol.coord),
            )
        )

    for index in range(1, n_coord + 1):
        atom, axis = coordinate_from_index(index)
        for sign in (1, -1):
            coord = mol.coord.copy()
            coord[atom, axis] += sign * step_ang
            result.append(
                Displacement(
                    name=displacement_name(prefix, index, sign),
                    index=index,
                    sign=sign,
                    molecule=Molecule(atoms=mol.atoms, coord=coord),
                )
            )

    return result
