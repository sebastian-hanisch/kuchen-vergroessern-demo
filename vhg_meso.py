"""MESO (mehrere für sich gleichwertige Angebote gleichzeitig): eine **Simulation unter Modellannahmen**, kein Befund über Menschen.

Modell. n = 4 Punkte mit je 5 Stufen x_i in {0; 0,25; 0,5; 0,75; 1} (Anteil des Punktes, der an den Spediteur B geht): 5⁴ = 625 Pakete. Die Gewichte a (Verlader A) und b (Spediteur B) sind
unabhängig Dirichlet(1) mit Summe 1, U_A = Σ a_i (1 − x_i), U_B = Σ b_i x_i. A kennt b nicht. A legt nur Pakete **im Band** vor (|U_A − 1/2| <= 0,025): für A (fast) gleichwertig. In jeder
Runde legt A k verschiedene Pakete des Bandes vor (noch nicht gezeigte, in zufälliger Reihenfolge); B wählt ehrlich das mit dem größten U_B. Aus allen Wahlen schätzt A b (Wahl >= jedes andere
vorgelegte Paket: w·(gewählt − anderes) >= 0) und macht als Endangebot das Paket im Band mit dem größten geschätzten U_B.

Kennzahl g = (U_B(Endangebot) − Mittel von U_B im Band) / (größtes U_B im Band − Mittel von U_B im Band): 0 für ein Zufallspaket des Bandes, 1 für das beste. Zwei Schätzer:
**Posterior-Mittel** (Mittel der Gewichte aus 50.000 festen Dirichlet(1)-Ziehungen, die alle Wahlen erklären, wenn A den Prior kennt) und **Max-Rand** (der Punkt im Simplex mit dem größten
Abstand t zu allen Wahl-Ungleichungen w·d >= t; bei mehreren gleich guten Ecken das Mittel dieser Ecken). Reine Funktionen, Zufall nur über SplitMix64; kein scipy zur Laufzeit."""

import itertools

import numpy as np

from vhg_rng import uniform_block

N_POINTS = 4
LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
EPS_BAND = 0.025
PRIOR_DRAWS = 50_000
PRIOR_SEED = 999
MIN_PRIOR_MATCHES = 5
ESTIMATORS = ("Posterior-Mittel", "Max-Rand")
MIN_BAND = 12                    # kleineres Band: Instanz verworfen (zu wenig Pakete zum Auswählen)
TOL = 1e-9

PACKAGES = np.array(list(itertools.product(LEVELS, repeat=N_POINTS)))        # 625 x 4


def dirichlet1(u) -> np.ndarray:
    """Gewichte Dirichlet(1) mit Summe 1 aus n Gleichverteilten (normierte Exponentialzahlen −ln(1 − u))."""
    e = -np.log(1.0 - np.asarray(u, dtype=float))
    return e / e.sum()


_E = -np.log(1.0 - uniform_block(PRIOR_SEED, PRIOR_DRAWS * N_POINTS).reshape(PRIOR_DRAWS, N_POINTS))
PRIOR = _E / _E.sum(axis=1, keepdims=True)           # Zeile für Zeile gleich dirichlet1 (Test)


def utilities(a, b) -> tuple[np.ndarray, np.ndarray]:
    """(U_A, U_B) aller 625 Pakete."""
    return (1.0 - PACKAGES) @ a, PACKAGES @ b


def band_of(u_a: np.ndarray, eps: float = EPS_BAND) -> np.ndarray:
    """Indizes der Pakete im Band |U_A − 1/2| <= eps (mit kleiner Rundungsreserve)."""
    return np.where(np.abs(u_a - 0.5) <= eps + 1e-12)[0]


def choose(offered: np.ndarray, u_b: np.ndarray) -> int:
    """B wählt aus den vorgelegten Paketen das mit dem größten U_B (Gleichstand: das erste vorgelegte)."""
    return int(offered[int(np.argmax(u_b[offered]))])


def constraints_from_choice(offered: np.ndarray, chosen: int) -> list[np.ndarray]:
    """Wahl-Ungleichungen: für jedes nicht gewählte Paket o gilt w·(x_gewählt − x_o) >= 0."""
    return [PACKAGES[chosen] - PACKAGES[o] for o in offered if o != chosen]


def posterior_mean(cons: list[np.ndarray]):
    """Mittel der Prior-Ziehungen, die alle Ungleichungen erfüllen; (Gewichte, Zahl der Treffer) oder (None, Treffer), wenn weniger als MIN_PRIOR_MATCHES passen."""
    if not cons:
        return PRIOR.mean(axis=0), PRIOR_DRAWS
    sel = np.all(PRIOR @ np.array(cons).T >= 0, axis=1)
    n = int(sel.sum())
    if n < MIN_PRIOR_MATCHES:
        return None, n
    return PRIOR[sel].mean(axis=0), n


_COMBOS: dict[int, np.ndarray] = {}


def _combos(total: int) -> np.ndarray:
    if total not in _COMBOS:
        _COMBOS[total] = np.array(list(itertools.combinations(range(total), N_POINTS)))
    return _COMBOS[total]


