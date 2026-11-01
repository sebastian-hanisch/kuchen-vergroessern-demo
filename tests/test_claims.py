"""Jede Zahl aus der README und den Hilfetexten, nachgerechnet (DEMO-PLAYBOOK §4).

Drei Quellen, alle plattformsicher:
* die gespeicherten Messreihen (`data/grid.json`: 4 Blöcke zu je 2.000 Instanzen je Zelle, `data/meso.json`: 8 Blöcke zu je 500 Instanzen; Erzeuger-Hash geprüft in `test_measurements.py`): die README-Zahl
  ist der gespeicherte Wert, gerundet;
* exakte Rechnung (Brüche, Formeln, Identitäten): Gleitkommagleichheit nur mit `approx`;
* die Zeilenbauer der App (`vhg_evaluation.*_table`, `*_display`): jede Zeile der README-Tabellen steht als Text in der README.
Keine Zeit-Assertion, keine exakten Zufallswerte einzelner Läufe. Zählungen über das Raster („in k von m Zellen“) stehen als Zählungen im Test, nicht als Urteilswort."""

import random
import re
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

import test_oracle_kuchen_vergroessern as ORA
import vhg_constants as C
import vhg_evaluation as V
import vhg_experiments as XP
import vhg_frontier as FR
import vhg_meso as ME
import vhg_sources as SO
import vhg_texts as T
from vhg_scenario import Settings

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def row_of(label):
    """Die Tabellenzeile der Hypothese (eine Zeile der README, beginnt mit `| Hn |`)."""
    return next(line for line in README.splitlines() if line.startswith(f"| {label} |"))


def has(row, *needles):
    missing = [n for n in needles if n not in row]
    assert not missing, missing


@pytest.fixture(scope="module")
def grid():
    return XP.load_grid()


@pytest.fixture(scope="module")
def meso():
    return XP.load_meso()


def _ints(rng, n, total=100):
    cuts = sorted(rng.sample(range(1, total), n - 1))
    return [b - a for a, b in zip([0] + cuts, cuts + [total])]


# --- README und App: dieselben Texte, dieselben Tabellenzeilen ---------------------------------------------------------------------------------
def test_assumption_table_is_the_same_text_in_app_and_readme():
    assert T.ASSUMPTIONS_MARKDOWN.strip() in README


def _md_row(d):
    return "| " + " | ".join(str(v) for v in d.values()) + " |"


def test_readme_tables_are_built_by_the_same_row_builders(grid, meso):
    bs = V.bet_summary(Settings())
    tables = (V.e1_table(grid, 4), V.asymmetry_table(grid), V.e2_table(grid), V.e3_table(grid), V.e3_level_table(grid), V.term_display(Settings(rs=1.0, rv=2.0, term=30)),
              V.risk_display(Settings()), V.bet_display(bs), V.bet_estimate_display(bs["gamma"]), V.meso_table(meso, 1))
    for rows in tables:
        for row in rows:
            assert _md_row(row) in README, row


def test_hypothesis_table_has_h1_to_h11_with_a_clear_stand():
    rows = re.findall(r"^\| (H\d+) \|(?:\\\||[^|])*\|\s*\*\*([^*]+)\*\*", README, flags=re.M)
    assert [h for h, _ in rows] == [f"H{i}" for i in range(1, 12)]
    assert all(a.split()[0].rstrip(",") in ("Ja", "Nein", "Offen") for _, a in rows)
    assert [a.split()[0].rstrip(",") for _, a in rows] == ["Ja"] * 6 + ["Nein"] * 4 + ["Ja"]


# --- Kernfrage -------------------------------------------------------------------------------------------------------------------------------
def test_core_question_numbers(grid):
    c = XP.find(grid["e1"], n=4, theta=1.0)
    e2 = XP.find(grid["e6"], theta=1.0)
    core = README.split("## Kernfrage")[1].split("## Befunde und Korrekturen")[0]
    has(core, V.de(c["gain"]["mean"], 1), V.pct(c["share_nash"]["mean"], 1), V.pct(c["share_ks"]["mean"], 1))
    assert round(e2["vier Einzelpunkte"]["mean"], 6) == 0 and "vier einzeln verhandelte Punkte 0 %" in core
    ts = V.term_summary(Settings(rs=1.0, rv=2.0, term=30))
    has(core, V.de(ts["gain_best"], 0) + " Euro", V.de(ts["d_star"], 1) + " Tagen", V.de(V.risk_summary(Settings())["gain_star"], 2) + " Euro")


