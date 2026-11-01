"""Feste Texte der App, die auch in der README stehen (ein Test vergleicht beide Fassungen, DEMO-PLAYBOOK §5). Zahlen aus Messungen stehen hier nicht, sie kommen aus der Rechnung (vhg_evaluation)."""

INTRO = """
**Ein Verlader und ein Spediteur verhandeln mehrere Punkte zugleich:** Lieferfenster, Zahlungsziel, Rückladung, Rampenzeit und, als Geld, den Preis. Das Vorgängerstück
([`verhandlung-demo`](https://github.com/sebastian-hanisch/verhandlung-demo)) teilte einen **festen** Kuchen; hier steht die Frage davor: **Woher kommt der Gewinn, und wann lässt sich der Kuchen vergrößern?**
Gezeigt werden (a) der **Tausch** von Punkten, die beide Seiten verschieden gewichten (Pareto-Grenze, Nash, Kalai–Smorodinsky, egalitär, Adjusted Winner), (b) die **Bündelgröße** statt einer Themenreihenfolge,
(c) die **Seitenzahlung** mit einer exakten Schwelle, (d) **Zeit**, (e) **Risiko** und (f) **Einschätzung** als weitere Quellen des Gewinns samt der Antwort auf den Streit, ob **bedingte Verträge** den Kuchen
vergrößern oder nur verteilen, und (g) **MESO**, mehrere gleichwertige Angebote auf einmal, als Simulation.

Abgrenzung: `kuchenteilung-demo` teilt einen teilbaren Kuchen ohne Verhandlung (dort ist „jede Einheit an die höchste Bewertung“ die Höchstwohlfahrt); hier
geht es um Verhandlungslösungen auf dieser Grenze, um Geld und um die Quellen des Gewinns. `verhandlung-demo` rechnet die Lösungen auf **einer** gekrümmten Verhandlungsmenge, hier ist die Grenze die stückweise
lineare eines Mehrpunkt-Tauschs. `pareto-dominanz-demo` und `kern-demo` kennen weder zwei Verhandlungsseiten noch den Weg zu einer Lösung auf der Grenze.
**Gewichte, Nutzenfunktionen und Eigennutz sind Modellannahmen**, keine Aussagen über echte Betriebe; die Zahlen sind erfunden.

Weiter unten: fünf Tabs mit sieben **🔬 Experimenten**, die Abschnitte **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""

EXPLAINER = r"""
1. **Punkte und Stellung.** Jeder Punkt $i$ hat eine Stellung $x_i$ von 0 (ganz zugunsten des Verladers) bis 1 (ganz zugunsten des Spediteurs). Der Verlader gewinnt $v_i\,(1-x_i)$ Euro je Tour, der Spediteur $s_i\,x_i$.
2. **Gewinn des Tauschs.** Gibt jeder Punkt an den, der ihn höher bewertet, ist die Summe der Nutzen $\sum_i \max(v_i, s_i)$; in der Mitte aller Punkte ($x_i = \tfrac12$) ist sie $\tfrac12(\sum v_i + \sum s_i)$. Der Unterschied ist
   $\tfrac12 \sum_i |v_i - s_i|$: **der Gewinn kommt aus verschiedenen Gewichten**, nicht aus Verhandlungsgeschick.
3. **Pareto-Grenze.** Man gibt die Punkte in absteigender Reihenfolge $s_i / v_i$ vom Verlader an den Spediteur ab; jeder Zwischenstand ist eine Ecke der Grenze.
4. **Lösungen auf der Grenze.** *Nash* maximiert das Produkt der Nutzen, *Kalai–Smorodinsky* liegt auf der Geraden zum Idealpunkt, *egalitär* gibt beiden gleich viel; *Adjusted Winner* erreicht das egalitäre Ergebnis
   mit höchstens einem geteilten Punkt, wenn beide Seiten ihre Gewichte auf dieselbe Summe normieren.
5. **Seitenzahlung.** Ein Preis-Punkt mit $v = s = M$ (1 Euro hier ist 1 Euro dort) verlängert die Grenze um ein Stück der Steigung −1. Ist der Spielraum $M$ so groß, dass die halbe größte Summe darauf liegt, teilt die Nash-Lösung die größte Summe hälftig;
   Kalai–Smorodinsky und egalitär tun es ebenso, wenn beide Seiten gleich viel insgesamt bewerten.
