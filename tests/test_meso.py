"""Einheiten von vhg_meso an von Hand gerechneten Mini-Instanzen, Zweige und Randfälle."""

import numpy as np
import pytest

import vhg_meso as ME
from vhg_rng import uniform_block


def _idx(levels):
    """Index eines Pakets in PACKAGES (Stufen als Viererreihe)."""
    hits = np.where(np.all(np.isclose(ME.PACKAGES, levels), axis=1))[0]
    assert len(hits) == 1
    return int(hits[0])


def test_there_are_625_packages_with_five_levels_each():
    assert ME.PACKAGES.shape == (625, 4) and set(np.unique(ME.PACKAGES)) == set(ME.LEVELS)


def test_utilities_of_a_package_by_hand():
    # a = (0,4; 0,3; 0,2; 0,1), b = (0,1; 0,2; 0,3; 0,4), Paket x = (1; 0; 0,5; 0,25): U_A = 0,3 · 1 + 0,2 · 0,5 + 0,1 · 0,75 = 0,3 + 0,1 + 0,075 = 0,475 (Punkt 1 ganz an S: 0)
    a, b = np.array([0.4, 0.3, 0.2, 0.1]), np.array([0.1, 0.2, 0.3, 0.4])
    u_a, u_b = ME.utilities(a, b)
    i = _idx([1.0, 0.0, 0.5, 0.25])
    assert u_a[i] == pytest.approx(0.0 + 0.3 + 0.1 + 0.075)
    assert u_b[i] == pytest.approx(0.1 + 0.0 + 0.15 + 0.1)       # 0,1 · 1 + 0,3 · 0,5 + 0,4 · 0,25


def test_band_is_inclusive_and_symmetric():
    u = np.array([0.475, 0.5, 0.525, 0.4749, 0.5251])
    assert list(ME.band_of(u)) == [0, 1, 2]


def test_choose_takes_the_best_for_b_and_the_first_on_a_tie():
    u_b = np.zeros(len(ME.PACKAGES))
    u_b[[3, 7, 9]] = [0.2, 0.5, 0.5]
    assert ME.choose(np.array([3, 7, 9]), u_b) == 7
    assert ME.choose(np.array([3]), u_b) == 3


def test_constraints_from_a_choice_are_differences_to_the_not_chosen():
    offered, chosen = np.array([_idx([0, 0, 0, 0]), _idx([1, 0, 0, 0]), _idx([0, 1, 0, 0])]), _idx([1, 0, 0, 0])
    cons = ME.constraints_from_choice(offered, chosen)
    assert len(cons) == 2
    assert np.allclose(cons[0], [1, 0, 0, 0]) and np.allclose(cons[1], [1, -1, 0, 0])


def test_max_margin_one_constraint_puts_everything_on_the_largest_entry():
    # d = (0,25; −0,25; 0; 0,5): w·d >= t → größtes t = 0,5 bei w = (0; 0; 0; 1)
    w, t = ME.max_margin([np.array([0.25, -0.25, 0.0, 0.5])])
    assert t == pytest.approx(0.5) and np.allclose(w, [0, 0, 0, 1])


def test_max_margin_tie_gives_the_mean_of_the_optimal_corners():
    # d = (0,5; 0,5; −0,5; 0): zwei gleich gute Ecken (1,0,0,0) und (0,1,0,0), Mitte (0,5; 0,5; 0; 0), t = 0,5
    w, t = ME.max_margin([np.array([0.5, 0.5, -0.5, 0.0])])
    assert t == pytest.approx(0.5) and np.allclose(w, [0.5, 0.5, 0, 0])


def test_max_margin_two_constraints_balance_them():
    # d1 = (1; −1; 0; 0), d2 = (−1; 1; 0; 0): w·d1 = −w·d2, beste Lage w0 = w1 (t = 0): Ecken (0,5; 0,5; 0; 0), (0; 0; 1; 0), (0; 0; 0; 1) und alle Mischungen von w2, w3 mit w0 = w1 …
    # größtes t = 0; Mittel aller verschiedenen optimalen Ecken: (1/2,1/2,0,0), (0,0,1,0), (0,0,0,1) → (1/6, 1/6, 1/3, 1/3)
    w, t = ME.max_margin([np.array([1.0, -1.0, 0.0, 0.0]), np.array([-1.0, 1.0, 0.0, 0.0])])
    assert t == pytest.approx(0.0, abs=1e-9) and np.allclose(w, [1 / 6, 1 / 6, 1 / 3, 1 / 3])


def test_max_margin_without_constraints_is_the_equal_weighting():
    w, t = ME.max_margin([])
    assert np.allclose(w, 0.25) and t == 0.0


def test_posterior_without_constraints_is_the_prior_mean_close_to_equal():
    w, n = ME.posterior_mean([])
    assert n == ME.PRIOR_DRAWS and np.allclose(w, 0.25, atol=0.003) and w.sum() == pytest.approx(1.0)


