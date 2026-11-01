"""Einheiten von vhg_frontier an den von Hand gerechneten Mini-Instanzen, Randfälle, Eigenschaften und Zweige (DEMO-PLAYBOOK §1b)."""

import random
from fractions import Fraction as F

import pytest

import vhg_frontier as FR


def _ints(rng, n, total=100):
    cuts = sorted(rng.sample(range(1, total), n - 1))
    return [b - a for a, b in zip([0] + cuts, cuts + [total])]


def test_order_and_frontier_of_the_hand_instance(hand2):
    verts, idx = FR.frontier(hand2["v"], hand2["s"])
    assert idx == hand2["order"] and verts == hand2["verts"]


def test_solutions_of_the_hand_instance(hand2):
    verts = hand2["verts"]
    assert FR.nash(verts) == hand2["nash"]
    assert FR.kalai_smorodinsky(verts) == hand2["ks"]
    assert FR.egalitarian(verts) == hand2["egal"]
    assert FR.position_compromise(hand2["v"], hand2["s"]) == hand2["compromise"]


def test_gain_and_its_identity_on_the_hand_instance(hand2):
    assert FR.gain_sum(hand2["v"], hand2["s"]) == hand2["gain"] == FR.half_abs_difference(hand2["v"], hand2["s"])
    assert FR.max_sum(hand2["verts"]) == 150


def test_share_of_gain_on_the_hand_instance(hand2):
    # Nash (80; 70): Summe 150 = größte Summe → Anteil 1; Kalai–Smorodinsky: 1600/11 = 145,45; (145,45 − 100) / 50 = 0,909
    assert FR.share_of_gain(hand2["nash"], hand2["v"], hand2["s"]) == 1
    assert FR.share_of_gain(hand2["ks"], hand2["v"], hand2["s"]) == (F(1600, 11) - 100) / 50


def test_share_of_gain_is_none_without_gain():
    assert FR.share_of_gain((F(50), F(50)), [F(50), F(50)], [F(50), F(50)]) is None


def test_adjusted_winner_on_the_hand_instance(hand2):
    x, (uv, us), split = FR.adjusted_winner(hand2["v"], hand2["s"])
    assert x == hand2["x_aw"] and uv == us == F(800, 11) and split == 1


def test_adjusted_winner_wikipedia_example(wikipedia_aw):
    x, (a, b), split = FR.adjusted_winner(wikipedia_aw["v"], wikipedia_aw["s"])
    assert 1 - x[1] == wikipedia_aw["alice_share_good2"]
    assert a == b == wikipedia_aw["each"] and split == 1
    assert x[0] == 0 and x[2] == 1 and x[3] == 1


def test_adjusted_winner_cannot_equalize_when_the_totals_differ_too_much():
    """v = (100, 0), s = (0, 10): Anfang Punkt 0 an V (100), Punkt 1 an S (10); V liegt vorn, hat aber keinen Punkt, den S überhaupt bewertet: die Übertragung bricht ab, die Nutzen bleiben ungleich
    (der egalitäre Punkt der Grenze (10; 10) ist dagegen erreichbar)."""
    x, (a, b), split = FR.adjusted_winner([F(100), F(0)], [F(0), F(10)])
    assert (a, b) == (100, 10) and split == 0 and x == [0, 1]
    assert FR.egalitarian(FR.frontier([F(100), F(0)], [F(0), F(10)])[0]) == (10, 10)


def test_adjusted_winner_without_transfer_when_equal_from_the_start():
    x, (a, b), split = FR.adjusted_winner([F(60), F(40)], [F(40), F(60)])
    assert (a, b) == (60, 60) and x == [0, 1] and split == 0


