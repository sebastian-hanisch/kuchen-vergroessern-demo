"""Einheiten von vhg_sources (Zeit, Risiko, Einschätzung) an den Handbeispielen, Zweige und Randfälle."""

import math

import pytest

import vhg_sources as SO


# --- Zeit ----------------------------------------------------------------------------------------------------------------------------
def test_term_optimum_and_gain_on_the_hand_instance(zeit_hand):
    z = zeit_hand
    d = SO.term_optimum(z["rs"], z["rv"])
    assert d == pytest.approx(z["d_star"], rel=1e-12) and d == pytest.approx(math.log(2) / 0.01, rel=1e-12)
    assert SO.term_gain(d, z["rs"], z["rv"], z["b"]) == pytest.approx(z["f_star"], rel=1e-12)
    assert SO.term_gain(30, z["rs"], z["rv"], z["b"]) == pytest.approx(z["f30"], abs=1e-3)


def test_term_gain_at_zero_days_is_zero_and_linear_overstates_the_middle(zeit_hand):
    z = zeit_hand
    assert SO.term_gain(0, z["rs"], z["rv"], z["b"]) == 0
    assert SO.term_gain_linear(30, z["rs"], z["rv"], z["b"]) == pytest.approx(300.0)      # 1000 · 0,01 · 30
    assert SO.term_gain(30, z["rs"], z["rv"], z["b"]) < 300.0


def test_branch_equal_rates_have_no_gain_and_no_optimum():
    assert SO.term_gain(45, 0.01, 0.01, 1000.0) == 0
    assert SO.term_optimum(0.01, 0.01) is None
    assert SO.best_term(0.01, 0.01, 90) == 0


def test_branch_patient_payer_loses_with_a_term():
    assert SO.term_gain(30, 0.02, 0.01, 1000.0) == pytest.approx(-192.0058, abs=1e-3)       # Vorzeichen gedreht
    assert SO.term_optimum(0.02, 0.01) is None and SO.best_term(0.02, 0.01, 90) == 0


def test_best_term_is_capped_at_the_maximum_and_without_optimum_for_zero_rate():
    assert SO.best_term(0.01, 0.02, 90) == pytest.approx(69.3147, abs=1e-4)
    assert SO.best_term(0.01, 0.02, 40) == 40
    assert SO.term_optimum(0.0, 0.02) is None and SO.best_term(0.0, 0.02, 90) == 90        # f wächst bis zur Grenze


# --- Risiko --------------------------------------------------------------------------------------------------------------------------
def test_ce_cara_of_a_sure_amount_is_the_amount_and_neutral_is_the_mean():
    assert SO.ce_cara([50.0, 50.0], [0.5, 0.5], 0.01) == pytest.approx(50.0, rel=1e-12)
    assert SO.ce_cara([200.0, 0.0], [0.5, 0.5], 0.0) == 100.0


def test_risk_gain_full_transfer_on_the_hand_instance(risiko_hand):
    h = risiko_hand
    assert SO.ce_cara([200.0, 0.0], [0.5, 0.5], h["gs"]) == pytest.approx(75.977, abs=1e-3)
    assert SO.risk_gain(1.0, h["gs"], 0.0, h["a"], h["p"]) == pytest.approx(h["gain_full"], abs=1e-3)
    assert SO.risk_share(h["gs"], 0.0) == 1.0
    assert SO.risk_share(0.005, 0.0025) == pytest.approx(h["q_half_vs"])


def test_risk_gain_is_zero_without_contract_and_when_both_neutral(risiko_hand):
    h = risiko_hand
    assert SO.risk_gain(0.0, h["gs"], 0.01, h["a"], h["p"]) == 0.0
    assert SO.risk_gain(0.7, 0.0, 0.0, h["a"], h["p"]) == pytest.approx(0.0, abs=1e-12)
    assert SO.risk_share(0.0, 0.0) is None