# --- H1 --------------------------------------------------------------------------------------------------------------------------------------
def test_h1_identity_in_3000_of_3000_and_no_gain_in_500_of_500():
    rng = random.Random(11)
    same = 0
    for _ in range(3000):
        n = rng.choice([2, 3, 4, 5, 6])
        v, s = [F(x) for x in _ints(rng, n)], [F(x) for x in _ints(rng, n)]
        same += FR.max_sum(FR.frontier(v, s)[0]) - sum(FR.position_compromise(v, s)) == FR.half_abs_difference(v, s)
    assert same == 3000
    rng = random.Random(12)
    null = 0
    for _ in range(500):
        n = rng.choice([2, 3, 4, 5, 6])
        v = [F(x) for x in _ints(rng, n)]
        verts = FR.frontier(v, v)[0]
        null += FR.nash(verts) == FR.position_compromise(v, v) and FR.gain_sum(v, v) == 0
    assert null == 500
    has(row_of("H1"), "3.000 von 3.000", "500 von 500")


def test_h1_hook_gain_in_euros_and_normalized_and_the_threshold():
    v, s = [F(40), F(30), F(10)], [F(80), F(60), F(20)]
    assert FR.gain_sum(v, s) == 40 and FR.gain_sum(FR.normalize(v), FR.normalize(s)) == 0 and FR.m_star(v, s) == 160
    has(row_of("H1"), "40", "bei auf je 100 normierten Gewichten 0", "M\\* = 160")
    verts = FR.frontier(*FR.with_price(v, s, F(200)))[0]
    assert FR.nash(verts) == (180, 180)


# --- H2 --------------------------------------------------------------------------------------------------------------------------------------
def test_h2_gain_is_linear_in_theta_per_instance_and_in_all_30_cells(grid):
    w, u = XP.weights("e1|n=4|block=0", 500, 4)
    worst = 0.0
    for i in range(500):
        g1 = FR.gain_sum(list(100 * w[i]), list(100 * XP.mix(w, u, 1.0)[i]))
        for th in (0.1, 0.5):
            worst = max(worst, abs(FR.gain_sum(list(100 * w[i]), list(100 * XP.mix(w, u, th)[i])) - th * g1))
    assert worst < 1e-9
    cells = [(n, th) for n in C.E1_NS for th in C.E1_THETAS]
    assert len(cells) == 30
    for n, th in cells:
        assert abs(XP.find(grid["e1"], n=n, theta=th)["gain"]["mean"] - th * XP.find(grid["e1"], n=n, theta=1.0)["gain"]["mean"]) < 1e-9
    row = row_of("H2")
    has(row, "500 Instanzen", "30 Zellen", *(V.de(XP.find(grid["e1"], n=4, theta=th)["gain"]["mean"], 2) for th in (0.1, 0.5, 1.0)))


def test_h2_kalai_smorodinsky_equals_egalitarian_in_the_cells_with_equal_sums(grid):
    """In E1 haben beide Seiten die Summe 100: Idealpunkt auf der Diagonalen, also fallen Kalai–Smorodinsky und egalitär zusammen (die Spalte der README ist eine)."""
    rng = random.Random(15)
    for _ in range(100):
        v, s = [F(x) for x in _ints(rng, 4)], [F(x) for x in _ints(rng, 4)]
        verts = FR.frontier(v, s)[0]
        assert FR.kalai_smorodinsky(verts) == FR.egalitarian(verts)
    for c in grid["e1"]:
        if c["share_ks"]["mean"] is not None:
            assert c["share_ks"]["mean"] == pytest.approx(c["share_egal"]["mean"], abs=1e-9)


