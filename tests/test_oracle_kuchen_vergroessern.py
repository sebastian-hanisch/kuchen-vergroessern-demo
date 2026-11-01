"""Orakel-Tests (DEMO-PLAYBOOK §12): jede Kernroutine gegen einen anderen Rechenweg.

* Greedy-Grenze gegen die Aufzählung aller 2^n Ecken (exakt in Brüchen) und gegen ein lineares Programm (scipy `linprog`);
* Nash-Lösung gegen das numerische Maximum des Produkts auf der LP-Grenze; egalitär gegen LP-Maximin; Kalai–Smorodinsky gegen Bisektion über die LP-Grenze;
* Adjusted Winner gegen das LP-Maximin und das Beispiel der englischen Wikipedia-Seite (die Seite, nicht die Originalquelle);
* Schwelle M* gegen das Abtasten ganzzahliger Preis-Spielräume;
* Zahlungsziel d*, Risikoanteil q*, Wettgröße w* gegen Gitter und `scipy.optimize.minimize_scalar`;
* Rubinstein auf der Grenze gegen die geschlossene Formel auf einer Strecke mit Steigung −1 und gegen die Wertiteration;
* Max-Rand-Schätzer gegen `linprog`.
Mini-Instanzen und feste Zufallsstände; zusammen unter 10 Sekunden. Die größeren Läufe (mehr als 200 Instanzen) liefen im Scratch-Verzeichnis beim Bau."""

import itertools
import math
import os
import random
from fractions import Fraction as F

import numpy as np
import pytest

import vhg_frontier as FR
import vhg_meso as ME
import vhg_sources as SO

# Zahl der Instanzen je Orakel (die Suite braucht unter 10 Sekunden; der Scratch-Lauf beim Bau setzt größere Werte)
SCALE = int(os.environ.get("VHG_ORACLE_SCALE", "1"))
N_ENUM, N_LP, N_LP_UNEQUAL, N_NASH, N_EGAL, N_KS, N_AW, N_MSTAR, N_ABOVE, N_TERM, N_RISK, N_BET, N_ITER, N_MARGIN = (
    SCALE * x for x in (60, 40, 40, 10, 40, 12, 60, 60, 80, 60, 60, 25, 25, 40))

linprog = pytest.importorskip("scipy.optimize").linprog
minimize_scalar = pytest.importorskip("scipy.optimize").minimize_scalar


def _ints(rng, n, total=100):
    cuts = sorted(rng.sample(range(1, total), n - 1))
    return [b - a for a, b in zip([0] + cuts, cuts + [total])]


def lp_front(v, s, u):
    """max U_S unter U_V >= u, 0 <= x <= 1."""
    res = linprog(-np.array(s, float), A_ub=[list(map(float, v))], b_ub=[float(sum(v)) - u], bounds=[(0, 1)] * len(v), method="highs")
    return -res.fun


def lp_egal(v, s):
    """max t unter U_V >= t, U_S >= t."""
    n = len(v)
    c = np.zeros(n + 1)
    c[-1] = -1
    A = [[float(x) for x in v] + [1.0], [-float(x) for x in s] + [1.0]]
    res = linprog(c, A_ub=A, b_ub=[float(sum(v)), 0.0], bounds=[(0, 1)] * n + [(0, None)], method="highs")
    return -res.fun


# --- Grenze ----------------------------------------------------------------------------------------------------------------------------
def test_greedy_frontier_equals_the_enumeration_of_all_corners():
    rng = random.Random(1)
    for _ in range(N_ENUM):
        n = rng.choice([2, 3, 4, 5, 6])
        v, s = [F(x) for x in _ints(rng, n)], [F(x) for x in _ints(rng, n)]
        verts, _ = FR.frontier(v, s)
        every = [(sum(v[i] for i in range(n) if bits[i] == 0), sum(s[i] for i in range(n) if bits[i] == 1)) for bits in itertools.product((0, 1), repeat=n)]
        for lam in (F(k, 20) for k in range(21)):
            assert max(lam * a + (1 - lam) * b for a, b in verts) == max(lam * a + (1 - lam) * b for a, b in every)


def test_greedy_frontier_equals_the_linear_program():
    rng = random.Random(2)
    for _ in range(N_LP):
        n = rng.choice([2, 3, 4, 5])
        v, s = _ints(rng, n), _ints(rng, n)
        verts, _ = FR.frontier([F(x) for x in v], [F(x) for x in s])
        for u in np.linspace(0, sum(v), 9):
            assert float(FR.frontier_value(verts, F(u).limit_denominator(10**9))) == pytest.approx(lp_front(v, s, u), abs=1e-6)


