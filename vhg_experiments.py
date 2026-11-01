"""Messreihen: Zufallsinstanzen für den Tausch (E1, E2, E6) und die MESO-Simulation (E5), vorgerechnet in data/grid.json und data/meso.json.

Eine **Zelle** besteht aus `GRID_BLOCKS` unabhängigen Blöcken zu je `GRID_INSTANCES` Instanzen (MESO: `MESO_BLOCKS` Blöcke zu je `MESO_INSTANCES`); jeder Block hat einen eigenen
SplitMix64-Strom aus seiner Bezeichnung (`seed_of`, FNV-1a: Python-`hash` ist je Prozess gesalzen und taugt nicht). **Innerhalb eines Blocks sind die Gewichte für alle Zellen mit gleichem n
(E1) bzw. gleichem θ-unabhängigen Teil gleich**: der Gewinn ist je Instanz exakt linear in θ, und die Reihen sind nach θ gepaart. Ausgewiesen werden Mittel und Standardfehler der Blockwerte.
Die Dateien tragen den Hash der Quellen, aus denen sie stammen."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

import vhg_constants as C
import vhg_frontier as FR
import vhg_meso as ME
from vhg_rng import uniform_block

ROOT = Path(__file__).resolve().parent
GRID_FILE = ROOT / "data" / "grid.json"
MESO_FILE = ROOT / "data" / "meso.json"
HASHED_FILES = ("vhg_frontier.py", "vhg_meso.py", "vhg_experiments.py", "vhg_rng.py", "vhg_constants.py")
TOL = 1e-9
HASH_END = "# --- ab hier nicht mehr im Erzeuger-Hash"      # in vhg_constants.py: nur der Teil davor (Messparameter) gehört zum Hash


def seed_of(label: str) -> int:
    """64-Bit-Seed aus einer Bezeichnung (FNV-1a über die UTF-8-Bytes)."""
    h = 0xCBF29CE484222325
    for byte in label.encode("utf-8"):
        h = ((h ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def generator_hash() -> str:
    """Hash der Quelldateien, von denen die gespeicherten Messreihen abhängen (Zeilenenden vereinheitlicht)."""
    h = hashlib.sha256()
    for name in HASHED_FILES:
        text = (ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n")
        if name == "vhg_constants.py":
            text = text.split(HASH_END)[0]
        h.update(name.encode() + b"\0" + text.encode("utf-8") + b"\0")
    return h.hexdigest()[:16]


def dirichlet_rows(u: np.ndarray) -> np.ndarray:
    """Zeilenweise Dirichlet(1)-Gewichte (Summe 1) aus Gleichverteilten."""
    e = -np.log(1.0 - u)
    return e / e.sum(axis=1, keepdims=True)


def weights(label: str, count: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Zwei unabhängige Gewichtsblöcke (count × n) aus dem Strom der Bezeichnung: (w, u)."""
    u = uniform_block(seed_of(label), 2 * count * n).reshape(2, count, n)
    return dirichlet_rows(u[0]), dirichlet_rows(u[1])


def mix(w: np.ndarray, u: np.ndarray, theta: float) -> np.ndarray:
    """Gewichte des Spediteurs: (1 − θ)·w + θ·u (θ = Gewichtsunterschied; 0: gleiches Profil, 1: unabhängig)."""
    return (1.0 - theta) * w + theta * u


# --------------------------------------------------------------------------------- Kennzahlen einer Instanz
def trade_metrics(v: list[float], s: list[float], price: float = 0.0) -> dict:
    """Gewinn, Anteile des möglichen Gewinns an Nash/KS/egalitär, Nutzen bei Nash und die Regel M >= M*. `v`, `s` ohne Preis; `price` hängt den Preis-Punkt an."""
    vm, sm = (v, s) if price == 0 else FR.with_price(v, s, price)
    verts, _ = FR.frontier(vm, sm)
    mid = (sum(vm) + sum(sm)) / 2
    t_max = FR.max_sum(verts)
    g = t_max - mid
    p, k, e = FR.nash(verts), FR.kalai_smorodinsky(verts), FR.egalitarian(verts)
    out = {"gain": FR.gain_sum(v, s), "nash_uv": p[0], "nash_us": p[1], "t": t_max}
    if g > TOL:
        out["share_nash"] = (p[0] + p[1] - mid) / g
        out["share_ks"] = (k[0] + k[1] - mid) / g
        out["share_egal"] = (e[0] + e[1] - mid) / g
        nash_half = abs(p[0] - t_max / 2) < 1e-7 and abs(p[1] - t_max / 2) < 1e-7
        out["nash_half"] = nash_half
        out["rule_hit"] = nash_half == (price >= FR.m_star(v, s) - TOL)
        out["all3_equal"] = max(abs(p[0] - k[0]), abs(p[0] - e[0]), abs(p[1] - k[1]), abs(p[1] - e[1])) < 1e-7
        out["gap_nash"] = abs(p[0] - p[1])
    return out