def max_margin(cons: list[np.ndarray]) -> tuple[np.ndarray, float]:
    """Max-Rand-Punkt: größtes t mit w·d_j >= t für alle Ungleichungen d_j, w im Simplex. Rückgabe (w, t).

    Das lineare Programm in (w, t) hat sein Maximum an einer Ecke: vier der N + m Randflächen (w_i >= 0 und w·d_j − t >= 0) sind scharf, dazu Σw = 1. Alle Kombinationen werden
    aufgezählt und gelöst; bei mehreren gleich guten Ecken gilt das Mittel dieser (verschiedenen) Ecken. Ohne Ungleichung: gleiche Gewichte (t = 0)."""
    if not cons:
        return np.full(N_POINTS, 1.0 / N_POINTS), 0.0
    d = np.array(cons)
    m = len(d)
    rows = np.vstack([np.hstack([np.eye(N_POINTS), np.zeros((N_POINTS, 1))]), np.hstack([d, -np.ones((m, 1))])])      # (N + m) x (N + 1), Zeile · (w, t) >= 0
    combos = _combos(N_POINTS + m)
    mats = np.empty((len(combos), N_POINTS + 1, N_POINTS + 1))
    mats[:, 0, :] = np.append(np.ones(N_POINTS), 0.0)
    mats[:, 1:, :] = rows[combos]
    rhs = np.zeros((len(combos), N_POINTS + 1))
    rhs[:, 0] = 1.0
    det = np.linalg.det(mats)
    ok = np.abs(det) > 1e-10
    sol = np.linalg.solve(mats[ok], rhs[ok][:, :, None])[:, :, 0]
    w, t = sol[:, :N_POINTS], sol[:, N_POINTS]
    feasible = np.all(w >= -TOL, axis=1) & np.all(w @ d.T - t[:, None] >= -TOL, axis=1)
    w, t = w[feasible], t[feasible]
    best = t.max()
    top = np.unique(np.round(w[t >= best - TOL], 9), axis=0)
    return top.mean(axis=0), float(best)


def estimate(cons: list[np.ndarray], estimator: str):
    """Schätzung der Gewichte von B; (Gewichte, benutzter Schätzer). Das Posterior-Mittel fällt auf Max-Rand zurück, wenn zu wenige Prior-Ziehungen passen."""
    if estimator == "Posterior-Mittel":
        w, _ = posterior_mean(cons)
        if w is not None:
            return w, "Posterior-Mittel"
        return max_margin(cons)[0], "Max-Rand (Rückfall)"
    if estimator == "Max-Rand":
        return max_margin(cons)[0], "Max-Rand"
    raise ValueError(f"Schätzer {estimator!r} unbekannt")


def final_offer(band: np.ndarray, w_hat: np.ndarray) -> int:
    """Endangebot von A: das Paket im Band mit dem größten geschätzten U_B (Gleichstand: das erste im Band)."""
    return int(band[int(np.argmax(PACKAGES[band] @ w_hat))])


def score(u_b: np.ndarray, band: np.ndarray, package: int) -> float | None:
    """g = (U_B(Paket) − Mittel U_B im Band) / (größtes U_B im Band − Mittel U_B im Band); None, wenn alle Pakete im Band gleich viel bringen."""
    mean = float(u_b[band].mean())
    den = float(u_b[band].max()) - mean
    if den < 1e-9:
        return None
    return (float(u_b[package]) - mean) / den


def make_instance(seed: int):
    """Eine Instanz aus einem Zufalls-Seed: (a, b, Reihenfolge der Pakete des Bandes); None, wenn das Band weniger als MIN_BAND Pakete hat."""
    u = uniform_block(seed, 2 * N_POINTS + len(PACKAGES))
    a, b = dirichlet1(u[:N_POINTS]), dirichlet1(u[N_POINTS:2 * N_POINTS])
    u_a, _ = utilities(a, b)
    band = band_of(u_a)
    if len(band) < MIN_BAND:
        return None
    keys = u[2 * N_POINTS:][band]
    return a, b, band[np.argsort(keys, kind="stable")]


def run(a, b, order: np.ndarray, k: int, rounds: int, estimator: str) -> dict:
    """Lässt `rounds` Runden zu je k Angeboten laufen (Pakete in der Reihenfolge `order`, ohne Zurücklegen); gibt die Runden, die Schätzung, das Endangebot und die Kennzahlen zurück.

    Sind weniger Pakete übrig als k, wird mit dem Rest vorgelegt; sind alle Pakete des Bandes vorgelegt, bleibt eine Runde leer."""
    u_a, u_b = utilities(a, b)
    band = band_of(u_a)
    cons: list[np.ndarray] = []
    shown: list[int] = []
    log = []
    pos = 0
    for r in range(1, rounds + 1):
        offered = np.array(order[pos:pos + k], dtype=int)
        pos += k
        chosen = None
        if len(offered):
            chosen = choose(offered, u_b)
            cons.extend(constraints_from_choice(offered, chosen))
            shown.extend(int(i) for i in offered)
        log.append({"round": r, "offered": [int(i) for i in offered], "chosen": chosen})
    w_hat, used = estimate(cons, estimator)
    fin = final_offer(band, w_hat)
    best_shown = max(shown, key=lambda i: u_b[i]) if shown else None
    return {
        "log": log, "w_hat": w_hat, "estimator_used": used, "final": fin,
        "g_end": score(u_b, band, fin),
        "g_shown": None if best_shown is None else score(u_b, band, best_shown),
        "error": float(0.5 * np.abs(w_hat - b).sum()),
        "error_equal": float(0.5 * np.abs(np.full(N_POINTS, 1.0 / N_POINTS) - b).sum()),
        "n_shown": len(shown), "band_size": int(len(band)), "constraints": len(cons),
    }