def test_frontier_with_unequal_totals_and_zero_weights_equals_the_linear_program():
    rng = random.Random(3)
    for _ in range(N_LP_UNEQUAL):
        n = rng.choice([2, 3, 4])
        v, s = [rng.choice([0, 0, 5, 20, 90]) for _ in range(n)], [rng.choice([0, 10, 40, 100]) for _ in range(n)]
        if sum(v) == 0:
            continue
        verts, _ = FR.frontier([F(x) for x in v], [F(x) for x in s])
        for u in np.linspace(0, sum(v), 7):
            assert float(FR.frontier_value(verts, F(u).limit_denominator(10**9))) == pytest.approx(lp_front(v, s, u), abs=1e-6)


# --- Lösungen --------------------------------------------------------------------------------------------------------------------------
def test_nash_equals_the_numerical_maximum_of_the_product_on_the_lp_frontier():
    rng = random.Random(4)
    for _ in range(N_NASH):
        n = rng.choice([2, 3, 4])
        v, s = _ints(rng, n), _ints(rng, n)
        a, b = FR.nash(FR.frontier([F(x) for x in v], [F(x) for x in s])[0])
        grid = np.linspace(0, sum(v), 81)
        k = int(np.argmax([u * lp_front(v, s, u) for u in grid]))
        res = minimize_scalar(lambda u: -(u * lp_front(v, s, u)), bounds=(grid[max(k - 1, 0)], grid[min(k + 1, 80)]), method="bounded", options={"xatol": 1e-10})
        assert float(a * b) == pytest.approx(-res.fun, rel=1e-6)


def test_egalitarian_equals_the_lp_maximin():
    rng = random.Random(5)
    for _ in range(N_EGAL):
        n = rng.choice([2, 3, 4, 5])
        v, s = _ints(rng, n), _ints(rng, n)
        e = FR.egalitarian(FR.frontier([F(x) for x in v], [F(x) for x in s])[0])
        assert float(e[0]) == pytest.approx(lp_egal(v, s), abs=1e-8) and e[0] == e[1]


def test_kalai_smorodinsky_equals_bisection_on_the_lp_frontier():
    """Größtes λ, bei dem (λ·ΣV, λ·ΣS) noch erreichbar ist: U_S(λ·ΣV) >= λ·ΣS."""
    rng = random.Random(6)
    for _ in range(N_KS):
        n = rng.choice([2, 3, 4])
        v, s = _ints(rng, n), _ints(rng, n, 120)
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if lp_front(v, s, mid * sum(v)) >= mid * sum(s) - 1e-12:
                lo = mid
            else:
                hi = mid
        k = FR.kalai_smorodinsky(FR.frontier([F(x) for x in v], [F(x) for x in s])[0])
        assert float(k[0]) == pytest.approx(lo * sum(v), abs=1e-6) and float(k[1]) == pytest.approx(lo * sum(s), abs=1e-6)


def test_adjusted_winner_equals_the_lp_maximin_and_keeps_its_properties():
    rng = random.Random(7)
    for _ in range(N_AW):
        n = rng.choice([2, 3, 4, 5])
        v, s = _ints(rng, n), _ints(rng, n)
        x, (a, b), split = FR.adjusted_winner([F(t) for t in v], [F(t) for t in s])
        assert a == b and float(a) == pytest.approx(lp_egal(v, s), abs=1e-8)
        assert split <= 1 and all(0 <= t <= 1 for t in x)
        assert a >= 50                                        # neidfrei: beide haben mindestens die Hälfte ihrer 100 Punkte
        assert (sum(F(t) * (1 - xi) for t, xi in zip(v, x)), sum(F(t) * xi for t, xi in zip(s, x))) == (a, b)
        verts = FR.frontier([F(t) for t in v], [F(t) for t in s])[0]
        assert FR.frontier_value(verts, a) == b               # auf der Pareto-Grenze


def test_adjusted_winner_wikipedia_example_against_the_lp(wikipedia_aw):
    v, s = wikipedia_aw["v"], wikipedia_aw["s"]
    assert float(wikipedia_aw["each"]) == pytest.approx(lp_egal([float(t) for t in v], [float(t) for t in s]), abs=1e-8)


