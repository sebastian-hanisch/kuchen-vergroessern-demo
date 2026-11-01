"""Die Pareto-Grenze eines Mehrpunkt-Tauschs und die Verhandlungslösungen darauf (linear-additive Nutzen, zwei Seiten).

Modell: Punkt i hat die Stellung x_i in [0, 1] (0: ganz zugunsten des Verladers V, 1: ganz zugunsten des Spediteurs S, dazwischen eine Mischung). Nutzen
U_V = Σ v_i (1 − x_i) und U_S = Σ s_i x_i mit v_i, s_i >= 0 (Euro je Tour). Jeder Punkt kommt nur einmal vor; ein Preis-Punkt hat v_i = s_i (1 Euro hier ist 1 Euro dort).
Der Rückfallwert ohne Einigung ist (0, 0).

**Grenze.** Gibt man die Punkte in absteigender Reihenfolge s_i / v_i von V an S ab, entsteht die Pareto-Grenze (Ecken = Zwischenstände). Alle Funktionen laufen unverändert mit
`int`, `fractions.Fraction` (exakt, für Tests) und `float` (Simulation). Keine Bibliothek außer der Standardbibliothek; kein Zustand."""

from functools import cmp_to_key


def _is_exact(x) -> bool:
    return not isinstance(x, float)


def _tol(x) -> float:
    """Toleranz für die Schnittpunkt-Prüfung: exakt bei ganzen Zahlen und Brüchen, 1e-12 bei Gleitkomma."""
    return 0 if _is_exact(x) else 1e-12


def order(v, s) -> list[int]:
    """Reihenfolge der Abgabe: absteigend s_i / v_i, per Kreuzmultiplikation (v_i = 0 erlaubt); Punkte mit v_i = s_i = 0 ändern nichts und stehen am Ende. Gleichstände: kleinere Nummer zuerst."""
    n = len(v)
    live = [i for i in range(n) if v[i] + s[i] > 0]
    dead = [i for i in range(n) if v[i] + s[i] <= 0]

    def cmp(i, j):
        a, b = s[i] * v[j], s[j] * v[i]
        return -1 if a > b else (1 if a < b else (-1 if i < j else 1))

    return sorted(live, key=cmp_to_key(cmp)) + dead


def frontier(v, s):
    """Ecken der Pareto-Grenze (U_V, U_S) von (Σv, 0) nach (0, Σs) und die Reihenfolge der Abgaben."""
    idx = order(v, s)
    uv = sum(v)
    us = 0 * uv
    verts = [(uv, us)]
    for i in idx:
        uv = uv - v[i]
        us = us + s[i]
        verts.append((uv, us))
    return verts, idx


def frontier_value(verts, u):
    """U_S auf der Grenze bei U_V = u (stückweise linear; u außerhalb von [0, Σv] wird auf den Rand gesetzt)."""
    top = verts[0][0]
    u = min(max(u, 0 * top), top)
    best = None
    for (a1, b1), (a2, b2) in zip(verts, verts[1:]):
        if a2 <= u <= a1:
            value = max(b1, b2) if a1 == a2 else b1 + (b2 - b1) * (a1 - u) / (a1 - a2)
            if best is None or value > best:
                best = value
    return verts[-1][1] if best is None else best


def point_on_segment(verts, k, t):
    (a1, b1), (a2, b2) = verts[k], verts[k + 1]
    return (a1 + t * (a2 - a1), b1 + t * (b2 - b1))


def nash(verts, d=(0, 0)):
    """Nash-Lösung: Maximum von (U_V − d_V)(U_S − d_S) auf der Grenze. Je Strecke eine Parabel, das Maximum liegt geschlossen am Scheitel oder an einer Ecke."""
    best = None
    for k in range(len(verts) - 1):
        (a1, b1), (a2, b2) = verts[k], verts[k + 1]
        da, db = a2 - a1, b2 - b1
        ts = [0 * da, 1 + 0 * da]
        if da * db != 0:
            t = -(da * (b1 - d[1]) + db * (a1 - d[0])) / (2 * da * db)
            if 0 <= t <= 1:
                ts.append(t)
        for t in ts:
            a, b = a1 + t * da, b1 + t * db
            if a < d[0] or b < d[1]:
                continue
            prod = (a - d[0]) * (b - d[1])
            if best is None or prod > best[0]:
                best = (prod, (a, b))
    return best[1] if best is not None else (verts[0][0], verts[0][1])


