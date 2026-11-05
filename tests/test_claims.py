"""Die Zahlen der README und der Verdikte, an den festen und frischen Instanzen der Reihe nachgerechnet (Messung, nicht Satz).

Lehre aus Stück 11: Mittelwerte der Verfahren, die von Rundung und Schleife abhängen, streuen mit der Hardware des Rechners. Die Toleranzen sind deshalb von Anfang an auf die Streuung zwischen Rechnern
ausgelegt (Windows-Lauf des Autors gegen Linux-CI), Abweichungen werden gesammelt gemeldet statt beim ersten abzubrechen. Zeiten stehen hier nie; Kosten und ganzzahlige Zählungen (Treffer, Knoten) sind genau.
Die Aussage „schneller“ gehört in die App und die README (Messung dieser Fassung), nicht in einen Test."""

import pytest

import avw_constants as C
import avw_evaluation as E
import avw_rule as R
import rows as RW

# mittleres Bedauern in Prozent (feste Instanzen; Windows-Lauf des Autors); Toleranz in Prozentpunkten, für Rundung und Schleife doppelt
MEAN = {
    8: {"rund": 11.00, "schleife": 7.87, "elektro": 6.03, "elektro_b": 2.75, "neu6": 0.35, "neu20": 0.04, "sa_s": 0.78},
    12: {"rund": 18.23, "schleife": 10.98, "elektro": 9.43, "elektro_b": 4.45, "neu6": 0.98, "neu20": 0.24, "sa_s": 1.16},
    16: {"rund": 20.05, "schleife": 13.47, "elektro": 9.66, "elektro_b": 4.98, "neu6": 1.87, "neu20": 0.66, "sa_s": 0.83},
    20: {"rund": 17.21, "schleife": 10.19, "elektro": 8.57, "elektro_b": 4.41, "neu6": 2.18, "neu20": 1.07, "sa_s": 1.19},
    25: {"rund": 16.87, "schleife": 9.98, "elektro": 8.53, "elektro_b": 4.22, "neu6": 2.85, "neu20": 1.35, "sa_s": 0.58},
    36: {"rund": 16.16, "schleife": 9.57, "elektro": 6.58, "elektro_b": 4.41, "neu6": 2.55, "neu20": 1.55, "sa_s": 0.21},
}
TOL = {8: 0.5, 12: 0.8, 16: 1.2, 20: 1.5, 25: 1.5, 36: 1.5}
RELAX = ("rund", "schleife", "elektro", "elektro_b")
# frische Instanzen (Seeds ab 200000): mittleres Bedauern der Regel
FRESH_RULE = {8: 0.03, 12: 0.17, 16: 0.58, 20: 0.50, 25: 0.34, 36: 0.63}
# Treffer (Zahl der Instanzen, in denen das Verfahren die besten Kosten der Instanz erreicht), Toleranz in Instanzen
HITS = {8: {"neu20": 174, "sa_s": 117}, 12: {"neu20": 71, "sa_s": 47}, 16: {"neu20": 27, "sa_s": 27}, 20: {"neu20": 9, "sa_s": 7}, 25: {"neu20": 5, "sa_s": 9}, 36: {"neu20": 6, "sa_s": 9}}
HIT_TOL = {8: 4, 12: 5, 16: 5, 20: 4, 25: 4, 36: 4}
# gepaarter Unterschied Annealing gegen 20 Neustarts (Prozentpunkte, Mittel); Vorzeichen und Größenordnung
PAIRED = {8: 0.75, 12: 0.92, 16: 0.17, 20: 0.12, 25: -0.76, 36: -1.34}
PAIRED_TOL = {8: 0.5, 12: 0.8, 16: 1.0, 20: 1.2, 25: 1.2, 36: 1.5}


def _check(mismatches):
    assert not mismatches, "Abweichungen:\n" + "\n".join(mismatches)