# --- Seitenzahlung ---------------------------------------------------------------------------------------------------------------------
def test_threshold_m_star_is_the_smallest_integer_price_room_with_nash_equal_to_half():
    rng = random.Random(8)
    for _ in range(N_MSTAR):
        n = rng.choice([2, 3, 4])
        v, s = [F(x) for x in _ints(rng, n)], [F(x) for x in _ints(rng, n)]
        first = None
        for m in range(0, 120):
            vp, sp = FR.with_price(v, s, F(m))
            verts = FR.frontier(vp, sp)[0]
            a, b = FR.nash(verts)
            if a == b == FR.max_sum(verts) / 2:
                first = m
                break
        ms = FR.m_star(v, s)
        assert first is not None and first == ms, (first, ms)


def test_with_price_above_the_threshold_nash_ks_and_egalitarian_coincide():
    rng = random.Random(9)
    for _ in range(N_ABOVE):
        v, s = [F(x) for x in _ints(rng, 4)], [F(x) for x in _ints(rng, 4)]
        m = FR.m_star(v, s) + rng.randint(0, 30)
        vp, sp = FR.with_price(v, s, m)
        verts = FR.frontier(vp, sp)[0]
        t = FR.max_sum(verts)
        assert FR.nash(verts) == FR.kalai_smorodinsky(verts) == FR.egalitarian(verts) == (t / 2, t / 2)


# --- Zeit, Risiko, Wette ---------------------------------------------------------------------------------------------------------------
def test_payment_term_optimum_equals_grid_and_scipy():
    rng = np.random.default_rng(7)
    for _ in range(N_TERM):
        a, b = sorted(rng.uniform(0.001, 0.05, size=2))
        if b - a < 1e-3:
            continue
        grid = np.arange(0, 1500, 0.01)
        vals = 1000 * (np.exp(-a * grid) - np.exp(-b * grid))
        d = SO.term_optimum(a, b)
        assert grid[int(np.argmax(vals))] == pytest.approx(d, rel=2e-3, abs=0.02)
        res = minimize_scalar(lambda x: -SO.term_gain(x, a, b, 1000.0), bounds=(0, 1500), method="bounded", options={"xatol": 1e-9})
        assert -res.fun == pytest.approx(SO.term_gain(d, a, b, 1000.0), abs=1e-6)


def test_risk_share_equals_grid_and_scipy():
    rng = np.random.default_rng(5)
    for _ in range(N_RISK):
        gs, gv = rng.uniform(0.001, 0.05, 2)
        p, a = rng.uniform(0.1, 0.9), rng.uniform(50, 300)
        q = SO.risk_share(gs, gv)
        qs = np.linspace(0, 1, 2001)
        vals = [SO.risk_gain(x, gs, gv, a, p) for x in qs]
        assert qs[int(np.argmax(vals))] == pytest.approx(q, abs=1e-3)
        res = minimize_scalar(lambda x: -SO.risk_gain(x, gs, gv, a, p), bounds=(0, 1), method="bounded", options={"xatol": 1e-11})
        assert res.x == pytest.approx(q, abs=1e-5)


def test_risk_gain_equals_a_direct_expected_utility_computation():
    """Gegenprobe der Sicherheitsäquivalente über die Nutzenfunktion u(x) = −exp(−γ x) und die Umkehrung."""
    a, p, gs, gv, q = 200.0, 0.5, 0.005, 0.0025, 0.4
    mean = p * a

    def ce(vals, g):
        eu = sum(pr * -math.exp(-g * x) for pr, x in zip((p, 1 - p), vals))
        return -math.log(-eu) / g

    inc_s = [x + q * (mean - x) for x in (a, 0.0)]
    inc_v = [-q * (mean - x) for x in (a, 0.0)]
    expected = ce(inc_s, gs) + ce(inc_v, gv) - ce([a, 0.0], gs) - ce([0.0, 0.0], gv)
    assert SO.risk_gain(q, gs, gv, a, p) == pytest.approx(expected, rel=1e-12)


def test_bet_size_equals_grid_and_scipy():
    rng = np.random.default_rng(9)
    for _ in range(N_BET):
        g = rng.uniform(0.0005, 0.03)
        a, b = sorted(rng.uniform(0.05, 0.95, 2))
        if b - a < 0.02:
            continue
        w = SO.bet_size_cara(a, b, g)
        res = minimize_scalar(lambda x: -SO.bet_gain_cara(x, a, b, g), bounds=(0, 8 * w), method="bounded", options={"xatol": 1e-10})
        assert res.x == pytest.approx(w, rel=1e-5)
        grid = np.linspace(0, 6 * w, 6001)
        assert grid[int(np.argmax([SO.bet_gain_cara(x, a, b, g) for x in grid]))] == pytest.approx(w, abs=6 * w / 6000 * 1.01)


