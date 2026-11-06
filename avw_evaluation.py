"""Das Portfolio auf einer Instanz, Vergleiche über feste und frische Instanzen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Alle Aussagen gelten für die gerechneten Instanzen, die sechs erfundenen Familien, die **erfundenen Pads** (Zahl, Ort, Gewicht, Verbindungen) und die Einstellungen der Stücke 3 bis 12 (Schleife: 15 Runden, Dichtestrafe: Randzone 0,5 und Ladungsbreite 3,
Annealing: Zugzahlen aus `avw_constants.BUDGETS`, ab n = 20 in dieser Demo gesetzt). **Bedauern** = (Kosten − beste Kosten aller Verfahren auf der Instanz) / beste Kosten; bis n = 9 gehört das aufgezählte Optimum zu den Verfahren,
ab n = 12 ist der Vergleichswert selbst ein Verfahrensergebnis: das Bedauern ist dann eine **obere** Grenze der Lücke zum Optimum und kann nie negativ sein.
**Aufwand** wird zweifach angegeben: als **Zeit** (Sekunden dieser Python-Fassung auf diesem Rechner, schwankt von Lauf zu Lauf; nur Größenordnungen sind belastbar; Zeiten stehen in Anzeigen, nie in Tests) und als **Zählung**
(Bewertungen einer Anordnung, Runden der Schleife, Auswertungen der Dichtestrafe, Knoten des Baums): die Einheiten sind nicht untereinander vergleichbar."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

import avw_bounds as B
import avw_constants as C
import avw_loop as Lp
import avw_lp as LP
import avw_penalty as Pn
import avw_place as Pl
import avw_rule as R
import avw_search as S
import avw_tree as T
from avw_instance import make_instance


@dataclass(frozen=True)
class Settings:
    family: str = C.DEFAULT_FAMILY
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    pads: int = C.DEFAULT_PADS
    task: str = C.DEFAULT_TASK
    budget: str = C.DEFAULT_BUDGET


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return de(100.0 * x, digits) + " %"


def fam(name: str) -> str:
    return C.FAMILY_NAMES.get(name, name)


def num(x: float) -> str:
    """Ganze Zahl ohne Nachkommastelle, sonst eine Stelle: 27 / 27,5 / −12,1."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else de(x, 1)