def test_posterior_with_a_constraint_is_by_hand_a_conditional_mean():
    d = np.array([1.0, -1.0, 0.0, 0.0])                     # w0 >= w1
    w, n = ME.posterior_mean([d])
    sel = ME.PRIOR[ME.PRIOR @ d >= 0]
    assert n == len(sel) and np.allclose(w, sel.mean(axis=0)) and w[0] > w[1]
    assert 0.45 * ME.PRIOR_DRAWS < n < 0.55 * ME.PRIOR_DRAWS     # Spiegelsymmetrie: etwa die Hälfte


def test_posterior_returns_none_when_fewer_than_five_draws_match():
    cons = [np.array([1.0, -1.0, 0.0, 0.0]), np.array([-1.0, 1.0, 0.0, 0.0])]       # w0 = w1 genau: trifft nie
    w, n = ME.posterior_mean(cons)
    assert w is None and n == 0


def test_estimate_falls_back_on_max_margin_and_names_it():
    cons = [np.array([1.0, -1.0, 0.0, 0.0]), np.array([-1.0, 1.0, 0.0, 0.0])]
    w, used = ME.estimate(cons, "Posterior-Mittel")
    assert used == "Max-Rand (Rückfall)" and w.sum() == pytest.approx(1.0)
    assert ME.estimate([], "Max-Rand")[1] == "Max-Rand"
    with pytest.raises(ValueError):
        ME.estimate([], "Orakel")


def test_final_offer_takes_the_first_best_package_of_the_band():
    band = np.array([_idx([0, 0, 0, 0]), _idx([1, 0, 0, 0]), _idx([0, 0, 0, 1])])
    assert ME.final_offer(band, np.array([0.2, 0.3, 0.1, 0.4])) == band[2]
    assert ME.final_offer(band, np.array([0.25, 0.25, 0.25, 0.25])) == band[1]     # 0,25 · 1 beide Male; erstes im Band mit dem Höchstwert: Index 1 vor 2


def test_score_is_zero_for_the_mean_one_for_the_best_and_none_for_a_flat_band():
    u_b = np.zeros(len(ME.PACKAGES))
    band = np.array([0, 1, 2, 3])
    u_b[band] = [0.1, 0.2, 0.3, 0.4]
    assert ME.score(u_b, band, 3) == pytest.approx(1.0)
    assert ME.score(u_b, band, 0) == pytest.approx((0.1 - 0.25) / (0.4 - 0.25))
    assert ME.score(np.zeros(len(ME.PACKAGES)), band, 0) is None


def test_dirichlet_rows_equal_the_scalar_function():
    u = uniform_block(5, 8).reshape(2, 4)
    assert np.allclose(ME.dirichlet1(u[1]), (-np.log(1 - u[1])) / (-np.log(1 - u[1])).sum())
    assert ME.dirichlet1(u[0]).sum() == pytest.approx(1.0)


def test_instance_is_reproducible_and_the_band_has_enough_packages():
    a1, b1, o1 = ME.make_instance(35)
    a2, b2, o2 = ME.make_instance(35)
    assert np.array_equal(a1, a2) and np.array_equal(o1, o2)
    u_a, _ = ME.utilities(a1, b1)
    assert sorted(o1) == sorted(ME.band_of(u_a)) and len(o1) >= ME.MIN_BAND
    assert not np.array_equal(ME.make_instance(36)[0], a1)


def test_run_with_one_offer_has_no_information_and_equals_equal_weights():
    a, b, order = ME.make_instance(35)
    for est in ME.ESTIMATORS:
        res = ME.run(a, b, order, 1, 3, est)
        assert res["constraints"] == 0 and res["n_shown"] == 3
        assert np.allclose(res["w_hat"], 0.25, atol=0.003)


def test_run_counts_offers_and_constraints():
    a, b, order = ME.make_instance(35)
    res = ME.run(a, b, order, 3, 2, "Max-Rand")
    assert res["n_shown"] == 6 and res["constraints"] == 4 and len(res["log"]) == 2 and res["band_size"] == len(order)
    assert all(len(r["offered"]) == 3 and r["chosen"] in r["offered"] for r in res["log"])


def test_run_stops_offering_when_the_band_is_exhausted():
    a, b, order = ME.make_instance(35)
    res = ME.run(a, b, order[:5], 3, 3, "Max-Rand")
    assert res["n_shown"] == 5 and res["log"][2]["chosen"] is None


def test_the_two_estimators_differ_on_at_least_one_instance():
    diffs = 0
    for seed in range(1, 21):
        inst = ME.make_instance(seed)
        if inst is None:
            continue
        a, b, order = inst
        r1, r2 = ME.run(a, b, order, 2, 1, "Posterior-Mittel"), ME.run(a, b, order, 2, 1, "Max-Rand")
        diffs += not np.allclose(r1["w_hat"], r2["w_hat"])
    assert diffs > 0