# --- H3 --------------------------------------------------------------------------------------------------------------------------------------
def test_h3_oracle_counts_are_the_loop_counts_of_the_oracle_tests():
    assert ORA.SCALE == 1
    row = row_of("H3")
    has(row, f"{ORA.N_ENUM} von {ORA.N_ENUM}", f"{ORA.N_LP} gegen das LP", f"in {ORA.N_NASH}", f"in {ORA.N_EGAL}", f"in {ORA.N_KS}", f"in {ORA.N_AW} von {ORA.N_AW}", "21 Stützstellen", "9 Stellen")
    has(row, *(str(x * 10) for x in (ORA.N_ENUM, ORA.N_LP, ORA.N_NASH, ORA.N_EGAL, ORA.N_KS, ORA.N_AW)))
    has(row, "95/156", "6847/52", "131,67")


def test_h3_wikipedia_example_numbers(wikipedia_aw):
    x, (a, b), _ = FR.adjusted_winner(wikipedia_aw["v"], wikipedia_aw["s"])
    assert 1 - x[1] == F(95, 156) and a == b == F(6847, 52) and round(float(a), 2) == 131.67


# --- H4 --------------------------------------------------------------------------------------------------------------------------------------
def test_h4_rule_in_17_of_17_cells_and_the_hand_instance(grid, hand2):
    assert len(grid["e2"]) == 17 and all(c["rule_hit"]["mean"] == 1.0 for c in grid["e2"])
    row = row_of("H4")
    has(row, "17 von 17 Zellen", f"{ORA.N_MSTAR} von {ORA.N_MSTAR}", "M\\* = 10", "(80; 70) bei M = 0", "(80; 75) bei 5", "(80; 80) bei 10", "(85; 85) bei 20")
    results = {}
    for m in (0, 5, 10, 20):
        v, s = FR.with_price(hand2["v"], hand2["s"], F(m))
        results[m] = FR.nash(FR.frontier(v, s)[0])
    assert results == {0: (80, 70), 5: (80, 75), 10: (80, 80), 20: (85, 85)}


def test_h4_level_rows_nash_reaches_zero_without_money_and_all_without_the_others_equal(grid):
    c0, c200 = XP.find(grid["e2"], theta=0.0, level=2.0, price=0), XP.find(grid["e2"], theta=0.0, level=2.0, price=200)
    assert round(c0["share_nash"]["mean"], 9) == 0 and c200["share_nash"]["mean"] == pytest.approx(1.0) and c200["nash_half"]["mean"] == 1.0 and c200["all3_equal"]["mean"] == 0.0
    assert c0["share_egal"]["mean"] == pytest.approx(-1 / 3, abs=1e-3) and "−0,333" in README
    has(row_of("H4"), "0 des Gewinns", "den vollen")


# --- H5, H6 ----------------------------------------------------------------------------------------------------------------------------------
def test_h5_numbers(zeit_hand):
    row = row_of("H5")
    z = zeit_hand
    has(row, f"{ORA.N_TERM} von {ORA.N_TERM}", "d\\* = 69,3 Tage", "250,0 Euro", "192,0 gegen 300,0", "−192,0 bei 30 Tagen")
    assert SO.term_optimum(z["rs"], z["rv"]) == pytest.approx(69.3147, abs=1e-4) and SO.term_gain(69.3147180559945, z["rs"], z["rv"], 1000.0) == pytest.approx(250.0)
    assert SO.term_gain(30, 0.02, 0.01, 1000.0) == pytest.approx(-192.0, abs=0.01) and SO.term_gain_linear(30, z["rs"], z["rv"], 1000.0) == 300.0


def test_h5_term_text_numbers_of_e4():
    ts = V.term_summary(Settings(rs=1.0, rv=2.0, term=30))
    sec = README.split("**Zahlungsziel**")[1].split("**Risiko**")[0]
    has(sec, V.de(SO.term_gain(90, 0.01, 0.02, 1000.0), 1), V.de(ts["mid_of_ends"], 1), V.de(ts["gain_mid"], 1), "45 Tagen")
    assert SO.term_gain(60, 0.01, 0.02, 1000.0) == pytest.approx(247.6, abs=0.05)


