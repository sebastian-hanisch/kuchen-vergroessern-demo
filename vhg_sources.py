"""Drei weitere Quellen des Gewinns, je ein Mini-Modell mit geschlossener Lösung: Zeit (Zahlungsziel), Risiko (Teilen eines Risikos) und Einschätzung (bedingter Vertrag).

Alle Modelle sind **Modellannahmen**, keine Aussagen über Betriebe. Alle Einheiten sind reine Funktionen ohne Zustand; die geschlossenen Formeln werden in den Tests gegen Gitter und
`scipy.optimize` geprüft, zur Laufzeit wird scipy nicht gebraucht.

**Zeit.** Eine Zahlung X, fällig nach d Tagen, kostet den Verlader V (Zahler) X·exp(−r_V·d) und ist dem Spediteur S (Empfänger) X·exp(−r_S·d) wert; r ist die Ungeduld (Zeitpräferenz) je Tag, wie
das δ = exp(−r·Δ) im Verhandlungsstück. Bleibt der Betrag B fest, ist der gemeinsame Gewinn des Zahlungsziels f(d) = B (exp(−r_S d) − exp(−r_V d)), größtmöglich bei d* = ln(r_V / r_S) / (r_V − r_S).

**Risiko.** Der Gewinn des Spediteurs je Tour ist A in der Lage „hoch“ (Wahrscheinlichkeit p), sonst 0; beide legen dieselbe Wahrscheinlichkeit zugrunde. Nutzen mit konstanter absoluter
Risikoscheu γ (CARA): Sicherheitsäquivalent CE = −ln E exp(−γ·x) / γ (γ = 0: der Erwartungswert). V trägt den Anteil q des Risikos (er zahlt S den Betrag q·(E − Gewinn), Mittel null); der Gewinn des Vertrags
ist die Summe der Sicherheitsäquivalente nach dem Vertrag minus vorher, am größten bei q* = γ_S / (γ_S + γ_V) (Borch-Regel bei CARA).

**Einschätzung.** V und S halten die Lage „hoch“ (der Markt steigt) für verschieden wahrscheinlich (p_V, p_S). Eine Gleitklausel zahlt in „hoch“ den Bonus b an die Seite, die „hoch“ für wahrscheinlicher hält;
bewertet jede Seite mit ihrer eigenen Einschätzung, entsteht der gemeinsame Gewinn |p_S − p_V|·b. Sind beide risikoscheu (γ), ist die Wette endlich: größter Gewinn bei der Wettgröße
w* = ln(Quotenverhältnis) / (2γ) mit Quotenverhältnis (p_S / (1 − p_S)) / (p_V / (1 − p_V))."""

import math

# --------------------------------------------------------------------------------- Zeit


def term_gain(d: float, r_s: float, r_v: float, amount: float) -> float:
    """Gemeinsamer Gewinn des Zahlungsziels d (Tage) bei festem Betrag: amount · (exp(−r_s·d) − exp(−r_v·d))."""
    return amount * (math.exp(-r_s * d) - math.exp(-r_v * d))


def term_optimum(r_s: float, r_v: float) -> float | None:
    """Zahlungsziel mit dem größten Gewinn, d* = ln(r_v / r_s) / (r_v − r_s); nur für r_v > r_s > 0 (sonst gibt es kein Maximum im Inneren: None)."""
    if not (r_v > r_s > 0):
        return None
    return math.log(r_v / r_s) / (r_v - r_s)


def best_term(r_s: float, r_v: float, d_max: float) -> float:
    """Bestes Zahlungsziel in [0, d_max]: d* (auf d_max begrenzt) für r_v > r_s; ist r_v <= r_s, ist jedes Ziel über 0 nicht besser als sofort (0), also 0. Bei r_s = 0 und r_v > 0 wächst f bis d_max."""
    if r_v <= r_s:
        return 0.0
    d_star = term_optimum(r_s, r_v)
    return d_max if d_star is None else min(d_star, d_max)


def term_gain_linear(d: float, r_s: float, r_v: float, amount: float) -> float:
    """Die lineare Näherung amount · (r_v − r_s) · d, wie ein Punkt ‚Zahlungsziel‘ mit gleichmäßigem Wert je Tag sie annähme."""
    return amount * (r_v - r_s) * d


# --------------------------------------------------------------------------------- Risiko


def ce_cara(values, probs, gamma: float) -> float:
    """Sicherheitsäquivalent bei konstanter absoluter Risikoscheu γ: −ln Σ p·exp(−γ·x) / γ; γ = 0 ist der Erwartungswert."""
    if gamma == 0:
        return sum(p * x for p, x in zip(probs, values))
    m = max(-gamma * x for x in values)
    return -(m + math.log(sum(p * math.exp(-gamma * x - m) for p, x in zip(probs, values)))) / gamma