def hit(verts, d, ray):
    """Der von d aus entlang `ray` am weitesten entfernte Punkt der Grenze (Schnitt des Strahls mit der Grenze); liegt d selbst auf dem Strahl nur im Ursprung, ist es d."""
    rx, ry = ray
    norm = rx * rx + ry * ry
    if norm == 0:
        return d
    eps = _tol(norm)
    best = None
    for (a1, b1), (a2, b2) in zip(verts, verts[1:]):
        px, py = a1 - d[0], b1 - d[1]
        qx, qy = a2 - a1, b2 - b1
        c0 = rx * py - ry * px
        c1 = rx * qy - ry * qx
        if c1 == 0:
            continue
        t = -c0 / c1
        if t < -eps or t > 1 + eps:
            continue
        t = min(max(t, 0 * t), 1 + 0 * t)
        x, y = px + t * qx, py + t * qy
        lam = (x * rx + y * ry) / norm
        if lam < 0:
            continue
        if best is None or lam > best[0]:
            best = (lam, (d[0] + x, d[1] + y))
    return best[1] if best is not None else d


def kalai_smorodinsky(verts, d=(0, 0)):
    """Kalai–Smorodinsky: der Punkt der Grenze auf der Geraden vom Rückfall d zum Idealpunkt (größtes U_V, größtes U_S)."""
    ideal = (verts[0][0], verts[-1][1])
    return hit(verts, d, (ideal[0] - d[0], ideal[1] - d[1]))


def egalitarian(verts, d=(0, 0)):
    """Egalitär: gleicher Nutzengewinn über dem Rückfall für beide (Schnitt der Diagonalen durch d mit der Grenze)."""
    one = 1 + 0 * verts[0][0]
    return hit(verts, d, (one, one))


def position_compromise(v, s):
    """Jeder Punkt in der Mitte (x_i = 1/2 für alle i): (Σv / 2, Σs / 2)."""
    return ((sum(v) + 0 * sum(v)) / 2, (sum(s) + 0 * sum(s)) / 2)


def max_sum(verts):
    """Größte Summe der Nutzen auf der Grenze: Σ max(v_i, s_i)."""
    return max(a + b for a, b in verts)


def gain_sum(v, s):
    """Gewinn des Tauschs: größte Summe minus Summe beim Positionskompromiss, Σ max(v_i, s_i) − (Σv + Σs) / 2."""
    return sum(max(a, b) for a, b in zip(v, s)) - (sum(v) + sum(s)) / 2


def half_abs_difference(v, s):
    """Die Identität dazu: ½ Σ |v_i − s_i| (jeder Punkt trägt den halben Unterschied seiner Gewichte bei)."""
    return sum(abs(a - b) for a, b in zip(v, s)) / 2


def share_of_gain(point, v, s):
    """Anteil des möglichen Gewinns, den die Summe der Nutzen am Punkt erreicht: (Summe am Punkt − Kompromisssumme) / Gewinn; ohne Gewinn None."""
    g = gain_sum(v, s)
    if g <= 0:
        return None
    return (point[0] + point[1] - (sum(v) + sum(s)) / 2) / g


def m_star(v, s):
    """Preis-Spielraum, ab dem die Seitenzahlung den Gewinn gleich teilt: M* = max(0, |Σ_{v>s} v − Σ_{s>v} s| − Σ_{v=s} v).

    Die ersten beiden Summen sind die Nutzen von V und S, wenn jeder Punkt an den höher Bewertenden geht. Punkte mit v_i = s_i (Verhältnis 1) liegen wie der Preis-Punkt auf dem Stück der
    Grenze mit Steigung −1 und verlängern es um ihr Gewicht; ohne solche Gleichstände (Zufallsgewichte) ist M* = |Σ_{v>s} v − Σ_{s>v} s|. Genau dann ist die Nash-Lösung die Hälfte der größten Summe."""
    uv = sum(a for a, b in zip(v, s) if a > b)
    us = sum(b for a, b in zip(v, s) if b > a)
    ties = sum(a for a, b in zip(v, s) if a == b)
    return max(abs(uv - us) - ties, 0 * uv)


def with_price(v, s, m):
    """Hängt den Preis-Punkt an (v = s = m); m = 0 heißt: kein Geld im Spiel."""
    return list(v) + [m], list(s) + [m]