def block_mean(rows: list[dict], key: str):
    vals = [r[key] for r in rows if key in r]
    return float(np.mean(vals)) if vals else None


def aggregate(blocks: list[dict]) -> dict:
    """Mittel und Standardfehler (Standardabweichung der Blockwerte durch √Blöcke) je Kennzahl."""
    out: dict = {"blocks": len(blocks)}
    for key in blocks[0]:
        vals = [b[key] for b in blocks]
        if any(x is None for x in vals):
            out[key] = {"mean": None, "se": None}
            continue
        arr = np.array(vals, dtype=float)
        out[key] = {"mean": float(arr.mean()), "se": float(arr.std(ddof=1) / math.sqrt(len(arr))) if len(arr) > 1 else 0.0}
    return out


KEYS = ("gain", "share_nash", "share_ks", "share_egal", "nash_uv", "nash_us", "nash_half", "rule_hit", "all3_equal", "gap_nash")


def _block_summary(rows: list[dict]) -> dict:
    out = {key: block_mean(rows, key) for key in KEYS}
    out["gain_small"] = float(np.mean([r["gain"] < 5.0 for r in rows]))
    out["n_gain"] = sum(1 for r in rows if "share_nash" in r)
    return out


# --------------------------------------------------------------------------------- E1 Tausch
def e1_block(n: int, theta: float, block: int, instances: int = C.GRID_INSTANCES) -> dict:
    w, u = weights(f"e1|n={n}|block={block}", instances, n)
    ws = mix(w, u, theta)
    rows = [trade_metrics(list(100.0 * w[i]), list(100.0 * ws[i])) for i in range(instances)]
    return _block_summary(rows)


def e1_symmetric_block(n: int, theta: float, block: int, instances: int = C.GRID_INSTANCES) -> dict:
    """Spiegel-Kontrolle zur Nash-Asymmetrie: beide Seiten mischen einen gemeinsamen Teil c mit je einem eigenen unabhängigen Teil (v = (1 − θ)c + θ·u₁, s = (1 − θ)c + θ·u₂)."""
    label = f"e1sym|n={n}|block={block}"
    u = uniform_block(seed_of(label), 3 * instances * n).reshape(3, instances, n)
    c, u1, u2 = (dirichlet_rows(x) for x in u)
    rows = [trade_metrics(list(100.0 * ((1 - theta) * c[i] + theta * u1[i])), list(100.0 * ((1 - theta) * c[i] + theta * u2[i]))) for i in range(instances)]
    return _block_summary(rows)


def concentration(w: np.ndarray) -> float:
    """Wie ungleich die Gewichte sind: Σ w² (gleiche Gewichte 1/n, ein einziger Punkt 1)."""
    return float((w ** 2).sum())


def asymmetry_block(theta: float, block: int, instances: int = C.GRID_INSTANCES, n: int = C.E2_N) -> dict:
    """Zur Asymmetrie der Nash-Lösung im Erzeuger von E1: mittlerer Nutzenabstand U_V − U_S bei Nash, aufgeteilt nach der Seite mit den ungleicheren Gewichten (größeres Σ w²), im Erzeuger von E1
    (V Dirichlet, S gemischt) und im symmetrischen Erzeuger (beide gemischt mit einem gemeinsamen Teil)."""
    out = {}
    w, u = weights(f"e1|n={n}|block={block}", instances, n)
    ws = mix(w, u, theta)
    raw = uniform_block(seed_of(f"e1sym|n={n}|block={block}"), 3 * instances * n).reshape(3, instances, n)
    c, u1, u2 = (dirichlet_rows(x) for x in raw)
    for tag, wv_all, ws_all in (("e1", w, ws), ("sym", (1 - theta) * c + theta * u1, (1 - theta) * c + theta * u2)):
        diffs, v_peaky = [], []
        for i in range(instances):
            p = FR.nash(FR.frontier(list(100.0 * wv_all[i]), list(100.0 * ws_all[i]))[0])
            diffs.append(p[0] - p[1])
            v_peaky.append(concentration(wv_all[i]) > concentration(ws_all[i]))
        d, vp = np.array(diffs), np.array(v_peaky)
        out[f"diff_{tag}"] = float(d.mean())
        out[f"share_v_peaky_{tag}"] = float(vp.mean())
        out[f"diff_{tag}_v_peaky"] = float(d[vp].mean()) if vp.any() else float("nan")
        out[f"diff_{tag}_s_peaky"] = float(d[~vp].mean()) if (~vp).any() else float("nan")
    return out