6. **Weitere Quellen.** Wer das Geld früher braucht, zahlt später (Zeit); wer das Risiko weniger scheut, trägt mehr davon (Risiko); wer den Markt anders einschätzt, kann auf die Differenz wetten (Einschätzung).
"""

CONTROLS_TABLE = """
| Regler | Was er tut | Wirkung auf die Frage |
|---|---|---|
| **Zahl der Punkte, Werte v und s** | Wie viele der Punkte Lieferfenster, Zahlungsziel, Rückladung und Rampenzeit verhandelt werden und was jeder Punkt jeder Seite wert ist (Euro je Tour). | Der Gewinn des Tauschs ist ½ Σ\\|v − s\\|; gleiche Werte heißen kein Gewinn. |
| **Preis-Spielraum M** | Ein Preis-Punkt mit gleichem Wert für beide (1 Euro hier = 1 Euro dort). 0 heißt: kein Geld im Spiel. | Verlängert die Grenze um ein Stück der Steigung −1; ab der Schwelle M\\* teilen die Lösungen die größte Summe hälftig. |
| **Bündelgröße** | Wie viele Punkte zusammen verhandelt werden; jedes Bündel wird für sich bei seiner Nash-Lösung abgeschlossen. | Einzelpunkte teilen jeweils in der Mitte; erst im Paket zeigen sich die verschiedenen Gewichte. |
| **Ungeduld, Zahlungsziel** | Kosten des Wartens auf das Geld (Prozent je Tag) und das vereinbarte Ziel in Tagen, bei festem Betrag von 1.000 Euro. | Der Gewinn entsteht, wenn die Seiten verschieden ungeduldig sind. |
| **Risikoscheu, Risikoanteil** | Konstante Risikoscheu γ je Seite (in Tausendsteln je Euro; 0 = neutral) und der Anteil des Risikos, den der Verlader trägt. | Optimal ist q\\* = γ_S / (γ_S + γ_V). |
| **Einschätzung p, Bonus, Risikoscheu der Wette** | Wie wahrscheinlich jede Seite „der Markt steigt“ hält, die Höhe des Bonus der Gleitklausel und die Risikoscheu für die endliche Wette. | Der Gewinn der Klausel hängt davon ab, mit wessen Wahrscheinlichkeit man ihn bewertet. |
| **Faktoren δ** | Geduld je Runde im Verhandlungsspiel (Brücke zum Vorgängerstück). | Teilt die größte Summe in der Rubinstein-Weise auf, solange der Spielraum reicht. |
| **Angebote k, Runden, Schätzer, Zufalls-Seed** | MESO: Angebote je Runde, Runden, wie die Gewichte der Gegenseite geschätzt werden, und die Instanz. | Simulation, kein Befund über Menschen. |
"""

ASSUMPTIONS_MARKDOWN = """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Nutzen sind linear-additiv** (jeder Punkt für sich, in Euro) | Hängen Punkte voneinander ab (ein kurzes Lieferfenster ist nur mit Rückladung etwas wert) oder ist der Nutzen eines Punktes gekrümmt, ist die Grenze nicht stückweise linear und die Reihenfolge der Punkte kann etwas ändern. Das ist nicht gerechnet. | – |
| **Zwei Seiten, volle Information über die eigenen Gewichte** | Mehr als zwei Beteiligte, private Information über die Gewichte der Gegenseite und Verhandlungsmacht sind nicht Teil der Modelle. Nur MESO schätzt die Gewichte der Gegenseite, unter bekannter Verteilung der Gewichte. | Stück zu Verhandeln mit Geheimnissen |
| **1 Euro ist 1 Euro** (übertragbarer Nutzen) | Ist Geld bei einer Seite knapp oder hat die Seite einen Grenznutzen, der mit der Menge fällt, ist die Seitenzahlung weniger wert. Das Zahlungsziel als „linearer Punkt“ ist eine grobe Annahme: der Gewinn des Ziels ist nicht linear in den Tagen (siehe E4). | – |
| **Fester Betrag beim Zahlungsziel** | Wäre der Betrag frei wählbar, wäre der Gewinn aus der Ungeduld unbeschränkt (eine Kette immer größerer Beträge). Betrag fest oder in einem Korridor ist Modellannahme. | – |
| **Konstante absolute Risikoscheu, ein zweiwertiges Risiko** | Andere Nutzenfunktionen und mehr Lagen verändern q\\* und die Wettgröße; die Formeln gelten für dieses Modell. Haftung wird nur als Risikoüberwälzung gezeigt, nicht als eigener Verhandlungspunkt. | – |
| **Bewertung der bedingten Verträge** | Die Standardlehre misst mit der Einschätzung jeder Seite, die Gegenposition mit einer gemeinsamen Wahrscheinlichkeit oder nachträglich. Beide Rechnungen stehen in E6; welche gilt, hängt an der Annahme, nicht an der Mathematik. Anreizwirkungen eines Vertrags (das Handeln hängt am Vertrag) sind nicht modelliert. | – |
| **MESO ist eine Simulation** (Prior bekannt = Erzeuger, ehrliche Wahl, festes Band, 4 Punkte mit 5 Stufen) | Das Ergebnis hängt am Schätzer (E7). Über Menschen sagt es nichts. | – |
| **Stichproben sind endlich und erzeugt** | Der Gewinn aus dem Tausch hängt am Erzeuger der Gewichte (unabhängig Dirichlet(1)), nicht an der Wirklichkeit; ± ist der Standardfehler über 4 Blöcke zu je 2.000 Instanzen. | – |
| **Literatur nur nach Auszug** | Thompson, Wang und Gunia (2010), Brams und Taylor (Adjusted Winner), Bazerman und Gillespie (1999), Brett (2007), Medvec und Galinsky, Leonardelli u. a. (2019), Hamburg (2009) sind nicht im Volltext gelesen; Kray, Lind und Thompson (2005) wurde nicht gefunden. Die Demo rechnet das hier beschriebene Modell und behauptet keine ihrer Aussagen. | – |
"""

MATH_MARKDOWN = r"""
**Lesehilfe.** Gegeben sind Werte $v_i, s_i \ge 0$ je Punkt; gesucht sind Stellungen $x_i \in [0,1]$.

