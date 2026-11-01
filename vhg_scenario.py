"""Die Einstellungen der App als unveränderliche Datenklasse (Zwischenspeicher-Schlüssel) und der Zugriff auf die Punkte."""

from dataclasses import dataclass

import vhg_constants as C


@dataclass(frozen=True)
class Settings:
    v: tuple = C.DEFAULT_V
    s: tuple = C.DEFAULT_S
    price: float = C.DEFAULT_PRICE
    bundle: int = C.DEFAULT_BUNDLE
    rs: float = C.DEFAULT_RS
    rv: float = C.DEFAULT_RV
    term: int = C.DEFAULT_TERM
    gs: float = C.DEFAULT_GS
    gv: float = C.DEFAULT_GV
    q: int = C.DEFAULT_Q
    pv: float = C.DEFAULT_PV
    ps: float = C.DEFAULT_PS
    bonus: float = C.DEFAULT_BONUS
    gb: float = C.DEFAULT_BET_GAMMA
    dv: float = C.DEFAULT_DELTA
    ds: float = C.DEFAULT_DELTA
    k: int = C.DEFAULT_MESO_K
    r: int = C.DEFAULT_MESO_R
    est: str = "Posterior-Mittel"
    seed: int = C.DEFAULT_SEED


def point_values(st: Settings) -> tuple[list[float], list[float], list[str]]:
    """Gewichte (v, s) und Namen der verhandelten Punkte ohne Preis. Ein Punkt, der beiden Seiten nichts wert ist (v = s = 0), wird nicht verhandelt und fehlt."""
    live = [i for i in range(len(st.v)) if st.v[i] + st.s[i] > 0]
    return [float(st.v[i]) for i in live], [float(st.s[i]) for i in live], [C.POINT_NAMES[i] for i in live]


def effective_bundle(st: Settings) -> int:
    """Bündelgröße, auf die Zahl der verhandelten Punkte begrenzt (mehr als Punkte vorhanden heißt ein Paket)."""
    return max(1, min(st.bundle, len(point_values(st)[0])))