def test_h6_numbers():
    row = row_of("H6")
    has(row, f"{ORA.N_RISK} von {ORA.N_RISK}", "24,02 / 15,73 / 11,65 / 7,66 / 2,04", "18,43")
    gains = [SO.risk_gain(SO.risk_share(0.005, g / 1000), 0.005, g / 1000, 200.0, 0.5) for g in (0.0, 2.5, 5.0, 10.0, 50.0)]
    assert [round(x, 2) for x in gains] == [24.02, 15.73, 11.65, 7.66, 2.04]
    assert round(SO.risk_gain(0.5, 0.005, 0.05, 200.0, 0.5), 2) == -18.43
    assert SO.risk_gain(0.5, 0.005, 0.005, 200.0, 0.5) == pytest.approx(SO.risk_gain(0.5, 0.005, 0.005, 200.0, 0.5))
    assert round(SO.ce_cara([200.0, 0.0], [0.5, 0.5], 0.005), 2) == 75.98 and "75,98" in README


def test_h6_risk_gain_needs_no_difference_of_estimates_and_leaves_expected_values_unchanged():
    """Beide legen p = ½ zugrunde; der Vertrag verschiebt nur Mittel-null-Zahlungen (Test in test_sources) und bringt trotzdem den Gewinn."""
    assert SO.risk_gain(1.0, 0.005, 0.0, 200.0, 0.5) > 24.0


# --- H7, H8 ----------------------------------------------------------------------------------------------------------------------------------
def test_h7_h8_numbers(wette_hand):
    h = wette_hand
    assert SO.bet_gain_subjective(h["pv"], h["ps"], h["bonus"]) == pytest.approx(30.0)
    for p in (0.4, 0.55, 0.7):
        a, b = SO.bet_sums(h["pv"], h["ps"], h["bonus"], p)
        assert a + b == 0
    has(row_of("H7"), "30,0", "15,0", "40 / 55 / 70 %", "in jedem Fall 0")
    assert round(SO.bet_gain_cara(100.0, 0.55, 0.55, 0.005), 2) == -12.25
    has(row_of("H8"), "250,0 Euro", "24,02 Euro", "55 %", "−12,25 Euro bei w = 100")


def test_h7_wager_size_and_quadratic_growth_text():
    sec = README.split("ist die Wette endlich")[1].split("**MESO**")[0]
    w = SO.bet_size_cara(0.4, 0.7, 0.005)
    has(sec, V.de(w, 1), V.de(SO.bet_gain_cara(w, 0.4, 0.7, 0.005), 2), "30,0")
    g = [SO.bet_gain_cara(SO.bet_size_cara(0.4, p, 0.005), 0.4, p, 0.005) for p in (0.5, 0.6, 0.7)]
    assert [round(x, 2) for x in g] == [2.03, 8.16, 19.08]
    # ungefähr quadratisch: Verdopplung des Abstands (0,1 → 0,2) vervierfacht den Gewinn ungefähr (2,03 → 8,16), 0,3 gibt das 9,4-fache
    assert 3.5 < g[1] / g[0] < 4.5


# --- H9 --------------------------------------------------------------------------------------------------------------------------------------
def test_h9_numbers_come_from_the_stored_meso_cells(meso):
    def c(est, k, r):
        return V._meso_cell(meso, est, k, r)["g_end"]["mean"]

    row = row_of("H9")
    pm = [c("Posterior-Mittel", k, 1) for k in (1, 2, 3, 5, 8)]
    has(row, *(V.de(x, 3) for x in pm), V.de(pm[1] - pm[0], 3), V.de(pm[4] - pm[2], 3), V.de(c("Posterior-Mittel", 8, 3), 3), V.de(c("Max-Rand", 2, 1), 3), V.de(meso["g_equal"]["mean"], 3))
    assert pm[1] - pm[0] > max(b - a for a, b in zip(pm[1:], pm[2:]))                 # der erste Zuwachs ist der größte
    assert c("Max-Rand", 2, 1) < meso["g_equal"]["mean"]
    better = {r: [k for k in C.MESO_KS if c("Max-Rand", k, r) > meso["g_equal"]["mean"]] for r in C.MESO_RS}
    assert min(better[1]) == 5 and min(better[2]) == 3 and min(better[3]) == 2
    assert pm[4] - pm[2] > 0.05                                                         # von drei auf acht Angebote bleibt mehr als ein Zehntel der Spanne übrig


