"""Auswertung: Kennzahlen der Einstellungen, Zeilenbauer der Tabellen und die Verdikte (reine Funktionen `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`)."""

from __future__ import annotations

from dataclasses import dataclass

import vhg_constants as C
import vhg_experiments as XP
import vhg_frontier as FR
import vhg_meso as ME
import vhg_sources as SO
from vhg_scenario import Settings, effective_bundle, point_values

TOL = 1e-9


# --------------------------------------------------------------------------------- Formate
def de(x: float, nd: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und echtem Minuszeichen (−)."""
    text = f"{x:.{nd}f}"
    if float(text) == 0.0:
        text = text.lstrip("-")
    return text.replace(".", ",").replace("-", "−")


def pct(x: float, nd: int = 1) -> str:
    """Anteil als Prozentzahl mit Komma und Leerzeichen vor dem Prozentzeichen."""
    return f"{de(100.0 * x, nd)} %"


def thousands(n: float) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def mean_se(c: dict, key: str, nd: int = 3, percent: bool = False) -> str:
    """Mittel ± Standardfehler einer Zelle als Text; fehlt der Wert (Zelle ohne Gewinn), ein Strich."""
    m = c[key]["mean"]
    if m is None:
        return "–"
    if percent:
        return f"{de(100 * m, nd)} ± {de(100 * c[key]['se'], nd)} %"
    return f"{de(m, nd)} ± {de(c[key]['se'], nd)}"


# --------------------------------------------------------------------------------- Tausch (live)
@dataclass(frozen=True)
class TradeView:
    names: list
    v: list
    s: list
    price: float
    vp: list                    # mit Preis-Punkt (falls price > 0)
    sp: list
    verts: list
    order: list
    gain: float
    compromise: tuple
    t_max: float
    nash: tuple
    ks: tuple
    egal: tuple
    aw: tuple | None            # (x, (U_V, U_S), geteilt) auf je Seite auf 100 normierten Gewichten (ohne Preis), sonst None
    m_star: float
    gain_normalized: float | None

    def point_names(self) -> list:
        return self.names + (["Preis"] if self.price > 0 else [])


def analyse(st: Settings) -> TradeView:
    v, s, names = point_values(st)
    vp, sp = (v, s) if st.price == 0 else FR.with_price(v, s, float(st.price))
    verts, order = FR.frontier(vp, sp)
    aw = None
    gain_norm = None
    if sum(v) > 0 and sum(s) > 0:
        vn, sn = FR.normalize(v), FR.normalize(s)
        gain_norm = FR.gain_sum(vn, sn)
        aw = FR.adjusted_winner(vn, sn)
    return TradeView(
        names=names, v=v, s=s, price=float(st.price), vp=vp, sp=sp, verts=verts, order=order,
        gain=FR.gain_sum(v, s), compromise=FR.position_compromise(vp, sp), t_max=FR.max_sum(verts),
        nash=FR.nash(verts), ks=FR.kalai_smorodinsky(verts), egal=FR.egalitarian(verts), aw=aw,
        m_star=FR.m_star(v, s), gain_normalized=gain_norm,
    )


def allocation(view: TradeView, point: tuple) -> list[float] | None:
    """Stellung x_i je Punkt (Anteil, der an S geht) für einen Punkt auf der Grenze; None, wenn der Punkt nicht auf der Grenze liegt (Toleranz)."""
    for k in range(len(view.verts) - 1):
        (a1, b1), (a2, b2) = view.verts[k], view.verts[k + 1]
        da, db = a2 - a1, b2 - b1
        if da != 0:
            t = (point[0] - a1) / da
        elif db != 0:
            t = (point[1] - b1) / db
        else:
            t = 0.0
        if -1e-9 <= t <= 1 + 1e-9 and abs(a1 + t * da - point[0]) < 1e-7 and abs(b1 + t * db - point[1]) < 1e-7:
            t = min(max(t, 0.0), 1.0)
            x = [0.0] * len(view.vp)
            for j, i in enumerate(view.order):
                if j < k:
                    x[i] = 1.0
                elif j == k:
                    x[i] = t
            return x
    return None


def solution_rows(view: TradeView) -> list[dict]:
    """Eine Zeile je Lösung: Nutzen, Summe, Anteil des möglichen Gewinns, Stellung der Punkte."""
    mid = sum(view.compromise)
    rows = []
    entries = [("Positionskompromiss (jeder Punkt in der Mitte)", view.compromise), ("Nash-Lösung", view.nash), ("Kalai–Smorodinsky", view.ks), ("Egalitär", view.egal)]
    for name, p in entries:
        g = view.t_max - mid
        share = None if g <= TOL else (p[0] + p[1] - mid) / g
        rows.append({"name": name, "uv": p[0], "us": p[1], "sum": p[0] + p[1], "share": share, "x": allocation(view, p)})
    return rows


def solution_table(view: TradeView) -> list[dict]:
    names = view.point_names()
    out = []
    for r in solution_rows(view):
        row = {"Lösung": r["name"], "Verlader": de(r["uv"], 1), "Spediteur": de(r["us"], 1), "Summe": de(r["sum"], 1),
               "Anteil des möglichen Gewinns": "kein Gewinn möglich" if r["share"] is None else pct(r["share"], 1)}
        if r["x"] is None:
            row["Stellung der Punkte (0 % = Verlader, 100 % = Spediteur)"] = "Mitte aller Punkte" if r["name"].startswith("Position") else "–"
        else:
            row["Stellung der Punkte (0 % = Verlader, 100 % = Spediteur)"] = ", ".join(f"{n} {de(100 * xi, 0)} %" for n, xi in zip(names, r["x"]))
        out.append(row)
    if view.aw is not None:
        x, (a, b), split = view.aw
        out.append({"Lösung": "Adjusted Winner (auf je 100 normiert, ohne Preis)", "Verlader": de(float(a), 1), "Spediteur": de(float(b), 1), "Summe": de(float(a + b), 1),
                    "Anteil des möglichen Gewinns": "(auf 100 normiert)",
                    "Stellung der Punkte (0 % = Verlader, 100 % = Spediteur)": ", ".join(f"{n} {de(100 * float(xi), 0)} %" for n, xi in zip(view.names, x)) + f"; geteilt: {split}"})
    return out


def bundle_rows(st: Settings) -> list[dict]:
    """Bündelgrößen 1 bis n für die Punkte (ohne Preis): Summe der Nutzen bei Nash je Bündel, Anteil des möglichen Gewinns."""
    v, s, _ = point_values(st)
    g = FR.gain_sum(v, s)
    base = (sum(v) + sum(s)) / 2
    rows = []
    for size in range(1, len(v) + 1):
        part = FR.bundle_partition(len(v), size)
        a, b = FR.bundle_nash(v, s, part)
        rows.append({"size": size, "parts": part, "uv": a, "us": b, "sum": a + b, "share": None if g <= TOL else (a + b - base) / g})
    return rows


def bundle_table(st: Settings) -> list[dict]:
    rows = bundle_rows(st)
    chosen = effective_bundle(st)
    names = point_values(st)[2]
    return [{"Bündelgröße": ("▶ " if r["size"] == chosen else "") + str(r["size"]), "Bündel": " | ".join("+".join(names[i] for i in p) for p in r["parts"]),
             "Verlader": de(r["uv"], 1), "Spediteur": de(r["us"], 1), "Anteil des möglichen Gewinns": "kein Gewinn möglich" if r["share"] is None else pct(r["share"], 1)} for r in rows]


# --------------------------------------------------------------------------------- Seitenzahlung (live)
def price_curve(st: Settings, prices=None) -> list[dict]:
    """Anteile von Nash/KS/egalitär über dem Preis-Spielraum M für die Punkte der Einstellungen (ohne den Preis der Seitenleiste)."""
    v, s, _ = point_values(st)
    ms = prices if prices is not None else list(range(0, C.PRICE_MAX + 1, 5))
    out = []
    for m in ms:
        met = XP.trade_metrics(v, s, float(m))
        out.append({"m": m, "t": met["t"], **{k: met.get(k) for k in ("share_nash", "share_ks", "share_egal", "nash_half", "all3_equal", "nash_uv", "nash_us")}})
    return out


def on_unit_slope(verts, point) -> bool:
    """Liegt der Punkt auf einem Stück der Grenze mit Steigung −1 (Länge > 0)? Dann wirkt eine Seitenzahlung: 1 Euro hier ist 1 Euro dort."""
    for (a1, b1), (a2, b2) in zip(verts, verts[1:]):
        da, db = a2 - a1, b2 - b1
        if abs(da) > TOL and abs(da + db) < 1e-9 and a2 - 1e-9 <= point[0] <= a1 + 1e-9:
            return True
    return False


def bridge(view: TradeView, delta_v: float, delta_s: float) -> dict:
    """Aufteilung der größten Summe T als Rubinstein-Spiel: Vorschlag P von V (V bietet zuerst) auf der Grenze der Einstellungen gegen T·(1 − δ_S) / (1 − δ_V δ_S)."""
    t = view.t_max
    p, q = FR.rubinstein_on_frontier(view.verts, delta_v, delta_s)
    share = FR.rubinstein_share(delta_v, delta_s)
    interior = abs(p[1] - delta_s * q[1]) < 1e-6 * max(1.0, t)          # S ist beim Vorschlag von V genau indifferent (sonst stößt V an die Grenze seines größten Nutzens)
    return {"p": p, "q": q, "t": t, "t_split": (t * share, t * (1 - share)), "interior": interior,
            "on_slope": interior and on_unit_slope(view.verts, p) and on_unit_slope(view.verts, q), "diff": abs(p[0] - t * share)}


# --------------------------------------------------------------------------------- Zeit, Risiko, Einschätzung (live)
def term_rows(st: Settings) -> list[dict]:
    rs, rv = st.rs / 100.0, st.rv / 100.0
    rows = []
    for d in C.TERM_GRID:
        rows.append({"d": d, "gain": SO.term_gain(d, rs, rv, C.AMOUNT), "linear": SO.term_gain_linear(d, rs, rv, C.AMOUNT)})
    return rows


def term_summary(st: Settings) -> dict:
    rs, rv = st.rs / 100.0, st.rv / 100.0
    d_star = SO.term_optimum(rs, rv)
    best = SO.best_term(rs, rv, C.TERM_MAX)
    return {"rs": rs, "rv": rv, "d_star": d_star, "best": best, "gain_best": SO.term_gain(best, rs, rv, C.AMOUNT), "days": st.term, "gain_chosen": SO.term_gain(st.term, rs, rv, C.AMOUNT),
            "gain_chosen_linear": SO.term_gain_linear(st.term, rs, rv, C.AMOUNT), "mid_of_ends": SO.term_gain(C.TERM_MAX, rs, rv, C.AMOUNT) / 2,
            "gain_mid": SO.term_gain(C.TERM_MAX / 2, rs, rv, C.AMOUNT)}


def risk_summary(st: Settings) -> dict:
    gs, gv, q = st.gs / 1000.0, st.gv / 1000.0, st.q / 100.0
    q_star = SO.risk_share(gs, gv)
    return {"gs": gs, "gv": gv, "q": q, "q_star": q_star, "gain_q": SO.risk_gain(q, gs, gv, C.RISK_A, C.RISK_P),
            "gain_star": None if q_star is None else SO.risk_gain(q_star, gs, gv, C.RISK_A, C.RISK_P), "gain_half": SO.risk_gain(0.5, gs, gv, C.RISK_A, C.RISK_P),
            "ce_alone": SO.ce_cara([C.RISK_A, 0.0], [C.RISK_P, 1 - C.RISK_P], gs), "mean": C.RISK_A * C.RISK_P}


def risk_table(st: Settings) -> list[dict]:
    gs = st.gs / 1000.0
    rows = []
    for g_milli in C.GAMMA_V_TABLE:
        gv = g_milli / 1000.0
        q = SO.risk_share(gs, gv)
        rows.append({"gv": g_milli, "q_star": q, "gain": None if q is None else SO.risk_gain(q, gs, gv, C.RISK_A, C.RISK_P), "gain_half": SO.risk_gain(0.5, gs, gv, C.RISK_A, C.RISK_P)})
    return rows


def bet_summary(st: Settings) -> dict:
    gamma = st.gb / 1000.0
    bonus = float(st.bonus)
    p_lo, p_hi = min(st.pv, st.ps), max(st.pv, st.ps)
    m = (st.pv + st.ps) / 2
    common = [(label, p) for label, p in (("kleinere Einschätzung", p_lo), ("Mitte", m), ("größere Einschätzung", p_hi))]
    w_star = SO.bet_size_cara(st.pv, st.ps, gamma)
    return {
        "subjective": SO.bet_gain_subjective(st.pv, st.ps, bonus),
        "each": SO.bet_gain_subjective(st.pv, st.ps, bonus) / 2,
        "common": [(label, SO.bet_sums(st.pv, st.ps, bonus, p)[0], p) for label, p in common],
        "hindsight": SO.bet_hindsight(st.pv, st.ps, bonus),
        "w_star": w_star, "gamma": gamma, "gain_star": None if w_star is None else SO.bet_gain_cara(w_star, st.pv, st.ps, gamma),
        "gain_bonus": SO.bet_gain_cara(bonus, st.pv, st.ps, gamma), "high_side": "Spediteur" if st.ps > st.pv else ("Verlader" if st.pv > st.ps else None),
        "odds": None if p_hi <= p_lo else SO.odds_ratio(p_lo, p_hi),
    }


def bet_by_estimate(gamma: float, p_v: float = 0.4) -> list[dict]:
    """Gewinn der besten Wette gegen den Abstand der Einschätzungen (p_V fest)."""
    rows = []
    for ps in (0.4, 0.45, 0.5, 0.6, 0.7, 0.8):
        w = SO.bet_size_cara(p_v, ps, gamma)
        rows.append({"ps": ps, "w": w, "gain": 0.0 if w is None else SO.bet_gain_cara(w, p_v, ps, gamma)})
    return rows


# --------------------------------------------------------------------------------- MESO (live)
def meso_live(st: Settings) -> dict | None:
    inst = ME.make_instance(st.seed)
    if inst is None:
        return None
    a, b, order = inst
    res = ME.run(a, b, order, st.k, st.r, st.est)
    res["a"], res["b"] = a, b
    res["u_a"], res["u_b"] = ME.utilities(a, b)
    return res


# --------------------------------------------------------------------------------- Tabellenzeilen (App und README bauen sie mit denselben Funktionen)
def e1_table(grid: dict, n: int) -> list[dict]:
    cells = [XP.find(grid["e1"], n=n, theta=th) for th in C.E1_THETAS]
    return [{"θ": de(c["theta"], 2), "Gewinn (Punkte)": mean_se(c, "gain", 2), "Anteil Nash": mean_se(c, "share_nash", 3), "Anteil Kalai–Smorodinsky und egalitär": mean_se(c, "share_ks", 3),
             "Nash: Verlader / Spediteur": f"{de(c['nash_uv']['mean'], 1)} / {de(c['nash_us']['mean'], 1)}", "Instanzen mit Gewinn unter 5": pct(c["gain_small"]["mean"], 0)} for c in cells]


def e2_table(grid: dict) -> list[dict]:
    full, half = XP.find(grid["e6"], theta=1.0), XP.find(grid["e6"], theta=0.5)
    return [{"Aufteilung (n = 4, Summe 100 je Seite)": name, "θ = 1": mean_se(full, name, 3, percent=True), "θ = 0,5": mean_se(half, name, 3, percent=True)} for name in XP.E6_PARTITIONS]


def e3_table(grid: dict) -> list[dict]:
    cells = [XP.find(grid["e2"], theta=1.0, level=1.0, price=m) for m in C.E2_MS]
    return [{"M": str(c["price"]), "Nash": mean_se(c, "share_nash", 3), "Kalai–Smorodinsky": mean_se(c, "share_ks", 3), "Egalitär": mean_se(c, "share_egal", 3),
             "Instanzen mit Nash = T/2": pct(c["nash_half"]["mean"], 1), "Regel M ≥ M* trifft": pct(c["rule_hit"]["mean"], 1), "Abstand der Nutzen bei Nash": mean_se(c, "gap_nash", 1)} for c in cells]


def e3_level_table(grid: dict) -> list[dict]:
    cells = [XP.find(grid["e2"], theta=0.0, level=2.0, price=m) for m in C.E2_LEVEL_MS]
    return [{"M": str(c["price"]), "Nash": mean_se(c, "share_nash", 3), "Kalai–Smorodinsky": mean_se(c, "share_ks", 3), "Egalitär": mean_se(c, "share_egal", 3),
             "Instanzen mit Nash = T/2": pct(c["nash_half"]["mean"], 1), "alle drei gleich": pct(c["all3_equal"]["mean"], 1)} for c in cells]


def term_display(st: Settings) -> list[dict]:
    return [{"Zahlungsziel (Tage)": str(r["d"]), "Gewinn (Euro je Tour)": de(r["gain"], 1), "lineare Annahme (Euro je Tour)": de(r["linear"], 1)} for r in term_rows(st)]


def risk_display(st: Settings) -> list[dict]:
    return [{"γ_V (‰ je Euro)": de(r["gv"], 1), "bester Risikoanteil q*": "–" if r["q_star"] is None else pct(r["q_star"], 1),
             "Gewinn bei q* (Euro je Tour)": "–" if r["gain"] is None else de(r["gain"], 2), "Gewinn bei halbe-halbe": de(r["gain_half"], 2)} for r in risk_table(st)]


def bet_display(bs: dict) -> list[dict]:
    rows = [{"Maßstab": "(a) eigene Einschätzung jeder Seite", "Seite mit höherer Einschätzung": de(bs["each"], 1), "andere Seite": de(bs["each"], 1), "Summe": de(bs["subjective"], 1)}]
    rows += [{"Maßstab": f"(b) gemeinsame Wahrscheinlichkeit {pct(p, 0)} ({label})", "Seite mit höherer Einschätzung": de(g, 1), "andere Seite": de(-g, 1), "Summe": de(0.0, 1)} for label, g, p in bs["common"]]
    rows += [{"Maßstab": "(c) nachträglich, Lage „hoch“", "Seite mit höherer Einschätzung": de(bs["hindsight"]["high_in_high"], 1), "andere Seite": de(-bs["hindsight"]["high_in_high"], 1), "Summe": de(0.0, 1)},
             {"Maßstab": "(c) nachträglich, Lage „nicht hoch“", "Seite mit höherer Einschätzung": de(bs["hindsight"]["high_in_low"], 1), "andere Seite": de(-bs["hindsight"]["high_in_low"], 1), "Summe": de(0.0, 1)}]
    return rows


def bet_estimate_display(gamma: float) -> list[dict]:
    return [{"p_S (p_V = 0,4)": de(r["ps"], 2), "beste Wettgröße w* (Euro)": "–" if r["w"] is None else de(r["w"], 1), "Gewinn (Euro je Tour)": de(r["gain"], 2)} for r in bet_by_estimate(gamma)]


def _meso_cell(meso: dict, est: str, k: int, r: int) -> dict:
    return next(c for c in meso["cells"] if c["estimator"] == est and c["k"] == k and c["r"] == r)


def meso_table(meso: dict, r: int) -> list[dict]:
    return [{"Angebote k": str(k), "g Posterior-Mittel": mean_se(_meso_cell(meso, "Posterior-Mittel", k, r), "g_end", 3), "g Max-Rand": mean_se(_meso_cell(meso, "Max-Rand", k, r), "g_end", 3),
             "Fehler der Schätzung (Posterior / Max-Rand)": f"{mean_se(_meso_cell(meso, 'Posterior-Mittel', k, r), 'error', 3)} / {mean_se(_meso_cell(meso, 'Max-Rand', k, r), 'error', 3)}"} for k in C.MESO_KS]


# --------------------------------------------------------------------------------- Verdikte
def verdict_trade(view: TradeView) -> tuple[str, str]:
    """Kernfrage: Gibt es etwas zu gewinnen, und was erreichen die Lösungen?"""
    if view.gain <= TOL:
        return "warning", (f"**Kein Tauschgewinn:** Die Gewichte beider Seiten stimmen Punkt für Punkt überein (oder die Summe ist schon bei jeder Teilung gleich). Die größte Summe der Nutzen ({de(view.t_max, 1)}) "
                           f"ist die Summe beim Positionskompromiss ({de(sum(view.compromise), 1)}): Jede Lösung auf der Grenze verteilt nur um.")
    rows = solution_rows(view)
    nash_share, ks_share = rows[1]["share"], rows[2]["share"]
    return "success", (f"**Gewinn des Tauschs: {de(view.gain, 1)}** (= ½ Σ|v − s|; größte Summe {de(view.t_max, 1)} statt {de(sum(view.compromise), 1)} beim Positionskompromiss). "
                       f"Die Nash-Lösung erreicht {pct(nash_share, 1)} davon, Kalai–Smorodinsky {pct(ks_share, 1)}; der Positionskompromiss (jeder Punkt halbe-halbe) erreicht 0 %.")


def verdict_hook(view: TradeView) -> tuple[str, str]:
    """Normierte gegen Euro-Gewichte: derselbe Gewinn nur bei gleichen Gesamtwerten."""
    if view.gain_normalized is None:
        return "info", "Eine Seite bewertet keinen Punkt: normieren ist nicht möglich."
    tv, ts = sum(view.v), sum(view.s)
    if abs(tv - ts) < TOL:
        return "info", f"Beide Seiten haben dieselbe Gesamtbewertung ({de(tv, 0)}): der Gewinn in Euro ({de(view.gain, 1)}) und der Gewinn bei auf je 100 normierten Gewichten ({de(view.gain_normalized, 1)}) stimmen überein."
    return "info", (f"Die Gesamtbewertungen sind verschieden (Verlader {de(tv, 0)}, Spediteur {de(ts, 0)}): in Euro beträgt der Gewinn {de(view.gain, 1)}, bei auf je 100 normierten Gewichten {de(view.gain_normalized, 1)}. "
                    "Der Unterschied kommt aus dem Niveau, nicht aus dem Profil der Gewichte.")


def verdict_money(view: TradeView) -> tuple[str, str]:
    """Seitenzahlung: Schwelle M* und Lage der Nash-Lösung."""
    if view.gain <= TOL and view.price == 0:
        return "warning", "Ohne Gewinn des Tauschs und ohne Geld gibt es nichts zu teilen: jede Lösung auf der Grenze liegt auf der Geraden der Summe."
    if view.price >= view.m_star - TOL:
        return "success", (f"Der Preis-Spielraum {de(view.price, 0)} reicht (Schwelle M* = {de(view.m_star, 0)}): Die Nash-Lösung teilt die größte Summe {de(view.t_max, 1)} hälftig, {de(view.nash[0], 1)} und {de(view.nash[1], 1)}."
                           + ("" if abs(sum(view.v) - sum(view.s)) < TOL else " Kalai–Smorodinsky und egalitär fallen nur bei gleichen Gesamtbewertungen mit ihr zusammen."))
    return "info", (f"Der Preis-Spielraum {de(view.price, 0)} liegt unter der Schwelle M* = {de(view.m_star, 0)}: Die Nash-Lösung ({de(view.nash[0], 1)}; {de(view.nash[1], 1)}) teilt die größte Summe "
                    f"{de(view.t_max, 1)} nicht hälftig, der Abstand der Nutzen ist {de(abs(view.nash[0] - view.nash[1]), 1)}.")


def verdict_bundle(st: Settings, rows: list[dict]) -> tuple[str, str]:
    if not rows:
        return "warning", "Es wird kein Punkt verhandelt (alle Werte beider Seiten sind 0): es gibt nichts zu bündeln."
    size = effective_bundle(st)
    row = rows[size - 1]
    if row["share"] is None:
        return "warning", "Ohne Tauschgewinn ändert die Bündelgröße nichts: jede Teilung liefert dieselbe Summe."
    single, package = rows[0]["share"], rows[-1]["share"]
    return "info", (f"Bündelgröße {size} von {len(rows)} Punkten: {pct(row['share'], 1)} des möglichen Gewinns (Einzelpunkte {pct(single, 1)}, ein Paket {pct(package, 1)}). "
                    "Einzelpunkte teilt die Nash-Lösung je Punkt in der Mitte; erst im Paket zeigt sich, wer welchen Punkt höher bewertet.")


def verdict_e1(grid: dict) -> tuple[str, str]:
    """E1: Gewinn gegen Gewichtsunterschied θ und Anteile der Lösungen (Zellen n = 4)."""
    zero, full = XP.find(grid["e1"], n=4, theta=0.0), XP.find(grid["e1"], n=4, theta=1.0)
    half = XP.find(grid["e1"], n=4, theta=0.5)
    dev = max(abs(XP.find(grid["e1"], n=n, theta=th)["gain"]["mean"] - th * XP.find(grid["e1"], n=n, theta=1.0)["gain"]["mean"]) for n in C.E1_NS for th in C.E1_THETAS)
    return "info", (f"**Befund:** Bei θ = 0 (gleiche Profile) ist der Gewinn {de(zero['gain']['mean'], 2)}; bei θ = 1 (unabhängige Gewichte) im Mittel {de(full['gain']['mean'], 1)} Punkte bei n = 4 (Summe 100 je Seite). "
                    f"Er wächst in jeder Zelle linear mit θ (größte Abweichung von θ · Gewinn(θ = 1): {de(dev, 6)} Punkte). Anteil des möglichen Gewinns bei n = 4 und θ = 1: Nash {mean_se(full, 'share_nash', 3)}, "
                    f"Kalai–Smorodinsky und egalitär {mean_se(full, 'share_ks', 3)}; bei θ = 0,5: Nash {mean_se(half, 'share_nash', 3)}, Kalai–Smorodinsky {mean_se(half, 'share_ks', 3)}.")


def asymmetry_table(grid: dict) -> list[dict]:
    """Zeilen zur Nash-Asymmetrie (n = 4): Erzeuger von E1 gegen symmetrischen Erzeuger, getrennt nach der Seite mit den ungleicheren Gewichten."""
    rows = []
    for c in grid["asym"]:
        rows.append({"θ": de(c["theta"], 2), "Anteil der Instanzen, in denen V die ungleicheren Gewichte hat (E1-Erzeuger)": pct(c["share_v_peaky_e1"]["mean"], 1),
                     "U_V − U_S im Mittel (E1-Erzeuger)": mean_se(c, "diff_e1", 1), "U_V − U_S im Mittel (symmetrischer Erzeuger)": mean_se(c, "diff_sym", 1),
                     "symmetrisch, wenn V die ungleicheren Gewichte hat": mean_se(c, "diff_sym_v_peaky", 1), "symmetrisch, wenn S sie hat": mean_se(c, "diff_sym_s_peaky", 1)})
    return rows


def verdict_asymmetry(grid: dict) -> tuple[str, str]:
    c = XP.find(grid["asym"], theta=0.5)
    return "info", (f"**Befund (n = 4, θ = 0,5):** Im Erzeuger von E1 bekommt der Verlader bei Nash im Mittel {de(c['diff_e1']['mean'], 1)} Punkte mehr als der Spediteur; im symmetrischen Erzeuger (beide mischen einen gemeinsamen Teil mit "
                    f"einem eigenen) sind es {de(c['diff_sym']['mean'], 1)}. Dort bekommt die Seite mit den ungleicheren Gewichten (größeres Σ w²) im Mittel {de(c['diff_sym_v_peaky']['mean'], 1)} Punkte mehr als die andere, wenn es der Verlader ist, und "
                    f"{de(-c['diff_sym_s_peaky']['mean'], 1)} Punkte mehr, wenn es der Spediteur ist. Im E1-Erzeuger hat der Verlader in {pct(c['share_v_peaky_e1']['mean'], 1)} der Instanzen die ungleicheren Gewichte. "
                    "Die Asymmetrie ist also ein Merkmal des Erzeugers; **warum** die ungleichere Seite bei Nash vorn liegt, ist hier gemessen (Zusammenhang), nicht bewiesen.")


def verdict_e2(grid: dict) -> tuple[str, str]:
    """E2: Bündelgröße (n = 4 Punkte, θ = 1 und θ = 0,5)."""
    full, half = XP.find(grid["e6"], theta=1.0), XP.find(grid["e6"], theta=0.5)
    total = sum(c["same_order"]["mean"] for c in grid["e6"]) * grid["blocks"]
    count = len(grid["e6"]) * grid["blocks"] * grid["instances_per_block"]
    return "info", (f"**Befund:** Anteil des möglichen Gewinns bei θ = 1 (θ = 0,5): vier Einzelpunkte {pct(full['vier Einzelpunkte']['mean'], 1)} ({pct(half['vier Einzelpunkte']['mean'], 1)}), zwei Paare {pct(full['zwei Paare']['mean'], 1)} ({pct(half['zwei Paare']['mean'], 1)}), "
                    f"drei und einer {pct(full['drei und einer']['mean'], 1)} ({pct(half['drei und einer']['mean'], 1)}), ein Paket {pct(full['ein Paket']['mean'], 1)} ({pct(half['ein Paket']['mean'], 1)}). "
                    f"Die Anteile steigen nicht stetig mit der Bündelgröße (drei und einer liegt unter zwei Paaren); die Reihenfolge der Bündel ändert nichts ({thousands(total)} von {thousands(count)} Instanzen gleich, "
                    "im additiven Modell per Konstruktion, weil jedes Bündel für sich abgeschlossen wird).")


def verdict_e3(grid: dict) -> tuple[str, str]:
    """E3: Seitenzahlung, θ = 1, n = 4."""
    cells = [XP.find(grid["e2"], theta=1.0, level=1.0, price=m) for m in C.E2_MS]
    hits = sum(c["rule_hit"]["mean"] == 1.0 for c in grid["e2"])
    c0, c50, c100 = cells[0], XP.find(grid["e2"], theta=1.0, level=1.0, price=50), XP.find(grid["e2"], theta=1.0, level=1.0, price=100)
    lvl0, lvl200 = XP.find(grid["e2"], theta=0.0, level=2.0, price=0), XP.find(grid["e2"], theta=0.0, level=2.0, price=200)
    return "info", (f"**Befund:** Die Regel „Nash-Lösung = Hälfte der größten Summe genau dann, wenn M ≥ M*“ stimmt in {hits} von {len(grid['e2'])} Zellen (je {thousands(grid['blocks'] * grid['instances_per_block'])} Instanzen) in jeder Instanz. "
                    f"Anteil der Instanzen mit Nash = T/2 bei θ = 1: {pct(c0['nash_half']['mean'], 1)} (M = 0), {pct(c50['nash_half']['mean'], 1)} (M = 50), {pct(c100['nash_half']['mean'], 1)} (M = 100). "
                    f"Anteil des Gewinns bei Nash: {mean_se(c0, 'share_nash', 3)} ohne Geld, {mean_se(c100, 'share_nash', 3)} bei M = 100. Bei s = 2v (gleiches Profil, doppeltes Niveau) erreicht Nash ohne Geld "
                    f"{de(lvl0['share_nash']['mean'], 3)} des Gewinns, mit M = 200 {de(lvl200['share_nash']['mean'], 3)}; dort fallen Nash und Kalai–Smorodinsky auseinander ({pct(lvl200['all3_equal']['mean'], 1)} der Instanzen mit allen drei gleich).")


def verdict_bridge(b: dict, delta_v: float, delta_s: float) -> tuple[str, str]:
    share = FR.rubinstein_share(delta_v, delta_s)
    if b["on_slope"]:
        return "success", (f"Beide Vorschläge liegen im Inneren des Stücks mit Steigung −1: V bekommt als erster Anbieter {de(b['p'][0], 1)} von {de(b['t'], 1)}, genau T · (1 − δ_S) / (1 − δ_V δ_S) = {de(b['t'], 1)} · {de(share, 3)}. "
                           "Die Aufteilung des Überschusses ist das Verhandlungsspiel des Vorgängerstücks mit T statt 1.")
    return "info", (f"Die Bedingung ist nicht erfüllt (beide vom Rubinstein-Gleichgewicht verlangten Vorschläge im Inneren des Stücks mit Steigung −1; zu wenig Spielraum): V bekommt {de(b['p'][0], 1)} statt "
                    f"T · {de(share, 3)} = {de(b['t_split'][0], 1)}, Abstand {de(b['diff'], 1)}. Die Übertragung auf T gilt nur, solange der Preis-Spielraum beide Vorschläge trägt.")


def verdict_time(t: dict) -> tuple[str, str]:
    days = de(t["days"], 0)
    if t["rv"] == t["rs"]:
        return "warning", f"Gleiche Ungeduld ({de(100 * t['rs'], 2)} % je Tag): ein Zahlungsziel verschiebt nur Geld zwischen den Seiten und bringt keinen gemeinsamen Gewinn, nach {days} Tagen {de(t['gain_chosen'], 1)} Euro."
    if t["rv"] < t["rs"]:
        return "warning", (f"Der Spediteur ist ungeduldiger als der Verlader ({de(100 * t['rs'], 2)} % gegen {de(100 * t['rv'], 2)} % je Tag): ein Zahlungsziel kostet gemeinsam, nach {days} Tagen {de(-t['gain_chosen'], 1)} Euro; "
                           "das beste Ziel ist sofortige Zahlung.")
    if t["d_star"] is None:
        return "info", f"Mit Ungeduld 0 beim Spediteur wächst der Gewinn mit dem Ziel bis zur Obergrenze von {C.TERM_MAX} Tagen ({de(t['gain_best'], 1)} Euro)."
    return "success", (f"Bestes Zahlungsziel d* = {de(t['d_star'], 1)} Tage mit {de(t['gain_best'], 1)} Euro Gewinn je Tour (Betrag {de(C.AMOUNT, 0)} Euro fest); beim gewählten Ziel von {days} Tagen "
                       f"sind es {de(t['gain_chosen'], 1)} Euro, eine lineare Annahme „gleicher Wert je Tag“ ergäbe {de(t['gain_chosen_linear'], 1)}.")


def verdict_risk(r: dict) -> tuple[str, str]:
    if r["q_star"] is None:
        return "warning", "Beide Seiten sind risikoneutral: jede Teilung des Risikos ist gleich gut, es gibt keinen Gewinn aus dem Risiko."
    return "success", (f"Optimaler Risikoanteil des Verladers q* = γ_S / (γ_S + γ_V) = {pct(r['q_star'], 1)}: Gewinn {de(r['gain_star'], 2)} Euro je Tour, obwohl beide dieselbe Wahrscheinlichkeit annehmen und jeder Erwartungswert "
                       f"unverändert bleibt. Halbe-halbe (50 %) bringt {de(r['gain_half'], 2)} Euro, das gewählte q = {pct(r['q'], 0)} bringt {de(r['gain_q'], 2)} Euro.")


def verdict_bet(b: dict, st: Settings) -> tuple[str, str]:
    if b["subjective"] <= TOL:
        return "warning", (f"Gleiche Einschätzung ({pct(st.pv, 0)}): Mit eigener Einschätzung gibt es keinen Gewinn der Klausel. Sind beide risikoscheu, kostet die Wette der Größe {de(st.bonus, 0)} sogar "
                           f"{de(-b['gain_bonus'], 2)} Euro je Tour.")
    text = (f"Mit der **eigenen** Einschätzung jeder Seite gewinnt jede {de(b['each'], 1)} Euro je Tour, zusammen {de(b['subjective'], 1)} = |p_S − p_V| · b. Mit einer **gemeinsamen** Wahrscheinlichkeit ist die Summe immer 0: "
            + ", ".join(f"bei {pct(p, 0)} ist der Erwartungswert der Seite mit der höheren Einschätzung {de(g, 1)} Euro" for _, g, p in b["common"]) + " (bei der anderen Seite das Negative); nachträglich heben sich die Zahlungen in jeder Lage auf.")
    return "info", text


def verdict_bet_cara(b: dict) -> tuple[str, str]:
    if b["w_star"] is None:
        return "warning", "Ohne Unterschied der Einschätzung (oder ohne Risikoscheu) gibt es keine endliche beste Wettgröße."
    return "success", (f"Sind beide risikoscheu (γ = {de(b['gamma'], 4)}), ist die Wette endlich: beste Größe w* = ln({de(b['odds'], 2)}) / (2γ) = {de(b['w_star'], 1)} Euro mit Gewinn {de(b['gain_star'], 2)} Euro je Tour; "
                       f"mit der Größe des gewählten Bonus wären es {de(b['gain_bonus'], 2)} Euro.")


def verdict_meso(meso: dict) -> tuple[str, str]:
    def cell(est, k, r):
        return next(c for c in meso["cells"] if c["estimator"] == est and c["k"] == k and c["r"] == r)

    pm1, pm2, pm3, pm5, pm8 = (cell("Posterior-Mittel", k, 1)["g_end"]["mean"] for k in (1, 2, 3, 5, 8))
    mr2 = cell("Max-Rand", 2, 1)["g_end"]["mean"]
    eq = meso["g_equal"]["mean"]
    return "info", (f"**Befund (Simulation):** Mit dem Posterior-Mittel steigt die Güte g des Endangebots in einer Runde von {de(pm1, 3)} (ein Angebot) auf {de(pm2, 3)} (zwei), {de(pm3, 3)} (drei), {de(pm5, 3)} (fünf) und {de(pm8, 3)} (acht); "
                    f"der Sprung von eins auf zwei ist der größte. Mit dem Max-Rand-Schätzer ergeben zwei Angebote {de(mr2, 3)}, schlechter als gleiche Gewichte als Schätzung ({de(eq, 3)}). "
                    "Das Ergebnis hängt am Schätzer: die Behauptung „mehr als drei Angebote bringen kaum etwas“ ist damit nicht bestätigt.")


def verdict_meso_live(res: dict | None) -> tuple[str, str]:
    if res is None:
        return "warning", "Für diesen Zufalls-Seed hat das Band weniger als 12 Pakete: anderen Seed wählen."
    g = res["g_end"]
    if g is None:
        return "warning", "Alle Pakete des Bandes bringen dem Spediteur gleich viel: nichts zu schätzen."
    return "info", (f"Endangebot mit Güte g = {de(g, 3)} (0 = Zufallspaket des Bandes, 1 = bestes Paket des Bandes für den Spediteur). Der Fehler der Schätzung der Gewichte ist {de(res['error'], 3)}, "
                    f"gleiche Gewichte als Schätzung hätten {de(res['error_equal'], 3)}. Vorgelegt wurden {res['n_shown']} von {res['band_size']} Paketen des Bandes; {res['constraints']} Wahl-Ungleichungen.")
