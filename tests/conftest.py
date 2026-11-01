"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b). Alle Erwartungswerte stehen als Rechnung dabei."""

import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def hand2():
    """Zwei Punkte, v = (80, 20), s = (30, 70) (Summe 100 je Seite).
    Verhältnisse s/v: Punkt 1 hat 70/20 = 3,5, Punkt 0 hat 30/80 = 0,375, also Abgabe zuerst Punkt 1: Ecken (100; 0), (80; 70), (0; 100).
    Nash: auf der ersten Strecke (100; 0) → (80; 70) liegt der Scheitel bei t = 2,5 > 1, also am Ende (80; 70) mit Produkt 5600; auf der zweiten (80; 70) → (0; 100) bei t < 0, also ebenfalls (80; 70).
    Kalai–Smorodinsky und egalitär: Schnitt der Diagonalen mit (80; 70) → (0; 100): 80 − 80t = 70 + 30t, t = 1/11, Punkt (800/11; 800/11).
    Positionskompromiss (50; 50); Gewinn = größte Summe 150 − 100 = 50 = ½ (|80 − 30| + |20 − 70|).
    Adjusted Winner: Anfang Punkt 0 an V, Punkt 1 an S → (80; 70), V liegt vorn; Punkt 0 ganz abgeben ginge nicht (0 < 100), also teilen: f = (80 − 70) / (80 + 30) = 1/11."""
    return {
        "v": [F(80), F(20)], "s": [F(30), F(70)],
        "verts": [(F(100), F(0)), (F(80), F(70)), (F(0), F(100))], "order": [1, 0],
        "nash": (F(80), F(70)), "ks": (F(800, 11), F(800, 11)), "egal": (F(800, 11), F(800, 11)), "compromise": (F(50), F(50)),
        "gain": F(50), "x_aw": [F(1, 11), F(1)], "m_star": F(10),
    }


@pytest.fixture
def hand_price():
    """Dasselbe Beispiel mit Preis-Punkt M = 10 (v = s = 10): Verhältnisse 3,5; 1; 0,375, Reihenfolge Punkt 1, Preis, Punkt 0; Ecken (110; 0), (90; 70), (80; 80), (0; 110).
    Größte Summe 160 (auf dem Stück (90; 70) → (80; 80) mit Steigung −1). Nash: Scheitel der ersten Parabel bei t = 1, also (80; 80), Produkt 6400 = (160/2)².
    Mit M = 20: Ecken (120; 0), (100; 70), (80; 90), (0; 120), Summe 170, Scheitel bei t = 0,75: (85; 85); mit M = 5: Ecken (105; 0), (85; 70), (80; 75), (0; 105), Nash (80; 75)."""
    return {"m10": ((F(80), F(80)), F(160)), "m20": ((F(85), F(85)), F(170)), "m5": ((F(80), F(75)), F(155))}


@pytest.fixture
def wikipedia_aw():
    """Beispiel der englischen Wikipedia-Seite „Adjusted winner procedure“ (abgerufen 2026-11-01; die Seite, nicht die Originalquelle von Brams und Taylor): Alice 86, 75, 30, 9; Bob 19, 81, 60, 40.
    Anfang: Gut 1 an Alice, Güter 2 bis 4 an Bob → Alice 86, Bob 181; Bob liegt vorn und gibt in der Reihenfolge s/v ab: Gut 2 (81/75 = 1,08) zuerst, geteilt:
    Ganz übertragen ginge nicht (Alice 161 gegen Bob 100), also teilen: Alice bekommt den Anteil f von Gut 2 mit 86 + 75 f = 181 − 81 f, das heißt f = 95/156 (die Seite nennt 95/156); beide haben danach
    86 + 75 · 95/156 = 6847/52 = 131,67."""
    return {"v": [F(86), F(75), F(30), F(9)], "s": [F(19), F(81), F(60), F(40)], "alice_share_good2": F(95, 156), "each": F(6847, 52)}


@pytest.fixture
def zeit_hand():
    """Ungeduld 1 % (Spediteur) und 2 % (Verlader) je Tag, Betrag 1.000 Euro: d* = ln 2 / 0,01 = 69,31 Tage, dort ist e^(−0,01 d*) = 1/2 und e^(−0,02 d*) = 1/4, also f(d*) = 1000 · (1/2 − 1/4) = 250.
    Nach 30 Tagen: 1000 · (e^(−0,3) − e^(−0,6)) = 1000 · (0,740818 − 0,548812) = 192,006."""
    return {"rs": 0.01, "rv": 0.02, "b": 1000.0, "d_star": 69.31471805599453, "f_star": 250.0, "f30": 192.0058}


@pytest.fixture
def risiko_hand():
    """A = 200, p = 1/2, γ_S = 0,005, V neutral: CE_S ohne Vertrag = −ln(½ e^(−1) + ½) / 0,005 = 0,379885 / 0,005 = 75,977; Erwartungswert 100; Gewinn bei voller Übernahme durch V = 100 − 75,977 = 24,023.
    q* = γ_S / (γ_S + γ_V): V neutral → 1; γ_V = 0,0025 → 0,005 / 0,0075 = 2/3."""
    return {"a": 200.0, "p": 0.5, "gs": 0.005, "gain_full": 24.0229, "q_half_vs": 2 / 3}


@pytest.fixture
def wette_hand():
    """p_V = 0,4, p_S = 0,7, Bonus 100: eigene Einschätzung: S gewinnt (0,7 − 0,55)·100 = 15, V (0,55 − 0,4)·100 = 15, gemeinsam 30. Gemeinsame Wahrscheinlichkeit 0,4: S (0,4 − 0,55)·100 = −15, bei 0,55: 0, bei 0,7: +15.
    Nachträglich: in „hoch“ bekommt S 100 − 55 = 45, sonst −55; V das Negative: Summe 0. Quotenverhältnis (0,7/0,3) / (0,4/0,6) = 3,5; w* mit γ = 0,005: ln 3,5 / 0,01 = 125,28."""
    return {"pv": 0.4, "ps": 0.7, "bonus": 100.0, "gamma": 0.005, "w_star": 125.2763}