def test_meso_text_numbers(meso):
    sec = README.split("**MESO** (Experiment E7")[1].split("**Brücke zum Verhandlungsstück**")[0]
    has(sec, V.de(meso["band_mean"], 1), f"kleinstes {meso['band_min']}", f"größtes {meso['band_max']}", f"in {meso['fallbacks']} von {V.thousands(meso['estimates'])} Schätzungen", "8 Blöcke zu je 500")
    assert meso["blocks"] == 8 and meso["instances_per_block"] == 500 and meso["skipped"] == 0
    has(README, V.de(meso["g_equal"]["mean"], 3) + " ± " + V.de(meso["g_equal"]["se"], 3))


def test_meso_at_k_equal_one_both_estimators_know_nothing(meso):
    """Bei k = 1 gibt es keine Wahl: Max-Rand ist gleiche Gewichte (g gleich der Grundlinie), das Posterior-Mittel das Mittel des Priors, das nicht genau ¼ je Punkt ist."""
    assert V._meso_cell(meso, "Max-Rand", 1, 1)["g_end"]["mean"] == pytest.approx(meso["g_equal"]["mean"], abs=1e-12)
    dev = np.abs(ME.PRIOR.mean(axis=0) - 0.25).max()
    assert 0 < dev < 0.002
    assert abs(V._meso_cell(meso, "Posterior-Mittel", 1, 1)["g_end"]["mean"] - meso["g_equal"]["mean"]) < 3 * meso["g_equal"]["se"]


def test_meso_comparison_with_the_plan_value_is_inside_noise(meso):
    """Plan: 0,654 aus 1.200 Instanzen; hier 8 × 500 mit Standardfehler 0,005: die Abweichung beträgt mehr als einen Standardfehler der Plan-Stichprobe (≈ 0,010) nicht um ein Vielfaches seiner eigenen Rundung."""
    assert abs(0.654 - meso["g_equal"]["mean"]) / 0.0105 < 4.0
    has(README, "0,654", "0,627", "0,625")


# --- H10 -------------------------------------------------------------------------------------------------------------------------------------
def test_h10_order_is_irrelevant_in_16000_of_16000_and_the_size_matters(grid):
    total = sum(c["same_order"]["mean"] for c in grid["e6"]) * grid["blocks"]
    assert total == 16000 and len(grid["e6"]) * grid["blocks"] * grid["instances_per_block"] == 16000
    has(row_of("H10"), "16.000 von 16.000")
    full = XP.find(grid["e6"], theta=1.0)
    assert full["drei und einer"]["mean"] < full["zwei Paare"]["mean"] < full["ein Paket"]["mean"]


# --- H11 -------------------------------------------------------------------------------------------------------------------------------------
def test_h11_bridge_holds_exactly_when_the_equilibrium_is_inside_the_price_stretch():
    w, u = XP.weights("bridge|probe", 200, 3)
    ms, dels = (0, 25, 50, 100, 200), [(0.9, 0.9), (0.8, 0.95), (0.6, 0.6), (0.99, 0.5)]
    total = hold = both = 0
    by_m = {m: 0 for m in ms}
    for i in range(200):
        v, s = tuple(int(round(100 * x)) for x in w[i]) + (0,), tuple(int(round(100 * x)) for x in u[i]) + (0,)
        for m in ms:
            view = V.analyse(Settings(v=v, s=s, price=m))
            for dv, ds in dels:
                b = V.bridge(view, dv, ds)
                holds = b["diff"] < 1e-6
                total += 1
                hold += holds
                both += holds == b["on_slope"]
                by_m[m] += holds
    assert (total, hold, both) == (4000, 1061, 4000)
    assert by_m[0] == 3 and by_m[200] == 458
    has(row_of("H11"), "1.061 von 4.000", "3 von 800", "458 von 800")


