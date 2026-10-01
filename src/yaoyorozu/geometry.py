from __future__ import annotations

from typing import Sequence

import numpy as np

from .core.molecule import Molecule

__all__ = ["kabsch", "rotate", "measure_geometry", "align_geometry"]


def kabsch(*, target: Molecule, ref: Molecule) -> Molecule:
    """target を ref に重ね合わせる(RMSD 最小の回転+並進)。"""
    if len(target.atoms) != len(ref.atoms):
        raise ValueError(
            f"Atom count mismatch: {len(target.atoms)} vs {len(ref.atoms)}"
        )

    P = target.coord
    Q = ref.coord

    Pg = P.mean(axis=0)
    Qg = Q.mean(axis=0)
    P0 = P - Pg
    Q0 = Q - Qg

    C = P0.T @ Q0
    V, _, Wt = np.linalg.svd(C)
    d = np.sign(np.linalg.det(V @ Wt))
    D = np.diag([1.0, 1.0, d])
    U = V @ D @ Wt

    return Molecule(atoms=target.atoms, coord=P0 @ U + Qg)


def rotate(*, mole: Molecule, R: np.ndarray) -> Molecule:
    R = np.asarray(R, dtype=float)
    if R.shape != (3, 3):
        raise ValueError(f"R must be 3x3, got {R.shape}")

    coord = mole.coord @ R.T  # (N,3) @ (3,3) -> (N,3)
    return Molecule(atoms=mole.atoms, coord=coord)


def measure_geometry(*, mole: Molecule, index: Sequence[int]) -> float:
    """len(index)==2: 結合長, ==3: 角度(度。index[1] が頂点)。"""
    xyz = mole.coord

    if len(index) == 2:  # bond length
        i, j = index
        return float(np.linalg.norm(xyz[i] - xyz[j]))

    if len(index) == 3:  # angle
        i, j, k = index
        v1 = xyz[i] - xyz[j]
        v2 = xyz[k] - xyz[j]
        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return float(np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0))))

    raise ValueError("index must have 2 (bond length) or 3 (angle) elements.")


_PLANE_NORMAL_AXIS = {"xy": 2, "xz": 1, "yz": 0}


def align_geometry(*, ref: Molecule, plane: str, index: Sequence[int]) -> Molecule:
    """
    index の原子の重心を原点に移し、plane に垂直な座標(xy なら z)の
    RMSD が最小になるよう分子全体を回転した新しい Molecule を返す。
    """
    key = "".join(sorted(plane.lower()))
    if key not in _PLANE_NORMAL_AXIS:
        raise ValueError(f"plane must be one of 'xy', 'yz', 'xz', got {plane!r}")
    axis = _PLANE_NORMAL_AXIS[key]

    idx = np.asarray(index, dtype=int)
    if idx.ndim != 1 or idx.size < 3:
        raise ValueError("index must contain at least 3 atoms")
    if idx.min() < -len(ref.atoms) or idx.max() >= len(ref.atoms):
        raise IndexError("index out of range")

    X = ref.coord
    origin = X[idx].mean(axis=0)
    P = X[idx] - origin

    # 最小固有値の固有ベクトル = 最適平面の法線 n
    _, V = np.linalg.eigh(P.T @ P)
    n = V[:, 0]

    e = np.zeros(3)
    e[axis] = 1.0
    if n @ e < 0:  # c >= 0 に揃えて回転角を小さくする(c=-1 の特異ケース回避)
        n = -n

    # n -> e への最小回転(Rodrigues)
    v = np.cross(n, e)
    c = float(n @ e)
    K = np.array([[0, -v[2], v[1]],
                  [v[2], 0, -v[0]],
                  [-v[1], v[0], 0]])
    R = np.eye(3) + K + K @ K / (1.0 + c)

    return Molecule(atoms=ref.atoms, coord=(X - origin) @ R.T)
