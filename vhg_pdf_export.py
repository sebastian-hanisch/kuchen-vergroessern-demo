"""PDF-Export (fpdf2, Kernschriften): Einstellungen, Kennzahlen und die Verdikte. Erst nach Klick erzeugt (DEMO-PLAYBOOK §1c)."""

from __future__ import annotations

from fpdf import FPDF

import vhg_evaluation as V
from vhg_scenario import Settings

_REPLACE = {"–": "-", "—": "-", "≤": "<=", "≥": ">=", "≠": "!=", "√": "Wurzel", "²": "2", "Σ": "Summe", "°": " Grad", "·": "*", "−": "-", "„": '"', "“": '"', "∞": "unendlich",
            "→": "->", "ε": "eps", "β": "beta", "α": "alpha", "θ": "theta", "λ": "lambda", "σ": "sigma", "π": "pi", "δ": "delta", "η": "eta", "Δ": "Delta", "γ": "gamma", "ρ": "rho",
            "≈": "~", "½": "1/2", "…": "...", "‚": ",", "‘": "'", "’": "'", "”": '"', "µ": "mu", "∈": "in", "⁻": "^-", "¹": "1", "₀": "0", "₁": "1", "₂": "2", "ₘ": "m", "ₛ": "s",
            "*": "*", "⁎": "*"}


def _latin(text: str) -> str:
    """Kernschriften kennen nur Latin-1 (Umlaute gehören dazu): Sonderzeichen ersetzen, Markdown-Sterne entfernen."""
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text.replace("**", "").replace("`", "").encode("latin-1", "replace").decode("latin-1")


def build_pdf(st: Settings, view: V.TradeView, verdicts: list[tuple[str, str]]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _latin("Woher kommt der Gewinn? Kuchen vergrößern"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pts = ", ".join(f"{n}: Verlader {V.de(a, 0)}, Spediteur {V.de(b, 0)}" for n, a, b in zip(view.names, view.v, view.s))
    pdf.multi_cell(0, 5, _latin(f"Punkte (Euro je Tour): {pts}; Preis-Spielraum M = {V.de(st.price, 0)}; Bündelgröße {st.bundle}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Lösungen auf der Pareto-Grenze", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for row in V.solution_table(view):
        pdf.multi_cell(0, 5, _latin(f"{row['Lösung']}: Verlader {row['Verlader']}, Spediteur {row['Spediteur']}, Summe {row['Summe']}; {row['Anteil des möglichen Gewinns']}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Verdikte", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for _, text in verdicts:
        pdf.multi_cell(0, 5, _latin(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _latin("Gewichte, Nutzenfunktionen und Eigennutz sind Modellannahmen, keine Aussagen über echte Betriebe. Alle Zahlen sind eigene Rechnung, gestützt durch Handrechnung, "
                                "zweite Rechenwege (Aufzählung, lineare Programme, Optimierer) und Simulation; MESO ist eine Simulation."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