def test_bridge_hand_numbers_in_the_readme(hand2):
    sec = README.split("**Brücke zum Verhandlungsstück**")[1].split("## Ehrliche Grenzen")[0]
    rows = {}
    for m in (0, 10, 20):
        view = V.analyse(Settings(v=(80, 20, 0, 0), s=(30, 70, 0, 0), price=m))
        rows[m] = V.bridge(view, 0.9, 0.9)
    share = FR.rubinstein_share(0.9, 0.9)
    assert round(share, 3) == 0.526
    has(sec, V.de(rows[0]["p"][0], 1), V.de(rows[0]["t"], 0), V.de(rows[0]["t_split"][0], 1), V.de(rows[20]["p"][0], 1), V.de(rows[20]["t"], 0), V.de(rows[10]["p"][0], 1), V.de(rows[10]["t_split"][0], 1))
    assert not rows[0]["on_slope"] and not rows[10]["on_slope"] and rows[20]["on_slope"] and rows[20]["p"][0] == pytest.approx(170 * share)


# --- Korrekturen, Asymmetrie ------------------------------------------------------------------------------------------------------------------
def test_correction_threshold_with_ties_example():
    v, s = [F(70), F(20), F(10)], [F(30), F(20), F(50)]
    assert FR.m_star(v, s) == 0 and abs(sum(a for a, b in zip(v, s) if a > b) - sum(b for a, b in zip(v, s) if b > a)) == 20
    sec = README.split("## Befunde und Korrekturen")[1].split("## Modell")[0]
    has(sec, "M\\* = 0", "gäbe 20", "v = (70, 20, 10), s = (30, 20, 50)")


def test_correction_max_margin_has_12650_combinations_at_most():
    from math import comb
    assert comb(ME.N_POINTS + 21, ME.N_POINTS) == 12650 and 3 * (C.MESO_K_MAX - 1) == 21
    has(README, "12.650 Kombinationen")


def test_asymmetry_numbers_in_the_text(grid):
    c = XP.find(grid["asym"], theta=0.5)
    sec = README.split("**Warum bekommt der Verlader bei Nash mehr?**")[1].split("**Bündelgröße**")[0]
    has(sec, V.pct(c["share_v_peaky_e1"]["mean"], 1), V.de(c["diff_sym"]["mean"], 1) + " ± " + V.de(c["diff_sym"]["se"], 1), V.de(c["diff_sym_v_peaky"]["mean"], 1), V.de(-c["diff_sym_s_peaky"]["mean"], 1))
    assert c["diff_sym_v_peaky"]["mean"] > 0 > c["diff_sym_s_peaky"]["mean"] and abs(c["diff_sym"]["mean"]) < 0.5 < c["diff_e1"]["mean"]


def test_the_nash_asymmetry_column_of_e1_shows_the_verlader_ahead_for_theta_below_one(grid):
    for th in (0.1, 0.25, 0.5, 0.75):
        c = XP.find(grid["e1"], n=4, theta=th)
        assert c["nash_uv"]["mean"] > c["nash_us"]["mean"]
    c = XP.find(grid["e1"], n=4, theta=1.0)
    assert abs(c["nash_uv"]["mean"] - c["nash_us"]["mean"]) < 0.5