@pytest.mark.parametrize("n", C.FIND_SIZES)
def test_mean_regret_of_the_methods_on_the_fixed_instances(n):
    rows = RW.find_rows(n)
    assert len(rows) == {8: 180, 12: 90, 16: 54, 20: 18, 25: 18, 36: 18}[n] and rows[0]["exact"] == (n <= 9)
    off = []
    for k, expected in MEAN[n].items():
        got = 100 * E.regret_stats(rows, k)["mean"]
        tol = TOL[n] * (2 if k in RELAX else 1)
        if abs(got - expected) > tol:
            off.append(f"n = {n}, {k}: {got:.2f} % statt {expected:.2f} % ± {tol}")
    _check(off)


@pytest.mark.parametrize("n", C.FIND_SIZES)
def test_the_relaxations_lose_to_neustarts_and_to_annealing_in_every_size(n):
    """Einmal runden, Schleife und Dichtestrafe (beide Wertungen) liegen im Mittel hinter 20 Neustarts und hinter Schleife mit Annealing."""
    rows = RW.find_rows(n)
    st = {k: E.regret_stats(rows, k)["mean"] for k in C.FIND_KEYS}
    off = [f"n = {n}: {r} {100 * st[r]:.2f} % nicht über {a} {100 * st[a]:.2f} %" for r in RELAX for a in ("neu20", "sa_s") if st[r] <= st[a] + 0.01]
    off += [f"n = {n}: 20 Neustarts {100 * st['neu20']:.2f} % nicht unter 6 Neustarts {100 * st['neu6']:.2f} %" for _ in [0] if st["neu20"] > st["neu6"] + 1e-9]
    _check(off)


@pytest.mark.parametrize("n", C.FIND_SIZES)
def test_hits_of_neustarts_and_annealing(n):
    rows = RW.find_rows(n)
    off = []
    for k, expected in HITS[n].items():
        got = E.regret_stats(rows, k)["hit"]
        if abs(got - expected) > HIT_TOL[n]:
            off.append(f"n = {n}, {k}: {got} Treffer statt {expected} ± {HIT_TOL[n]}")
    _check(off)


def test_twenty_restarts_meet_the_enumerated_optimum_at_eight_places():
    rows = RW.find_rows(8)
    opt_hits = sum(r["cost"]["neu20"] <= r["opt"] + 1e-9 for r in rows)
    assert abs(opt_hits - 174) <= 4 and all(r["best"] == r["opt"] or r["best"] < r["opt"] + 1e-9 for r in rows) and all(r["gap"][k] >= 0 for r in rows for k in C.FIND_KEYS)


@pytest.mark.parametrize("n", C.FIND_SIZES)
def test_paired_difference_of_annealing_against_neustarts(n):
    rows = RW.find_rows(n)
    pr = E.paired(rows, "sa_s", "neu20")
    assert abs(pr["mean"] - PAIRED[n]) <= PAIRED_TOL[n], f"n = {n}: Unterschied {pr['mean']:.2f} statt {PAIRED[n]:.2f} ± {PAIRED_TOL[n]}"
    assert pr["better"] + pr["worse"] + pr["equal"] == len(rows) == pr["count"]


def test_the_crossing_in_quality_annealing_is_better_from_25_on_and_neustarts_are_better_below():
    pr = {n: E.paired(RW.find_rows(n), "sa_s", "neu20")["mean"] for n in C.FIND_SIZES}
    assert pr[8] > 0 and pr[12] > 0 and pr[25] < 0 and pr[36] < 0, pr
    assert pr[36] < pr[25] + 1.0 and pr[8] > pr[36]


@pytest.mark.parametrize("fresh", (False, True))
def test_the_rule_loses_little_against_the_better_of_the_two_fixed_choices(fresh):
    """Die Regel gegen die bessere der beiden festen Wahlen (im Mittel): sie verliert höchstens ein halbes Prozent (gemessen höchstens 0,2 Prozentpunkte)."""
    off = []
    for n in C.FIND_SIZES:
        r = E.rule_regret(RW.find_rows(n, fresh))
        better = min(r["neu20"], r["sa_s"])
        if r["rule"] - better > 0.005:
            off.append(f"n = {n}, {'frisch' if fresh else 'fest'}: Regel {100 * r['rule']:.2f} % gegen {100 * better:.2f} %")
        assert r["rule_key"] == R.rule_key(n) and r["oracle2"] <= better + 1e-12 and r["oracle2"] >= 0
    _check(off)