| Symbol | Bedeutung |
|---|---|
| $v_i$, $s_i$ | Wert des Punktes $i$ für Verlader (V) und Spediteur (S), Euro je Tour |
| $x_i$ | Stellung: Anteil des Punktes, der an S geht |
| $U_V$, $U_S$ | Nutzen der beiden Seiten |
| $M$ | Preis-Spielraum (Preis-Punkt mit $v = s = M$) |
| $r_V$, $r_S$ | Ungeduld je Tag; $d$ Zahlungsziel in Tagen; $B$ fester Betrag |
| $\gamma_V$, $\gamma_S$ | konstante absolute Risikoscheu; $q$ Risikoanteil des Verladers |
| $p_V$, $p_S$ | Einschätzung der Lage „hoch“; $b$ Bonus; $w$ Wettgröße |

**Nutzen und Grenze.** $U_V = \sum_i v_i (1 - x_i)$, $U_S = \sum_i s_i x_i$. Die Pareto-Grenze entsteht, wenn die Punkte in absteigender Reihenfolge $s_i / v_i$ von V an S abgegeben werden.

**Gewinn des Tauschs.**
$$\sum_i \max(v_i, s_i) - \tfrac12\Big(\sum_i v_i + \sum_i s_i\Big) = \tfrac12 \sum_i |v_i - s_i|.$$

**Nash-Lösung.** Auf einer Strecke $(a_1, b_1) + t\,(\Delta a, \Delta b)$, $t \in [0,1]$, maximiert $(a_1 + t\Delta a)(b_1 + t\Delta b)$ den Scheitel
$$t^\ast = -\frac{\Delta a\, b_1 + \Delta b\, a_1}{2\,\Delta a\,\Delta b},$$
begrenzt auf $[0, 1]$; das größte Produkt über alle Strecken ist die Nash-Lösung. *Kalai–Smorodinsky:* Schnitt der Geraden vom Ursprung zum Idealpunkt $(\sum v_i, \sum s_i)$ mit der Grenze. *Egalitär:* Schnitt der Diagonalen $U_V = U_S$.

**Schwelle der Seitenzahlung.** Mit $U_V^0 = \sum_{v_i > s_i} v_i$, $U_S^0 = \sum_{s_i > v_i} s_i$ und $\tau = \sum_{v_i = s_i} v_i$:
$$M^\ast = \max\big(0,\ |U_V^0 - U_S^0| - \tau\big).$$
Für $M \ge M^\ast$ liegt die halbe größte Summe $T/2$ auf dem Stück der Steigung $-1$ und die Nash-Lösung ist $(T/2,\ T/2)$.

**Zahlungsziel.**
$$f(d) = B\big(e^{-r_S d} - e^{-r_V d}\big), \qquad d^\ast = \frac{\ln(r_V / r_S)}{r_V - r_S}.$$

**Risiko (CARA).** $\mathrm{CE} = -\tfrac1\gamma \ln \mathbb{E}\, e^{-\gamma X}$; der Gewinn des Vertrags ist die Summe der Sicherheitsäquivalente nach dem Vertrag minus vorher, am größten bei
$$q^\ast = \frac{\gamma_S}{\gamma_S + \gamma_V}.$$

**Bedingter Vertrag.** Bei eigener Einschätzung: gemeinsamer Gewinn $|p_S - p_V|\, b$. Beide risikoscheu mit $\gamma$ und Quotenverhältnis $\rho = \dfrac{p_S/(1-p_S)}{p_V/(1-p_V)}$:
$$w^\ast = \frac{\ln \rho}{2\gamma}.$$

**Rubinstein auf der Grenze.** Bietet V zuerst, gilt für die Vorschläge $P$ (von V) und $Q$ (von S) auf der Grenze $U_S = f(U_V)$: $P_S = \delta_S Q_S$ und $Q_V = \delta_V P_V$, also
$f(P_V) = \delta_S\, f(\delta_V P_V)$. Auf einer Geraden $U_V + U_S = T$ ist $P_V = T\,\dfrac{1 - \delta_S}{1 - \delta_V \delta_S}$.

**Literatur** (nicht im Volltext geprüft): Nash (1950); Kalai und Smorodinsky (1975); Rubinstein (1982); Brams und Taylor (Adjusted Winner); Borch (1962, Risikoteilung); Thompson, Wang und Gunia (2010).
"""
