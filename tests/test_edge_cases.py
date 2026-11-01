"""Randfälle der Auswertung und der App (DEMO-PLAYBOOK §12, §1d): leere Menge von Punkten, ein Punkt, nur der Preis, Gleichstände, alle Regler an den Rändern, PDF."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import vhg_constants as C
import vhg_evaluation as V
import vhg_pdf_export as PDF
import vhg_presets as P
from vhg_scenario import Settings

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def test_no_point_and_no_price_is_defined_everywhere():
    st = Settings(v=(0, 0, 0, 0), s=(0, 0, 0, 0), price=0)
    view = V.analyse(st)
    assert view.names == [] and view.gain == 0 and view.t_max == 0 and view.nash == (0, 0) and view.aw is None and view.gain_normalized is None
    assert V.verdict_trade(view)[0] == "warning" and V.verdict_money(view)[0] == "warning" and V.verdict_hook(view)[0] == "info"
    assert V.solution_table(view)[0]["Anteil des möglichen Gewinns"] == "kein Gewinn möglich"
    assert V.bundle_table(st) == [] and V.price_curve(st, prices=[0, 10])[0]["share_nash"] is None
    assert V.verdict_bundle(st, V.bundle_rows(st))[0] == "warning"


def test_a_single_point_has_one_segment_and_the_nash_solution_in_the_middle():
    view = V.analyse(Settings(v=(60, 0, 0, 0), s=(40, 0, 0, 0)))
    assert view.names == ["Lieferfenster"] and view.nash == (30.0, 20.0) and view.gain == 10.0 and view.m_star == 60.0
    assert V.bundle_rows(Settings(v=(60, 0, 0, 0), s=(40, 0, 0, 0)))[0]["share"] == pytest.approx(0.0)


def test_only_a_price_gives_a_straight_frontier_and_the_half_split():
    view = V.analyse(Settings(v=(0, 0, 0, 0), s=(0, 0, 0, 0), price=80))
    assert view.names == [] and view.point_names() == ["Preis"] and view.t_max == 80 and view.nash == (40.0, 40.0) and view.gain == 0
    assert V.verdict_money(view)[0] == "success"


def test_ties_in_the_weights_and_equal_values_do_not_break_the_solutions():
    view = V.analyse(Settings(v=(50, 30, 20, 0), s=(50, 30, 20, 0), price=0))
    assert view.gain == 0 and view.nash == (50.0, 50.0) and view.ks == (50.0, 50.0) and view.egal == (50.0, 50.0) and view.aw[2] == 0
    assert view.m_star == 0                                                              # alle Punkte Gleichstand: Verlängerung des Preis-Stücks ist die ganze Grenze


def test_allocation_matches_the_solution_points():
    view = V.analyse(Settings(v=(80, 20, 0, 0), s=(30, 70, 0, 0)))
    x = V.allocation(view, view.nash)
    assert x == [0.0, 1.0] or x == pytest.approx([0.0, 1.0])                              # Nash (80; 70): Zwischenstand der Grenze, Punkt 2 an S, Punkt 1 an V
    x = V.allocation(view, view.ks)
    assert x == pytest.approx([1 / 11, 1.0])                                              # (800/11; 800/11): 1/11 von Punkt 1 an S
    assert V.allocation(view, (1.0, 1.0)) is None                                         # ein Punkt unter der Grenze


def test_pdf_is_a_pdf_and_survives_special_characters():
    st = Settings()
    view = V.analyse(st)
    data = PDF.build_pdf(st, view, [("a", "γ_S ≥ θ · Σ – „Anführung“ ½ ≈ ∈ ‰")])
    assert data[:5] == b"%PDF-" and len(data) > 1000


def _run(**values):
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in values.items():
        at.session_state[key] = value
    at.run()
    return at


@pytest.mark.parametrize("name", ["alle Minima", "alle Maxima", "alle Werte null", "nur Preis"])
def test_corner_matrix_over_all_sliders(name):
    values = {}
    for state_key, spec in P.SETTING_SPECS.items():
        if spec.choices is not None:
            values[state_key] = spec.choices[-1 if name == "alle Maxima" else 0]
        elif name == "alle Minima":
            values[state_key] = spec.lo
        elif name == "alle Maxima":
            values[state_key] = spec.hi
        elif state_key[:2] in ("v1", "v2", "v3", "v4", "s1", "s2", "s3", "s4") and name in ("alle Werte null", "nur Preis"):
            values[state_key] = 0
        elif state_key == "price_slider" and name == "nur Preis":
            values[state_key] = C.PRICE_MAX
    at = _run(**values)
    assert not at.exception, (name, [str(e) for e in at.exception])


def test_every_preset_runs_and_each_shows_its_verdicts():
    for name in C.PRESETS:
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
        at.run()
        at.sidebar.button(key=f"preset_{name}").click().run()
        assert not at.exception, name
        assert len(at.success) + len(at.info) + len(at.warning) >= 8, name


def test_pdf_button_builds_a_download():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    next(b for b in at.button if b.key == "pdf_button").click().run()
    assert not at.exception and at.session_state["pdf_bytes"][:5] == b"%PDF-"


def test_permalink_values_are_clipped_to_the_slider_bounds():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["preis"] = "99999"
    at.query_params["schaetzer"] = "unsinn"
    at.query_params["rs"] = "nan"
    at.run()
    assert not at.exception
    assert at.session_state["price_slider"] == C.PRICE_MAX and at.session_state["est_select"] == "Posterior-Mittel" and at.session_state["rs_slider"] == C.DEFAULT_RS