def count(x: float) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 1200 → „1 200“."""
    return C.n_text(int(round(x)))


def secs(x: float) -> str:
    """Sekunden mit sinnvoller Stellenzahl: 0,016 s / 0,42 s / 5,1 s / 31 s."""
    if x < 0.1:
        return de(x, 3) + " s"
    if x < 10:
        return de(x, 2 if x < 1 else 1) + " s"
    return de(x, 0) + " s"


def rel(a: float, b: float) -> float:
    """(a − b) / b; 0, wenn beide Null sind; Rundungsreste unter 1e-12 werden zu 0."""
    if not b:
        return 0.0 if not a else float("nan")
    r = (a - b) / b
    return 0.0 if abs(r) < 1e-12 else r


def timed(f):
    t = time.perf_counter()
    r = f()
    return r, time.perf_counter() - t


# ----------------------------------------------------------------------------- Finden: das Portfolio auf einer Instanz

def optimum(inst, c):
    """Das aufgezählte Optimum (bis n = 9), sonst None."""
    if inst.n in C.EXACT_SIZES:
        return float(Pl.all_costs(inst, c)[1].min())
    return None


def solve_find(family: str, n: int, seed: int, p: int) -> dict:
    """Alle Verfahren der Platzierungsseite auf derselben Instanz (Pads `p`), mit Kosten, Zeit und Zählung.

    Schlüssel: C.FIND_KEYS. Zeit bei zusammengesetzten Verfahren: die Summe der Teile. Die 20 Neustarts des Abstiegs bilden `neu6` (die ersten sechs) und `neu20`."""
    inst = make_instance(family, n, seed)
    pads = Pl.make_pads(inst, p, seed, C.DEFAULT_FACTOR)
    c = Pl.linear_costs(inst, pads)
    F, D = inst.F.astype(float), inst.D.astype(float)
    cost, sec, work, perm = {}, {}, {}, {}

    def cst(q):
        return Pl.cost_of(q, F, D, c)

    X9, t = timed(lambda: Pl.positions(inst, pads, C.ROUND_REWEIGHTS))
    perm["rund"], t2 = timed(lambda: Pl.round_to_slots(inst, X9))
    cost["rund"], sec["rund"], work["rund"] = cst(perm["rund"]), t + t2, {"runden": 1}
    loop, sec["schleife"] = timed(lambda: Lp.run_loop(inst, pads, c))
    perm["schleife"], cost["schleife"] = loop.rounds[-1].perm, loop.rounds[-1].upper
    work["schleife"] = {"runden": len(loop.rounds)}
    pen, t = timed(lambda: Pn.run_penalty(inst, pads, c, "electro", C.DEFAULT_MARGIN, C.DEFAULT_WIDTH, seed))
    k = pen.best_index
    perm["elektro"], cost["elektro"] = pen.stages[-1].perm, pen.stages[-1].cost
    perm["elektro_b"], cost["elektro_b"] = pen.stages[k].perm, pen.stages[k].cost
    sec["elektro"] = sec["elektro_b"] = t
    work["elektro"] = work["elektro_b"] = {"auswertungen": pen.evals, "stufen": len(pen.stages)}
    start_rand = S.start_perms(inst, pads, c, seed)["random"]
    for key, start, base, w0 in (("abs_z", start_rand, 0.0, {}), ("abs_r", perm["rund"], sec["rund"], work["rund"]), ("abs_s", perm["schleife"], sec["schleife"], work["schleife"]), ("abs_e", perm["elektro_b"], sec["elektro"], work["elektro"])):
        d, t = timed(lambda: S.descent_counted(start, F, D, c))
        perm[key], cost[key], sec[key] = d.perm, d.cost, base + t
        work[key] = {**w0, "bewertungen": d.evals}
    # Neustarts des Abstiegs aus Zufall (SplitMix64 wie in `S.restarts`), mit der Zeit nach jedem Neustart
    rng = S.SplitMix64(seed * 977 + 3)
    best, bestp, cum, evals, curve, perm_at = None, None, 0.0, 0, [], {}
    for _ in range(C.RESTARTS_LONG):
        st = list(range(n))
        rng.shuffle(st)
        d, t = timed(lambda: S.descent_counted(st, F, D, c))
        cum += t
        evals += d.evals
        if best is None or d.cost < best - 1e-9:
            best, bestp = d.cost, d.perm
        curve.append((cum, best, evals))
        perm_at[len(curve)] = bestp
    for key, kk in (("neu6", C.RESTARTS_SHORT), ("neu20", C.RESTARTS_LONG)):
        cost[key], sec[key], work[key] = curve[kk - 1][1], curve[kk - 1][0], {"bewertungen": curve[kk - 1][2]}
    perm["neu6"], perm["neu20"] = perm_at[C.RESTARTS_SHORT], perm_at[C.RESTARTS_LONG]
    a, t = timed(lambda: S.anneal(perm["schleife"], F, D, c, S.budget_for(n), C.SA_LOOP_T0, seed))
    perm["sa_s"], cost["sa_s"], sec["sa_s"] = a.perm, a.cost, sec["schleife"] + t
    work["sa_s"] = {**work["schleife"], "bewertungen": a.moves + n * (n - 1) // 2}
    opt = optimum(inst, c)
    best_cost = min(list(cost.values()) + ([opt] if opt is not None else []))
    return {"family": family, "n": n, "seed": seed, "p": p, "inst": inst, "pads": pads, "c": c, "exact": opt is not None, "opt": opt, "best": best_cost,
            "cost": cost, "sec": sec, "work": work, "perm": perm, "curve": curve,
            "gap": {k_: rel(cost[k_], best_cost) for k_ in C.FIND_KEYS}, "hit": {k_: cost[k_] <= best_cost + 1e-9 for k_ in C.FIND_KEYS}}


def find_row(family: str, n: int, seed: int, p: int) -> dict:
    """Eine Instanz eines Vergleichs: wie `solve_find`, ohne Anordnungen, Instanz und Kurve (spart Speicher)."""
    v = solve_find(family, n, seed, p)
    return {k: v[k] for k in ("family", "n", "seed", "p", "exact", "opt", "best", "cost", "sec", "work", "gap", "hit")}


def find_jobs(n: int, fresh: bool = False) -> list:
    """Die Instanzen eines Vergleichs: (Familie, n, Seed, Pads). Fest: Seeds ab 100000; frisch: ab 200000. Bis n = 16 Pads 2 / 4 / 8, ab n = 20 nur 4."""
    seed0 = C.FRESH_SEED0 if fresh else C.FIXED_SEED0
    seeds = (C.SEEDS_FRESH if fresh else C.SEEDS_FIND if n <= 16 else {n: C.SEEDS_LARGE})[n]
    pads = C.PAD_CHOICES if n <= 16 else (C.LARGE_PADS,)
    return [(f, n, s, p) for f in C.FAMILIES for s in range(seed0, seed0 + seeds) for p in pads]


def find_sweep(family: str, n: int, fresh: bool = False) -> list:
    return [find_row(*job) for job in find_jobs(n, fresh) if job[0] == family]


def pooled(by_family: dict) -> list:
    return [r for f in C.FAMILIES if f in by_family for r in by_family[f]]


# ----------------------------------------------------------------------------- Beweisen: Schranken und Baum auf einer Instanz (reine Zuordnung)

def solve_prove(family: str, n: int, seed: int, tree: bool = True, cap: int | None = None) -> dict:
    """Schranken, Abstiege und Branch and Bound auf der reinen Zuordnung (ohne Pads). `tree=False`: nur Gilmore–Lawler und die Abstiege (für n über 12)."""
    cap = C.PROVE_CAP if cap is None else cap
    inst = make_instance(family, n, seed)
    F, D = inst.F, inst.D
    sec, bound = {}, {}
    (ub20, _), sec["ub20"] = timed(lambda: B.best_found(F, D, seed, 20))
    (ub, ub_perm), sec["ub200"] = timed(lambda: B.best_found(F, D, seed, C.PROVE_STARTS))
    g, sec["glb"] = timed(lambda: B.gilmore_lawler(F, D))
    bound["glb"] = g.glb
    if tree:
        da, sec["da5"] = timed(lambda: B.dual_ascent(F, D, 5))
        bound["da5"] = da.final
        if n <= C.LP_MAX_N:
            lp, sec["lp"] = timed(lambda: LP.solve_lp(F, D))
            bound["lp"] = lp.value
    row = {"family": family, "n": n, "seed": seed, "cap": cap, "inst": inst, "ub20": ub20, "ub200": ub, "ub_perm": ub_perm, "bound": bound, "sec": sec, "tree": {}}
    if tree:
        for art in C.TREE_ARTS:
            if art == "lin" and n > C.LIN_MAX_N:
                continue
            tr = T.solve(F, D, art, incumbent=ub, cap=cap)
            row["tree"][art] = {"nodes": tr.nodes, "best": tr.best, "capped": tr.capped, "sec": tr.seconds, "root": tr.root, "share": tr.share, "perm": tr.perm}
        g_ = row["tree"]["glb"]
        row["opt"] = None if g_["capped"] else g_["best"]
    else:
        row["opt"] = None
    row["ref"] = row["opt"] if row["opt"] is not None else ub
    return row


def prove_row(family: str, n: int, seed: int) -> dict:
    v = solve_prove(family, n, seed)
    return {k: v[k] for k in ("family", "n", "seed", "cap", "ub20", "ub200", "bound", "sec", "tree", "opt", "ref")}


def prove_sweep(family: str, n: int) -> list:
    return [prove_row(family, n, s) for s in range(C.FIXED_SEED0, C.FIXED_SEED0 + C.SEEDS_PROVE[n])]


# ----------------------------------------------------------------------------- Auswertungen

def regret_stats(rows: list, key: str) -> dict:
    """Mittleres und mittleres Bedauern, Zahl der Instanzen, in denen `key` das Beste erreicht, und Median der Zeit."""
    g = [r["gap"][key] for r in rows]
    return {"count": len(rows), "mean": float(np.mean(g)), "median": float(np.median(g)), "hit": sum(r["hit"][key] for r in rows), "sec": float(np.median([r["sec"][key] for r in rows]))}


def front(rows: list, keys=C.FIND_KEYS) -> list:
    """Verfahren auf der Kante aus Median der Zeit und mittlerem Bedauern: kein anderes ist zugleich schneller (oder gleich schnell) und besser."""
    pts = sorted((regret_stats(rows, k)["sec"], regret_stats(rows, k)["mean"], k) for k in keys)
    out, lo = [], float("inf")
    for _, g, k in pts:
        if g < lo - 1e-12:
            out.append(k)
            lo = g
    return out


def paired(rows: list, a: str, b: str) -> dict:
    """Unterschied der Kosten von `a` gegen `b` je Instanz in Prozent der besten Kosten (negativ: `a` ist besser): Mittel, Standardfehler, Zahl besser / schlechter / gleich."""
    d = np.array([100.0 * (r["cost"][a] - r["cost"][b]) / r["best"] for r in rows])
    se = float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan")
    better = int((d < -1e-9).sum())
    worse = int((d > 1e-9).sum())
    return {"mean": float(d.mean()), "se": se, "better": better, "worse": worse, "equal": len(d) - better - worse, "count": len(d)}


def faster(rows: list, a: str, b: str) -> int:
    """Zahl der Instanzen, in denen `a` weniger Sekunden braucht als `b` (Messung dieser Fassung, rechnerabhängig)."""
    return sum(r["sec"][a] < r["sec"][b] for r in rows)


def rule_regret(rows: list) -> dict:
    """Mittleres Bedauern der Regel (Zeitbudget normal) gegen immer 20 Neustarts, immer Schleife mit Annealing und das bessere der beiden je Instanz.

    Bedauern gegen die besten Kosten aller Verfahren der Instanz. Gruppe: bis n = 16 `neu20`, ab n = 20 `sa_s`."""
    n = rows[0]["n"]
    key = R.rule_key(n)
    both = [min(r["cost"]["neu20"], r["cost"]["sa_s"]) for r in rows]
    best = [r["best"] for r in rows]
    return {"n": n, "count": len(rows), "rule_key": key,
            "rule": float(np.mean([r["gap"][key] for r in rows])), "neu20": float(np.mean([r["gap"]["neu20"] for r in rows])), "sa_s": float(np.mean([r["gap"]["sa_s"] for r in rows])),
            "oracle2": float(np.mean([rel(c, b) for c, b in zip(both, best)]))}


def bound_gap(rows: list, key: str) -> dict:
    """Lücke (Vergleichswert − Schranke) / Vergleichswert der Schranke `key` und Median der Zeit, über die Zeilen, in denen sie gerechnet wurde."""
    rs = [r for r in rows if key in r["bound"]]
    gaps = [100.0 * (r["ref"] - r["bound"][key]) / r["ref"] for r in rs]
    return {"count": len(rs), "median": float(np.median(gaps)), "mean": float(np.mean(gaps)), "sharp": sum(abs(g) < 1e-9 for g in gaps), "sec": float(np.median([r["sec"][key] for r in rs]))}


def tree_stats(rows: list, art: str) -> dict:
    rs = [r for r in rows if art in r["tree"]]
    nodes = [r["tree"][art]["nodes"] for r in rs]
    return {"count": len(rs), "median": float(np.median(nodes)), "max": int(max(nodes)), "sec": float(np.median([r["tree"][art]["sec"] for r in rs])), "sec_max": float(max(r["tree"][art]["sec"] for r in rs)),
            "capped": sum(r["tree"][art]["capped"] for r in rs)}


def restart_hits(rows: list) -> dict:
    """Zahl der bewiesenen Instanzen, in denen 20 bzw. 200 Abstiege aus Zufall das Optimum treffen."""
    proved = [r for r in rows if r["opt"] is not None]
    return {"proved": len(proved), "count": len(rows), "hit20": sum(r["ub20"] == r["opt"] for r in proved), "hit200": sum(r["ub200"] == r["opt"] for r in proved)}


def work_text(w: dict) -> str:
    """Zählung eines Verfahrens als Text: „16 Runden · 1 234 Bewertungen“. Die Einheiten sind nicht vergleichbar."""
    parts = []
    if "runden" in w:
        parts.append(f"{count(w['runden'])} Runde" + ("" if w["runden"] == 1 else "n"))
    if "stufen" in w:
        parts.append(f"{count(w['stufen'])} Stufen")
    if "auswertungen" in w:
        parts.append(f"{count(w['auswertungen'])} Auswertungen")
    if "bewertungen" in w:
        parts.append(f"{count(w['bewertungen'])} Bewertungen")
    return " · ".join(parts)


def work_split(w: dict) -> tuple:
    """Die Zählung für eine Kennzahl: (Zahl, Einheit). Bewertungen vor Auswertungen vor Runden; was sonst noch gezählt wurde, steht in der Einheit: („3 304“, „Bewertungen und 16 Runden“)."""
    for key, unit in (("bewertungen", "Bewertungen"), ("auswertungen", "Auswertungen"), ("runden", "Runden")):
        if key in w:
            rest = [f"{count(w[k])} {u}" for k, u in (("runden", "Runden"), ("stufen", "Stufen")) if k in w and k != key]
            return count(w[key]), unit + (" und " + ", ".join(rest) if rest else "")
    return "–", ""


# ----------------------------------------------------------------------------- Verdikte

def _head(s: Settings, v: dict) -> str:
    inst = v["inst"]
    pads = "" if s.task == "prove" else f", {s.pads} Pads"
    return f"Familie **{fam(s.family)}**, {s.n} Bauteile, Raster {inst.rows}×{inst.cols}, Seed {s.seed}{pads}"


def _refname(v: dict) -> str:
    return "das aufgezählte Optimum" if v["exact"] else "das beste Ergebnis aller Verfahren (obere Grenze des Optimums)"


def _method(v: dict, k: str) -> str:
    return f"{C.FIND_NAMES[k]} ({C.FIND_PIECE[k]}): Kosten {num(v['cost'][k])}, Bedauern {pct(v['gap'][k], 1)}, {secs(v['sec'][k])}"


def verdict_find(s: Settings, v: dict):
    adv = R.advise(s.n, "find", s.budget)
    k = adv.find
    best_keys = [x for x in C.FIND_KEYS if v["hit"][x]]
    kind = "success" if v["hit"][k] else "info"
    fastest = min(best_keys, key=lambda x: v["sec"][x]) if best_keys else None
    hit_text = (f"Die Regel trifft den Vergleichswert ({num(v['best'])}). " if v["hit"][k] else f"Die Regel liegt {pct(v['gap'][k], 1)} über dem Vergleichswert {num(v['best'])}. ")
    other = f"Von den Verfahren, die den Vergleichswert erreichen, ist {C.FIND_NAMES[fastest]} das schnellste ({secs(v['sec'][fastest])}). " if fastest else ""
    return kind, (f"{_head(s, v)}, Zeitbudget {C.BUDGET_NAMES[s.budget]}: die Regel empfiehlt **{adv.label}** ({C.FIND_PIECE[k]}): Kosten {num(v['cost'][k])} in {secs(v['sec'][k])} (Bedauern {pct(v['gap'][k], 1)} gegen {_refname(v)} {num(v['best'])}). "
                  + hit_text + other + f"Zum Vergleich: {_method(v, 'rund')}; {_method(v, 'schleife')}; {_method(v, 'elektro')}. Eine Instanz, kein Befund über die Familie; Zeiten sind Messungen dieser Fassung auf diesem Rechner.")


def verdict_core(s: Settings, v: dict):
    """Die Kernfrage „Welches Verfahren, gemessen woran?“ für die Eingaben (Aufgabe finden oder beweisen)."""
    if s.task == "prove":
        return verdict_prove(s, v)
    return verdict_find(s, v)


def verdict_prove(s: Settings, v: dict):
    n = s.n
    b = v["bound"]
    ref = v["ref"]
    parts = []
    for k in C.BOUND_KEYS:
        if k in b:
            parts.append(f"{C.BOUND_NAMES[k]} ({C.BOUND_PIECE[k]}) {de(b[k], 1)} (Lücke {pct(rel(ref, b[k]), 1)}, {secs(v['sec'][k])})")
    hit = "treffen das Optimum" if v["opt"] is not None and v["ub20"] == v["opt"] else "treffen das Optimum nicht" if v["opt"] is not None else "stehen ohne Beweis da"
    head = _head_prove(s, v)
    if not v["tree"]:
        return "info", (f"{head}: bis n = {R.PROVE_MAX_N} wird der Beweis hier gerechnet, darüber nicht. Gilmore–Lawler-Schranke {de(b['glb'], 1)} gegen die beste von {C.PROVE_STARTS} Abstiegen {num(v['ub200'])} (Lücke {pct(rel(v['ub200'], b['glb']), 1)}): "
                        f"die Güte ist belegt, das Optimum nicht. 20 Abstiege ({secs(v['sec']['ub20'])}) liefern {num(v['ub20'])}.")
    tg = v["tree"]["glb"]
    tree_txt = f"Branch and Bound mit Gilmore–Lawler: {count(tg['nodes'])} Knoten, {secs(tg['sec'])}" + (f", **Obergrenze von {count(v.get('cap', C.PROVE_CAP))} Knoten erreicht, nicht bewiesen**" if tg["capped"] else f", Optimum **{num(tg['best'])}** bewiesen")
    if "lin" in v["tree"]:
        tl = v["tree"]["lin"]
        tree_txt += f"; mit linearen Knotenschranken {count(tl['nodes'])} Knoten, {secs(tl['sec'])}"
    kind = "success" if v["opt"] is not None else "warning"
    find_part = (f"Finden ist billig: 20 Abstiege aus Zufall ({secs(v['sec']['ub20'])}) {hit} (Kosten {num(v['ub20'])}), 200 Abstiege ({secs(v['sec']['ub200'])}) liefern {num(v['ub200'])}. " if v["opt"] is not None else
                 f"20 Abstiege ({secs(v['sec']['ub20'])}) liefern {num(v['ub20'])}, 200 Abstiege {num(v['ub200'])}. ")
    return kind, f"{head}: " + find_part + "Beweisen kostet: " + tree_txt + ". Schranken allein: " + "; ".join(parts) + f". Vergleichswert für die Lücken: {'das bewiesene Optimum' if v['opt'] is not None else 'die beste von 200 Abstiegen'} {num(ref)}. Eine Instanz; Zeiten sind Messungen dieser Fassung."


def _head_prove(s: Settings, v: dict) -> str:
    inst = v["inst"]
    return f"Familie **{fam(s.family)}**, {s.n} Bauteile, Raster {inst.rows}×{inst.cols}, Seed {s.seed}, reine Zuordnung ohne Pads"


def verdict_path(s: Settings, v: dict):
    """Der Entscheidungsweg in Worten (die Fragen stehen in der App als Liste)."""
    adv = R.advise(s.n, s.task, s.budget)
    steps = " → ".join(f"{st.question} {st.answer}" for st in adv.steps)
    return "info", f"Entscheidungsweg für n = {s.n}, Aufgabe {C.TASK_NAMES[s.task].split(':')[0].lower()}, Zeitbudget {C.BUDGET_NAMES[s.budget]}: {steps}. Die Regel liest nur Größe, Aufgabe und Zeitbudget, nicht Familie oder Pad-Zahl; ob der Wechsel auch von der Familie abhängt, ist mit den wenigen Instanzen ab n = 20 nicht entschieden."


def verdict_find_sweep(n: int, rows: list):
    exact = rows[0]["exact"]
    stats = {k: regret_stats(rows, k) for k in C.FIND_KEYS}
    ranked = sorted(C.FIND_KEYS, key=lambda k: stats[k]["mean"])
    fr = front(rows)
    cheap = [f"{C.FIND_NAMES[k]} {pct(stats[k]['mean'], 1)}" for k in ("rund", "schleife", "elektro", "elektro_b")]
    neu = stats["neu20"]
    ps = sorted({r["p"] for r in rows})
    return "info", (f"Bei n = {n}, {len(rows)} Instanzen (Pads {', '.join(map(str, ps))}), mittleres Bedauern: " + "; ".join(f"{C.FIND_NAMES[k]} {pct(stats[k]['mean'], 2)}" for k in ranked[:4]) + f" (die besten vier von elf); relaxierende Verfahren: " + ", ".join(cheap) + ". "
                    f"20 Neustarts erreichen das Beste in {neu['hit']} von {len(rows)} Instanzen, Median der Zeit {secs(neu['sec'])}; Dichtestrafe {secs(stats['elektro']['sec'])}, Schleife mit Annealing {secs(stats['sa_s']['sec'])}. "
                    f"Auf der Kante aus Zeit und Bedauern liegen: {', '.join(C.FIND_NAMES[k] for k in fr)}." + ("" if exact else " Der Vergleichswert ist das beste Ergebnis aller Verfahren der Instanz: das Bedauern ist eine obere Grenze der Lücke zum Optimum.")
                    + " Zeiten sind Messungen dieser Fassung auf diesem Rechner.")


def verdict_cross(rows_by_n: dict):
    ns = sorted(rows_by_n)
    parts = []
    first_sa = None
    for n in ns:
        rs = rows_by_n[n]
        a, b = regret_stats(rs, "neu20"), regret_stats(rs, "sa_s")
        pr = paired(rs, "sa_s", "neu20")
        faster_sa = faster(rs, "sa_s", "neu20")
        parts.append(f"n = {n}: Neustarts {pct(a['mean'], 2)} in {secs(a['sec'])}, Schleife mit Annealing {pct(b['mean'], 2)} in {secs(b['sec'])} (Unterschied {de(pr['mean'], 2)} ± {de(pr['se'], 2)} Prozentpunkte, Annealing besser in {pr['better']}, schlechter in {pr['worse']} von {pr['count']}; schneller in {faster_sa} von {len(rs)})")
        if first_sa is None and b["mean"] < a["mean"]:
            first_sa = n
    cross = (f"Im Mittel ist das Annealing erstmals bei n = {first_sa} besser." if first_sa else "Im Mittel ist das Annealing in keiner gerechneten Größe besser.")
    return "info", ("; ".join(parts) + ". " + cross + " Der Qualitätsunterschied ist klein gegen die Streuung (± ist der Standardfehler des gepaarten Unterschieds); belastbarer ist der Zeitunterschied, der zu dieser Python-Fassung gehört.")


def verdict_rule(fixed: dict, fresh: dict):
    """`fixed`, `fresh`: n → Zeilen (feste bzw. frische Instanzen)."""
    def line(label, by_n):
        out = []
        for n in sorted(by_n):
            r = rule_regret(by_n[n])
            out.append(f"n = {n}: Regel ({C.FIND_NAMES[r['rule_key']]}) {pct(r['rule'], 2)}, immer Neustarts {pct(r['neu20'], 2)}, immer Schleife mit Annealing {pct(r['sa_s'], 2)}, bestes der beiden {pct(r['oracle2'], 2)}")
        return f"{label}: " + "; ".join(out)
    rr = [rule_regret(rows) for by_n in (fixed, fresh) for rows in by_n.values()]
    worst_fixed = max(r["rule"] - min(r["neu20"], r["sa_s"]) for r in rr) * 100
    worst_oracle = max(r["rule"] - r["oracle2"] for r in rr) * 100
    return "info", (line("Feste Instanzen", fixed) + ". " + line("Frische Instanzen", fresh) + f". Gegen die bessere der beiden festen Wahlen (im Mittel) verliert die Regel höchstens {de(worst_fixed, 2)} Prozentpunkte, "
                    f"gegen das bessere der beiden je Instanz (im Voraus unbekannt) höchstens {de(worst_oracle, 2)}. "
                    "Die Regel wurde an den festen Instanzen gebildet; die frischen Instanzen (Seeds ab 200000) sind unabhängig davon gezogen.")


def verdict_prove_sweep(rows_by_n: dict):
    parts = []
    for n in sorted(rows_by_n):
        rs = rows_by_n[n]
        hits = restart_hits(rs)
        g = bound_gap(rs, "glb")
        d = bound_gap(rs, "da5")
        tg = tree_stats(rs, "glb")
        line = (f"n = {n} ({len(rs)} Instanzen): 20 Abstiege treffen das Optimum in {hits['hit20']} von {hits['proved']} bewiesenen, 200 in {hits['hit200']}; "
                f"Lücke der Schranken (Median) Gilmore–Lawler {de(g['median'], 1)} %, Dual Ascent {de(d['median'], 1)} %" + (f", Linearisierung {de(bound_gap(rs, 'lp')['median'], 1)} % ({secs(bound_gap(rs, 'lp')['sec'])})" if any("lp" in r["bound"] for r in rs) else "")
                + f"; Branch and Bound (Gilmore–Lawler) im Median {count(tg['median'])} Knoten und {secs(tg['sec'])}, größter Fall {count(tg['max'])} Knoten und {secs(tg['sec_max'])}" + (f", {tg['capped']} an der Obergrenze" if tg["capped"] else ""))
        parts.append(line)
    return "info", "; ".join(parts) + ". Das Optimum zu finden kostet Bruchteile einer Sekunde; es zu beweisen wächst mit n von Zehntelsekunden auf Sekunden bis Minuten. Zeiten sind Messungen dieser Fassung."


# ----------------------------------------------------------------------------- Handbeispiel

def hand_prove() -> dict:
    """Vier Plätze auf einer Zeile (Stück 3, 5, 8): Gilmore–Lawler-Wurzel, Optimum und die Knoten des Baums von Hand."""
    from avw_instance import hand_instance
    inst = hand_instance(C.HAND_GAP_FLOWS, *C.HAND_GAP_GRID)
    F, D = inst.F, inst.D
    g = B.gilmore_lawler(F, D)
    out = {"inst": inst, "root": g.glb}
    for art in ("glb", "lin", "none"):
        out[art] = T.solve(F, D, art, incumbent=6)
    out["glb_free"] = T.solve(F, D, "glb")
    out["opt"] = out["glb"].best
    return out