# --- Preset-Hilfen ---------------------------------------------------------------------------------------------------------------------------
def test_preset_help_numbers():
    h = C.PRESET_HELP
    std = h["Standard (drei Punkte, ohne Geld)"]
    v, s = [60.0, 25.0, 15.0], [20.0, 30.0, 50.0]
    assert FR.gain_sum(v, s) == 40.0 and sum(v) == sum(s) == 100.0
    has(std, "60, 25, 15", "20, 30, 50", "Summe 100", "40 Punkte")
    hand = h["Handbeispiel (zwei Punkte)"]
    verts = FR.frontier([F(80), F(20)], [F(30), F(70)])[0]
    assert verts == [(100, 0), (80, 70), (0, 100)] and FR.egalitarian(verts) == (F(800, 11), F(800, 11)) and round(float(F(800, 11)), 1) == 72.7
    has(hand, "(100; 0), (80; 70) und (0; 100)", "(80; 70)", "(72,7; 72,7) = (800/11; 800/11)")
    thr = h["Seitenzahlung bis zur Schwelle"]
    assert FR.m_star([F(80), F(20)], [F(30), F(70)]) == 10 and FR.max_sum(FR.frontier(*FR.with_price([F(80), F(20)], [F(30), F(70)], F(10)))[0]) == 160
    has(thr, "Preis-Spielraum 10 Euro", "M* = |80 − 70|", "160", "(80; 80)")
    lvl = h["Gleiches Profil, doppeltes Niveau"]
    has(lvl, "(40, 30, 10)", "(80, 60, 20)", "40 Euro", "200", "160")
    assert FR.gain_sum([40.0, 30.0, 10.0], [80.0, 60.0, 20.0]) == 40.0 and FR.m_star([40, 30, 10], [80, 60, 20]) == 160
    zeit = h["Zeit: Verlader ungeduldiger"]
    has(zeit, "1 %", "2 %", "1.000 Euro", "69,3 Tage", "250 Euro", "30 Tage bringen 192 Euro")
    risk = h["Risiko: nur der Spediteur scheut"]
    has(risk, "0,005", "24,02 Euro", "q = 100 %")
    assert C.PRESETS["Risiko: nur der Spediteur scheut"]["q"] == 100 and C.PRESETS["Zeit: Verlader ungeduldiger"]["term"] == 70
    assert SO.term_gain(70, 0.01, 0.02, 1000.0) == pytest.approx(250.0, abs=0.02)
    eq = h["Gleiche Einschätzung (kein Gewinn)"]
    has(eq, "55 %")
    meso_help = h["MESO: Max-Rand-Schätzer, zwei Angebote"]
    has(meso_help, "Zufalls-Seed 35")
    assert C.PRESETS["MESO: Max-Rand-Schätzer, zwei Angebote"] | {} == {**C.BASE, "k": 2, "r": 1, "est": "Max-Rand"}


def test_equal_weights_preset_reports_no_gain_and_equal_estimates_preset_reports_none():
    """§11a: ein Preset ohne Effekt darf keinen Effekt melden."""
    p = C.PRESETS["Gleiche Gewichte (kein Gewinn)"]
    st = Settings(v=(p["v1"], p["v2"], p["v3"], p["v4"]), s=(p["s1"], p["s2"], p["s3"], p["s4"]))
    assert V.verdict_trade(V.analyse(st))[0] == "warning"
    q = C.PRESETS["Gleiche Einschätzung (kein Gewinn)"]
    st = Settings(pv=q["pv"], ps=q["ps"])
    assert V.verdict_bet(V.bet_summary(st), st)[0] == "warning"


# --- Zahlen in den Texten der App ---------------------------------------------------------------------------------------------------------
def test_numbers_in_the_app_texts_are_the_model_constants():
    """Beschreibungen in app.py und vhg_texts.py nennen: Betrag 1.000 Euro, Gewinn 200 Euro mit Wahrscheinlichkeit ½, 4 Punkte mit 5 Stufen (625 Pakete), Band ±0,025, 4 Blöcke zu je 2.000 Instanzen, n = 4."""
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert C.AMOUNT == 1000.0 and C.RISK_A == 200.0 and C.RISK_P == 0.5 and C.E2_N == 4 and C.E6_N == 4 and C.GRID_BLOCKS == 4 and C.GRID_INSTANCES == 2000
    assert ME.N_POINTS == 4 and len(ME.LEVELS) == 5 and len(ME.PACKAGES) == 625 and ME.EPS_BAND == 0.025 and ME.PRIOR_DRAWS == 50_000
    has(app, "1.000 Euro", "200 Euro mit Wahrscheinlichkeit ½", "625 Pakete", "±0,025", "4 Blöcke zu je 2.000 Instanzen")
    has(T.ASSUMPTIONS_MARKDOWN, "4 Blöcke zu je 2.000 Instanzen", "4 Punkte mit 5 Stufen")
    assert C.TERM_MAX == 90 and "{C.TERM_MAX} Tage" in app and "Betrag von 1.000 Euro" in app


def test_quadratic_growth_of_the_best_wager_gain_in_the_difference_of_estimates():
    g = [SO.bet_gain_cara(SO.bet_size_cara(0.4, p, 0.005), 0.4, p, 0.005) for p in (0.5, 0.6, 0.7)]
    assert 3.5 < g[1] / g[0] < 4.5 and 8.5 < g[2] / g[0] < 10.0
