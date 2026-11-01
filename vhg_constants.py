"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Rechenaufwand am Slider-Maximum (DEMO-PLAYBOOK §1c): Grenze, Nash, Kalai–Smorodinsky, egalitär und Adjusted Winner kosten O(n log n) mit n <= 5 Punkten (Mikrosekunden); Zeit, Risiko und
Wette sind geschlossene Formeln. Die Rubinstein-Rechnung auf der Grenze ist eine Bisektion mit 200 Schritten über eine Grenze mit höchstens 6 Ecken (unter einer Millisekunde). Die MESO-Instanz
der App rechnet eine Instanz mit höchstens 3 Runden zu je 8 Angeboten: bis 21 Wahl-Ungleichungen, beim Max-Rand-Schätzer 12.650 Kombinationen von je 5 × 5 Gleichungen (rund 20 ms), beim
Posterior-Mittel eine 50.000 × 21-Matrix (rund 5 ms). Die Messreihen (Gitter, MESO) sind vorgerechnet (tools/make_grid.py, tools/make_meso.py)."""

# --- Punkte und ihre Werte ----------------------------------------------------------------------------------------------------------------
POINT_NAMES = ("Lieferfenster", "Zahlungsziel", "Rückladung", "Rampenzeit")
VALUE_MIN, VALUE_MAX = 0, 100                          # Wert eines Punktes für eine Seite, Euro je Tour
DEFAULT_V = (60, 25, 15, 0)                            # ein Punkt mit v = s = 0 zählt nicht (kein Gewicht für beide Seiten)
DEFAULT_S = (20, 30, 50, 0)
PRICE_MIN, PRICE_MAX, DEFAULT_PRICE = 0, 200, 0        # Preis-Spielraum M (Euro je Tour): der Preis-Punkt hat v = s = M
BUNDLE_MIN, BUNDLE_MAX, DEFAULT_BUNDLE = 1, 4, 3       # Bündelgröße (Punkte je Bündel; mehr als Punkte vorhanden heißt ein Paket)

# --- Zeit ---------------------------------------------------------------------------------------------------------------------------------
AMOUNT = 1000.0                                        # fester Betrag je Tour (Euro), Modellannahme
RATE_MIN, RATE_MAX, DEFAULT_RS, DEFAULT_RV = 0.0, 5.0, 1.0, 2.0     # Ungeduld in Prozent je Tag
TERM_MIN, TERM_MAX, DEFAULT_TERM = 0, 90, 30           # Zahlungsziel in Tagen
TERM_GRID = (0, 15, 30, 60, 90)

# --- Risiko -------------------------------------------------------------------------------------------------------------------------------
RISK_A, RISK_P = 200.0, 0.5                            # Gewinn des Spediteurs in der Lage „hoch“ (Euro je Tour) und seine Wahrscheinlichkeit
GAMMA_MIN, GAMMA_MAX, DEFAULT_GS, DEFAULT_GV = 0.0, 50.0, 5.0, 0.0   # Risikoscheu γ in Tausendsteln je Euro (γ = Wert / 1000)
Q_MIN, Q_MAX, DEFAULT_Q = 0, 100, 50                   # Risikoanteil des Verladers in Prozent
GAMMA_V_TABLE = (0.0, 2.5, 5.0, 10.0, 50.0)            # Tausendstel

# --- Einschätzung -------------------------------------------------------------------------------------------------------------------------
P_MIN, P_MAX, DEFAULT_PV, DEFAULT_PS = 0.05, 0.95, 0.4, 0.7
BONUS_MIN, BONUS_MAX, DEFAULT_BONUS = 0, 300, 100      # Bonus b der Gleitklausel (Euro je Tour)
BET_GAMMA_MIN, BET_GAMMA_MAX, DEFAULT_BET_GAMMA = 0.5, 20.0, 5.0     # Tausendstel je Euro
BASE_PRICE = 1000.0

# --- Brücke zum Verhandlungsstück ---------------------------------------------------------------------------------------------------------
DELTA_MIN, DELTA_MAX, DEFAULT_DELTA = 0.5, 0.99, 0.9   # Faktor δ je Runde (Rubinstein)

# --- MESO ---------------------------------------------------------------------------------------------------------------------------------
MESO_K_MIN, MESO_K_MAX, DEFAULT_MESO_K = 1, 8, 3
MESO_R_MIN, MESO_R_MAX, DEFAULT_MESO_R = 1, 3, 2
SEED_MAX, DEFAULT_SEED = 999_999, 35

# --- Messreihen ---------------------------------------------------------------------------------------------------------------------------
GRID_BLOCKS = 4                                        # unabhängige Blöcke (Zufallsströme) je Zelle
GRID_INSTANCES = 2000                                  # Instanzen je Block
E1_NS = (2, 3, 4, 5, 8)
E1_THETAS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)
E2_THETAS = (1.0, 0.5)
E2_N = 4
E2_MS = (0, 5, 10, 25, 50, 100, 200)
E2_LEVEL_MS = (0, 50, 200)                             # Zeilen mit s = 2 v
E6_N = 4
E6_THETAS = (1.0, 0.5)
ASYM_THETAS = (0.25, 0.5, 0.75, 1.0)
MESO_BLOCKS = 8
MESO_INSTANCES = 500                                   # Instanzen je Block
MESO_KS = (1, 2, 3, 4, 5, 6, 8)
MESO_RS = (1, 2, 3)
EXP_SEED = 20261101                                    # Grundlage der Seeds der Live-Stichproben in den Tests

# --- ab hier nicht mehr im Erzeuger-Hash der Messreihen (Farben, Presets) ---------------------------------------------------------
# --- Farben -------------------------------------------------------------------------------------------------------------------------------
COLOR_V = "#2F6B65"            # Verlader
COLOR_S = "#C0762B"            # Spediteur
COLOR_FRONTIER = "#4c78a8"
COLOR_GREY = "rgba(150,150,150,0.65)"
COLOR_NASH = "#d62728"
COLOR_KS = "#9467bd"
COLOR_EGAL = "#17becf"
COLOR_AW = "#8c564b"
COLOR_MID = "#7f7f7f"

# --- Presets ------------------------------------------------------------------------------------------------------------------------------
BASE = {
    "v1": DEFAULT_V[0], "v2": DEFAULT_V[1], "v3": DEFAULT_V[2], "v4": DEFAULT_V[3],
    "s1": DEFAULT_S[0], "s2": DEFAULT_S[1], "s3": DEFAULT_S[2], "s4": DEFAULT_S[3],
    "price": DEFAULT_PRICE, "bundle": DEFAULT_BUNDLE, "rs": DEFAULT_RS, "rv": DEFAULT_RV, "term": DEFAULT_TERM,
    "gs": DEFAULT_GS, "gv": DEFAULT_GV, "q": DEFAULT_Q, "pv": DEFAULT_PV, "ps": DEFAULT_PS, "bonus": DEFAULT_BONUS, "gb": DEFAULT_BET_GAMMA,
    "dv": DEFAULT_DELTA, "ds": DEFAULT_DELTA, "k": DEFAULT_MESO_K, "r": DEFAULT_MESO_R, "est": "Posterior-Mittel", "seed": DEFAULT_SEED,
}
PRESETS = {
    "Standard (drei Punkte, ohne Geld)": dict(BASE),
    "Handbeispiel (zwei Punkte)": {**BASE, "v1": 80, "v2": 20, "v3": 0, "s1": 30, "s2": 70, "s3": 0, "bundle": 2},
    "Seitenzahlung bis zur Schwelle": {**BASE, "v1": 80, "v2": 20, "v3": 0, "s1": 30, "s2": 70, "s3": 0, "bundle": 2, "price": 10},
    "Gleiche Gewichte (kein Gewinn)": {**BASE, "v1": 50, "v2": 30, "v3": 20, "s1": 50, "s2": 30, "s3": 20},
    "Gleiches Profil, doppeltes Niveau": {**BASE, "v1": 40, "v2": 30, "v3": 10, "s1": 80, "s2": 60, "s3": 20, "price": 200},
    "Zeit: Verlader ungeduldiger": {**BASE, "rs": 1.0, "rv": 2.0, "term": 70},
    "Risiko: nur der Spediteur scheut": {**BASE, "gs": 5.0, "gv": 0.0, "q": 100},
    "Gleiche Einschätzung (kein Gewinn)": {**BASE, "pv": 0.55, "ps": 0.55},
    "MESO: Max-Rand-Schätzer, zwei Angebote": {**BASE, "k": 2, "r": 1, "est": "Max-Rand"},
}
PRESET_HELP = {
    "Standard (drei Punkte, ohne Geld)": "Drei Punkte (Lieferfenster, Zahlungsziel, Rückladung) mit Gewichten 60, 25, 15 für den Verlader und 20, 30, 50 für den Spediteur, ohne Geld. Beide Seiten haben dieselbe Summe 100; "
                                          "der Gewinn des Tauschs ist ½ Σ|v − s| = 40 Punkte.",
    "Handbeispiel (zwei Punkte)": "Zwei Punkte mit v = (80, 20) und s = (30, 70): die Ecken der Grenze sind (100; 0), (80; 70) und (0; 100). Nash-Lösung (80; 70), Kalai–Smorodinsky und egalitär (72,7; 72,7) = (800/11; 800/11).",
    "Seitenzahlung bis zur Schwelle": "Dasselbe Handbeispiel mit Preis-Spielraum 10 Euro, genau der Schwelle M* = |80 − 70|: ab hier teilen Nash, Kalai–Smorodinsky und egalitär die größte Summe 160 hälftig (80; 80).",
    "Gleiche Gewichte (kein Gewinn)": "Beide Seiten gewichten die drei Punkte gleich (50, 30, 20): der Tausch bringt nichts, die Grenze ist die Gerade der Summe 100 und der Positionskompromiss (50; 50) liegt auf ihr.",
    "Gleiches Profil, doppeltes Niveau": "Der Spediteur bewertet alle Punkte doppelt so hoch wie der Verlader (v = (40, 30, 10), s = (80, 60, 20)): gleiche Verhältnisse, kein Tauschgewinn der Punkte allein, aber ein Gewinn von 40 Euro in der "
                                         "Summe, erreichbar erst mit Geld (Preis-Spielraum 200 ≥ M* = 160).",
    "Zeit: Verlader ungeduldiger": "Zahlungsziel mit Ungeduld 1 % je Tag beim Spediteur und 2 % beim Verlader, Betrag 1.000 Euro: das beste Ziel ist d* = 69,3 Tage mit einem Gewinn von 250 Euro; 30 Tage bringen 192 Euro.",
    "Risiko: nur der Spediteur scheut": "Der Spediteur scheut das Risiko (γ = 0,005 je Euro), der Verlader ist neutral und trägt das ganze Risiko (q = 100 %): Gewinn 24,02 Euro je Tour, obwohl beide dieselbe Wahrscheinlichkeit annehmen.",
    "Gleiche Einschätzung (kein Gewinn)": "Beide halten „der Markt steigt“ für gleich wahrscheinlich (55 %): die Gleitklausel bringt in der Summe der Einschätzungen nichts, und mit Risikoscheu kostet jede Wette.",
    "MESO: Max-Rand-Schätzer, zwei Angebote": "Simulation: der Verlader legt in einer Runde zwei gleichwertige Pakete vor und schätzt die Gewichte des Spediteurs mit dem Max-Rand-Schätzer (Zufalls-Seed 35). Im Mittel ist dieser Schätzer bei zwei Angeboten schlechter als gar keine Information (E7). Modellannahmen, kein Befund über Menschen.",
}
