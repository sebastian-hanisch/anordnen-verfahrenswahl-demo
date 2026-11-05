"""Konstanten: Größen, Raster, Familien der Flussmatrix, die Kerne der Stücke 3 bis 12, das Portfolio der Verfahren, feste Reihen der Experimente, Farben und Presets."""

FIND_SIZES = (8, 12, 16, 20, 25, 36)                  # Finden: Größen der Vergleiche (Raster 2×4 bis 6×6)
PROVE_SIZES = (8, 9, 12)                              # Beweisen: reine Zuordnung ohne Pads (Stück 8: Baum bis n = 12)
SIZES = (8, 9, 12, 16, 20, 25, 36)
EXACT_SIZES = (6, 8, 9)                               # alle n! Anordnungen werden aufgezählt: das Optimum ist bekannt
DEFAULT_N = 8
GRID = {6: (2, 3), 8: (2, 4), 9: (3, 3), 12: (3, 4), 16: (4, 4), 20: (4, 5), 25: (5, 5), 36: (6, 6)}    # Plätze als Raster (Zeilen, Spalten), Abstand = Manhattan
SEED_MAX, DEFAULT_SEED = 999999, 48
FIXED_SEED0 = 100000                                  # feste Instanzen: Seeds ab 100000 (nie ein einzelner Seed als Befund)
FRESH_SEED0 = 200000                                  # frische Instanzen für die Regel (Experiment 5): Seeds ab 200000
SEEDS_FIND = {8: 10, 12: 5, 16: 3}                    # Seeds je Familie und Pad-Zahl: 10 / 5 / 3 → 180 / 90 / 54 Instanzen (Pads 2, 4, 8)
SEEDS_LARGE = 3                                       # n = 20, 25, 36: drei Seeds je Familie, nur 4 Pads → 18 Instanzen
SEEDS_FRESH = {8: 5, 12: 3, 16: 2, 20: 3, 25: 3, 36: 3}   # frische Instanzen: 90 / 54 / 36 / 18 / 18 / 18
SEEDS_PROVE = {8: 5, 9: 3, 12: 3}                     # Beweisen: 30 / 18 / 18 Instanzen (sechs Familien)
PROVE_CAP = 300_000                                   # Obergrenze der Knoten des Branch and Bound
PROVE_STARTS = 200                                    # Abstiege aus Zufallsstarts für den Anfangswert des Branch and Bound
STARTS = 100                                          # nur für den Kern `reference` der Platzierung (ab n = 12); die Demo vergleicht mit dem besten Verfahren der Instanz
FAQ_STARTS = 20


PAD_CHOICES = (2, 4, 8)                               # Zahl der festen Pads (Anker) auf dem Ring um das Raster
LARGE_PADS = 4                                        # ab n = 20 nur diese Pad-Zahl
DEFAULT_PADS = 4
PAD_LINKS = 2                                         # jedes Pad hängt an so vielen zufälligen Bauteilen
DEFAULT_FACTOR = 1.0                                  # Pad-Gewicht = Faktor · Grundgewicht (Median der positiven Flüsse, mindestens 1); fest
EPS = 0.3                                             # untere Grenze der Länge in der Umgewichtung F / max(|Δ|, EPS) (in Platzabständen); zugleich die Rundung γ der glatten Länge
CENTER_ANCHOR = 1e-6                                  # schwacher Anker in der Mitte: Bauteile ohne Weg zu einem Pad fallen auf einen Punkt, das System bleibt lösbar
RING_MARGIN = 1.5                                     # Abstand des Pad-Rings vom Raster der Plätze (in Platzabständen)
TIE_DECIMALS = 8                                      # Stellen (relativ zum größten Betrag), auf die Abstandsquadrate und Koordinaten vor Zuordnung und Sortierung gerundet werden
LOOP_ROUNDS, LOOP_REWEIGHTS, LOOP_ANCHOR = 15, 2, 0.2  # die Schleife aus Stück 10 (Zuordnung) als Vergleich
DEFAULT_ROUNDS, DEFAULT_REWEIGHTS, DEFAULT_ANCHOR = LOOP_ROUNDS, LOOP_REWEIGHTS, LOOP_ANCHOR
ROUND_REWEIGHTS = 2                                   # Umgewichtungen der Platzierung für den Startwert und die Rundung aus Stück 9
FACTOR_CHOICES = (0.25, 1.0, 4.0, 16.0)               # Faktoren auf das Pad-Gewicht, nur für Kern-Tests (aus Stück 9)
ANCHOR_CHOICES = (0.02, 0.2, 1.0)                     # nur für die Kern-Tests der Schleife (aus Stück 10)
REWEIGHT_CHOICES = (0, 2)
LEGALIZERS = ("assign", "bisect")
DEFAULT_LEGALIZER = "assign"
T_END = 0.01                                          # Endtemperatur des Annealing in Vielfachen von s (mittlerer Betrag der Kostenänderung aller Tausche)
SA_LOOP_T0 = 0.1                                      # Starttemperatur beim kalten Annealing aus der Schleife
BUDGETS = {6: 800, 8: 1500, 9: 2000, 12: 3000, 16: 6000, 20: 9000, 25: 12000, 36: 20000}   # Zugzahl des Annealing je Größe; ab n = 20 in dieser Demo gesetzt (Stück 12 definiert sie nur bis n = 16)
DEFAULT_BUDGET_FACTOR = 1.0
RESTART_KS = (1, 3, 6, 20)
START_CHOICES = ("random", "round", "loop")           # Startlösungen des Abstiegs (nur für die Kern-Tests)
T0_CHOICES = (0.1, 0.5, 2.0)                          # Starttemperaturen des Annealing in Vielfachen von s (nur für die Kern-Tests)
RESTARTS_SHORT, RESTARTS_LONG = 6, 20                 # Neustarts des Abstiegs aus Zufall: knapp / normal