def test_risk_expected_values_do_not_change(risiko_hand):
    """Der Vertrag verschiebt keinen Erwartungswert: V zahlt q·(E − Gewinn), Mittel 0."""
    a, p, q = 200.0, 0.5, 0.3
    mean = p * a
    inc_s = [x + q * (mean - x) for x in (a, 0.0)]
    assert p * inc_s[0] + (1 - p) * inc_s[1] == pytest.approx(mean)


def test_half_and_half_risk_is_only_best_when_equally_averse(risiko_hand):
    h = risiko_hand
    at_half = SO.risk_gain(0.5, 0.005, 0.005, h["a"], h["p"])
    assert at_half == pytest.approx(SO.risk_gain(SO.risk_share(0.005, 0.005), 0.005, 0.005, h["a"], h["p"]), rel=1e-12)
    assert SO.risk_gain(0.5, 0.005, 0.0025, h["a"], h["p"]) < SO.risk_gain(2 / 3, 0.005, 0.0025, h["a"], h["p"])
    assert SO.risk_gain(0.5, 0.005, 0.05, h["a"], h["p"]) < 0                     # Halbe-halbe kann sogar kosten


# --- Einschätzung --------------------------------------------------------------------------------------------------------------------
def test_bet_subjective_and_common_probability_on_the_hand_instance(wette_hand):
    h = wette_hand
    assert SO.bet_gain_subjective(h["pv"], h["ps"], h["bonus"]) == pytest.approx(30.0)
    for p_common, expect in ((0.4, -15.0), (0.55, 0.0), (0.7, 15.0)):
        high, low = SO.bet_sums(h["pv"], h["ps"], h["bonus"], p_common)
        assert high == pytest.approx(expect, abs=1e-9) and high + low == 0
    hind = SO.bet_hindsight(h["pv"], h["ps"], h["bonus"])
    assert hind["high_in_high"] == pytest.approx(45.0) and hind["high_in_low"] == pytest.approx(-55.0)


def test_bet_with_equal_estimates_has_no_subjective_gain_and_no_best_size(wette_hand):
    assert SO.bet_gain_subjective(0.55, 0.55, 100.0) == 0
    assert SO.bet_size_cara(0.55, 0.55, 0.005) is None
    assert SO.bet_gain_cara(100.0, 0.55, 0.55, 0.005) < 0                                    # jede Wette kostet Sicherheitsäquivalent
    assert SO.bet_gain_cara(0.0, 0.55, 0.55, 0.005) == 0


def test_bet_best_size_on_the_hand_instance(wette_hand):
    h = wette_hand
    assert SO.odds_ratio(0.4, 0.7) == pytest.approx(3.5)
    w = SO.bet_size_cara(h["pv"], h["ps"], h["gamma"])
    assert w == pytest.approx(math.log(3.5) / 0.01) == pytest.approx(h["w_star"], abs=1e-3)
    assert SO.bet_gain_cara(w, h["pv"], h["ps"], h["gamma"]) > SO.bet_gain_cara(0.8 * w, h["pv"], h["ps"], h["gamma"])
    assert SO.bet_gain_cara(w, h["pv"], h["ps"], h["gamma"]) > SO.bet_gain_cara(1.2 * w, h["pv"], h["ps"], h["gamma"])


def test_bet_is_symmetric_in_the_two_sides():
    assert SO.bet_size_cara(0.4, 0.7, 0.005) == SO.bet_size_cara(0.7, 0.4, 0.005)
    assert SO.bet_gain_cara(80.0, 0.4, 0.7, 0.005) == SO.bet_gain_cara(80.0, 0.7, 0.4, 0.005)


def test_bet_size_is_none_for_neutral_and_for_boundary_probabilities():
    assert SO.bet_size_cara(0.4, 0.7, 0.0) is None
    assert SO.bet_size_cara(0.0, 0.7, 0.005) is None
    assert SO.bet_size_cara(0.4, 1.0, 0.005) is None
