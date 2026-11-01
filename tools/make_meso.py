"""Rechnet die MESO-Simulation (E5) neu und schreibt data/meso.json samt Erzeuger-Hash.

Aufruf (im Demo-Ordner, mit dem Test-venv):  python tools/make_meso.py [--workers 4]
Gleiche Hash-Regel wie bei tools/make_grid.py. Dauer: einige Minuten (8 Blöcke zu je 500 Instanzen, je Instanz 2 Schätzer × 7 Werte k × 3 Rundenstände)."""

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vhg_constants as C  # noqa: E402
import vhg_experiments as XP  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=C.MESO_BLOCKS)
    args = ap.parse_args()
    start = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        blocks = list(ex.map(XP.meso_block, range(C.MESO_BLOCKS)))
    payload = XP.assemble_meso(blocks)
    XP.write_meso(payload)
    print(f"geschrieben: {XP.MESO_FILE}  ({time.time() - start:.0f} s, Hash {XP.generator_hash()}, {payload['estimates']} Schätzungen, Rückfälle {payload['fallbacks']})")


if __name__ == "__main__":
    main()