# --- Rubinstein auf der Grenze ---------------------------------------------------------------------------------------------------------
def test_rubinstein_on_a_straight_frontier_equals_the_closed_formula():
    """Gerade Grenze U_V + U_S = T (nur ein Preis-Punkt): P_V = T (1 − δ_S) / (1 − δ_V δ_S), Q_V = δ_V P_V."""
    for t in (1.0, 160.0):
        verts = [(t, 0.0), (0.0, t)]
        for dv, ds in ((0.9, 0.9), (0.8, 0.95), (0.99, 0.5), (0.6, 0.6)):
            p, q = FR.rubinstein_on_frontier(verts, dv, ds)
            assert p[0] == pytest.approx(t * FR.rubinstein_share(dv, ds), rel=1e-9) and p[0] + p[1] == pytest.approx(t)
            assert q[0] == pytest.approx(dv * p[0], rel=1e-9)


def test_rubinstein_share_by_hand():
    # δ_V = δ_S = 1/2: (1 − 1/2) / (1 − 1/4) = 2/3
    assert FR.rubinstein_share(0.5, 0.5) == pytest.approx(2 / 3)
    assert FR.rubinstein_share(F(1, 2), F(1, 2)) == F(2, 3)


def test_rubinstein_on_the_frontier_equals_value_iteration():
    rng = random.Random(10)
    for _ in range(N_ITER):
        n = rng.choice([2, 3, 4])
        v, s = [float(x) for x in _ints(rng, n)], [float(x) for x in _ints(rng, n)]
        verts = FR.frontier(v, s)[0]
        dv, ds = rng.uniform(0.6, 0.97), rng.uniform(0.6, 0.97)
        p, q = FR.rubinstein_on_frontier(verts, dv, ds)

        def inverse(value):
            """Größtes U_V mit f(U_V) >= value (die Grenze fällt in U_V)."""
            lo, hi = 0.0, verts[0][0]
            for _ in range(80):
                mid = (lo + hi) / 2
                if FR.frontier_value(verts, mid) >= value:
                    lo = mid
                else:
                    hi = mid
            return lo

        pv = 0.0
        for _ in range(400):                                   # Wertiteration: S bietet, V bietet, abwechselnd
            qs = FR.frontier_value(verts, dv * pv)
            pv = inverse(ds * qs)
        assert pv == pytest.approx(p[0], abs=1e-6)


# --- MESO ------------------------------------------------------------------------------------------------------------------------------
def test_max_margin_equals_the_linear_program():
    rng = np.random.default_rng(11)
    for _ in range(N_MARGIN):
        m = int(rng.integers(1, 9))
        b = rng.dirichlet(np.ones(4))
        cons = []
        for _ in range(m):                                     # Ungleichungen, die b erfüllt (eine echte Wahl)
            d = ME.PACKAGES[rng.integers(0, 625)] - ME.PACKAGES[rng.integers(0, 625)]
            cons.append(d if d @ b >= 0 else -d)
        w, t = ME.max_margin(cons)
        D = np.array(cons)
        res = linprog(np.r_[np.zeros(4), -1.0], A_ub=np.hstack([-D, np.ones((m, 1))]), b_ub=np.zeros(m), A_eq=[[1, 1, 1, 1, 0]], b_eq=[1], bounds=[(0, None)] * 4 + [(None, None)], method="highs")
        assert t == pytest.approx(-res.fun, abs=1e-8)
        assert w.sum() == pytest.approx(1.0) and np.all(w >= -1e-9) and np.all(D @ w >= t - 1e-8)


def test_posterior_mean_equals_a_loop_over_the_prior():
    rng = np.random.default_rng(12)
    b = rng.dirichlet(np.ones(4))
    cons = []
    while len(cons) < 3:
        d = ME.PACKAGES[rng.integers(0, 625)] - ME.PACKAGES[rng.integers(0, 625)]
        if np.any(d != 0):
            cons.append(d if d @ b >= 0 else -d)
    w, n = ME.posterior_mean(cons)
    full = [row for row in ME.PRIOR if all(row @ c >= 0 for c in cons)]
    assert w is not None and n == len(full) and np.allclose(w, np.mean(full, axis=0))