def test_the_rule_on_fresh_instances():
    off = []
    for n in C.FIND_SIZES:
        got = 100 * E.rule_regret(RW.find_rows(n, True))["rule"]
        if abs(got - FRESH_RULE[n]) > TOL[n]:
            off.append(f"n = {n}: Regel {got:.2f} % statt {FRESH_RULE[n]:.2f} % ± {TOL[n]}")
    _check(off)
    counts = {n: len(RW.find_rows(n, True)) for n in C.FIND_SIZES}
    assert counts == {8: 90, 12: 54, 16: 36, 20: 18, 25: 18, 36: 18}


# --- Beweisen: ganzzahlige Zählungen sind auf jedem Rechner gleich ---------------------------------------------------------------------------------

PROVE_HITS = {8: (30, 30, 30), 9: (18, 18, 18), 12: (18, 12, 17)}                      # bewiesene Instanzen, Treffer von 20 und von 200 Abstiegen
GLB_NODES = {8: (240, 924), 9: (675, 5733), 12: (7990, 190916)}                          # Median, größter Fall
LIN_NODES = {8: (2334, 12716), 9: (12235, 163673)}
GAP_MEDIAN = {"glb": {8: 8.3, 9: 10.2, 12: 13.3}, "da5": {8: 5.2, 9: 8.0, 12: 11.3}, "lp": {8: 1.5, 9: 1.8}}


@pytest.mark.parametrize("n", C.PROVE_SIZES)
def test_twenty_descents_find_what_the_tree_proves(n):
    rows = RW.prove_rows(n)
    h = E.restart_hits(rows)
    assert len(rows) == {8: 30, 9: 18, 12: 18}[n] and (h["proved"], h["hit20"], h["hit200"]) == PROVE_HITS[n]
    assert all(r["opt"] is not None and r["ref"] == r["opt"] and r["ub20"] >= r["opt"] and r["ub200"] >= r["opt"] for r in rows)


@pytest.mark.parametrize("n", C.PROVE_SIZES)
def test_node_counts_of_the_proof(n):
    rows = RW.prove_rows(n)
    tg = E.tree_stats(rows, "glb")
    assert (tg["median"], tg["max"], tg["capped"]) == (GLB_NODES[n][0], GLB_NODES[n][1], 0)
    if n in LIN_NODES:
        tl = E.tree_stats(rows, "lin")
        assert (tl["median"], tl["max"], tl["capped"]) == (LIN_NODES[n][0], LIN_NODES[n][1], 0)
        assert all(r["tree"]["glb"]["nodes"] <= r["tree"]["lin"]["nodes"] for r in rows) and all(r["tree"]["glb"]["best"] == r["tree"]["lin"]["best"] for r in rows)
    else:
        assert all("lin" not in r["tree"] for r in rows)


@pytest.mark.parametrize("n", C.PROVE_SIZES)
def test_gaps_of_the_bounds_to_the_optimum(n):
    rows = RW.prove_rows(n)
    off = []
    for k, exp in GAP_MEDIAN.items():
        if n not in exp:
            assert all(k not in r["bound"] for r in rows)
            continue
        got = E.bound_gap(rows, k)["median"]
        if abs(got - exp[n]) > 0.3:
            off.append(f"n = {n}, {k}: Lücke {got:.2f} % statt {exp[n]} % ± 0,3")
    _check(off)
    assert all(r["bound"]["glb"] <= r["bound"]["da5"] + 1e-9 <= r["opt"] + 1e-6 for r in rows)
    assert all(r["bound"]["lp"] <= r["opt"] + 1e-6 for r in rows if "lp" in r["bound"])
    assert (n <= 9) == all("lp" in r["bound"] for r in rows)
