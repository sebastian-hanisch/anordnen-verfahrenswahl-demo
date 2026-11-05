"""Hilfen für die Tests: eine zweite, unabhängig geschriebene Kostenrechnung, die Aufzählung und künstliche Zeilen (ORACLE-PLAYBOOK §5)."""

from itertools import permutations

import avw_constants as C
import avw_evaluation as E


def independent_cost(perm, inst, pads=None):
    """Kosten einer Anordnung als einfache Doppelschleife: Σ_{i<k} F·|Δ|₁ (+ Σ_{i,Pad} w·|Δ|₁)."""
    xy = inst.xy
    total = 0.0
    for i in range(inst.n):
        for k in range(i + 1, inst.n):
            total += float(inst.F[i, k]) * (abs(int(xy[perm[i]][0]) - int(xy[perm[k]][0])) + abs(int(xy[perm[i]][1]) - int(xy[perm[k]][1])))
        if pads is not None:
            for j in range(pads.count):
                total += float(pads.w[i, j]) * (abs(xy[perm[i]][0] - pads.pos[j][0]) + abs(xy[perm[i]][1] - pads.pos[j][1]))
    return total


def brute_force(inst, pads=None):
    """(kleinste Kosten, eine beste Anordnung) über alle n! Anordnungen mit der unabhängigen Kostenrechnung (nur n ≤ 6 sinnvoll)."""
    best = None
    for q in permutations(range(inst.n)):
        v = independent_cost(q, inst, pads)
        if best is None or v < best[0] - 1e-9:
            best = (v, list(q))
    return best


def make_row(n, cost, sec=None, p=4, exact=False, opt=None, family="cluster", seed=100000, work=None):
    """Künstliche Zeile eines Vergleichs mit den Feldern von `find_row` (Kosten je Verfahren in `cost`, fehlende gleich dem größten Wert)."""
    top = max(cost.values())
    cost = {k: float(cost.get(k, top)) for k in C.FIND_KEYS}
    sec = {k: float((sec or {}).get(k, 0.1)) for k in C.FIND_KEYS}
    best = min(list(cost.values()) + ([opt] if opt is not None else []))
    return {"family": family, "n": n, "seed": seed, "p": p, "exact": exact, "opt": opt, "best": best, "cost": cost, "sec": sec,
            "work": work or {k: {"bewertungen": 10} for k in C.FIND_KEYS}, "gap": {k: E.rel(cost[k], best) for k in C.FIND_KEYS}, "hit": {k: cost[k] <= best + 1e-9 for k in C.FIND_KEYS}}