MODELS = ("electro", "overflow", "none")              # Dichtestrafe: elektrostatisch (Poisson), lokale Überlaufstrafe, keine
MODEL_NAMES = {"electro": "Elektrostatisch", "overflow": "Lokale Überlaufstrafe", "none": "Keine Dichtestrafe"}
MODEL_HELP = {"electro": "Ladung minus Mittelwert, Poisson-Gleichung mit Neumann-Rand: jedes Bauteil spürt alle anderen (langreichweitig).",
              "overflow": "Quadrat des Überlaufs je Bin (Dichte über dem Sollwert): nur dort, wo es zu voll ist (kurzreichweitig).",
              "none": "Nur die glatte lineare Länge: alles zieht sich zu den Pads und zueinander, es bleibt bei einem Klumpen."}
DEFAULT_MODEL = "electro"
MARGIN_CHOICES = (0.0, 0.25, 0.5, 1.0)                # Randzone um den Block der Plätze, in Platzabständen
DEFAULT_MARGIN = 0.5
WIDTH_CHOICES = (1.0, 2.0, 3.0, 4.0)                  # Kantenlänge der Ladung zu Beginn (Platzabstände); sie sinkt linear auf 1 (1 = ohne Weichzeichnen)
DEFAULT_WIDTH = 3.0
RULES = ("last", "best")                              # Rundungsregel: die letzte Stufe oder die billigste der legalen Anordnungen aller Stufen
RULE_NAMES = {"last": "Letzte Stufe", "best": "Billigste Stufe"}
DEFAULT_RULE = "last"
BINS_PER_SLOT = 2                                     # Bins je Platzabstand und Achse
STAGES = 12                                           # Stufen des Strafverfahrens (feste Zahl)
INNER = 25                                            # Abstiegsschritte je Stufe
GROWTH = 1.8                                          # Wachstum von λ je Stufe
JITTER = 0.3                                          # Breite der festen Streuung des Startwerts (Platzabstände, ±0,15)
MAX_MOVE = 0.25                                       # größte Verschiebung eines Bauteils je Schritt (nur zur Schranke der Schrittweite)
ARMIJO = 1e-4                                         # Armijo-Konstante der Rückverfolgung

# Das Portfolio der Platzierungsseite (Finden): Schlüssel, Name, Stück
FIND_KEYS = ("rund", "schleife", "elektro", "elektro_b", "abs_z", "abs_r", "abs_s", "abs_e", "neu6", "neu20", "sa_s")
FIND_NAMES = {"rund": "Einmal runden", "schleife": "Schleife", "elektro": "Dichtestrafe, letzte Stufe", "elektro_b": "Dichtestrafe, billigste Stufe", "abs_z": "Abstieg aus Zufall", "abs_r": "Abstieg aus der Rundung",
              "abs_s": "Abstieg aus der Schleife", "abs_e": "Abstieg aus der Dichtestrafe", "neu6": "6 Neustarts", "neu20": "20 Neustarts", "sa_s": "Schleife und Annealing"}
