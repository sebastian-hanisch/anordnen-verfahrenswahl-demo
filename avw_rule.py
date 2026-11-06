"""Die Entscheidungsregel: aus Größe, Aufgabe und Zeitbudget das Verfahren. Eine reine Funktion, ohne Rechnung und ohne Zeit.

Die Regel fasst die Messungen der Phase 0 und dieser Demo zusammen (Messung an den sechs erfundenen Familien, nicht Satz):
  * Beweisen verlangt: bis n = 12 Branch and Bound mit der Gilmore–Lawler-Schranke (Stück 8); darüber ist der Baum in dieser Fassung zu groß, es bleiben die Schranken als Güteaussage und das Finden.
  * Finden bis n = 16: Neustarts des Abstiegs aus Zufall (20; bei knappem Zeitbudget 6).
  * Finden ab n = 20: die Schleife aus Stück 10 als Startlösung, danach kaltes Annealing (bei knappem Zeitbudget nur der Abstieg aus der Schleife).
Die Grenze zwischen 16 und 20 ist die der gemessenen Größen; die Kreuzung der Zeit liegt zwischen n = 20 und n = 25 (bei n = 20 zeigen die Messreihen verschiedene Sieger)."""

from __future__ import annotations

from dataclasses import dataclass

import avw_constants as C

PROVE_MAX_N = 12                 # größte Größe, für die der Beweis in dieser Fassung gerechnet wird
CROSS_N = 20                     # ab hier: Schleife mit Annealing statt Neustarts


@dataclass(frozen=True)
class Step:
    question: str                # die Frage
    answer: str                  # die Antwort für diese Eingabe
    piece: str                   # Verweis auf das Stück der Reihe
    keys: tuple = ()             # Verfahren (Schlüssel), die die Frage entscheidet


@dataclass(frozen=True)
class Advice:
    task: str
    n: int
    budget: str
    steps: tuple                 # Entscheidungsweg
    proof: str | None            # Art des Beweises ("glb") oder None (kein Beweis verlangt / nicht in Reichweite)
    find: str | None             # Schlüssel des Verfahrens für das Finden (FIND_KEYS) oder None
    bounds: tuple                # Schranken, die als Güteaussage gerechnet werden (BOUND_KEYS)
    label: str                   # kurzer Name der Empfehlung


def advise(n: int, task: str, budget: str = C.DEFAULT_BUDGET) -> Advice:
    """Die Empfehlung für Größe `n`, Aufgabe (`find` / `prove`) und Zeitbudget (`tight` / `normal`)."""
    if task not in C.TASKS or budget not in C.BUDGET_CHOICES:
        raise ValueError("unbekannte Aufgabe oder unbekanntes Zeitbudget")
    steps = []
    bounds = ("glb",) if n > PROVE_MAX_N else tuple(k for k in C.BOUND_KEYS if k != "lp" or n <= C.LP_MAX_N)
    if task == "prove":
        steps.append(Step("Muss das Optimum bewiesen werden?", "ja", "Stück 3 bis 8", ("glb", "tree")))
        if n <= PROVE_MAX_N:
            steps.append(Step(f"Ist n höchstens {PROVE_MAX_N}?", "ja", "Stück 8", ("tree",)))
            steps.append(Step("Welcher Beweis?", "Branch and Bound mit der Gilmore–Lawler-Schranke; als Anfangswert die beste von 200 Abstiegen", "Stück 8", ("tree",)))
            return Advice(task, n, budget, tuple(steps), "glb", None, bounds, "Branch and Bound mit Gilmore–Lawler")
        steps.append(Step(f"Ist n höchstens {PROVE_MAX_N}?", "nein", "Stück 8", ("tree",)))
        steps.append(Step("Was bleibt?", "Der Beweis ist hier nicht in Reichweite; die Schranke belegt eine Güte, gefunden wird wie unten", "Stück 3", ("glb",)))
    else:
        steps.append(Step("Muss das Optimum bewiesen werden?", "nein", "Stück 3 bis 8", ()))
    big = n >= CROSS_N
    steps.append(Step(f"Ist n mindestens {CROSS_N}?", "ja" if big else "nein", "Stück 12", ("sa_s", "neu20")))
    steps.append(Step("Wie knapp ist die Rechenzeit?", C.BUDGET_NAMES[budget], "Stück 12", ()))
    if big:
        key = "abs_s" if budget == "tight" else "sa_s"
    else:
        key = "neu6" if budget == "tight" else "neu20"
    steps.append(Step("Welches Verfahren?", C.FIND_NAMES[key], C.FIND_PIECE[key], (key,)))
    return Advice(task, n, budget, tuple(steps), None, key, bounds, C.FIND_NAMES[key])


def rule_key(n: int, budget: str = C.DEFAULT_BUDGET) -> str:
    """Das Verfahren der Regel für das Finden: `neu20` bis n = 16, `sa_s` ab n = 20 (Zeitbudget normal); knapp: `neu6` / `abs_s`."""
    return advise(n, "find", budget).find
