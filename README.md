# Woher kommt der Gewinn? Kuchen vergrößern – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-kuchen-vergroessern-demo.streamlit.app/)** -->

Stück der Linie **regeln-verhandeln** (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Es folgt auf [`verhandlung-demo`](https://github.com/sebastian-hanisch/verhandlung-demo), das einen **festen** Überschuss teilt; hier steht die Frage davor: **woher der Überschuss kommt und wann er sich vergrößern lässt**. Vehikel: ein **Verlader** und ein **Spediteur** verhandeln mehrere Punkte zugleich (Lieferfenster, Zahlungsziel, Rückladung, Rampenzeit und als Geld den Preis). Gewichte, Nutzenfunktionen und Eigennutz sind **Modellannahmen**, keine Aussagen über echte Betriebe; die Zahlen sind erfunden.

Abgrenzung: `kuchenteilung-demo` teilt einen teilbaren Kuchen mit Protokollen ohne Verhandlung; seine Höchstwohlfahrt („jede Stunde an die höchste Bewertung“) ist dieselbe Art Grenze wie die Greedy-Grenze hier, die Frage ist eine andere (Preis der Neidfreiheit dort; Verhandlungslösungen, Seitenzahlung und Quellen des Gewinns hier). `verhandlung-demo` rechnet Nash, Kalai–Smorodinsky und egalitär auf **einer** gekrümmten Verhandlungsmenge; hier ist die Grenze die stückweise lineare eines Mehrpunkt-Tauschs. [`pareto-dominanz-demo`](https://github.com/sebastian-hanisch/pareto-dominanz-demo) kennt Dominanz von Alternativen, aber keine zwei Verhandlungsseiten und keine Lösung auf der Grenze; [`kern-demo`](https://github.com/sebastian-hanisch/kern-demo) teilt einen gegebenen Gewinn ohne Verhandlungsablauf.

## Kernfrage

*Wann lässt sich der Kuchen vergrößern, und wie teilt man den größeren?* Die Antwort hat drei Teile. (1) **Der Gewinn des Tauschs ist ½ Σ|v − s|**: er kommt aus verschiedenen Gewichten der Punkte, nicht aus Verhandlungsgeschick; bei unabhängig gezogenen Gewichten (Dirichlet-Erzeuger) und vier Punkten (Summe 100 je Seite) sind es im Mittel 43,0 Punkte, die Nash-Lösung hebt davon 96,8 %, Kalai–Smorodinsky 90,0 %; wer jeden der vier Punkte einzeln in der Mitte teilt, hebt per Konstruktion 0 %. (2) **Geld schließt die Lücke**, genau ab der Schwelle M*: dann teilt die Nash-Lösung die größte Summe hälftig (Kalai–Smorodinsky und egalitär ebenso, wenn beide Seiten gleich viel insgesamt bewerten); **der Kuchen wächst aber auch ohne verschiedene Einschätzungen**, aus Zeit (250 Euro bei Ungeduld 1 % gegen 2 % je Tag und 69,3 Tagen) und aus Risiko (24,02 Euro je Tour bei einseitiger Risikoscheu und gleicher Wahrscheinlichkeit). (3) **Bedingte Verträge** vergrößern den Kuchen *oder* verteilen nur um, je nachdem, mit welcher Wahrscheinlichkeit man bewertet; und MESO (mehrere gleichwertige Angebote) hängt in der Simulation am Schätzer, mit dem der Anbieter lernt.

## Befunde und Korrekturen gegenüber dem Plan

Der Einzelplan (Vormessung vom 2026-11-01) wurde nicht blind übernommen; jede Zahl ist im Bau neu gemessen. Abweichungen und neue Funde:

- **Die Schwelle M\* braucht eine Gleichstandskorrektur** (Fund des Orakeltests): Punkte mit v = s liegen wie der Preis-Punkt auf dem Stück der Steigung −1 und verlängern es. Richtig ist M\* = max(0, \|Σ_{v>s} v − Σ_{s>v} s\| − Σ_{v=s} v); die Formel des Plans gilt ohne solche Punkte (Zufallsgewichte). Beispiel: v = (70, 20, 10), s = (30, 20, 50) hat M\* = 0 (die Formel ohne Korrektur gäbe 20).
- **Adjusted Winner nur bei normierten Gewichten:** beide Seiten auf dieselbe Summe 100 gebracht (die App tut das für die Anzeige und lässt den Preis weg); bei verschiedenen Summen ist Gleichheit der Nutzen nicht immer erreichbar.
- **Bündelgröße statt Reiter „Themenreihenfolge“:** die Reihenfolge ändert im additiven Modell nichts (per Konstruktion), die Bündelgröße schon. Die Reihenfolge-Literatur (Hamburg 2009) wurde nicht im Volltext gelesen.
- **Die Brücke zum Vorgängerstück (H11) ist gemessen**, im Plan war sie nur hergeleitet. **Die Ursache der Nash-Asymmetrie** aus der Vormessung ist untersucht (Erzeuger der Gewichte, siehe unten).
- **MESO neu gemessen** mit eigenem SplitMix64-Strom und 8 Blöcken zu je 500 Instanzen (Plan: 4 × 300 mit numpy). Eine Vergleichsrechnung mit 20.000 Instanzen je Erzeuger gibt für „gleiche Gewichte“ g = 0,627 (numpy) und 0,625 (SplitMix64), beide ± 0,004: die Erzeuger stimmen überein (Scratch-Lauf beim Bau, nicht in der Suite); die Zahl des Plans (0,654) liegt gut zwei Standardfehler über dem Wert der größeren Stichproben (rund 0,62; hier 0,614 ± 0,005 aus 4.000); die Differenz ist wahrscheinlich Zufall, aber nicht sicher.
- **Laufzeit ohne scipy:** der Max-Rand-Schätzer (ein lineares Programm) ist hier eine Aufzählung aller Ecken (bis zu 12.650 Kombinationen von je 5 × 5 Gleichungen), bei mehreren gleich guten Ecken gilt deren Mittel; `scipy.linprog` ist nur Orakel im Test. Der Plan hatte HiGHS verwendet.

## Modell

Punkt *i* hat die Stellung *xᵢ* in [0, 1] (0: ganz zugunsten des Verladers, 1: ganz zugunsten des Spediteurs). Nutzen *U_V* = Σ *vᵢ* (1 − *xᵢ*), *U_S* = Σ *sᵢ xᵢ* in Euro je Tour; ein Preis-Punkt hat *v* = *s* = *M*; ohne Einigung ist der Nutzen 0. Die **Pareto-Grenze** entsteht, wenn die Punkte in absteigender Reihenfolge *sᵢ*/*vᵢ* vom Verlader an den Spediteur abgegeben werden. Darauf rechnet `vhg_frontier.py` Nash (je Strecke der Scheitel einer Parabel), Kalai–Smorodinsky (Schnitt der Geraden zum Idealpunkt), egalitär (Schnitt der Diagonalen) und Adjusted Winner. Dazu drei Mini-Modelle mit geschlossenen Optima (`vhg_sources.py`): **Zeit** (Zahlungsziel *d*, fester Betrag, Ungeduld *r*), **Risiko** (CARA-Risikoscheu γ, Anteil *q*) und **Einschätzung** (Gleitklausel mit Bonus *b*, Wette der Größe *w*). **MESO** (`vhg_meso.py`) ist eine Simulation. Formeln, Lesehilfe und Symboltabelle stehen im 📐-Expander der App.

## Methodik

- **Kern ohne scipy:** `vhg_frontier.py` läuft unverändert mit `int`, `fractions.Fraction` und `float`; die Tests rechnen exakt in Brüchen.
- **Orakel** (`tests/test_oracle_kuchen_vergroessern.py`, anderer Rechenweg): Greedy-Grenze gegen die Aufzählung aller 2ⁿ Ecken (exakt) und gegen ein lineares Programm; Nash gegen das numerische Maximum des Produkts auf der LP-Grenze; egalitär gegen LP-Maximin; Kalai–Smorodinsky gegen Bisektion über die LP-Grenze; Adjusted Winner gegen LP-Maximin und gegen das Beispiel der englischen Wikipedia-Seite; M\* gegen das Abtasten ganzzahliger Preis-Spielräume; *d\**, *q\**, *w\** gegen Gitter und `scipy.optimize.minimize_scalar`; Rubinstein auf der Grenze gegen die geschlossene Formel und gegen eine Wertiteration; der Max-Rand-Schätzer gegen `linprog`; das Posterior-Mittel gegen eine Schleife.
- **Messreihen** (`tools/make_grid.py`, `tools/make_meso.py`): vorgerechnet in `data/grid.json` und `data/meso.json`, mit Hash der Quellen; jeder Block hat einen eigenen SplitMix64-Strom aus seiner Bezeichnung; ± ist der Standardfehler über die Blöcke.
- **Zufall:** `vhg_rng.py` ist eine wörtliche Kopie von `ab-test-demo/abt_rng.py` (SplitMix64) mit Kopietest.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. „Zellen“ der Gitter sind 4 Blöcke zu je 2.000 Zufallsinstanzen (Summe 100 je Seite, Gewichte Dirichlet(1), der Spediteur mischt mit θ: (1 − θ) · Gewichte des Verladers + θ · unabhängige); die Höhe des Gewinns hängt an diesem Erzeuger, nicht an der Wirklichkeit.

| Nr. | Hypothese | Stand | Befund |
|---|---|---|---|
| H1 | Der Gewinn des Tauschs ist ½ Σ\|v − s\| und null bei gleichen Gewichten | **Ja** | Identität größte Summe − Positionskompromiss = ½ Σ\|v − s\| exakt in Brüchen in 3.000 von 3.000 Instanzen (n = 2 bis 6, Summe 100 je Seite); bei v = s ist der Gewinn 0 und Nash gleich dem Positionskompromiss in 500 von 500. Hook mit Einschränkung: gleiches Profil bei doppeltem Niveau (v = (40, 30, 10), s = 2 v) hat in Euro einen Gewinn von 40, bei auf je 100 normierten Gewichten 0; erreichbar ist er erst mit Geld (M\* = 160) |
| H2 | Der Gewinn wächst mit dem Unterschied der Gewichte | **Ja** | je Instanz exakt linear in θ (größte Abweichung von θ · Gewinn(θ = 1) unter 10⁻⁹ Punkten in 500 Instanzen und in allen 30 Zellen); n = 4: 4,30 / 21,52 / 43,03 Punkte bei θ = 0,1 / 0,5 / 1 (Tabelle unten) |
| H3 | Greedy-Grenze = Aufzählung = LP; Adjusted Winner = egalitär | **Ja** | Suite: 60 von 60 Instanzen (21 Stützstellen) gegen die Aufzählung aller Ecken, 40 gegen das LP (9 Stellen); Nash gegen numerisches Maximum in 10, egalitär gegen LP in 40, Kalai–Smorodinsky gegen Bisektion in 12, Adjusted Winner gleich LP-Maximin, höchstens ein geteilter Punkt, neidfrei und auf der Grenze in 60 von 60; Wikipedia-Beispiel: 95/156 von Gut 2 und 6847/52 = 131,67 je Seite. Dieselben Tests mit zehnfacher Instanzzahl im Scratch-Lauf (600 / 400 / 100 / 400 / 120 / 600): alle bestanden |
| H4 | Mit Seitenzahlung teilt die Nash-Lösung die größte Summe hälftig, genau wenn M ≥ M\*; bei gleichen Gesamtwerten auch Kalai–Smorodinsky und egalitär | **Ja** | Regel in 17 von 17 Zellen in jeder Instanz (je 8.000); M\* gleich dem kleinsten ganzzahligen Spielraum mit Nash = T/2 in 60 von 60 Instanzen; Handbeispiel v = (80, 20), s = (30, 70): M\* = 10, Nash (80; 70) bei M = 0, (80; 75) bei 5, (80; 80) bei 10, (85; 85) bei 20. Nash = Kalai–Smorodinsky nur bei gleichen Gesamtwerten: bei s = 2 v erreicht Nash ohne Geld 0 des Gewinns, mit M = 200 den vollen, dort sind nicht alle drei gleich |
| H5 | Zeit: es gibt ein bestes Zahlungsziel, null bei gleicher Ungeduld | **Ja** | d\* = ln(r_V / r_S) / (r_V − r_S) gleich Gitter und `minimize_scalar` in 60 von 60 Fällen; Ungeduld 1 % und 2 % je Tag, 1.000 Euro: d\* = 69,3 Tage, Gewinn 250,0 Euro, nach 30 Tagen 192,0 gegen 300,0 bei linearer Annahme; Vorzeichen dreht, wenn der Spediteur ungeduldiger ist (−192,0 bei 30 Tagen) |
| H6 | Risiko: der Verlader trägt q\* = γ_S / (γ_S + γ_V), der Gewinn braucht keinen Unterschied der Einschätzung | **Ja** | q\* gleich Gitter und `minimize_scalar` in 60 von 60 Fällen; Gewinn 24,02 / 15,73 / 11,65 / 7,66 / 2,04 Euro je Tour bei γ_V = 0 / 2,5 / 5 / 10 / 50 ‰ (γ_S = 5 ‰); halbe-halbe ist nur bei γ_V = γ_S optimal und kostet bei γ_V = 50 ‰ 18,43 Euro |
| H7 | Bedingte Verträge ändern nur die Verteilung | **Nein**, hängt am Maßstab | mit der Einschätzung jeder Seite wächst der Kuchen um \|p_S − p_V\| · b = 30,0 (je Seite 15,0); mit einer gemeinsamen Wahrscheinlichkeit (40 / 55 / 70 %) oder nachträglich ist die Summe in jedem Fall 0 |
| H8 | Der Kuchen wächst nur bei verschiedener Einschätzung | **Nein** | Zeit (250,0 Euro) und Risiko (24,02 Euro) vergrößern ihn bei gleicher Einschätzung; bei gleicher Einschätzung (55 %) kostet jede Wette mit Risikoscheu: −12,25 Euro bei w = 100 |
| H9 | MESO: mehr als drei Angebote bringen kaum etwas | **Nein**, nicht bestätigt, hängt am Schätzer | Posterior-Mittel, eine Runde: g = 0,622 (ein Angebot), 0,755 (zwei), 0,809 (drei), 0,862 (fünf), 0,902 (acht): der erste Zuwachs ist der größte (0,133), von drei auf acht Angebote kommen aber noch 0,093 dazu; mit drei Runden 0,974 bei acht Angeboten. Max-Rand-Schätzer: zwei Angebote in einer Runde 0,307, **schlechter als gleiche Gewichte als Schätzung** (0,614); er liegt über ihnen erst ab fünf Angeboten (eine Runde), drei (zwei Runden) bzw. zwei (drei Runden) |
| H10 | Die Themenreihenfolge kostet Effizienz | **Nein** | im additiven Modell null (die Reihenfolge der Bündel ändert in 16.000 von 16.000 Instanzen nichts, per Konstruktion); die Bündelgröße ändert viel, nicht stetig (Tabelle unten) |
| H11 | Die Aufteilung von T bei Seitenzahlung ist das Verhandlungsspiel des Vorgängerstücks mit T statt 1 | **Ja**, mit Bedingung | gilt genau dann, wenn das Rubinstein-Gleichgewicht im Inneren des Stücks der Steigung −1 liegt (beide Vorschläge, S genau indifferent): 1.061 von 4.000 Fällen (200 Instanzen, 5 Preis-Spielräume, 4 Paare δ) gleich in beiden Richtungen; bei M = 0 in 3 von 800, bei M = 200 in 458 von 800; in diesen Fällen bekommt der erste Anbieter T · (1 − δ_S) / (1 − δ_V δ_S) |

**Gewinn und Lösungen** (Experiment E1; n = 4 Punkte, Anteil des möglichen Gewinns; bei θ = 0 gibt es keinen Gewinn und keinen Anteil; Kalai–Smorodinsky und egalitär fallen bei gleichen Summen zusammen):

| θ | Gewinn (Punkte) | Anteil Nash | Anteil Kalai–Smorodinsky und egalitär | Nash: Verlader / Spediteur | Instanzen mit Gewinn unter 5 |
|---|---|---|---|---|---|
| 0,00 | 0,00 ± 0,00 | – | – | 50,0 / 50,0 | 100 % |
| 0,10 | 4,30 ± 0,02 | 0,816 ± 0,002 | 0,800 ± 0,002 | 52,8 / 50,6 | 65 % |
| 0,25 | 10,76 ± 0,05 | 0,864 ± 0,002 | 0,824 ± 0,002 | 57,2 / 52,0 | 10 % |
| 0,50 | 21,52 ± 0,10 | 0,926 ± 0,001 | 0,861 ± 0,002 | 63,9 / 56,1 | 2 % |
| 0,75 | 32,27 ± 0,14 | 0,956 ± 0,001 | 0,889 ± 0,001 | 68,3 / 62,9 | 0 % |
| 1,00 | 43,03 ± 0,19 | 0,968 ± 0,001 | 0,900 ± 0,001 | 71,0 / 71,2 | 0 % |

**Warum bekommt der Verlader bei Nash mehr?** (offener Punkt aus der Vormessung; n = 4; U_V − U_S bei Nash im Mittel, getrennt nach der Seite mit den ungleicheren Gewichten, größeres Σ w²):

| θ | Anteil der Instanzen, in denen V die ungleicheren Gewichte hat (E1-Erzeuger) | U_V − U_S im Mittel (E1-Erzeuger) | U_V − U_S im Mittel (symmetrischer Erzeuger) | symmetrisch, wenn V die ungleicheren Gewichte hat | symmetrisch, wenn S sie hat |
|---|---|---|---|---|---|
| 0,25 | 87,1 % | 5,2 ± 0,1 | 0,1 ± 0,1 | 2,9 ± 0,1 | −2,8 ± 0,1 |
| 0,50 | 80,0 % | 7,8 ± 0,1 | 0,2 ± 0,2 | 4,4 ± 0,1 | −4,1 ± 0,3 |
| 0,75 | 66,6 % | 5,4 ± 0,2 | 0,1 ± 0,2 | 3,4 ± 0,2 | −3,2 ± 0,3 |
| 1,00 | 48,8 % | −0,2 ± 0,2 | 0,0 ± 0,1 | 4,7 ± 0,3 | −4,8 ± 0,2 |

Im Erzeuger von E1 sind die Gewichte des Verladers meist ungleicher als die des Spediteurs (80,0 % der Instanzen bei θ = 0,5), im symmetrischen Erzeuger gibt es keinen Vorsprung des Verladers (0,2 ± 0,2 Punkte); dort liegt **die Seite mit den ungleicheren Gewichten bei Nash vorn** (im Mittel 4,4 Punkte, wenn es der Verlader ist, 4,1, wenn es der Spediteur ist). Gemessen ist der Zusammenhang, nicht der Beweis, warum die Parabel-Scheitel so liegen.

**Bündelgröße** (Experiment E2; n = 4, Anteil des möglichen Gewinns bei Nash je Bündel; „zwei Paare“ in beiden Reihenfolgen gleich):

| Aufteilung (n = 4, Summe 100 je Seite) | θ = 1 | θ = 0,5 |
|---|---|---|
| vier Einzelpunkte | 0,000 ± 0,000 % | 0,000 ± 0,000 % |
| zwei Paare | 73,227 ± 0,216 % | 64,870 ± 0,234 % |
| zwei Paare, andere Reihenfolge | 73,227 ± 0,216 % | 64,870 ± 0,234 % |
| drei und einer | 66,697 ± 0,278 % | 62,365 ± 0,333 % |
| ein Paket | 96,812 ± 0,027 % | 92,722 ± 0,068 % |

**Seitenzahlung** (Experiment E3; θ = 1, n = 4, Preis-Spielraum M):

| M | Nash | Kalai–Smorodinsky | Egalitär | Instanzen mit Nash = T/2 | Regel M ≥ M* trifft | Abstand der Nutzen bei Nash |
|---|---|---|---|---|---|---|
| 0 | 0,968 ± 0,000 | 0,901 ± 0,000 | 0,901 ± 0,000 | 0,0 % | 100,0 % | 13,0 ± 0,0 |
| 5 | 0,975 ± 0,000 | 0,923 ± 0,000 | 0,923 ± 0,000 | 11,9 % | 100,0 % | 10,7 ± 0,0 |
| 10 | 0,981 ± 0,000 | 0,941 ± 0,000 | 0,941 ± 0,000 | 23,6 % | 100,0 % | 8,6 ± 0,0 |
| 25 | 0,992 ± 0,000 | 0,976 ± 0,000 | 0,976 ± 0,000 | 54,4 % | 100,0 % | 4,0 ± 0,0 |
| 50 | 0,999 ± 0,000 | 0,997 ± 0,000 | 0,997 ± 0,000 | 87,8 % | 100,0 % | 0,7 ± 0,0 |
| 100 | 1,000 ± 0,000 | 1,000 ± 0,000 | 1,000 ± 0,000 | 100,0 % | 100,0 % | 0,0 ± 0,0 |
| 200 | 1,000 ± 0,000 | 1,000 ± 0,000 | 1,000 ± 0,000 | 100,0 % | 100,0 % | 0,0 ± 0,0 |

Zeilen mit gleichem Profil, doppeltem Niveau (s = 2 v, θ = 0): wo der Spediteur es mehr braucht, entsteht der Gewinn nur mit Geld; der egalitäre Punkt liegt ohne Geld sogar unter dem Positionskompromiss (Anteil −0,333).

| M | Nash | Kalai–Smorodinsky | Egalitär | Instanzen mit Nash = T/2 | alle drei gleich |
|---|---|---|---|---|---|
| 0 | 0,000 ± 0,000 | 0,000 ± 0,000 | −0,333 ± 0,000 | 0,0 % | 0,0 % |
| 50 | 0,500 ± 0,000 | 0,364 ± 0,000 | 0,000 ± 0,000 | 0,0 % | 0,0 % |
| 200 | 1,000 ± 0,000 | 1,000 ± 0,000 | 1,000 ± 0,000 | 100,0 % | 0,0 % |

**Zahlungsziel** (Experiment E4; Ungeduld 1 % des Spediteurs, 2 % des Verladers je Tag, 1.000 Euro): das Ziel als „linearer Punkt“ ist eine grobe Annahme; die Mitte der Endwerte (0 Euro sofort, 241,3 nach 90 Tagen) wäre 120,6, das Ziel von 45 Tagen bringt 231,1.

| Zahlungsziel (Tage) | Gewinn (Euro je Tour) | lineare Annahme (Euro je Tour) |
|---|---|---|
| 0 | 0,0 | 0,0 |
| 15 | 119,9 | 150,0 |
| 30 | 192,0 | 300,0 |
| 60 | 247,6 | 600,0 |
| 90 | 241,3 | 900,0 |

**Risiko** (Experiment E5; Gewinn des Spediteurs 200 Euro mit Wahrscheinlichkeit ½, γ_S = 5 ‰ je Euro; Sicherheitsäquivalent des Spediteurs allein 75,98 Euro statt 100):

| γ_V (‰ je Euro) | bester Risikoanteil q* | Gewinn bei q* (Euro je Tour) | Gewinn bei halbe-halbe |
|---|---|---|---|
| 0,0 | 100,0 % | 24,02 | 17,84 |
| 2,5 | 66,7 % | 15,73 | 14,72 |
| 5,0 | 50,0 % | 11,65 | 11,65 |
| 10,0 | 33,3 % | 7,66 | 5,83 |
| 50,0 | 9,1 % | 2,04 | −18,43 |

**Bedingter Vertrag** (Experiment E6; p_V = 0,4, p_S = 0,7, Bonus 100 Euro; Erwartungsgewinn je Tour in Euro). Die Standardlehre misst mit der Einschätzung jeder Seite, die Gegenposition (englische Wikipedia-Seite „Contingent contract“ nennt Brett 2007; die Quelle ist nicht eingesehen) mit einer gemeinsamen Wahrscheinlichkeit oder nachträglich; die Tabelle zeigt denselben Vertrag mit allen Maßstäben. **Beide Aussagen stimmen, mit verschiedener Bewertung**; welche gilt, hängt an der Bewertungsannahme, nicht an der Mathematik.

| Maßstab | Seite mit höherer Einschätzung | andere Seite | Summe |
|---|---|---|---|
| (a) eigene Einschätzung jeder Seite | 15,0 | 15,0 | 30,0 |
| (b) gemeinsame Wahrscheinlichkeit 40 % (kleinere Einschätzung) | −15,0 | 15,0 | 0,0 |
| (b) gemeinsame Wahrscheinlichkeit 55 % (Mitte) | 0,0 | 0,0 | 0,0 |
| (b) gemeinsame Wahrscheinlichkeit 70 % (größere Einschätzung) | 15,0 | −15,0 | 0,0 |
| (c) nachträglich, Lage „hoch“ | 45,0 | −45,0 | 0,0 |
| (c) nachträglich, Lage „nicht hoch“ | −55,0 | 55,0 | 0,0 |

Sind beide risikoscheu (γ = 5 ‰), ist die Wette endlich: w\* = ln(3,5) / (2γ) = 125,3 Euro mit Gewinn 19,08 Euro je Tour gegen 30,0 risikoneutral; der Gewinn der besten Wette wächst ungefähr quadratisch im Unterschied der Einschätzungen (p_V = 0,4 fest):

| p_S (p_V = 0,4) | beste Wettgröße w* (Euro) | Gewinn (Euro je Tour) |
|---|---|---|
| 0,40 | – | 0,00 |
| 0,45 | 20,5 | 0,51 |
| 0,50 | 40,5 | 2,03 |
| 0,60 | 81,1 | 8,16 |
| 0,70 | 125,3 | 19,08 |
| 0,80 | 179,2 | 36,80 |

**MESO** (Experiment E7, **Simulation**: 4 Punkte mit je 5 Stufen, 625 Pakete; Gewichte unabhängig Dirichlet(1); der Verlader legt nur Pakete vor, die ihm (fast) gleich viel bringen, Band \|U_V − ½\| ≤ 0,025, im Mittel 50,7 Pakete (kleinstes 17, größtes 125); der Spediteur wählt ehrlich das beste; g = 0 für ein Zufallspaket des Bandes, 1 für das beste; eine Runde; 8 Blöcke zu je 500 Instanzen, das Posterior-Mittel fiel in 4 von 168.000 Schätzungen auf Max-Rand zurück):

| Angebote k | g Posterior-Mittel | g Max-Rand | Fehler der Schätzung (Posterior / Max-Rand) |
|---|---|---|---|
| 1 | 0,622 ± 0,005 | 0,614 ± 0,005 | 0,317 ± 0,001 / 0,317 ± 0,001 |
| 2 | 0,755 ± 0,006 | 0,307 ± 0,007 | 0,282 ± 0,001 / 0,614 ± 0,004 |
| 3 | 0,809 ± 0,004 | 0,463 ± 0,007 | 0,263 ± 0,001 / 0,538 ± 0,004 |
| 4 | 0,843 ± 0,003 | 0,569 ± 0,006 | 0,250 ± 0,001 / 0,484 ± 0,003 |
| 5 | 0,862 ± 0,004 | 0,637 ± 0,010 | 0,242 ± 0,001 / 0,453 ± 0,003 |
| 6 | 0,877 ± 0,003 | 0,676 ± 0,006 | 0,236 ± 0,001 / 0,431 ± 0,002 |
| 8 | 0,902 ± 0,003 | 0,744 ± 0,007 | 0,229 ± 0,002 / 0,395 ± 0,004 |

**Brücke zum Verhandlungsstück** (H11; Handbeispiel v = (80, 20), s = (30, 70), δ_V = δ_S = 0,9, Verlader bietet zuerst, Vorschlag des Verladers): ohne Geld (M = 0) bekommt er 81,3 von der größten Summe 150, die Formel T · (1 − δ_S) / (1 − δ_V δ_S) gäbe 78,9; mit M = 20 genau 89,5 = 170 · 0,526; mit M = 10 liegt der Vorschlag noch nicht im Inneren des Stücks (87,6 gegen 84,2).

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Nutzen sind linear-additiv** (jeder Punkt für sich, in Euro) | Hängen Punkte voneinander ab (ein kurzes Lieferfenster ist nur mit Rückladung etwas wert) oder ist der Nutzen eines Punktes gekrümmt, ist die Grenze nicht stückweise linear und die Reihenfolge der Punkte kann etwas ändern. Das ist nicht gerechnet. | – |
| **Zwei Seiten, volle Information über die eigenen Gewichte** | Mehr als zwei Beteiligte, private Information über die Gewichte der Gegenseite und Verhandlungsmacht sind nicht Teil der Modelle. Nur MESO schätzt die Gewichte der Gegenseite, unter bekannter Verteilung der Gewichte. | Stück zu Verhandeln mit Geheimnissen |
| **1 Euro ist 1 Euro** (übertragbarer Nutzen) | Ist Geld bei einer Seite knapp oder hat die Seite einen Grenznutzen, der mit der Menge fällt, ist die Seitenzahlung weniger wert. Das Zahlungsziel als „linearer Punkt“ ist eine grobe Annahme: der Gewinn des Ziels ist nicht linear in den Tagen (siehe E4). | – |
| **Fester Betrag beim Zahlungsziel** | Wäre der Betrag frei wählbar, wäre der Gewinn aus der Ungeduld unbeschränkt (eine Kette immer größerer Beträge). Betrag fest oder in einem Korridor ist Modellannahme. | – |
| **Konstante absolute Risikoscheu, ein zweiwertiges Risiko** | Andere Nutzenfunktionen und mehr Lagen verändern q\* und die Wettgröße; die Formeln gelten für dieses Modell. Haftung wird nur als Risikoüberwälzung gezeigt, nicht als eigener Verhandlungspunkt. | – |
| **Bewertung der bedingten Verträge** | Die Standardlehre misst mit der Einschätzung jeder Seite, die Gegenposition mit einer gemeinsamen Wahrscheinlichkeit oder nachträglich. Beide Rechnungen stehen in E6; welche gilt, hängt an der Annahme, nicht an der Mathematik. Anreizwirkungen eines Vertrags (das Handeln hängt am Vertrag) sind nicht modelliert. | – |
| **MESO ist eine Simulation** (Prior bekannt = Erzeuger, ehrliche Wahl, festes Band, 4 Punkte mit 5 Stufen) | Das Ergebnis hängt am Schätzer (E7). Über Menschen sagt es nichts. | – |
| **Stichproben sind endlich und erzeugt** | Der Gewinn aus dem Tausch hängt am Erzeuger der Gewichte (unabhängig Dirichlet(1)), nicht an der Wirklichkeit; ± ist der Standardfehler über 4 Blöcke zu je 2.000 Instanzen. | – |
| **Literatur nur nach Auszug** | Thompson, Wang und Gunia (2010), Brams und Taylor (Adjusted Winner), Bazerman und Gillespie (1999), Brett (2007), Medvec und Galinsky, Leonardelli u. a. (2019), Hamburg (2009) sind nicht im Volltext gelesen; Kray, Lind und Thompson (2005) wurde nicht gefunden. Die Demo rechnet das hier beschriebene Modell und behauptet keine ihrer Aussagen. | – |

Dazu im Einzelnen:

- **Linear-additive Nutzen, zwei Seiten.** Abhängigkeiten zwischen Punkten (ein kurzes Fenster ist nur mit Rückladung etwas wert), gekrümmte Nutzen, Verhandlungsmacht, private Information und mehr als zwei Beteiligte sind nicht gerechnet. Die Reihenfolge, in der Themen verhandelt werden, spielt deshalb keine Rolle (E2).
- **Der Gewinn aus dem Tausch hängt am Erzeuger.** 43,0 Punkte bei n = 4 und θ = 1 gelten für unabhängig gezogene Dirichlet(1)-Gewichte, nicht für echte Betriebe.
- **Zahlungsziel als linearer Punkt** ist grob (E4); bei frei wählbarem Betrag wäre der Gewinn unbeschränkt, hier ist der Betrag fest.
- **Risiko und Wette** gelten für konstante absolute Risikoscheu und zwei Lagen; Anreizwirkungen von Verträgen (das Handeln hängt am Vertrag) sind nicht modelliert.
- **Der Streit um bedingte Verträge** ist nicht entschieden, sondern aufgelöst: er hängt an der Wahrscheinlichkeit, mit der bewertet wird. Höchstens eine Seite hat mit ihrer Einschätzung recht.
- **MESO ist eine Simulation** (Prior bekannt = Erzeuger, ehrliche Wahl, festes Band, 4 Punkte mit 5 Stufen); das Ergebnis hängt am Schätzer und sagt nichts über Menschen. Der Max-Rand-Schätzer ist eine eigene Wahl (bei Gleichstand Mittel der besten Ecken) und kein Verfahren aus der Literatur.
- **Adjusted Winner** ist nur für auf dieselbe Summe normierte Gewichte definiert; die App zeigt ihn ohne den Preis.
- **Die Brücke H11** ist an einem Gitter von 200 Instanzen, 5 Preis-Spielräumen und 4 Paaren von Faktoren gemessen, nicht allgemein bewiesen.

## Literatur (nicht im Volltext gelesen)

Wo nicht anders vermerkt, nach Suchauszug oder Abstract; die Demo rechnet das hier beschriebene Modell und behauptet keine Aussage dieser Quellen: Nash (1950); Kalai und Smorodinsky (1975); Rubinstein (1982); Brams und Taylor (Adjusted Winner; Beispiel nach der englischen Wikipedia-Seite „Adjusted winner procedure“, abgerufen 2026-11-01, nicht nach der Originalquelle); Borch (1962, Risikoteilung; Borch-Regel aus dem Gedächtnis, hier numerisch geprüft); Thompson, Wang und Gunia (2010; vier Quellen des Gewinns laut Suchauszug); Bazerman und Gillespie (1999) und Brett (2007) nur über die Wikipedia-Seite „Contingent contract“; Medvec und Galinsky, Leonardelli u. a. (2019, OBHDP, laut Abstract) zu MESO; Hamburg (2009) zur Reihenfolge der Themen. Kray, Lind und Thompson (2005) wurde nicht gefunden.

## Tests

**217 Tests**, Laufzeit rund 5,6 Minuten seriell (am 2026-11-02 gemessen) auf Windows mit Python 3.14 (den größten Teil brauchen die AppTest-Dateien; die Linux-CI mit Python 3.12 ist noch nicht gelaufen). Zusammensetzung:

- **Orakel (19, `test_oracle_kuchen_vergroessern.py`):** Greedy-Grenze gegen Aufzählung und LP, Nash, egalitär, Kalai–Smorodinsky, Adjusted Winner, Schwelle M\*, Zahlungsziel, Risikoanteil, Wettgröße, Rubinstein auf der Grenze, Max-Rand-Schätzer, Posterior-Mittel; mit der Umgebungsvariablen `VHG_ORACLE_SCALE=10` laufen dieselben Tests mit zehnfacher Instanzzahl (beim Bau einmal gelaufen: 19 von 19 bestanden, rund 94 Sekunden).
- **Einheiten an von Hand gerechneten Mini-Instanzen (37 + 15 + 21, `test_frontier.py`, `test_sources.py`, `test_meso.py`):** Grenze, Lösungen, Adjusted Winner (Wikipedia-Beispiel), M\* mit und ohne Gleichstände, Bündel, Zeit, Risiko, Wette, MESO-Einheiten; Eigenschaften (Seiten tauschen, alle Werte skalieren, positiv-affine Umrechnung einer Seite, zusätzlicher Preis-Punkt, Gewinn nie negativ) und Zweige (Schwelle M\* von beiden Seiten, Nash gleich und ungleich Kalai–Smorodinsky, kein Gewinn, gleiche Ungeduld, γ_V = 0 gegen > 0, die zwei Schätzer weichen ab).
- **Claims (33, `test_claims.py`):** jede Zahl der README und der Preset-Hilfen; die README-Tabellen werden mit denselben Zeilenbauern der App erzeugt und im Test als Text in der README gesucht; Hypothesenzeilen H1 bis H11.
- **Messdateien (8, `test_measurements.py`):** Erzeuger-Hash, Achsen, Zellen, Reproduktion eines Blocks und einer ganzen Zelle neu gerechnet.
- **Verdikte, Presets, Randfälle (14 + 7 + 13):** jede Zahl und Schwelle im Text an handgesetzten Werten; Eckfall-Matrix über alle Regler (alle Minima, alle Maxima, alle Werte null, nur Preis), jedes Preset, PDF, Permalink.
- **Kopie des Zufallsgenerators (5), Laufzeit-Importe (1), Oberfläche (39 + 3 + 2):** Layout (fester Kopf, Schnellstart, Hervorhebung, jeder Regler hebt sie auf), AppTest-Rauchtest (jeder Knopf, jeder Regler an beiden Rändern), Footer.
- Die Messreihen (Gitter, MESO) stehen nirgends exakt in einem Test der Rechnung, sondern als gespeicherte Werte (README-Zahl gleich dem gespeicherten Wert) und als Reproduktion mit Marge.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: fünf Tabs mit sieben Experimenten, Presets, PDF-Export |
| `data/grid.json`, `data/meso.json` | vorgerechnete Messreihen mit Erzeuger-Hash |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (nur Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/make_grid.py`, `tools/make_meso.py` | rechnen die Messreihen neu |
| `vhg_constants.py` | Regler-Grenzen, Messparameter, Farben, Presets |
| `vhg_evaluation.py` | Kennzahlen, Zeilenbauer der Tabellen, Verdikte als reine Funktionen |
| `vhg_experiments.py` | Messreihen (Gitter, MESO), Seeds, Erzeuger-Hash |
| `vhg_frontier.py` | Pareto-Grenze, Nash, Kalai–Smorodinsky, egalitär, Adjusted Winner, Schwelle M\*, Bündel, Rubinstein auf der Grenze |
| `vhg_layout.py` | Fester Kopf (Stylesheet) |
| `vhg_meso.py` | MESO-Simulation: Pakete, Band, Wahl, zwei Schätzer |
| `vhg_pdf_export.py` | PDF-Export (fpdf2), erst nach Klick |
| `vhg_presets.py` | Permalink, Presets (Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `vhg_rng.py` | SplitMix64, wörtliche Kopie von `ab-test-demo/abt_rng.py` |
| `vhg_scenario.py` | Einstellungen als unveränderliche Datenklasse, Zugriff auf die Punkte |
| `vhg_sources.py` | Zeit, Risiko und Einschätzung als Mini-Modelle mit geschlossenen Optima |
| `vhg_texts.py` | feste Texte der App (Einleitung, Erklärtabelle, Annahmen, Formeln), auch in der README |
| `vhg_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Mini-Instanzen von Hand, Einheiten, Orakel, Claims, Messdateien, Presets, Layout, AppTest-Smoke, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Abhängigkeiten zwischen Punkten und gekrümmte Nutzen** (Mediation): nicht gerechnet; dort würde die Reihenfolge der Themen etwas ändern.
- **Verhandlungsmacht, private Information, mehr als zwei Seiten, Wiederholung:** nicht Teil der Modelle.
- **Haftung als eigener Verhandlungspunkt:** sie ist Risikoüberwälzung und braucht ein nichtlineares Nutzenmodell; sie kommt nur im Risiko-Experiment vor.
- **Reiter „Themenreihenfolge“:** ersetzt durch den Regler Bündelgröße (E2).
- **Daten echter Verhandler und echte Betriebe:** die Demo rechnet Modelle; MESO ist eine Simulation, keine Studie.
- **Verhandlungsagenten:** ein späteres Stück der Linie; die Pareto-Grenze (`vhg_frontier.py`) ist so geschrieben, dass sie als Orakel kopiert werden kann.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Python 3.12 oder neuer; die in der Streamlit Community Cloud eingestellte Python-Version ist beim Deploy zu notieren.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