def test_adjusted_winner_when_the_spediteur_leads():
    x, (a, b), split = FR.adjusted_winner([F(40), F(60)], [F(90), F(10)])
    # Anfang Punkt 0 an S (90 > 40), Punkt 1 an V (60 > 10): V 60, S 90; S liegt vorn; abgeben Punkt 0 ganz ginge nicht (0 < 100), also teilen: 90 − 90 f = 60 + 40 f, f = 30/130 = 3/13
    assert x == [1 - F(3, 13), 0] and a == b == 60 + 40 * F(3, 13) and split == 1


def test_m_star_of_the_hand_instance(hand2, hand_price):
    assert FR.m_star(hand2["v"], hand2["s"]) == hand2["m_star"] == abs(80 - 70)


@pytest.mark.parametrize("key,price", [("m5", 5), ("m10", 10), ("m20", 20)])
def test_nash_with_price_on_the_hand_instance(hand2, hand_price, key, price):
    v, s = FR.with_price(hand2["v"], hand2["s"], F(price))
    verts, _ = FR.frontier(v, s)
    point, total = hand_price[key]
    assert FR.nash(verts) == point and FR.max_sum(verts) == total


def test_price_segment_has_slope_minus_one_and_length_m(hand2):
    top, bottom = FR.price_segment(hand2["v"], hand2["s"], F(10))
    assert (top, bottom) == (90, 80)


def test_branch_nash_equals_ks_below_threshold_is_not_equal_to_half(hand2):
    """Zweig M < M*: Nash ist nicht die Hälfte der größten Summe; Zweig M >= M*: doch (beide Seiten der Schwelle laufen)."""
    for m, expect_half in ((F(9), False), (F(10), True), (F(11), True)):
        v, s = FR.with_price(hand2["v"], hand2["s"], m)
        verts, _ = FR.frontier(v, s)
        a, b = FR.nash(verts)
        t = FR.max_sum(verts)
        assert (a == b == t / 2) is expect_half, m


def test_branch_nash_differs_from_ks_on_at_least_one_instance():
    rng = random.Random(3)
    found = 0
    for _ in range(200):
        v, s = [F(x) for x in _ints(rng, 4)], [F(x) for x in _ints(rng, 4)]
        verts, _ = FR.frontier(v, s)
        found += FR.nash(verts) != FR.kalai_smorodinsky(verts)
    assert found > 0


def test_no_gain_branch_nash_is_the_compromise():
    v = [F(50), F(30), F(20)]
    verts, _ = FR.frontier(v, v)
    assert FR.nash(verts) == FR.position_compromise(v, v) == (50, 50) and FR.gain_sum(v, v) == 0


# --- Eigenschaften -------------------------------------------------------------------------------------------------------------------
def test_identity_gain_equals_half_the_summed_differences_exactly():
    rng = random.Random(11)
    for _ in range(300):
        n = rng.choice([2, 3, 4, 5, 6])
        v, s = [F(x) for x in _ints(rng, n)], [F(x) for x in _ints(rng, n)]
        verts, _ = FR.frontier(v, s)
        assert FR.max_sum(verts) - sum(FR.position_compromise(v, s)) == FR.half_abs_difference(v, s) == FR.gain_sum(v, s)


def test_gain_is_never_negative_even_with_unequal_totals():
    rng = random.Random(5)
    for _ in range(200):
        n = rng.choice([1, 2, 3, 4])
        v, s = [F(rng.randint(0, 100)) for _ in range(n)], [F(rng.randint(0, 100)) for _ in range(n)]
        assert FR.gain_sum(v, s) >= 0


def test_swapping_the_sides_swaps_the_solutions():
    rng = random.Random(8)
    for _ in range(100):
        n = rng.choice([2, 3, 4])
        v, s = [F(x) for x in _ints(rng, n)], [F(x) for x in _ints(rng, n)]
        a, b = FR.frontier(v, s)[0], FR.frontier(s, v)[0]
        for f in (FR.nash, FR.kalai_smorodinsky, FR.egalitarian):
            assert f(a) == f(b)[::-1]


