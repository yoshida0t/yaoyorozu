"""単位換算係数。単位変換はここの定数だけを使って行う。"""

__all__ = ["BOHR_TO_ANG", "ANG_TO_BOHR"]

# Bohr 半径 (CODATA 2018)
BOHR_TO_ANG = 0.529177210903
ANG_TO_BOHR = 1.0 / BOHR_TO_ANG
