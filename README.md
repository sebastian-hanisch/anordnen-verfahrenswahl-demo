# Verfahrenswahl beim Anordnen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-anordnen-verfahrenswahl-demo.streamlit.app/)** -->

Stück 15 von 15 (Abschluss) der **Konzepte-Reihe „Anordnen: relaxieren und runden“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Konzepte-Seite der Reihe gibt es noch nicht). Die Stücke [3, Gilmore–Lawler](https://github.com/sebastian-hanisch/gilmore-lawler-demo), [5, Linearisierung und Dual Ascent](https://github.com/sebastian-hanisch/linearisierung-schranke-demo) und [8, Branch and Bound](https://github.com/sebastian-hanisch/schranke-im-baum-demo) liefern die Schranken und den Baum, [9, Quadratische Platzierung](https://github.com/sebastian-hanisch/quadratische-platzierung-demo), [10, Look-ahead-Legalisierung](https://github.com/sebastian-hanisch/look-ahead-legalisierung-demo), [11, Dichte und Drahtlänge](https://github.com/sebastian-hanisch/dichte-elektrostatik-demo) und [12, Detailplatzierung](https://github.com/sebastian-hanisch/detailplatzierung-demo) die Verfahren der Platzierungsseite. Dieses Stück rechnet **nichts Neues**: es stellt die Verfahren auf denselben Instanzen nebeneinander und fragt, **welches wofür taugt, gemessen woran**. Gelb (optional): Stück 7, 13 und 14 sind als eigene Demos gebaut, hier nicht verglichen.

## Warum dieses Problem

Stück 3 bis 12 haben zehn Verfahren angesammelt: eine Schranke nach der anderen (Gilmore–Lawler, projizierte Eigenwerte, Dual Ascent, Linearisierung, konvexe Relaxation), einen Baum, der die Schranken benutzt, und auf der Platzierungsseite die Rundung, die Schleife, die Dichtestrafe, den Tauschabstieg und das Annealing. Jedes Stück hat sein Verfahren an seinem Maß gemessen. Hier steht die Frage, die man vor einer Aufgabe stellt: **Welches nehme ich, und was kostet mich die Wahl?** Wie in den anderen Abschlussstücken der Konzepte-Reihen steht die Regel **vor** der Messung, und die Messung sagt, wo sie hält.

Es gibt zwei Aufgaben. **Finden** heißt: eine gute Anordnung liefern. **Beweisen** heißt: belegen, dass keine bessere existiert. Die Antwort dieser Messung: **Finden ist billig, Beweisen kostet.** Bis `n = 12` schlagen **20 Neustarts** des einfachen Tauschabstiegs aus Zufall jede Relaxation deutlich; bei `n = 16` liegen sie im Mittel vor der Schleife mit Annealing, der Unterschied liegt aber im Rahmen der Streuung; ab `n = 25` (bei `n = 20` noch nicht; die Kreuzung liegt zwischen 20 und 25 Bauteilen) sind die **Schleife aus Stück 10 als Startlösung plus kaltes Annealing** schneller und im Mittel etwas besser; einmal runden und die Dichtestrafe aus Stück 11 liefern nirgends die beste Qualität (einmal runden ist nur das schnellste Verfahren). Die Relaxationen zahlen sich an anderer Stelle aus: als **Schranke** (sie belegt eine Güte, ohne zu enumerieren) und als **Startlösung**. Den Beweis des Optimums bezahlt man mit dem Baum: im Median 240 / 675 / 7 990 Knoten bei `n` = 8 / 9 / 12, im größten Fall 190 916.

## Modell

- **Aufgabe** (wie in Stück 1 bis 12): `n` Bauteile auf `n` Plätze eines Rasters (Manhattan-Abstand), Fluss `F` zwischen den Bauteilen; **Finden** mit `p` festen **Pads** (Anker auf einem Ring um das Raster), `cost(π) = Σ_{i<k} F[i,k] · |p_i − p_k|₁ + Σ_{i,Pad} w · |p_i − Pad|₁`; **Beweisen** ohne Pads (reine Zuordnung nach Koopmans und Beckmann). Raster von 2×4 (`n = 8`) bis 6×6 (`n = 36`); sechs erfundene Familien der Flussmatrix (Netzliste, gleichverteilt, dünn besetzt, zwei Cluster, Stern, wenige starke Flüsse).
- **Die Regel** (`avw_rule.py`, reine Funktion von Größe, Aufgabe und Zeitbudget): *Beweis verlangt?* Dann bis `n = 12` Branch and Bound mit der Gilmore–Lawler-Schranke (Anfangswert: beste von 200 Abstiegen); darüber ist der Baum in dieser Fassung zu groß, es bleiben die Schranke als Güteaussage und das Finden. *Finden:* bis `n = 16` 20 Neustarts des Abstiegs aus Zufall, ab `n = 20` die Schleife (Stück 10) als Startlösung mit kaltem Annealing (Stück 12). Bei **knappem Zeitbudget** 6 Neustarts bzw. nur der Abstieg aus der Schleife. Die Regel liest weder Familie noch Pad-Zahl noch Kosten.
- **Finden, elf Verfahren** (`avw_evaluation.solve_find`, Kerne aus Stück 9 bis 12): einmal runden, die Schleife (15 Runden), die Dichtestrafe (elektrostatisch, letzte und billigste Stufe), vier Tauschabstiege (aus Zufall, Rundung, Schleife, Dichtestrafe), 6 und 20 Neustarts, Schleife mit Annealing (Starttemperatur 0,1; Zugzahlen 1 500 / 3 000 / 6 000 für `n` = 8 / 12 / 16 aus Stück 12, **9 000 / 12 000 / 20 000 für `n` = 20 / 25 / 36 in dieser Demo gesetzt**).
- **Beweisen** (`avw_bounds.py`, `avw_lp.py`, `avw_tree.py`, Kerne aus Stück 3, 5 und 8): Gilmore–Lawler, Dual Ascent (5 Runden), Linearisierung (LP, HiGHS über scipy, nur bis `n = 9`), 20 und 200 Abstiege aus Zufall, Branch and Bound mit Gilmore–Lawler-Knotenschranken und mit linearen Knotenschranken (nur bis `n = 9`; Obergrenze 300 000 Knoten). Die projizierte Eigenwertschranke (Stück 4) und die konvexe Schranke (Stück 6) stehen nur als Tafel „nicht gerechnet“.
- **Bedauern** = `(Kosten − beste Kosten aller Verfahren auf der Instanz) / beste Kosten`. Bis `n = 9` gehört das aufgezählte Optimum zu den Verfahren, ab `n = 12` ist der Vergleichswert selbst ein Verfahrensergebnis: das Bedauern ist eine **obere** Grenze der Lücke zum Optimum und nie negativ. (Die Vormessung verglich ab `n = 12` zusätzlich mit der besten von 100 Abstiegen; die Demo lässt das weg, weil es bei `n = 36` rund 30 Sekunden je Instanz kostet. Die Werte unten sind deshalb etwas kleiner als in der Vormessung.)
- **Aufwand** doppelt: **Zeit** in Sekunden (live gemessen, Messung dieser Python-Fassung auf dem jeweiligen Rechner; sie schwankt von Lauf zu Lauf um das Doppelte) und **Zählung** (Bewertungen einer Anordnung, Runden der Schleife, Auswertungen der Dichtestrafe, Knoten des Baums: verschiedene Einheiten). **Zeiten stehen in Anzeigen, nie in Tests.**
- **Feste und frische Instanzen:** Finden `n` = 8 / 12 / 16 mit 180 / 90 / 54 Instanzen (Seeds ab 100000, Pads 2 / 4 / 8), `n` = 20 / 25 / 36 mit je 18 Instanzen (vier Pads); Beweisen `n` = 8 / 9 / 12 mit 30 / 18 / 18 Instanzen ohne Pads. **Frische** Instanzen (Seeds ab 200000: 90 / 54 / 36 / 18 / 18 / 18) prüfen die Regel, die an den festen gebildet wurde.
- **Experimente:** (1) der Weg durch den Baum (Entscheidungsweg, alle Verfahren auf einer Instanz, Handbeispiel); (2) Beweisen kostet; (3) Finden über feste Instanzen; (4) die Kreuzung; (5) die Regel auf frischen Instanzen. Formeln im 📐-Expander der App.

## Methodik

Der Abschnitt „Ergebnis“ und Experiment 1 rechnen **eine** Instanz (Familie, `n` = 8 bis 36, Seed, Pads, Aufgabe, Zeitbudget sind Regler; `n = 12` beweisen nur auf Knopfdruck). Die Experimente 2 bis 5 rechnen auf Knopfdruck über feste Instanzen und brauchen einige Minuten (auf Streamlit Cloud länger): vier Knöpfe (Beweisen; Finden `n` ≤ 16; Finden `n` ≥ 20; frische Instanzen). Standard: Zwei Cluster, `n = 8`, Seed 48, vier Pads, Finden, Zeitbudget normal. Die Zeilen der Vergleiche enthalten Kosten, Zeit, Zählung und Bedauern je Verfahren; die Auswertung (mittleres Bedauern, Treffer, **Kante** aus Median der Zeit und mittlerem Bedauern, **gepaarter Unterschied** mit Standardfehler) rechnet daraus.

## Befunde (gemessen, keine Behauptungen)

Alles Messung an den sechs erfundenen Familien und den erfundenen Pads; Zeiten sind die dieser Fassung auf dem Rechner des Autors (Windows).

1. **Finden ist billig, Beweisen kostet.** 20 Abstiege aus Zufall treffen das bewiesene Optimum in **30 von 30** (`n` = 8), **18 von 18** (`n` = 9) und **12 von 18** (`n` = 12) Instanzen, 200 Abstiege in 30, 18 und 17 (die letzte liegt um eine Kosteneinheit darüber), in Hundertstelsekunden. Der Beweis per Branch and Bound mit der Gilmore–Lawler-Schranke braucht im Median **240 / 675 / 7 990 Knoten** (0,03 / 0,08 / 1,1 s), im größten Fall 924 / 5 733 / 190 916 Knoten (0,09 / 0,9 / 27 s); mit linearen Knotenschranken 2 334 / 12 235 Knoten bei `n` = 8 / 9 (bei `n = 9` bis 164 000 Knoten, 12 s). Die Schranken allein bleiben weit vom Optimum: Lücke im Median **8,3 / 10,2 / 13,3 %** (Gilmore–Lawler), **5,2 / 8,0 / 11,3 %** (Dual Ascent, fünf Runden), **1,5 / 1,8 %** (Linearisierung, aber 0,6 und 3 Sekunden, das 2 000- bis 8 000-fache der Gilmore–Lawler-Schranke).
2. **Bis `n = 16` gewinnt im Mittel der einfachste Weg (bei `n = 16` nur knapp): 20 Neustarts des Abstiegs aus Zufall.** Mittleres Bedauern **0,04 / 0,24 / 0,66 %** bei `n` = 8 / 12 / 16, Median 0 %; sie erreichen den Vergleichswert in 174 von 180, 71 von 90 und 27 von 54 Instanzen, in 0,007 / 0,020 / 0,047 s. Einmal runden (11,0 / 18,2 / 20,1 %), die Schleife (7,9 / 11,0 / 13,5 %) und die Dichtestrafe (6,0 / 9,4 / 9,7 % in der letzten, 2,8 / 4,5 / 5,0 % in der billigsten Stufe) liegen weit dahinter, die Dichtestrafe kostet das Vier- bis Zwanzigfache an Zeit (0,14 bis 0,17 s gegen 0,007 bis 0,047 s).
3. **Zwischen `n = 20` und `n = 25` kippt es, und zwar in der Zeit.** Schleife als Startlösung plus kaltes Annealing ist ab `n = 25` schneller als 20 Neustarts (in 17 bis 18 von 18 Instanzen bei `n = 25` und in 18 von 18 bei `n = 36`; 0,26 gegen 0,65 s und 0,53 gegen 4,5 s) und im Mittel besser: Bedauern **0,58 / 0,21 %** gegen **1,35 / 1,55 %** bei `n` = 25 / 36. Der Unterschied in der Qualität ist klein gegen die Streuung: gepaart −0,76 ± 0,34 und −1,34 ± 0,55 Prozentpunkte (Annealing besser in 12, schlechter in 6 von 18). Bei `n = 20` liegen beide gleichauf (1,07 gegen 1,19 %, +0,12 ± 0,61; auf frischen Instanzen −0,41 ± 0,36) und die 20 Neustarts sind in dieser Messung noch schneller (0,12 gegen 0,18 s); in der Vormessung lag die Kreuzung der Zeit bei `n = 20`. **Die Lage der Kreuzung gehört zu dieser Python-Fassung und diesem Rechner;** das Vorzeichen des Qualitätsunterschieds (Neustarts deutlich besser bis `n = 12`, Annealing im Mittel schwach besser ab `n = 25`) ist der robustere Befund.
4. **Einmal runden und die Dichtestrafe liefern nirgends die beste Qualität, als Startlösung hilft die Relaxation.** Die Dichtestrafe allein liegt in keiner der zwölf Reihen (sechs Größen, fest und frisch) auf der Kante aus Median der Zeit und mittlerem Bedauern; der Tauschabstieg aus ihrem Ergebnis nur bei `n = 36`. Mit anschließendem Abstieg sinkt das Bedauern der Rundung von 11,0 auf 1,2 % (`n = 8`, Abstieg aus Rundung), der Schleife von 7,9 auf 1,2 %. Das Annealing aus der Schleife ist die einzige Verwendung der Relaxation, die ab `n = 25` das beste mittlere Bedauern liefert.
5. **Die Regel hält auf frischen Instanzen.** Mittleres Bedauern der Regel auf frischen Instanzen (`n` = 8 bis 36): 0,03 / 0,17 / 0,58 / 0,50 / 0,34 / 0,63 %; gegen die bessere der beiden festen Wahlen (immer Neustarts, immer Schleife mit Annealing, im Mittel) verliert sie höchstens 0,12 Prozentpunkte (`n = 20`, feste Instanzen), gegen das bessere der beiden **je Instanz** (im Voraus unbekannt) bis zu 1,05. Die Regel liest nur die Größe; ob der Wechsel auch von der Familie abhängt, lässt sich mit 3 Instanzen je Familie ab `n = 20` nicht entscheiden (bis `n = 12` haben alle Familien und Pad-Zahlen dasselbe Vorzeichen).

### Mittleres Bedauern in Prozent (feste Instanzen)

| Verfahren | n = 8 | 12 | 16 | 20 | 25 | 36 |
|---|---|---|---|---|---|---|
| einmal runden (Stück 9) | 11,0 | 18,2 | 20,1 | 17,2 | 16,9 | 16,2 |
| Schleife (Stück 10) | 7,9 | 11,0 | 13,5 | 10,2 | 10,0 | 9,6 |
| Dichtestrafe, letzte / billigste Stufe (Stück 11) | 6,0 / 2,8 | 9,4 / 4,5 | 9,7 / 5,0 | 8,6 / 4,4 | 8,5 / 4,2 | 6,6 / 4,4 |
| Abstieg aus Zufall (Stück 12) | 3,2 | 4,1 | 6,4 | 5,3 | 6,3 | 4,4 |
| Abstieg aus Rundung / Schleife / Dichtestrafe | 1,2 / 1,2 / 1,3 | 2,5 / 2,5 / 1,9 | 2,4 / 2,6 / 2,2 | 3,0 / 2,7 / 2,5 | 2,1 / 1,8 / 2,5 | 2,6 / 2,0 / 1,8 |
| 6 / **20** Neustarts | 0,35 / **0,04** | 0,98 / **0,24** | 1,87 / **0,66** | 2,2 / 1,07 | 2,9 / 1,35 | 2,6 / 1,55 |
| Schleife mit Annealing | 0,78 | 1,16 | 0,83 | 1,19 | **0,58** | **0,21** |
| Zeit, 20 Neustarts (Median) | 0,007 s | 0,020 s | 0,047 s | 0,12 s | 0,65 s | 4,5 s |
| Zeit, Schleife mit Annealing (Median) | 0,032 s | 0,072 s | 0,13 s | 0,18 s | 0,26 s | 0,53 s |
| Zeit, Dichtestrafe (Median) | 0,14 s | 0,17 s | 0,17 s | 0,17 s | 0,19 s | 0,24 s |

Instanzen: 180 / 90 / 54 / 18 / 18 / 18 (bei `n ≤ 16` Pads 2, 4 und 8; ab `n = 20` vier Pads). Die Werte der Neustarts, des Abstiegs aus Zufall und des Annealing stehen mit Toleranz in `tests/test_claims.py`; die Zeiten stehen in keinem Test.

## Ehrliche Grenzen

- **Zeit ist implementierungsabhängig:** vektorisierte Python-Fassungen (numpy). In anderer Sprache oder mit anderer Umsetzung liegen Zeiten und Kreuzung woanders; auf demselben Rechner schwankte die Zeit zweier Läufe um das Doppelte (Vormessung: 20 Neustarts bei `n = 20` 0,42 s, hier 0,12 s). Nur Größenordnungen und Rangfolgen mit großem Abstand sind belastbar. In Tests stehen Kosten und ganzzahlige Zählungen.
- **Kleine Stichprobe ab `n = 20`:** 18 Instanzen je Größe, nur vier Pads; der gepaarte Unterschied hat 0,3 bis 0,6 Prozentpunkte Unsicherheit. „Schneller“ ab `n = 25` ist stark, „im Mittel besser“ schwach. Der Standardfehler nimmt unabhängige Instanzen an; die Instanzen bis `n = 16` teilen sich je drei Pad-Zahlen einen Seed, der Fehler ist dort eine Näherung.
- **Annealing-Zugzahl ab `n = 20` selbst gesetzt:** Stück 12 definiert sie nur bis `n = 16`. Die Vormessung hat die Empfindlichkeit gemessen (halbe und doppelte Zugzahl: das Bedauern sinkt mit der Zugzahl, die Reihenfolge gegen die Neustarts blieb bei `n` = 25 und 36, bei `n = 20` hängt sie von der Zugzahl ab), trotzdem ist es eine Einstellung dieser Demo.
- **Vergleichswert ab `n = 12` ist selbst ein Verfahrensergebnis:** das Bedauern ist eine obere Grenze der Lücke zum Optimum; „0 %“ heißt „so gut wie das Beste dieser elf“.
- **Dichtestrafe mit den Einstellungen aus Stück 11** (Randzone 0,5, Ladungsbreite 3, zwölf Stufen): bei anderen Parametern kann sie besser abschneiden. Der Befund „auf keiner Kante“ gilt für diese Einstellungen.
- **Pads und Familien erfunden;** jede Aussage nennt die Pad-Zahl. Beweisen rechnet die reine Zuordnung; mit Pads (linearen Anfangskosten) ist der Baum in dieser Demo nicht gemessen.
- **Größen nur bis `n = 36`,** keine Instanzen aus QAPLIB; Aussagen der Literatur zur Größe exakter Verfahren stehen hier nicht (nicht nachgelesen).
- **Rechnerabhängigkeit:** Rundung, Schleife und Dichtestrafe sind empfindlich; einzelne Anordnungen ändern sich mit dem Rechner, die Mittel über viele Instanzen sind auf wenige Zehntel bis wenige Prozentpunkte stabil (deshalb die Toleranzen in `tests/test_claims.py`, wie in Stück 11). Die ganzzahligen Zählungen der Beweisseite (Knoten, Treffer der Abstiege) sind auf jedem Rechner gleich.
- **Quellen:** keine neuen; die Quellen der Stücke 3 bis 12 stehen dort (zum Teil „nicht eingesehen“). Alle Zahlen sind eigene Rechnungen an eigenen, erfundenen Familien und Pads.

## Verifikation

- **Tests** (`pytest tests/`): **396 Tests**, rund neun Minuten (Windows, Python 3.14; die festen und frischen Instanzen der Zahlen-Tests rechnen parallel). Handwerte (Vier Plätze auf einer Zeile: Gilmore–Lawler-Wurzel 5, Optimum 6, Baum mit 4 / 16 / 64 Knoten mit dem Anfangswert 6 und 10 / 19 / 64 ohne ihn), Eigenschaften (Bedauern nie negativ und null für das beste Verfahren, die Regel liest nur Größe, Aufgabe und Zeitbudget, das Orakel liegt unter jedem festen Verfahren, die Kante enthält kein dominiertes Verfahren, Schranken steigen mit den Runden), Orakel (die Aufzählung aller Anordnungen für das Optimum bis `n = 8`, eine zweite, unabhängig geschriebene Kostenrechnung für jede ausgegebene Anordnung, Schranken unter dem Optimum, Branch and Bound gegen Aufzählung, `linear_sum_assignment` für die Zuordnung), Verdikte (Art und Text folgen den Zahlen, jeder Zweig an festen Eingaben), AppTest (alle Regler an ihren Grenzen, alle Rechenknöpfe mit verkleinerten Reihen, PDF), und die **Zahlen der README** an den festen und frischen Instanzen (`tests/test_claims.py`, parallel gerechnet, mit Toleranzen für die Streuung zwischen Rechnern und Sammelmeldung statt Abbruch beim ersten Fehler).
- **Kopie:** die Kerne sind Kopien aus Stück 1 bis 12 mit eigenen Tests; Tests vergleichen die Familien mit denen von Stück 1 bis 12, sofern die Schwester-Repos nebenan liegen.
- **Nicht getestet:** Zeiten; kein Mutationstest; Linux-CI: grün im ersten Lauf (396 bestanden, knapp acht Minuten; die Toleranzen waren von Anfang an auf die Streuung zwischen Rechnern ausgelegt); die Zahlen der Tabellen stammen aus dem Windows-Lauf.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Entscheidungsweg, fünf Experimente, Grenzen, Formulierung |
| `avw_rule.py` | Die Regel: Größe, Aufgabe, Zeitbudget → Verfahren (reine Funktion) |
| `avw_evaluation.py` | Das Portfolio auf einer Instanz, Zeilen der Vergleiche, Bedauern, Kante, gepaarter Unterschied, Verdikte |
| `avw_rng.py`, `avw_cost.py`, `avw_landscape.py` | SplitMix64, Kosten, Aufzählung (Kopien aus Stück 1 und 2) |
| `avw_instance.py` | Sechs Familien der Flussmatrix, Raster bis 6×6, Handbeispiele |
| `avw_assignment.py` | Ungarische Methode samt Dualwerten (Kopie aus Stück 8) |
| `avw_bounds.py` | Gilmore–Lawler, Dual Ascent, Abstiege aus Zufall (Kopie aus Stück 3 und 5) |
| `avw_lp.py` | Linearisierung als LP (Kopie aus Stück 5, scipy) |
| `avw_tree.py` | Branch and Bound (Kopie aus Stück 8, nur die Arten ohne / linear / Gilmore–Lawler) |
| `avw_place.py`, `avw_loop.py` | Pads, Platzierung, Rundung; Schleife (Kopien aus Stück 9 und 10) |
| `avw_density.py`, `avw_penalty.py` | Bin-Raster und Poisson-Gleichung; Strafverfahren (Kopien aus Stück 11) |
| `avw_search.py` | Tauschabstieg mit Zählung, Annealing, Neustarts (Kopie aus Stück 12) |
| `avw_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `avw_pdf_export.py` | PDF-Export des Ergebnisses |
| `avw_constants.py` | Größen, Familien, Portfolio, feste und frische Reihen, Farben, Presets |
| `avw_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Button |
| `avw_layout.py` | Fester Kopf (Stylesheet) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; `scipy` nur für die Linearisierung) |
| `tests/` | Regel, Auswertung, Verdikte, Schranken, Baum, Kerne, Abbildungen, Presets, Layout, AppTest, Orakel, Zahlen der README (`test_claims.py`, `rows.py`), Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Neue Verfahren.** Das Stück vergleicht, es erfindet nichts.
- **Beweis mit Pads, QAPLIB, Instanzen über `n = 36`.**
- **Die gelben Stücke 7, 13 und 14** der Reihe: als eigene Demos gebaut, hier nicht verglichen.
- **Zeiten in Tests.**
- **Asymmetrische Flüsse und Abstände.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version in den App-Einstellungen prüfen (lokal Python 3.14, CI Python 3.12); der Code verwendet nur Merkmale, die in Python 3.12 laufen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, pandas, SciPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