def test_scaling_all_values_scales_the_solutions_and_keeps_the_shares():
    rng = random.Random(9)
    for _ in range(100):
        v, s = [F(x) for x in _ints(rng, 3)], [F(x) for x in _ints(rng, 3)]
        c = F(rng.randint(2, 9), rng.randint(2, 9))
        for f in (FR.nash, FR.kalai_smorodinsky, FR.egalitarian):
            p, q = f(FR.frontier(v, s)[0]), f(FR.frontier([c * x for x in v], [c * x for x in s])[0])
            assert q == (c * p[0], c * p[1])
        g = FR.gain_sum(v, s)
        if g > 0:
            p = FR.nash(FR.frontier(v, s)[0])
            q = FR.nash(FR.frontier([c * x for x in v], [c * x for x in s])[0])
            assert FR.share_of_gain(p, v, s) == FR.share_of_gain(q, [c * x for x in v], [c * x for x in s])


def test_positive_affine_rescaling_of_one_side_keeps_nash_and_ks_but_not_the_egalitarian_point():
    v, s = [F(80), F(20)], [F(30), F(70)]
    v2 = [3 * x for x in v]                       # Nutzen des Verladers in einer anderen Einheit
    a, b = FR.frontier(v, s)[0], FR.frontier(v2, s)[0]
    for f in (FR.nash, FR.kalai_smorodinsky):
        p, q = f(a), f(b)
        assert q == (3 * p[0], p[1])
    assert FR.egalitarian(b) != (3 * FR.egalitarian(a)[0], FR.egalitarian(a)[1])


def test_an_extra_price_point_keeps_the_absolute_gain():
    rng = random.Random(21)
    for _ in range(100):
        v, s = [F(x) for x in _ints(rng, 4)], [F(x) for x in _ints(rng, 4)]
        m = F(rng.randint(0, 200))
        vp, sp = FR.with_price(v, s, m)
        assert FR.gain_sum(vp, sp) == FR.gain_sum(v, s)


def test_normalize_gives_the_requested_total_and_keeps_zeros():
    assert FR.normalize([F(1), F(3)]) == [25, 75]
    assert FR.normalize([0, 0]) == [0, 0]


# --- Randfälle -----------------------------------------------------------------------------------------------------------------------
def test_single_point_frontier_is_one_segment():
    verts, idx = FR.frontier([F(60)], [F(40)])
    assert verts == [(60, 0), (0, 40)] and idx == [0]
    assert FR.nash(verts) == (30, 20)                      # Scheitel bei t = 1/2: (30; 20), Produkt 600


def test_exactly_two_points_with_equal_ratio_have_a_straight_frontier():
    verts, _ = FR.frontier([F(60), F(40)], [F(30), F(20)])
    assert verts == [(100, 0), (40, 30), (0, 50)]
    # beide Strecken liegen auf einer Geraden; Nash am Scheitel (50; 25) im Punkt t = 5/6 der ersten Strecke
    assert FR.nash(verts) == (50, 25)


def test_zero_valued_point_changes_nothing():
    base, _ = FR.frontier([F(80), F(20)], [F(30), F(70)])
    v, s = FR.with_price([F(80), F(20)], [F(30), F(70)], F(0))
    assert FR.frontier(v, s)[0][:3] == base and FR.frontier(v, s)[0][-1] == base[-1]
    assert FR.nash(FR.frontier(v, s)[0]) == FR.nash(base)


def test_all_zero_instance_is_defined():
    verts, _ = FR.frontier([F(0), F(0)], [F(0), F(0)])
    assert verts == [(0, 0)] * 3
    assert FR.nash(verts) == (0, 0) and FR.kalai_smorodinsky(verts) == (0, 0) and FR.egalitarian(verts) == (0, 0)
    assert FR.gain_sum([0, 0], [0, 0]) == 0


