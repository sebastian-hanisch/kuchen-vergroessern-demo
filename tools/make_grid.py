"""Rechnet die Messreihen des Tauschs (E1 Gewinn und Lösungen, E2 Seitenzahlung, E6 Bündelgröße) neu und schreibt data/grid.json samt Erzeuger-Hash.

Aufruf (im Demo-Ordner, mit dem Test-venv):  python tools/make_grid.py [--workers 14]
Ändert sich vhg_frontier.py, vhg_meso.py, vhg_experiments.py, vhg_rng.py oder vhg_constants.py, stimmt der Hash nicht mehr (tests/test_measurements.py schlägt an, die App zeigt die Reihen dann nicht);
danach diesen Aufruf wiederholen. Jeder Block hat einen festen Zufalls-Seed aus seiner Bezeichnung (vhg_experiments.seed_of): die Reihen sind bei gleichem Code Zahl für Zahl dieselben, auch bei
anderer Zahl von Prozessen. Dauer: unter einer Minute."""

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vhg_experiments as XP  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()
    start = time.time()
    jobs = XP.grid_jobs()
    results = {}
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for job, res in ex.map(XP.run_grid_job, jobs, chunksize=2):
            results[job] = res
    payload = XP.assemble_grid(results)
    XP.write_grid(payload)
    print(f"geschrieben: {XP.GRID_FILE}  ({time.time() - start:.0f} s, Hash {XP.generator_hash()}, {len(jobs)} Aufträge)")


if __name__ == "__main__":
    main()
