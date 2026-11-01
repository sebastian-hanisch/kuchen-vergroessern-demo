"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import vhg_constants as C
import vhg_experiments as XP
import vhg_sources as SO


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend_below=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.22) if legend_below else dict())
    return lock_axes(fig)


def build_frontier(view):
    """Pareto-Grenze mit dem erreichbaren Bereich (grau), dem Positionskompromiss und den Lösungen."""
    xs = [a for a, _ in view.verts]
    ys = [b for _, b in view.verts]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0.0] + xs, y=[0.0] + ys, fill="toself", fillcolor="rgba(150,150,150,0.15)", line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=C.COLOR_FRONTIER, width=3), marker=dict(size=6), name="Pareto-Grenze (Ecken = Zwischenstände)",
                             hovertemplate="Verlader %{x:.1f} | Spediteur %{y:.1f}<extra></extra>"))
    top = max(xs[0], ys[-1], 1.0)
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line=dict(color=C.COLOR_GREY, dash="dot", width=1), name="gleicher Nutzen", hoverinfo="skip"))
    marks = [("Positionskompromiss", view.compromise, C.COLOR_MID, "square"), ("Nash", view.nash, C.COLOR_NASH, "circle"), ("Kalai–Smorodinsky / egalitär", view.ks, C.COLOR_KS, "diamond")]
    for name, p, color, symbol in marks:
        fig.add_trace(go.Scatter(x=[p[0]], y=[p[1]], mode="markers", marker=dict(size=13, color=color, symbol=symbol, line=dict(width=1, color="white")), name=name,
                                 hovertemplate=f"{name}: %{{x:.1f}} | %{{y:.1f}}<extra></extra>"))
    if abs(view.ks[0] - view.egal[0]) > 1e-6 or abs(view.ks[1] - view.egal[1]) > 1e-6:
        fig.add_trace(go.Scatter(x=[view.egal[0]], y=[view.egal[1]], mode="markers", marker=dict(size=11, color=C.COLOR_EGAL, symbol="x"), name="Egalitär",
                                 hovertemplate="Egalitär: %{x:.1f} | %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text="Nutzen des Verladers", range=[-0.02 * top, 1.05 * top])
    fig.update_yaxes(title_text="Nutzen des Spediteurs", range=[-0.02 * top, 1.05 * top])
    return _base(fig, 420)


def build_lines(series: dict, x_title: str, y_title: str, yrange=None, categorical=False, height=340):
    """`series`: Name → (x, y, Standardfehler oder None). Linien mit Markern, optional mit Fehlerbalken."""
    fig = go.Figure()
    for i, (name, (xs, ys, se)) in enumerate(series.items()):
        err = dict(type="data", array=list(se), visible=True) if se is not None else None
        fig.add_trace(go.Scatter(x=list(xs), y=list(ys), mode="lines+markers", name=name, error_y=err, hovertemplate=f"{name}: %{{x}} | %{{y:.3f}}<extra></extra>"))
    fig.update_xaxes(title_text=x_title, type="category" if categorical else None)
    fig.update_yaxes(title_text=y_title, range=yrange)
    return _base(fig, height)


def build_theta(grid, n: int):
    cells = [XP.find(grid["e1"], n=n, theta=th) for th in C.E1_THETAS[1:]]
    xs = [c["theta"] for c in cells]
    return build_lines({"Nash": (xs, [c["share_nash"]["mean"] for c in cells], [c["share_nash"]["se"] for c in cells]),
                        "Kalai–Smorodinsky und egalitär": (xs, [c["share_ks"]["mean"] for c in cells], [c["share_ks"]["se"] for c in cells])},
                       "Gewichtsunterschied θ", "Anteil des möglichen Gewinns", yrange=[0.5, 1.02])


def build_gain_theta(grid):
    fig = go.Figure()
    for n in C.E1_NS:
        cells = [XP.find(grid["e1"], n=n, theta=th) for th in C.E1_THETAS]
        fig.add_trace(go.Scatter(x=list(C.E1_THETAS), y=[c["gain"]["mean"] for c in cells], mode="lines+markers", name=f"n = {n}", hovertemplate=f"n = {n}: θ = %{{x}}, Gewinn %{{y:.1f}}<extra></extra>"))
    fig.update_xaxes(title_text="Gewichtsunterschied θ")
    fig.update_yaxes(title_text="Gewinn des Tauschs (Punkte bei Summe 100 je Seite)")
    return _base(fig, 340)


def build_price(rows, m_star: float):
    xs = [r["m"] for r in rows]
    fig = go.Figure()
    for key, name, color in (("share_nash", "Nash", C.COLOR_NASH), ("share_ks", "Kalai–Smorodinsky", C.COLOR_KS), ("share_egal", "Egalitär", C.COLOR_EGAL)):
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in rows], mode="lines", name=name, line=dict(color=color, width=3 if key == "share_nash" else 2, dash="solid" if key != "share_egal" else "dot"),
                                 connectgaps=False, hovertemplate=f"{name}: M = %{{x}} | Anteil %{{y:.3f}}<extra></extra>"))
    if m_star <= max(xs):
        fig.add_vline(x=m_star, line=dict(color=C.COLOR_GREY, dash="dash"), annotation_text="Schwelle M*", annotation_position="top")
    fig.update_xaxes(title_text="Preis-Spielraum M (Euro je Tour)")
    fig.update_yaxes(title_text="Anteil des möglichen Gewinns")
    return _base(fig, 340)


