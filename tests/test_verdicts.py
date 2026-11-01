"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Die Verdikte sind reine Funktionen (Art, Text) in `vhg_evaluation.py`. Die Handinstanz ist v = (80, 20), s = (30, 70): Gewinn 50, größte Summe 150, Nash (80; 70), Kalai–Smorodinsky 1600/11 = 145,45 in der Summe,
also (145,45 − 100) / 50 = 90,9 % des möglichen Gewinns."""

import vhg_evaluation as V
from vhg_scenario import Settings

HAND = dict(v=(80, 20, 0, 0), s=(30, 70, 0, 0))


def _view(**kw):
    return V.analyse(Settings(**{**HAND, **kw}))


def test_trade_verdict_with_gain_names_gain_sums_and_shares():
    kind, text = V.verdict_trade(_view())
    assert kind == "success"
    assert "**Gewinn des Tauschs: 50,0**" in text and "größte Summe 150,0 statt 100,0" in text
    assert "Nash-Lösung erreicht 100,0 % davon, Kalai–Smorodinsky 90,9 %" in text


def test_trade_verdict_without_gain_is_a_warning_and_claims_no_effect():
    kind, text = V.verdict_trade(_view(v=(50, 30, 0, 0), s=(50, 30, 0, 0)))
    assert kind == "warning" and "Kein Tauschgewinn" in text and "80,0" in text and "Gewinn des Tauschs" not in text


def test_hook_verdict_equal_totals_and_unequal_totals():
    assert "dieselbe Gesamtbewertung (100): der Gewinn in Euro (50,0) und der Gewinn bei auf je 100 normierten Gewichten (50,0) stimmen überein" in V.verdict_hook(_view())[1]
    text = V.verdict_hook(V.analyse(Settings(v=(40, 30, 10, 0), s=(80, 60, 20, 0))))[1]       # gleiches Profil, doppeltes Niveau: Euro 40, normiert 0
    assert "Verlader 80, Spediteur 160" in text and "in Euro beträgt der Gewinn 40,0, bei auf je 100 normierten Gewichten 0,0" in text and "Niveau, nicht aus dem Profil" in text


def test_money_verdict_threshold_is_inclusive_at_m_star():
    kind, text = V.verdict_money(_view(price=10))               # M* = |80 − 70| = 10: genau auf der Schwelle
    assert kind == "success" and "Schwelle M* = 10" in text and "hälftig, 80,0 und 80,0" in text and "Kalai–Smorodinsky und egalitär fallen nur bei gleichen" not in text
    kind, text = V.verdict_money(_view(price=9))
    assert kind == "info" and "liegt unter der Schwelle M* = 10" in text and "Abstand der Nutzen ist" in text
    # Ungleiche Gesamtwerte: der Zusatz über Kalai–Smorodinsky erscheint
    assert "nur bei gleichen Gesamtbewertungen" in V.verdict_money(V.analyse(Settings(v=(40, 30, 0, 0), s=(80, 60, 0, 0), price=200)))[1]


def test_money_verdict_without_gain_and_without_money_is_a_warning():
    assert V.verdict_money(_view(v=(50, 50, 0, 0), s=(50, 50, 0, 0)))[0] == "warning"


def test_bundle_verdict_names_the_size_and_the_bounds():
    st = Settings(**{**HAND, "bundle": 1})
    kind, text = V.verdict_bundle(st, V.bundle_rows(st))
    assert kind == "info" and "Bündelgröße 1 von 2 Punkten: 0,0 %" in text and "ein Paket 100,0 %" in text
    st = Settings(**{**HAND, "bundle": 4})                     # größer als die Punktzahl: ein Paket
    assert "Bündelgröße 2 von 2 Punkten: 100,0 %" in V.verdict_bundle(st, V.bundle_rows(st))[1]
    flat = Settings(v=(50, 50, 0, 0), s=(50, 50, 0, 0))
    assert V.verdict_bundle(flat, V.bundle_rows(flat))[0] == "warning"


def test_bridge_verdict_on_a_straight_frontier_and_below_the_slack():
    view = V.analyse(Settings(v=(0, 0, 0, 0), s=(0, 0, 0, 0), price=100))     # nur der Preis: Gerade U_V + U_S = 100
    kind, text = V.verdict_bridge(V.bridge(view, 0.9, 0.9), 0.9, 0.9)
    assert kind == "success" and "52,6 von 100,0" in text and "100,0 · 0,526" in text
    kind, text = V.verdict_bridge(V.bridge(_view(), 0.9, 0.9), 0.9, 0.9)           # ohne Geld: keine Gerade
    assert kind == "info" and "zu wenig Spielraum" in text


def test_time_verdict_branches():
    base = dict(rs=1.0, rv=2.0, term=30)
    kind, text = V.verdict_time(V.term_summary(Settings(**base)))
    assert kind == "success" and "d* = 69,3 Tage mit 250,0 Euro" in text and "30 Tagen sind es 192,0 Euro" in text and "ergäbe 300,0" in text
    kind, text = V.verdict_time(V.term_summary(Settings(rs=2.0, rv=2.0, term=30)))
    assert kind == "warning" and "Gleiche Ungeduld (2,00 % je Tag)" in text and "0,0 Euro" in text
    kind, text = V.verdict_time(V.term_summary(Settings(rs=2.0, rv=1.0, term=30)))
    assert kind == "warning" and "kostet gemeinsam, nach 30 Tagen 192,0 Euro" in text
    kind, text = V.verdict_time(V.term_summary(Settings(rs=0.0, rv=1.0, term=30)))
    assert kind == "info" and "Obergrenze von 90 Tagen" in text


def test_risk_verdict_branches():
    kind, text = V.verdict_risk(V.risk_summary(Settings(gs=5.0, gv=0.0, q=100)))
    assert kind == "success" and "q* = γ_S / (γ_S + γ_V) = 100,0 %" in text and "Gewinn 24,02 Euro" in text and "das gewählte q = 100 % bringt 24,02" in text
    kind, text = V.verdict_risk(V.risk_summary(Settings(gs=0.0, gv=0.0, q=50)))
    assert kind == "warning" and "risikoneutral" in text


def test_bet_verdict_branches():
    kind, text = V.verdict_bet(V.bet_summary(Settings(pv=0.4, ps=0.7, bonus=100)), Settings(pv=0.4, ps=0.7, bonus=100))
    assert kind == "info" and "gewinnt jede 15,0 Euro je Tour, zusammen 30,0" in text and "bei 55 % ist der Erwartungswert der Seite mit der höheren Einschätzung 0,0 Euro" in text
    assert "bei 40 % ist der Erwartungswert der Seite mit der höheren Einschätzung −15,0 Euro" in text
    st = Settings(pv=0.55, ps=0.55, bonus=100, gb=5.0)
    kind, text = V.verdict_bet(V.bet_summary(st), st)
    assert kind == "warning" and "Gleiche Einschätzung (55 %)" in text and "kostet die Wette der Größe 100 sogar 12,25 Euro" in text


def test_bet_cara_verdict_branches():
    kind, text = V.verdict_bet_cara(V.bet_summary(Settings(pv=0.4, ps=0.7, bonus=100, gb=5.0)))
    assert kind == "success" and "w* = ln(3,50) / (2γ) = 125,3 Euro" in text and "Gewinn 19,08 Euro" in text
    assert V.verdict_bet_cara(V.bet_summary(Settings(pv=0.5, ps=0.5)))[0] == "warning"


def _cell(est, k, r, g):
    return {"estimator": est, "k": k, "r": r, "g_end": {"mean": g, "se": 0.0}}


def test_meso_verdict_names_the_jump_and_the_bad_estimator():
    cells = [_cell("Posterior-Mittel", k, 1, g) for k, g in ((1, 0.62), (2, 0.74), (3, 0.80), (5, 0.855), (8, 0.90))] + [_cell("Max-Rand", 2, 1, 0.29)]
    cells += [_cell("Posterior-Mittel", k, 1, 0.9) for k in (4, 6)]
    kind, text = V.verdict_meso({"cells": cells, "g_equal": {"mean": 0.60, "se": 0.01}})
    assert kind == "info" and "von 0,620 (ein Angebot) auf 0,740 (zwei), 0,800 (drei), 0,855 (fünf) und 0,900 (acht)" in text
    assert "zwei Angebote 0,290, schlechter als gleiche Gewichte als Schätzung (0,600)" in text


def test_meso_live_verdict_branches():
    assert V.verdict_meso_live(None)[0] == "warning"
    assert V.verdict_meso_live({"g_end": None})[0] == "warning"
    kind, text = V.verdict_meso_live({"g_end": 0.5, "error": 0.2, "error_equal": 0.3, "n_shown": 6, "band_size": 50, "constraints": 4})
    assert kind == "info" and "Güte g = 0,500" in text and "Fehler der Schätzung der Gewichte ist 0,200" in text and "hätten 0,300" in text and "6 von 50 Paketen" in text and "4 Wahl-Ungleichungen" in text


def test_number_formats():
    assert V.de(-0.0004, 2) == "0,00" and V.de(-1.5, 1) == "−1,5" and V.pct(0.1234, 1) == "12,3 %" and V.thousands(8000) == "8.000"