FIND_PIECE = {"rund": "Stück 9", "schleife": "Stück 10", "elektro": "Stück 11", "elektro_b": "Stück 11", "abs_z": "Stück 12", "abs_r": "Stück 12", "abs_s": "Stück 12", "abs_e": "Stück 12", "neu6": "Stück 12", "neu20": "Stück 12", "sa_s": "Stück 12"}
TASKS = ("find", "prove")
TASK_NAMES = {"find": "Finden: eine gute Anordnung", "prove": "Beweisen: das Optimum belegen"}
DEFAULT_TASK = "find"
BUDGET_CHOICES = ("tight", "normal")
BUDGET_NAMES = {"tight": "knapp", "normal": "normal"}
DEFAULT_BUDGET = "normal"
BOUND_KEYS = ("glb", "da5", "lp")
BOUND_NAMES = {"glb": "Gilmore–Lawler", "da5": "Dual Ascent (5 Runden)", "lp": "Linearisierung (LP)"}
BOUND_PIECE = {"glb": "Stück 3", "da5": "Stück 5", "lp": "Stück 5"}
LP_MAX_N = 9                                          # die Linearisierung (LP) rechnet nur bis n = 9
LIN_MAX_N = 9                                         # Branch and Bound mit linearen Knotenschranken nur bis n = 9 (sonst Obergrenze regelmäßig erreicht)
TREE_ARTS = ("glb", "lin")
TREE_NAMES = {"glb": "Branch and Bound, Gilmore–Lawler", "lin": "Branch and Bound, lineare Knotenschranken"}
NOT_COMPUTED = (("Projizierte Eigenwertschranke", "Stück 4", "Lücke 12,6 / 19,7 / 27,5 % bei n = 8 / 9 / 12 (Messung der Phase 0)"),
                ("Konvexe Schranke (Birkhoff, Stück 6)", "Stück 6", "Lücke über 100 % bei n = 8, 9, 12 (Messung der Phase 0)"))
CROSS_SIZES = FIND_SIZES                               # Größen der Kreuzung (Experiment 4)

FAMILIES = ("netlist", "uniform", "sparse", "cluster", "star", "skewed")
DEFAULT_FAMILY = "cluster"
FAMILY_NAMES = {"netlist": "Netzliste", "uniform": "Gleichverteilt", "sparse": "Dünn besetzt", "cluster": "Zwei Cluster", "star": "Stern", "skewed": "Wenige starke Flüsse"}
FAMILY_HELP = {
    "netlist": "Netzliste aus Dreiergruppen (IC, Kondensator, Widerstand), jedes Paar in einem Netz zählt Fluss 1: die Familie aus Stück 1.",
    "uniform": "Jedes Paar von Bauteilen hat einen zufälligen Fluss von 0 bis 9, gleichverteilt: dichte Matrix ohne Struktur.",
    "sparse": "Nur drei von zehn Paaren haben Fluss (1 bis 9), die übrigen keinen: dünn besetzt ohne weitere Struktur.",
    "cluster": "Zwei Gruppen von Bauteilen: innerhalb einer Gruppe starker Fluss (8 bis 10), zwischen den Gruppen schwacher (0 bis 2).",
    "star": "Ein Bauteil (die Nabe) hat starken Fluss (1 bis 9) zu allen anderen; zwischen den übrigen höchstens 1.",
    "skewed": "Die Flüsse sind schief verteilt: viele Paare ohne oder mit kleinem Fluss, wenige mit sehr großem (bis 60).",
}

# Netzliste (wie in Stück 1 bis 5)
N_NETS_PER_COMPONENT = 1.5
NET_SIZES = (2, 3, 4)
NET_WEIGHTS = (5, 3, 2)
LOCAL_NET_PERCENT = 70
GROUP = 3
# Dünn besetzt, Cluster, Stern, schief (wie in Stück 2)
SPARSE_PERCENT = 30
UNIFORM_MAX = 9
CLUSTER_STRONG, CLUSTER_WEAK_MAX = 8, 2
SKEW_VALUES = (0, 1, 2, 4, 8, 16, 32, 60)
SKEW_WEIGHTS = (45, 22, 13, 8, 6, 3, 2, 1)           # ganzzahlige Gewichte (Summe 100), schweres Ende

