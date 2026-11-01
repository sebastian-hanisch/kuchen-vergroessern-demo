"""Die vorgerechneten Messreihen (data/grid.json, data/meso.json) gehören zum aktuellen Rechencode und werden von der Rechnung reproduziert.

Eigene Datei, weil jede Änderung an vhg_frontier, vhg_meso, vhg_experiments, vhg_rng oder den Messparametern in vhg_constants den Erzeuger-Hash ändert. Reproduziert wird plattformsicher: einzelne Blöcke
neu gerechnet und mit dem gespeicherten Mittel der Zelle verglichen (die Blockwerte hängen nur vom Seed der Blockbezeichnung ab; eine Marge bleibt wegen unterschiedlicher Summationsreihenfolge)."""

import json

import pytest

import vhg_constants as C
import vhg_experiments as XP


@pytest.fixture(scope="module")
def grid():
    return json.loads(XP.GRID_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meso():
    return json.loads(XP.MESO_FILE.read_text(encoding="utf-8"))


def test_files_match_the_generator_hash(grid, meso):
    assert grid["generator_hash"] == XP.generator_hash() == meso["generator_hash"], "Quellcode geändert: python tools/make_grid.py und python tools/make_meso.py ausführen"
    assert XP.load_grid() is not None and XP.load_meso() is not None


def test_load_returns_none_for_a_stale_hash_and_for_a_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(XP, "generator_hash", lambda: "0000000000000000")
    assert XP.load_grid() is None and XP.load_meso() is None
    monkeypatch.undo()
    monkeypatch.setattr(XP, "GRID_FILE", tmp_path / "fehlt.json")
    monkeypatch.setattr(XP, "MESO_FILE", tmp_path / "fehlt.json")
    assert XP.load_grid() is None and XP.load_meso() is None


def test_hash_ignores_the_presets_part_of_the_constants():
    text = (XP.ROOT / "vhg_constants.py").read_text(encoding="utf-8")
    before, after = text.split(XP.HASH_END)
    assert "E1_NS" in before and "MESO_KS" in before and "PRESETS = {" in after and "PRESETS = {" not in before
    assert "MESO_KS" in text.split(XP.HASH_END)[0] and "PRESETS = {" in text.split(XP.HASH_END)[1]


def test_cells_match_the_code(grid):
    assert grid["blocks"] == C.GRID_BLOCKS and grid["instances_per_block"] == C.GRID_INSTANCES
    assert [(c["n"], c["theta"]) for c in grid["e1"]] == [(n, th) for n in C.E1_NS for th in C.E1_THETAS]
    assert [(c["theta"], c["price"], c["level"]) for c in grid["e2"]] == [(th, m, 1.0) for th in C.E2_THETAS for m in C.E2_MS] + [(0.0, m, 2.0) for m in C.E2_LEVEL_MS]
    assert [c["theta"] for c in grid["e6"]] == list(C.E6_THETAS) and [c["theta"] for c in grid["asym"]] == list(C.ASYM_THETAS)
    assert all(c["blocks"] == C.GRID_BLOCKS for key in ("e1", "e1sym", "e2", "e6", "asym") for c in grid[key])
    assert len(XP.grid_jobs()) == len(set(XP.grid_jobs())) == 236


def test_meso_cells_match_the_code(meso):
    assert meso["blocks"] == C.MESO_BLOCKS and meso["instances_per_block"] == C.MESO_INSTANCES
    assert [(c["estimator"], c["k"], c["r"]) for c in meso["cells"]] == [(e, k, r) for e in ("Posterior-Mittel", "Max-Rand") for k in C.MESO_KS for r in C.MESO_RS]
    assert meso["estimates"] == C.MESO_BLOCKS * C.MESO_INSTANCES * 2 * len(C.MESO_KS) * len(C.MESO_RS)
    assert meso["skipped"] == 0


def test_a_stored_e1_block_is_reproduced_by_the_code(grid):
    """Block 0 der Zelle (n = 3, θ = 0,5) neu gerechnet: liegt innerhalb der gespeicherten Blockstreuung der Zelle."""
    cell = XP.find(grid["e1"], n=3, theta=0.5)
    fresh = XP.e1_block(3, 0.5, 0)
    for key in ("gain", "share_nash", "share_ks"):
        assert abs(fresh[key] - cell[key]["mean"]) <= 6 * cell[key]["se"] * 2 + 1e-9


def test_the_whole_cell_is_reproduced_exactly_from_its_blocks(grid):
    cell = XP.find(grid["e2"], theta=1.0, level=1.0, price=25)
    blocks = [XP.e2_block(1.0, 25, b) for b in range(C.GRID_BLOCKS)]
    agg = XP.aggregate(blocks)
    for key in ("share_nash", "share_ks", "nash_half", "rule_hit"):
        assert agg[key]["mean"] == pytest.approx(cell[key]["mean"], abs=5e-4)       # plattformsicher: ein Entscheidungsfall von 8.000 verschöbe den Anteil um 1,25e-4


def test_a_stored_meso_block_is_reproduced_by_the_code(meso):
    """Block 0 der Zelle (Posterior-Mittel, k = 3, R = 1) mit allen 300 Instanzen neu gerechnet: weicht vom Mittel der vier gespeicherten Blöcke um höchstens 0,05 ab (Blockstreuung der Zelle rund 0,014)."""
    cell = next(c for c in meso["cells"] if c["estimator"] == "Posterior-Mittel" and c["k"] == 3 and c["r"] == 1)
    fresh = XP.meso_block(0, ks=(3,), rs=(1,))
    assert abs(fresh["cells"]["Posterior-Mittel|3|1"]["g_end"] - cell["g_end"]["mean"]) < 0.05
    assert fresh["estimates"] == C.MESO_INSTANCES * 2 and fresh["skipped"] == 0