def adjusted_winner(v, s):
    """Adjusted Winner (Brams und Taylor): Anfangszuteilung an den höher Bewertenden, dann Übertragung in der Reihenfolge des kleinsten Verhältnisses, bis beide gleich viel haben; höchstens ein Punkt wird geteilt.

    Rückgabe: x (Anteil von S je Punkt), (U_V, U_S), Zahl der geteilten Punkte. Gedacht für Gewichte, die je Seite auf dieselbe Summe normiert sind (sonst ist Gleichheit der Nutzen
    nicht immer erreichbar: dann bricht die Übertragung ab, ohne zu gleichen). Gleichstände v_i = s_i bleiben beim Verlader."""
    n = len(v)
    one = 1 + 0 * sum(v)
    zero = 0 * one
    x = [one if s[i] > v[i] else zero for i in range(n)]
    uv = sum(v[i] * (1 - x[i]) for i in range(n))
    us = sum(s[i] * x[i] for i in range(n))
    if uv == us:
        return x, (uv, us), 0
    if uv > us:
        cand = [i for i in range(n) if x[i] == 0 and v[i] + s[i] > 0 and s[i] > 0]
        cand.sort(key=cmp_to_key(lambda i, j: -1 if v[i] * s[j] < v[j] * s[i] else (1 if v[i] * s[j] > v[j] * s[i] else (-1 if i < j else 1))))
        for i in cand:
            if uv - v[i] >= us + s[i]:
                x[i] = one
                uv -= v[i]
                us += s[i]
            else:
                f = (uv - us) / (v[i] + s[i])
                x[i] = f
                uv -= f * v[i]
                us += f * s[i]
                break
    else:
        cand = [i for i in range(n) if x[i] == 1 and v[i] > 0]
        cand.sort(key=cmp_to_key(lambda i, j: -1 if s[i] * v[j] < s[j] * v[i] else (1 if s[i] * v[j] > s[j] * v[i] else (-1 if i < j else 1))))
        for i in cand:
            if us - s[i] >= uv + v[i]:
                x[i] = zero
                us -= s[i]
                uv += v[i]
            else:
                f = (us - uv) / (v[i] + s[i])
                x[i] = 1 - f
                us -= f * s[i]
                uv += f * v[i]
                break
    split = sum(1 for xi in x if 0 < xi < 1)
    return x, (uv, us), split


def normalize(values, total=100):
    """Skaliert Gewichte auf die Summe `total` (für Adjusted Winner); alle null bleiben null."""
    s = sum(values)
    if s == 0:
        return [0 * total for _ in values]
    return [total * x / s for x in values]


def bundle_partition(n: int, size: int) -> list[list[int]]:
    """Punkte 0..n−1 in Bündel zu je `size` aufeinanderfolgenden Punkten (das letzte kleiner, wenn es nicht aufgeht). size >= n heißt: ein Paket."""
    if n < 0 or size < 1:
        raise ValueError("n >= 0 und size >= 1")
    return [list(range(i, min(i + size, n))) for i in range(0, n, size)]


def bundle_nash(v, s, partition):
    """Jedes Bündel wird für sich bei seiner Nash-Lösung (Rückfall 0) abgeschlossen. Rückgabe: (Summe U_V, Summe U_S) über alle Bündel."""
    tv = 0 * sum(v)
    ts = 0 * tv
    for idx in partition:
        vv, ss = [v[i] for i in idx], [s[i] for i in idx]
        verts, _ = frontier(vv, ss)
        a, b = nash(verts)
        tv, ts = tv + a, ts + b
    return tv, ts


def rubinstein_share(delta_v, delta_s):
    """Anteil des ersten Anbieters V am Kuchen 1 im Rubinstein-Spiel (V bietet zuerst, Faktoren δ je Runde): (1 − δ_S) / (1 − δ_V δ_S)."""
    return (1 - delta_s) / (1 - delta_v * delta_s)


def rubinstein_on_frontier(verts, delta_v, delta_s, iterations=200):
    """Stationäres teilspielperfektes Gleichgewicht, wenn V zuerst bietet und die Menge die Grenze `verts` ist (keine Kosten je Runde, Rückfall 0).

    Es gilt P = Vorschlag von V, Q = Vorschlag von S, beide auf der Grenze, P_S = δ_S · Q_S und Q_V = δ_V · P_V. Also f(P_V) = δ_S · f(δ_V · P_V) mit der Grenzfunktion f = U_S(U_V);
    die Differenz fällt in P_V, Bisektion. Rückgabe: (P, Q)."""
    top = verts[0][0]
    lo, hi = 0.0, float(top)

    def g(u):
        return frontier_value(verts, u) - delta_s * frontier_value(verts, delta_v * u)

    for _ in range(iterations):
        mid = (lo + hi) / 2
        if g(mid) > 0:
            lo = mid
        else:
            hi = mid
    pv = (lo + hi) / 2
    p = (pv, frontier_value(verts, pv))
    qv = delta_v * pv
    q = (qv, frontier_value(verts, qv))
    return p, q


def price_segment(v, s, m):
    """(U_V am oberen Ende, U_V am unteren Ende) des Preis-Stücks der Grenze (Steigung −1, Länge m), wenn der Preis-Punkt als letzter Punkt (Nummer n) angehängt wurde; sonst None."""
    vv, ss = with_price(v, s, m)
    verts, idx = frontier(vv, ss)
    k = idx.index(len(v))
    return verts[k][0], verts[k + 1][0]