HAND_FLOWS = ((0, 1, 5), (1, 2, 1))                   # Handbeispiel 1: drei Bauteile auf einer Zeile, Fluss A–B 5, B–C 1
HAND_GRID = (1, 3)
HAND_GAP_FLOWS = ((0, 2, 1), (0, 3, 1), (1, 2, 1), (1, 3, 1))   # Handbeispiel 3: vier Bauteile auf einer Zeile, A und B gegen C und D
HAND_GAP_GRID = (1, 4)
HAND_GRID_FLOWS = ((0, 1, 3), (0, 2, 1), (1, 3, 2), (2, 3, 4))  # Handbeispiel 2 (aus Stück 1): Raster 2×2
HAND_GRID_GRID = (2, 2)

COLORS = {"best": "#2F6B65", "local": "#c0504d", "pad": "#b08a2e", "cont": "#c0504d", "other": "rgba(150,150,150,0.6)", "line": "#4c78a8", "ok": "#2F6B65", "warn": "#b08a2e", "bad": "#b34a4a",
          "family": {"netlist": "#4c78a8", "uniform": "#9c755f", "sparse": "#b08a2e", "cluster": "#2F6B65", "star": "#8e6bb0", "skewed": "#c0504d"}}

_BASE = {"family": DEFAULT_FAMILY, "n": DEFAULT_N, "seed": DEFAULT_SEED, "pads": DEFAULT_PADS, "task": DEFAULT_TASK, "budget": DEFAULT_BUDGET}
PRESETS = {
    "Standardfall: Finden, acht Bauteile": dict(_BASE),
    "Beweisen, acht Bauteile": dict(_BASE, task="prove"),
    "Beweisen, zwölf Bauteile": dict(_BASE, task="prove", n=12),
    "Finden, zwölf Bauteile": dict(_BASE, n=12),
    "Finden, sechzehn Bauteile": dict(_BASE, n=16),
    "Finden, die Kreuzung (n = 20)": dict(_BASE, n=20),
    "Finden, 36 Bauteile": dict(_BASE, n=36),
    "Finden, wenig Zeit": dict(_BASE, n=25, budget="tight"),
}
PRESET_HELP = {
    "Standardfall: Finden, acht Bauteile": "Acht Bauteile, vier Pads: alle Verfahren der Platzierungsseite auf einer Instanz; die Regel empfiehlt 20 Neustarts des Abstiegs aus Zufall.",
    "Beweisen, acht Bauteile": "Dieselbe Aufgabe ohne Pads, aber mit verlangtem Beweis des Optimums: Schranken und Branch and Bound (Stück 3 bis 8).",
    "Beweisen, zwölf Bauteile": "Zwölf Bauteile: der Baum wird groß (Tausende bis Hunderttausende Knoten); die Rechnung läuft nur auf Knopfdruck.",
    "Finden, zwölf Bauteile": "Zwölf Bauteile mit Pads: die Neustarts treffen den Vergleichswert noch fast immer, die Relaxationen liegen darüber.",
    "Finden, sechzehn Bauteile": "Sechzehn Bauteile: die Neustarts sind noch am besten, das Annealing aus der Schleife holt auf.",
    "Finden, die Kreuzung (n = 20)": "Zwanzig Bauteile: hier liegen Neustarts und Schleife mit Annealing nah beieinander; die Rechenzeit entscheidet.",
    "Finden, 36 Bauteile": "36 Bauteile: Schleife mit Annealing ist deutlich schneller als 20 Neustarts.",
    "Finden, wenig Zeit": "25 Bauteile, knappes Zeitbudget: die Regel empfiehlt die Schleife mit anschließendem Abstieg statt Annealing.",
}


def n_text(n: int) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 362880 → „362 880“."""
    return f"{n:,}".replace(",", " ")


assert set(PRESETS) == set(PRESET_HELP) and set(FAMILY_NAMES) == set(FAMILIES) == set(FAMILY_HELP) and set(FIND_NAMES) == set(FIND_KEYS) == set(FIND_PIECE)
assert all(p["n"] in SIZES and p["family"] in FAMILIES and 0 <= p["seed"] <= SEED_MAX and p["pads"] in PAD_CHOICES and p["task"] in TASKS and p["budget"] in BUDGET_CHOICES for p in PRESETS.values())
assert all(r * c == n for n, (r, c) in GRID.items()) and sum(SKEW_WEIGHTS) == 100 and set(SIZES) <= set(GRID) and set(BUDGETS) >= set(SIZES)