def test_one_side_values_nothing():
    verts, _ = FR.frontier([F(50), F(50)], [F(0), F(0)])
    assert verts[0] == (100, 0) and verts[-1] == (0, 0) and FR.max_sum(verts) == 100
    assert FR.nash(verts) == (100, 0)                       # Produkt überall 0, erste Ecke
    assert FR.egalitarian(verts) == (0, 0)


def test_floats_and_fractions_agree():
    v, s = [80.0, 20.0, 35.0], [30.0, 70.0, 5.0]
    vf, sf = [F(80), F(20), F(35)], [F(30), F(70), F(5)]
    for f in (FR.nash, FR.kalai_smorodinsky, FR.egalitarian):
        got, exact = f(FR.frontier(v, s)[0]), f(FR.frontier(vf, sf)[0])
        assert got == pytest.approx((float(exact[0]), float(exact[1])), rel=1e-12)


def test_frontier_value_interpolates_and_clamps(hand2):
    verts = hand2["verts"]
    assert FR.frontier_value(verts, F(90)) == 35               # Mitte der ersten Strecke (100 → 80, 0 → 70)
    assert FR.frontier_value(verts, F(100)) == 0
    assert FR.frontier_value(verts, F(80)) == 70
    assert FR.frontier_value(verts, F(0)) == 100
    assert FR.frontier_value(verts, F(40)) == 85               # Mitte der zweiten Strecke (80 → 0, 70 → 100)
    assert FR.frontier_value(verts, F(-5)) == 100 and FR.frontier_value(verts, F(500)) == 0


def test_bundle_partition_cases():
    assert FR.bundle_partition(4, 1) == [[0], [1], [2], [3]]
    assert FR.bundle_partition(4, 3) == [[0, 1, 2], [3]]
    assert FR.bundle_partition(3, 5) == [[0, 1, 2]]
    assert FR.bundle_partition(0, 2) == []
    with pytest.raises(ValueError):
        FR.bundle_partition(3, 0)


def test_bundle_nash_single_points_give_the_compromise_and_one_package_the_nash_point(hand2):
    v, s = hand2["v"], hand2["s"]
    assert FR.bundle_nash(v, s, FR.bundle_partition(2, 1)) == (50, 50)       # jeder Einzelpunkt: Mitte (x = 1/2)
    assert FR.bundle_nash(v, s, FR.bundle_partition(2, 2)) == hand2["nash"]


def test_bundle_nash_is_independent_of_the_bundle_order(hand2):
    v, s = [F(50), F(30), F(10), F(10)], [F(10), F(10), F(30), F(50)]
    a = FR.bundle_nash(v, s, [[0, 1], [2, 3]])
    b = FR.bundle_nash(v, s, [[2, 3], [0, 1]])
    assert a == b


def test_m_star_counts_tied_points_as_part_of_the_price_stretch():
    """v = (70, 20, 10), s = (30, 20, 50): Punkt 1 ist ein Gleichstand (20 = 20) und liegt wie ein Preis auf dem Stück mit Steigung −1. Ecken (100; 0), (90; 50), (70; 70), (0; 100):
    die größte Summe 140 wird schon ohne Geld bei (70; 70) hälftig geteilt, M* = max(0, |70 − 50| − 20) = 0 (die Formel ohne Gleichstände gäbe 20)."""
    v, s = [F(70), F(20), F(10)], [F(30), F(20), F(50)]
    verts, _ = FR.frontier(v, s)
    assert verts == [(100, 0), (90, 50), (70, 70), (0, 100)]
    assert FR.nash(verts) == (70, 70) and FR.m_star(v, s) == 0


def test_frontier_value_takes_the_top_of_stacked_vertical_segments():
    verts, _ = FR.frontier([F(0), F(0), F(10)], [F(5), F(7), F(3)])
    assert verts == [(10, 0), (10, 5), (10, 12), (0, 15)]            # Gleichstand beider unendlicher Verhältnisse: kleinere Nummer zuerst
    assert FR.frontier_value(verts, F(10)) == 12