def build_term(st_summary):
    rs, rv = st_summary["rs"], st_summary["rv"]
    ds = np.linspace(0, C.TERM_MAX, 91)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ds, y=[SO.term_gain(d, rs, rv, C.AMOUNT) for d in ds], mode="lines", name="Gewinn des Zahlungsziels", line=dict(color=C.COLOR_FRONTIER, width=3),
                             hovertemplate="Ziel %{x:.0f} Tage: %{y:.1f} Euro<extra></extra>"))
    fig.add_trace(go.Scatter(x=ds, y=[SO.term_gain_linear(d, rs, rv, C.AMOUNT) for d in ds], mode="lines", name="lineare Annahme (gleicher Wert je Tag)", line=dict(color=C.COLOR_GREY, dash="dot"),
                             hovertemplate="Ziel %{x:.0f} Tage: %{y:.1f} Euro<extra></extra>"))
    fig.add_trace(go.Scatter(x=[st_summary["best"]], y=[st_summary["gain_best"]], mode="markers", name="bestes Ziel", marker=dict(size=12, color=C.COLOR_NASH, symbol="circle")))
    fig.update_xaxes(title_text="Zahlungsziel (Tage)")
    fig.update_yaxes(title_text="Gemeinsamer Gewinn (Euro je Tour)")
    return _base(fig, 340)


def build_risk(st_summary):
    qs = np.linspace(0, 1, 101)
    gs, gv = st_summary["gs"], st_summary["gv"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=qs * 100, y=[SO.risk_gain(q, gs, gv, C.RISK_A, C.RISK_P) for q in qs], mode="lines", name="Gewinn des Vertrags", line=dict(color=C.COLOR_FRONTIER, width=3),
                             hovertemplate="Risikoanteil %{x:.0f} %: %{y:.2f} Euro<extra></extra>"))
    if st_summary["q_star"] is not None:
        fig.add_trace(go.Scatter(x=[100 * st_summary["q_star"]], y=[st_summary["gain_star"]], mode="markers", name="bester Anteil q*", marker=dict(size=12, color=C.COLOR_NASH)))
    fig.add_trace(go.Scatter(x=[100 * st_summary["q"]], y=[st_summary["gain_q"]], mode="markers", name="gewählter Anteil", marker=dict(size=11, color=C.COLOR_V, symbol="diamond")))
    fig.update_xaxes(title_text="Risikoanteil des Verladers (%)")
    fig.update_yaxes(title_text="Gewinn (Euro je Tour)")
    return _base(fig, 340)


def build_bet(b, p_v, p_s):
    gamma = b["gamma"]
    w_max = 2.5 * (b["w_star"] if b["w_star"] else 300.0)
    ws = np.linspace(0, w_max, 101)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ws, y=[SO.bet_gain_cara(w, p_v, p_s, gamma) for w in ws], mode="lines", name="Gewinn der Wette (beide risikoscheu)", line=dict(color=C.COLOR_FRONTIER, width=3),
                             hovertemplate="Wettgröße %{x:.0f}: %{y:.2f} Euro<extra></extra>"))
    fig.add_trace(go.Scatter(x=ws, y=[abs(p_s - p_v) * w for w in ws], mode="lines", name="risikoneutral: |p_S − p_V| · w", line=dict(color=C.COLOR_GREY, dash="dot")))
    if b["w_star"] is not None:
        fig.add_trace(go.Scatter(x=[b["w_star"]], y=[b["gain_star"]], mode="markers", name="beste Größe w*", marker=dict(size=12, color=C.COLOR_NASH)))
    fig.update_xaxes(title_text="Wettgröße w (Euro je Tour)")
    fig.update_yaxes(title_text="Gemeinsamer Gewinn (Euro je Tour)")
    return _base(fig, 340)


def build_meso(meso):
    fig = go.Figure()
    for est, dash in (("Posterior-Mittel", "solid"), ("Max-Rand", "dash")):
        for r in C.MESO_RS:
            cells = [next(c for c in meso["cells"] if c["estimator"] == est and c["k"] == k and c["r"] == r) for k in C.MESO_KS]
            fig.add_trace(go.Scatter(x=list(C.MESO_KS), y=[c["g_end"]["mean"] for c in cells], mode="lines+markers", name=f"{est}, {r} Runde{'n' if r > 1 else ''}", line=dict(dash=dash),
                                     error_y=dict(type="data", array=[c["g_end"]["se"] for c in cells], visible=True), hovertemplate=f"{est}, {r}: k = %{{x}}, g = %{{y:.3f}}<extra></extra>"))
    fig.add_hline(y=meso["g_equal"]["mean"], line=dict(color=C.COLOR_GREY, dash="dot"), annotation_text="gleiche Gewichte (keine Information)", annotation_position="bottom right")
    fig.update_xaxes(title_text="Angebote je Runde k")
    fig.update_yaxes(title_text="Güte des Endangebots g", range=[0.2, 1.02])
    return _base(fig, 420)


def build_bundles(rows, chosen: int):
    xs = [str(r["size"]) for r in rows]
    ys = [0.0 if r["share"] is None else r["share"] for r in rows]
    colors = [C.COLOR_NASH if r["size"] == chosen else C.COLOR_FRONTIER for r in rows]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors, hovertemplate="Bündelgröße %{x}: %{y:.3f}<extra></extra>"))
    fig.update_xaxes(title_text="Bündelgröße (Punkte je Bündel)", type="category")
    fig.update_yaxes(title_text="Anteil des möglichen Gewinns", range=[0, 1.02])
    return _base(fig, 280)