# --------------------------------------------------------------------------------- E2 Seitenzahlung
def e2_block(theta: float, price: float, block: int, level: float = 1.0, instances: int = C.GRID_INSTANCES) -> dict:
    n = C.E2_N
    w, u = weights(f"e2|block={block}", instances, n)
    ws = mix(w, u, theta)
    rows = [trade_metrics(list(100.0 * w[i]), list(level * 100.0 * ws[i]), price) for i in range(instances)]
    return _block_summary(rows)


# --------------------------------------------------------------------------------- E6 Bündelgröße
E6_PARTITIONS = {
    "vier Einzelpunkte": [[0], [1], [2], [3]],
    "zwei Paare": [[0, 1], [2, 3]],
    "zwei Paare, andere Reihenfolge": [[2, 3], [0, 1]],
    "drei und einer": [[0, 1, 2], [3]],
    "ein Paket": [[0, 1, 2, 3]],
}


def e6_block(theta: float, block: int, instances: int = C.GRID_INSTANCES) -> dict:
    n = C.E6_N
    w, u = weights(f"e6|block={block}", instances, n)
    ws = mix(w, u, theta)
    acc = {name: [] for name in E6_PARTITIONS}
    same_order = 0
    gains = []
    for i in range(instances):
        v, s = list(100.0 * w[i]), list(100.0 * ws[i])
        g = FR.gain_sum(v, s)
        gains.append(g)
        totals = {}
        for name, part in E6_PARTITIONS.items():
            a, b = FR.bundle_nash(v, s, part)
            totals[name] = a + b
            if g > TOL:
                acc[name].append((a + b - 100.0) / g)
        same_order += abs(totals["zwei Paare"] - totals["zwei Paare, andere Reihenfolge"]) < 1e-9
    out = {name: float(np.mean(vals)) for name, vals in acc.items()}
    out["gain"] = float(np.mean(gains))
    out["same_order"] = float(same_order)
    return out


# --------------------------------------------------------------------------------- Aufträge und Datei
def grid_jobs() -> list[tuple]:
    jobs = []
    for b in range(C.GRID_BLOCKS):
        for n in C.E1_NS:
            for th in C.E1_THETAS:
                jobs.append(("e1", n, th, b))
        for th in C.E1_THETAS:
            jobs.append(("e1sym", 4, th, b))
        for th in C.E2_THETAS:
            for m in C.E2_MS:
                jobs.append(("e2", th, m, b, 1.0))
        for m in C.E2_LEVEL_MS:
            jobs.append(("e2", 0.0, m, b, 2.0))
        for th in C.E6_THETAS:
            jobs.append(("e6", th, b))
        for th in C.ASYM_THETAS:
            jobs.append(("asym", th, b))
    return jobs


def run_grid_job(job: tuple):
    kind = job[0]
    if kind == "e1":
        return job, e1_block(job[1], job[2], job[3])
    if kind == "e1sym":
        return job, e1_symmetric_block(job[1], job[2], job[3])
    if kind == "e2":
        return job, e2_block(job[1], job[2], job[3], job[4])
    if kind == "e6":
        return job, e6_block(job[1], job[2])
    if kind == "asym":
        return job, asymmetry_block(job[1], job[2])
    raise ValueError(kind)


def assemble_grid(results: dict) -> dict:
    """Fasst die Blockergebnisse zu Zellen zusammen (Reihenfolge wie `grid_jobs`)."""
    cells: dict[str, list] = {"e1": [], "e1sym": [], "e2": [], "e6": [], "asym": []}
    seen = []
    for job in grid_jobs():
        key = _cell_key(job)
        if key not in seen:
            seen.append(key)
    for key in seen:
        blocks = [results[j] for j in grid_jobs() if _cell_key(j) == key]
        kind = key[0]
        if kind in ("e6", "asym"):
            cells[kind].append({"theta": key[1], **aggregate(blocks)})
        elif kind == "e2":
            cells["e2"].append({"theta": key[1], "price": key[2], "level": key[3], **aggregate(blocks)})
        else:
            cells[kind].append({"n": key[1], "theta": key[2], **aggregate(blocks)})
    return {"generator_hash": generator_hash(), "blocks": C.GRID_BLOCKS, "instances_per_block": C.GRID_INSTANCES, **cells}


def _cell_key(job: tuple) -> tuple:
    if job[0] in ("e1", "e1sym"):
        return (job[0], job[1], job[2])
    if job[0] == "e2":
        return ("e2", job[1], job[2], job[4])
    return (job[0], job[1])