def risk_total(q: float, g_s: float, g_v: float, a: float, p: float) -> float:
    """Summe der Sicherheitsäquivalente von S und V, wenn V den Anteil q des Risikos trägt (Gewinn A in „hoch“ mit Wahrscheinlichkeit p, sonst 0)."""
    mean = p * a
    gains = (a, 0.0)
    probs = (p, 1 - p)
    inc_s = [x + q * (mean - x) for x in gains]
    inc_v = [-q * (mean - x) for x in gains]
    return ce_cara(inc_s, probs, g_s) + ce_cara(inc_v, probs, g_v)


def risk_gain(q: float, g_s: float, g_v: float, a: float, p: float) -> float:
    """Gewinn des Vertrags mit Risikoanteil q des Verladers: Summe der Sicherheitsäquivalente nach dem Vertrag minus vorher (q = 0)."""
    return risk_total(q, g_s, g_v, a, p) - risk_total(0.0, g_s, g_v, a, p)


def risk_share(g_s: float, g_v: float) -> float | None:
    """Optimaler Risikoanteil des Verladers, q* = γ_S / (γ_S + γ_V); sind beide risikoneutral, ist jede Teilung gleich gut (None)."""
    if g_s + g_v <= 0:
        return None
    return g_s / (g_s + g_v)


# --------------------------------------------------------------------------------- Einschätzung


def bet_gain_subjective(p_v: float, p_s: float, bonus: float) -> float:
    """Gemeinsamer Gewinn des Bonus b, wenn jede Seite mit ihrer eigenen Einschätzung rechnet und beide risikoneutral sind: |p_S − p_V|·b."""
    return abs(p_s - p_v) * bonus


def bet_sums(p_v: float, p_s: float, bonus: float, p_common: float) -> tuple[float, float]:
    """Erwartungswerte (Gewinn der Seite mit der höheren Einschätzung, der anderen) bei **gemeinsamer** Wahrscheinlichkeit p_common, wenn der Preis so gesetzt ist, dass die
    eigene Einschätzung den Gewinn hälftig teilt: der Bonus geht an die Seite mit dem höheren p, ihr Preisnachlass ist m·b mit m = (p_V + p_S)/2; ihr Erwartungswert ist (p_common − m)·b."""
    m = (p_v + p_s) / 2
    high = (p_common - m) * bonus
    return high, -high


def bet_hindsight(p_v: float, p_s: float, bonus: float) -> dict:
    """Nachträglich, in jeder Lage: Gewinn der Seite mit dem höheren p in „hoch“ (b − m·b) und in „nicht hoch“ (−m·b); die andere Seite hat das Negative, die Summe ist 0."""
    m = (p_v + p_s) / 2
    return {"high_in_high": bonus - m * bonus, "high_in_low": -m * bonus}


def odds_ratio(p_lo: float, p_hi: float) -> float:
    """Quotenverhältnis (p_hi / (1 − p_hi)) / (p_lo / (1 − p_lo)) für 0 < p_lo <= p_hi < 1."""
    return (p_hi * (1 - p_lo)) / ((1 - p_hi) * p_lo)


def bet_total_cara(w: float, p_v: float, p_s: float, gamma: float) -> float:
    """Summe der Sicherheitsäquivalente beider Seiten bei Wettgröße w: die Seite mit dem höheren p bekommt w in „hoch“, die andere zahlt w; beide rechnen mit der eigenen Einschätzung."""
    p_lo, p_hi = min(p_v, p_s), max(p_v, p_s)
    return ce_cara([w, 0.0], [p_hi, 1 - p_hi], gamma) + ce_cara([-w, 0.0], [p_lo, 1 - p_lo], gamma)


def bet_size_cara(p_v: float, p_s: float, gamma: float) -> float | None:
    """Beste Wettgröße w* = ln(Quotenverhältnis) / (2γ); ohne Unterschied der Einschätzung oder bei γ = 0 (dann unbeschränkt) gibt es keine endliche beste Größe (None)."""
    p_lo, p_hi = min(p_v, p_s), max(p_v, p_s)
    if gamma <= 0 or p_hi <= p_lo or p_lo <= 0 or p_hi >= 1:
        return None
    return math.log(odds_ratio(p_lo, p_hi)) / (2 * gamma)


def bet_gain_cara(w: float, p_v: float, p_s: float, gamma: float) -> float:
    """Gewinn der Wette der Größe w (gegenüber keiner Wette), beide risikoscheu mit gleichem γ und eigener Einschätzung."""
    return bet_total_cara(w, p_v, p_s, gamma) - bet_total_cara(0.0, p_v, p_s, gamma)
