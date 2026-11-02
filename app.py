"""Woher kommt der Gewinn? Kuchen vergrößern - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „Regeln setzen, verhandeln, kontrollieren“. Ein Verlader und ein Spediteur verhandeln mehrere Punkte zugleich. Die Demo rechnet die Pareto-Grenze des Tauschs, die Lösungen darauf
(Nash, Kalai–Smorodinsky, egalitär, Adjusted Winner), die Seitenzahlung mit ihrer Schwelle, Zeit, Risiko und Einschätzung als weitere Quellen des Gewinns und eine MESO-Simulation.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import vhg_constants as C
import vhg_evaluation as V
import vhg_experiments as XP
import vhg_meso as ME
import vhg_texts as T
import vhg_visualization as Z
from vhg_layout import dunkles_design, kopf_css
from vhg_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    settings_from_state,
    sidebar_presets,
    sync_query_params,
)
from vhg_scenario import effective_bundle

st.set_page_config(page_title="Kuchen vergrößern – Sebastian Hanisch", layout="wide")


# --- Zwischenspeicher (Schlüssel = alle Eingaben inklusive Zufalls-Seed) --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _grid():
    return XP.load_grid()


@st.cache_data(show_spinner=False)
def _meso():
    return XP.load_meso()


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return V.analyse(settings)


@st.cache_data(show_spinner=False)
def _meso_live(settings):
    return V.meso_live(settings)


def show(verdict):
    kind, text = verdict
    getattr(st, kind)(text)


def table(rows):
    st.dataframe(rows, hide_index=True, width="stretch")


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in vhg_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🥧 Woher kommt der Gewinn? Kuchen vergrößern")
st.markdown(T.INTRO)

with st.expander("So entsteht der Gewinn in sechs Schritten", expanded=True):
    st.markdown(T.EXPLAINER)

with st.expander("Erklärtabelle: was die Regler tun"):
    st.markdown(T.CONTROLS_TABLE)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("📦 Punkte und Tausch")
    st.caption("Ein Punkt, der beiden Seiten nichts wert ist (beide Werte 0), wird nicht verhandelt.")
    st.markdown("**Wert für den Verlader** (Euro je Tour)")
    for i in range(1, 5):
        st.slider(f"{C.POINT_NAMES[i - 1]} (Verlader)", *bounds(f"v{i}_slider"), key=f"v{i}_slider", step=1,
                  help="Was dieser Punkt dem Verlader wert ist, wenn er ganz zu seinen Gunsten entschieden wird.")
    st.markdown("**Wert für den Spediteur** (Euro je Tour)")
    for i in range(1, 5):
        st.slider(f"{C.POINT_NAMES[i - 1]} (Spediteur)", *bounds(f"s{i}_slider"), key=f"s{i}_slider", step=1,
                  help="Was dieser Punkt dem Spediteur wert ist, wenn er ganz zu seinen Gunsten entschieden wird.")
    st.slider("Preis-Spielraum M (Euro je Tour)", *bounds("price_slider"), key="price_slider", step=1,
              help="Ein Preis-Punkt, der beiden gleich viel wert ist (1 Euro hier = 1 Euro dort). 0 heißt: kein Geld im Spiel, nur Tausch der Punkte.")
    st.slider("Bündelgröße", *bounds("bundle_slider"), key="bundle_slider", step=1,
              help="Wie viele Punkte zusammen verhandelt werden (jedes Bündel für sich bei seiner Nash-Lösung, ohne Preis). Größer als die Zahl der Punkte heißt: ein Paket.")
    st.header("⏱️ Zeit: Zahlungsziel")
    st.slider("Ungeduld des Spediteurs r_S (% je Tag)", *bounds("rs_slider"), key="rs_slider", step=0.05, help="Wie viel dem Spediteur ein Tag Warten auf das Geld wert ist (Prozent des Betrags je Tag, wie das δ = exp(−r·Δ) im Verhandlungsstück).")
    st.slider("Ungeduld des Verladers r_V (% je Tag)", *bounds("rv_slider"), key="rv_slider", step=0.05, help="Dasselbe für den Verlader: wer das Geld früher braucht, zahlt lieber später.")
    st.slider("Zahlungsziel d (Tage)", *bounds("term_slider"), key="term_slider", step=1, help="Vereinbartes Ziel bei festem Betrag von 1.000 Euro je Tour.")
    st.header("🎲 Risiko")
    st.slider("Risikoscheu des Spediteurs γ_S (‰ je Euro)", *bounds("gs_slider"), key="gs_slider", step=0.5, help="Konstante absolute Risikoscheu in Tausendsteln je Euro; 0 ist risikoneutral.")
    st.slider("Risikoscheu des Verladers γ_V (‰ je Euro)", *bounds("gv_slider"), key="gv_slider", step=0.5, help="Dasselbe für den Verlader.")
    st.slider("Risikoanteil des Verladers q (%)", *bounds("q_slider"), key="q_slider", step=5, help="Welchen Anteil des Auslastungsrisikos (Gewinn 200 Euro mit Wahrscheinlichkeit ½, sonst 0) der Verlader trägt.")
    st.header("🔮 Einschätzung")
    st.slider("Einschätzung des Verladers p_V", *bounds("pv_slider"), key="pv_slider", step=0.05, help="Wie wahrscheinlich der Verlader hält, dass die Marktrate steigt.")
    st.slider("Einschätzung des Spediteurs p_S", *bounds("ps_slider"), key="ps_slider", step=0.05, help="Dasselbe für den Spediteur.")
    st.slider("Bonus b der Gleitklausel (Euro je Tour)", *bounds("bonus_slider"), key="bonus_slider", step=10, help="Steigt die Marktrate, bekommt die Seite mit der höheren Einschätzung diesen Bonus.")
    st.slider("Risikoscheu der Wette γ (‰ je Euro)", *bounds("gb_slider"), key="gb_slider", step=0.5, help="Für die endliche Wette: beide Seiten mit derselben Risikoscheu.")
    st.header("🤝 Verhandlungsspiel")
    st.slider("Geduld des Verladers δ_V je Runde", *bounds("dv_slider"), key="dv_slider", step=0.01, help="Faktor je Runde im Rubinstein-Spiel; der Verlader bietet zuerst.")
    st.slider("Geduld des Spediteurs δ_S je Runde", *bounds("ds_slider"), key="ds_slider", step=0.01, help="Faktor je Runde für den Spediteur.")
    st.header("🧪 MESO (Simulation)")
    st.slider("Angebote je Runde k", *bounds("k_slider"), key="k_slider", step=1, help="Wie viele gleichwertige Pakete der Verlader je Runde vorlegt.")
    st.slider("Runden", *bounds("r_slider"), key="r_slider", step=1, help="Wie viele Runden der Verlader lernt, ehe er sein Endangebot macht.")
    st.selectbox("Schätzer", ("Posterior-Mittel", "Max-Rand"), key="est_select", help="Wie der Verlader aus den Wahlen die Gewichte des Spediteurs schätzt.")
    st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

settings = settings_from_state()
sync_query_params({k: st.session_state[k] for k in SETTING_SPECS})

verdicts = []      # Verdikte für den PDF-Export
grid = _grid()
meso = _meso()
if grid is None or meso is None:
    st.warning("Die vorgerechneten Messreihen (data/grid.json, data/meso.json) fehlen oder gehören zu einem anderen Rechencode: `python tools/make_grid.py` und `python tools/make_meso.py` ausführen. Die Experimente zeigen dann keine Reihen.")

view = _analysis(settings)

# --- Hauptansicht --------------------------------------------------------------------------------------------------------------------------
st.markdown("## 🎯 Ergebnis: Tausch auf der Pareto-Grenze")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Gewinn", V.de(view.gain, 1), help="Gewinn des Tauschs: größte Summe der Nutzen minus Summe beim Positionskompromiss (jeder Punkt in der Mitte) = ½ Σ|v − s|. Der Preis-Punkt ändert ihn nicht.")
m2.metric("Größte Summe", V.de(view.t_max, 1), help="Auf der Pareto-Grenze: Σ max(v, s) plus der Preis-Spielraum M.")
m3.metric("Nash: Verlader", V.de(view.nash[0], 1), help="Nutzen des Verladers bei der Nash-Lösung (Maximum des Produkts der Nutzen auf der Grenze, Rückfall 0).")
m4.metric("Nash: Spediteur", V.de(view.nash[1], 1), help="Nutzen des Spediteurs bei der Nash-Lösung.")
m5.metric("Schwelle M*", V.de(view.m_star, 0), help="Ab diesem Preis-Spielraum teilt die Nash-Lösung die größte Summe hälftig (Gleichstände v = s verlängern das Stück der Steigung −1).")
col_a, col_b = st.columns([3, 2])
with col_a:
    st.plotly_chart(Z.build_frontier(view), width="stretch", key="frontier_chart")
    st.caption("Grau: erreichbare Nutzenpaare; blau: Pareto-Grenze, deren Ecken die Zwischenstände der Abgabe sind (absteigend nach s/v). Alles unterhalb der Grenze ist dominiert.")
with col_b:
    table([{"Punkt": n, "v (Verlader)": V.de(a, 0), "s (Spediteur)": V.de(b, 0), "s / v": "–" if a == 0 else V.de(b / a, 2), "Reihenfolge der Abgabe": str(view.order.index(i) + 1)}
           for i, (n, a, b) in enumerate(zip(view.point_names(), view.vp, view.sp))])
    st.caption("Reihenfolge der Abgabe: die Punkte mit dem größten s / v gehen zuerst vom Verlader an den Spediteur.")
st.markdown("#### ❓ Kernfrage: Gibt es etwas zu gewinnen, und was erreichen die Lösungen?")
v_trade = V.verdict_trade(view)
show(v_trade)
verdicts.append(v_trade)

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["1 Tausch und Bündel", "2 Seitenzahlung", "3 Zeit und Risiko", "4 Bedingter Vertrag", "5 MESO"])

# --- Tab 1 ---------------------------------------------------------------------------------------------------------------------------------
with tab1:
    st.subheader("🔬 Experiment E1: Woher kommt der Gewinn des Tauschs?")
    st.caption("**Erwartung:** Der Gewinn wächst mit dem Unterschied der Gewichte und ist null, wenn beide Seiten gleich gewichten. "
               "Zufallsgewichte: Verlader Dirichlet(1), Spediteur (1 − θ) · Verlader + θ · unabhängig Dirichlet(1); je Zelle 4 Blöcke zu je 2.000 Instanzen, ± ist der Standardfehler der Blöcke, Summe 100 je Seite.")
    st.markdown("**Die Regler der Seitenleiste:**")
    table(V.solution_table(view))
    v_hook = V.verdict_hook(view)
    show(v_hook)
    if grid:
        e1_n = st.selectbox("Zahl der Punkte n der Reihe", C.E1_NS, index=2, key="e1_n")
        table(V.e1_table(grid, e1_n))
        col_c, col_d = st.columns(2)
        with col_c:
            st.plotly_chart(Z.build_gain_theta(grid), width="stretch", key="gain_theta_chart")
            st.caption("Gewinn über dem Gewichtsunterschied θ, je Zahl der Punkte: je Instanz exakt linear in θ.")
        with col_d:
            st.plotly_chart(Z.build_theta(grid, e1_n), width="stretch", key="theta_chart")
            st.caption("Anteil des möglichen Gewinns, den Nash und Kalai–Smorodinsky erreichen (θ = 0: kein Gewinn, kein Anteil).")
        v1 = V.verdict_e1(grid)
        show(v1)
        verdicts.append(v1)
        st.markdown("**Offener Punkt aus dem Plan: warum bekommt in E1 der Verlader mehr?**")
        table(V.asymmetry_table(grid))
        va = V.verdict_asymmetry(grid)
        show(va)
        verdicts.append(va)
    st.markdown("---")
    st.subheader("🔬 Experiment E2: Bündelgröße statt Themenreihenfolge")
    st.caption("**Erwartung:** Verhandelt man die Punkte einzeln nacheinander, geht Gewinn verloren; je größer das Bündel, desto mehr wird gehoben, und die Reihenfolge der Themen kostet Effizienz. "
               "Jedes Bündel wird für sich bei seiner Nash-Lösung (Rückfall 0) abgeschlossen; der Preis ist nicht dabei.")
    rows_b = V.bundle_table(settings)
    table(rows_b)
    st.plotly_chart(Z.build_bundles(V.bundle_rows(settings), effective_bundle(settings)), width="stretch", key="bundle_chart")
    v_b = V.verdict_bundle(settings, V.bundle_rows(settings))
    show(v_b)
    verdicts.append(v_b)
    if grid:
        table(V.e2_table(grid))
        v2 = V.verdict_e2(grid)
        show(v2)
        verdicts.append(v2)

# --- Tab 2 ---------------------------------------------------------------------------------------------------------------------------------
with tab2:
    st.subheader("🔬 Experiment E3: Seitenzahlung und die Schwelle M*")
    st.caption("**Erwartung:** Mit genug Geld teilen Nash, Kalai–Smorodinsky und egalitär die größte Summe hälftig; ohne Geld bleibt der Gewinn teilweise liegen. "
               "Preis-Punkt mit v = s = M; Anteil des möglichen Gewinns bei den Punkten der Seitenleiste (ohne deren Preis-Spielraum).")
    v_money = V.verdict_money(view)
    show(v_money)
    verdicts.append(v_money)
    curve = V.price_curve(settings)
    st.plotly_chart(Z.build_price(curve, view.m_star), width="stretch", key="price_chart")
    st.caption("Anteil des möglichen Gewinns über dem Preis-Spielraum M für die Punkte der Seitenleiste. Ab M* teilen die drei Lösungen die größte Summe hälftig, bei gleichen Gesamtwerten.")
    if grid:
        table(V.e3_table(grid))
        st.caption("Zufallsgewichte θ = 1, n = 4 Punkte, Summe 100 je Seite, 4 Blöcke zu je 2.000 Instanzen. Zeilen s = 2 v (gleiches Profil, doppeltes Niveau):")
        table(V.e3_level_table(grid))
        v3 = V.verdict_e3(grid)
        show(v3)
        verdicts.append(v3)
    st.markdown("**Brücke zum Verhandlungsstück: die Aufteilung der größten Summe T als Rubinstein-Spiel** (Faktoren δ_V und δ_S der Seitenleiste, Punkte und Preis-Spielraum wie eingestellt)")
    bridge = V.bridge(view, settings.dv, settings.ds)
    table([{"": "Vorschlag von V (V bietet zuerst)", "Verlader": V.de(bridge["p"][0], 1), "Spediteur": V.de(bridge["p"][1], 1)},
           {"": "Gegenvorschlag von S", "Verlader": V.de(bridge["q"][0], 1), "Spediteur": V.de(bridge["q"][1], 1)},
           {"": "T · (1 − δ_S) / (1 − δ_V δ_S), T = größte Summe", "Verlader": V.de(bridge["t_split"][0], 1), "Spediteur": V.de(bridge["t_split"][1], 1)}])
    v_bridge = V.verdict_bridge(bridge, settings.dv, settings.ds)
    show(v_bridge)
    verdicts.append(v_bridge)

# --- Tab 3 ---------------------------------------------------------------------------------------------------------------------------------
with tab3:
    st.subheader("🔬 Experiment E4: Zeit als Quelle des Gewinns")
    st.caption("**Erwartung:** Ein Zahlungsziel bringt nur etwas, wenn die Seiten verschieden ungeduldig sind, und der Gewinn wächst mit dem Ziel. Betrag fest 1.000 Euro je Tour; Modellannahme.")
    ts = V.term_summary(settings)
    st.plotly_chart(Z.build_term(ts), width="stretch", key="term_chart")
    table(V.term_display(settings))
    st.caption(f"Das Zahlungsziel als „linearer Punkt“ ist eine grobe Annahme: die Mitte der beiden Endwerte (sofort 0 Euro, {C.TERM_MAX} Tage {V.de(ts['mid_of_ends'] * 2, 1)} Euro) wäre {V.de(ts['mid_of_ends'], 1)} Euro, "
               f"das Ziel von {V.de(C.TERM_MAX / 2, 0)} Tagen bringt {V.de(ts['gain_mid'], 1)} Euro.")
    v_time = V.verdict_time(ts)
    show(v_time)
    verdicts.append(v_time)
    st.markdown("---")
    st.subheader("🔬 Experiment E5: Risiko als Quelle des Gewinns")
    st.caption("**Erwartung:** Ein Vertrag, der das Risiko teilt, bringt nur etwas, wenn die Seiten verschieden viel dafür verlangen, und halbe-halbe ist optimal. "
               f"Der Gewinn des Spediteurs je Tour ist {V.de(C.RISK_A, 0)} Euro mit Wahrscheinlichkeit ½, sonst 0; beide nehmen dieselbe Wahrscheinlichkeit an und jeder Erwartungswert bleibt unverändert.")
    rs_ = V.risk_summary(settings)
    st.plotly_chart(Z.build_risk(rs_), width="stretch", key="risk_chart")
    table(V.risk_display(settings))
    st.caption(f"Zeilen mit γ_S = {V.de(settings.gs, 1)} ‰ je Euro. Sicherheitsäquivalent des Spediteurs allein: {V.de(rs_['ce_alone'], 2)} Euro statt Erwartungswert {V.de(rs_['mean'], 0)}.")
    v_risk = V.verdict_risk(rs_)
    show(v_risk)
    verdicts.append(v_risk)

# --- Tab 4 ---------------------------------------------------------------------------------------------------------------------------------
with tab4:
    st.subheader("🔬 Experiment E6: Ändern bedingte Verträge nur die Verteilung?")
    st.caption("**Erwartung (die Gegenposition):** Eine Gleitklausel verteilt nur um, sie vergrößert den Kuchen nicht. Die Standardlehre misst mit der Einschätzung jeder Seite, "
               "die Gegenposition (englische Wikipedia-Seite „Contingent contract“ nennt Brett 2007; Quelle nicht eingesehen) mit einer gemeinsamen Wahrscheinlichkeit oder nachträglich. Hier derselbe Vertrag mit allen drei Maßstäben.")
    bs = V.bet_summary(settings)
    table(V.bet_display(bs))
    st.caption("Erwartungsgewinn je Tour in Euro. Der Preis ist so gesetzt, dass die eigene Einschätzung den Gewinn hälftig teilt. "
               + ("Die Klausel zahlt an den " + bs["high_side"] + "." if bs["high_side"] else "Bei gleicher Einschätzung zahlt die Klausel an niemanden."))
    v_bet = V.verdict_bet(bs, settings)
    show(v_bet)
    verdicts.append(v_bet)
    st.markdown("**Auflösung:** Beide Aussagen stimmen, mit verschiedener Bewertung. Mit der eigenen Einschätzung wächst der Kuchen um |p_S − p_V| · b; mit einer gemeinsamen Wahrscheinlichkeit oder nachträglich ist die Summe 0. "
                "Der Gewinn ist ein „gefühlter“, und höchstens eine Seite hat recht; welche Rechnung gilt, hängt an der Bewertungsannahme, nicht an der Mathematik.")
    st.markdown("**Sind beide risikoscheu, ist die Wette endlich**")
    st.plotly_chart(Z.build_bet(bs, settings.pv, settings.ps), width="stretch", key="bet_chart")
    table(V.bet_estimate_display(bs["gamma"]))
    st.caption(f"Zeilen mit γ = {V.de(bs['gamma'], 4)} je Euro, p_V = 0,4 fest: der Gewinn der besten Wette wächst ungefähr quadratisch im Unterschied der Einschätzungen.")
    v_cara = V.verdict_bet_cara(bs)
    show(v_cara)
    verdicts.append(v_cara)

# --- Tab 5 ---------------------------------------------------------------------------------------------------------------------------------
with tab5:
    st.subheader("🔬 Experiment E7: MESO – mehrere gleichwertige Angebote (Simulation)")
    st.caption("**Erwartung:** Mehr als drei Angebote je Runde bringen kaum etwas. **Simulation unter Modellannahmen, kein Befund über Menschen:** 4 Punkte mit je 5 Stufen (625 Pakete), Gewichte unabhängig Dirichlet(1), "
               "der Verlader legt nur Pakete vor, die ihm (fast) gleich viel bringen (Band ±0,025 um ½), der Spediteur wählt ehrlich das beste, der Verlader schätzt seine Gewichte und macht ein Endangebot. "
               "g = 0 für ein Zufallspaket des Bandes, g = 1 für das beste.")
    if meso:
        r_pick = st.selectbox("Runden der Reihe", C.MESO_RS, index=0, key="meso_r")
        table(V.meso_table(meso, r_pick))
        st.caption(f"Vorgerechnet: {meso['blocks']} Blöcke zu je {meso['instances_per_block']} Instanzen; Band im Mittel {V.de(meso['band_mean'], 1)} Pakete (kleinstes {meso['band_min']}, größtes {meso['band_max']}). "
                   f"Gleiche Gewichte als Schätzung (keine Information): g = {V.mean_se({'g': meso['g_equal']}, 'g', 3)}, Fehler {V.mean_se({'e': meso['err_equal']}, 'e', 3)}.")
        st.plotly_chart(Z.build_meso(meso), width="stretch", key="meso_chart")
        v_meso = V.verdict_meso(meso)
        show(v_meso)
        verdicts.append(v_meso)
    st.markdown("**Eine Instanz live** (Angebote, Runden, Schätzer und Zufalls-Seed der Seitenleiste)")
    live = _meso_live(settings)
    v_live = V.verdict_meso_live(live)
    show(v_live)
    verdicts.append(v_live)
    if live is not None:
        table([{"Runde": str(r["round"]), "vorgelegte Pakete (Stufen der vier Punkte)": " | ".join(", ".join(f"{x:g}" for x in ME.PACKAGES[i]) for i in r["offered"]) or "–",
                "gewählt": "–" if r["chosen"] is None else ", ".join(f"{x:g}" for x in ME.PACKAGES[r["chosen"]])} for r in live["log"]])
        table([{"": "wahre Gewichte des Spediteurs", **{C.POINT_NAMES[i]: V.de(float(live["b"][i]), 2) for i in range(4)}},
               {"": f"Schätzung ({live['estimator_used']})", **{C.POINT_NAMES[i]: V.de(float(live["w_hat"][i]), 2) for i in range(4)}}])

# --- Verwandte Demos, Grenzen, Formeln -----------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔗 Verwandte Demos")
st.markdown(
    "- [`verhandlung-demo`](https://github.com/sebastian-hanisch/verhandlung-demo): Nash, Kalai–Smorodinsky, egalitär und Rubinstein auf **einer** Verhandlungsmenge; die Aufteilung des Überschusses.\n"
    "- `kuchenteilung-demo`: teilbarer Kuchen ohne Verhandlung, Protokolle und Preis der Neidfreiheit.\n"
    "- [`pareto-dominanz-demo`](https://github.com/sebastian-hanisch/pareto-dominanz-demo): Dominanz von Alternativen, keine zwei Verhandlungsseiten.\n"
    "- [`kern-demo`](https://github.com/sebastian-hanisch/kern-demo): Aufteilung eines gegebenen Gewinns ohne Verhandlungsablauf."
)

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(T.ASSUMPTIONS_MARKDOWN)

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(T.MATH_MARKDOWN)

st.subheader("📄 Ergebnisse als PDF")
if st.button("PDF erstellen", key="pdf_button"):
    from vhg_pdf_export import build_pdf
    st.session_state["pdf_bytes"] = build_pdf(settings, view, verdicts)
if st.session_state.get("pdf_bytes"):
    st.download_button("⬇️ PDF herunterladen", st.session_state["pdf_bytes"], file_name="kuchen-vergroessern.pdf", mime="application/pdf", key="pdf_download")

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Regeln setzen, verhandeln, kontrollieren](https://sebastianhanisch.net/konzepte-verhandeln.html)."
)