def write_grid(payload: dict) -> None:
    GRID_FILE.parent.mkdir(exist_ok=True)
    GRID_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def load_grid() -> dict | None:
    """Die vorgerechneten Reihen; None, wenn die Datei fehlt oder zu anderem Rechencode gehört."""
    try:
        data = json.loads(GRID_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if data.get("generator_hash") == generator_hash() else None


def find(cells: list[dict], **spec) -> dict:
    """Die Zelle mit genau diesen Eigenschaften (Gleitkommazahlen mit Toleranz)."""
    for c in cells:
        if all(abs(c[k] - v) < 1e-9 if isinstance(v, float) else c[k] == v for k, v in spec.items()):
            return c
    raise KeyError(spec)


# --------------------------------------------------------------------------------- E5 MESO
def meso_instance_seed(block: int, i: int) -> int:
    return seed_of(f"meso|block={block}|i={i}")


def meso_block(block: int, instances: int = C.MESO_INSTANCES, ks=C.MESO_KS, rs=C.MESO_RS) -> dict:
    """Ein Block MESO-Instanzen: je (Schätzer, k, R) die Mittel von g_end, g_shown, Fehler der Schätzung, Zahl vorgelegter Pakete; dazu das Bandmaß und die Rückfälle."""
    acc: dict = {}
    base_g, base_err, bands, skipped, fallbacks, total_est = [], [], [], 0, 0, 0
    done, i = 0, 0
    while done < instances:
        inst = ME.make_instance(meso_instance_seed(block, i))
        i += 1
        if inst is None:
            skipped += 1
            continue
        a, b, order = inst
        u_a, u_b = ME.utilities(a, b)
        band = ME.band_of(u_a)
        g_eq = ME.score(u_b, band, ME.final_offer(band, np.full(ME.N_POINTS, 0.25)))
        if g_eq is None:
            skipped += 1
            continue
        done += 1
        bands.append(len(band))
        base_g.append(g_eq)
        base_err.append(float(0.5 * np.abs(np.full(ME.N_POINTS, 0.25) - b).sum()))
        for est in ME.ESTIMATORS:
            for k in ks:
                for r in rs:
                    res = ME.run(a, b, order, k, r, est)
                    if res["g_end"] is None:
                        continue
                    total_est += 1
                    fallbacks += res["estimator_used"].endswith("(Rückfall)")
                    cell = acc.setdefault((est, k, r), {"g_end": [], "g_shown": [], "error": [], "n_shown": []})
                    cell["g_end"].append(res["g_end"])
                    cell["g_shown"].append(res["g_shown"] if res["g_shown"] is not None else float("nan"))
                    cell["error"].append(res["error"])
                    cell["n_shown"].append(res["n_shown"])
    return {
        "cells": {f"{est}|{k}|{r}": {key: float(np.nanmean(vals)) for key, vals in cell.items()} for (est, k, r), cell in acc.items()},
        "g_equal": float(np.mean(base_g)), "err_equal": float(np.mean(base_err)), "band_mean": float(np.mean(bands)),
        "band_min": int(min(bands)), "band_max": int(max(bands)), "skipped": skipped, "fallbacks": fallbacks, "estimates": total_est,
    }


def assemble_meso(blocks: list[dict]) -> dict:
    cells = []
    for est in ME.ESTIMATORS:
        for k in C.MESO_KS:
            for r in C.MESO_RS:
                key = f"{est}|{k}|{r}"
                one = [b["cells"][key] for b in blocks]
                cells.append({"estimator": est, "k": k, "r": r, **aggregate(one)})
    return {
        "generator_hash": generator_hash(), "blocks": len(blocks), "instances_per_block": C.MESO_INSTANCES, "cells": cells,
        "g_equal": aggregate([{"g": b["g_equal"]} for b in blocks])["g"], "err_equal": aggregate([{"e": b["err_equal"]} for b in blocks])["e"],
        "band_mean": float(np.mean([b["band_mean"] for b in blocks])), "band_min": min(b["band_min"] for b in blocks), "band_max": max(b["band_max"] for b in blocks),
        "skipped": sum(b["skipped"] for b in blocks), "fallbacks": sum(b["fallbacks"] for b in blocks), "estimates": sum(b["estimates"] for b in blocks),
    }


def write_meso(payload: dict) -> None:
    MESO_FILE.parent.mkdir(exist_ok=True)
    MESO_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def load_meso() -> dict | None:
    try:
        data = json.loads(MESO_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if data.get("generator_hash") == generator_hash() else None
