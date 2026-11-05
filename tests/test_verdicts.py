"""Verdikte: datengetrieben (Art und Text folgen den Zahlen), jeder Zweig an festen Eingaben (DEMO-PLAYBOOK §1b)."""

import copy

import pytest

import avw_constants as C
import avw_evaluation as E
from oracle import make_row

S8 = E.Settings("cluster", 8, 100020, 4, "find", "normal")


@pytest.fixture(scope="module")
def find8():
    return E.solve_find("cluster", 8, 100020, 4)


@pytest.fixture(scope="module")
def prove8():
    return E.solve_prove("cluster", 8, 100020)


def test_find_verdict_success_when_the_rule_reaches_the_comparison_value(find8):
    kind, text = E.verdict_find(S8, find8)
    assert find8["hit"]["neu20"] and kind == "success" and "20 Neustarts" in text and "trifft den Vergleichswert" in text and "Optimum" in text and "Eine Instanz" in text


def test_find_verdict_info_when_the_rule_misses_and_names_the_gap(find8):
    v = copy.deepcopy(find8)
    v["cost"]["neu20"] = v["best"] * 1.05
    v["gap"]["neu20"] = 0.05
    v["hit"]["neu20"] = False
    kind, text = E.verdict_find(S8, v)
    assert kind == "info" and "5,0 % über dem Vergleichswert" in text


def test_find_verdict_follows_the_budget_and_the_size(find8):
    _, tight = E.verdict_find(E.Settings("cluster", 8, 100020, 4, "find", "tight"), find8)
    assert "6 Neustarts" in tight and "Zeitbudget knapp" in tight
    v12 = E.solve_find("cluster", 12, 100020, 4)
    _, t12 = E.verdict_find(E.Settings("cluster", 12, 100020, 4, "find", "normal"), v12)
    assert "obere Grenze" in t12 or "beste Ergebnis aller Verfahren" in t12


def test_core_verdict_dispatches_on_the_task(find8, prove8):
    assert E.verdict_core(S8, find8) == E.verdict_find(S8, find8)
    sp = E.Settings("cluster", 8, 100020, 4, "prove", "normal")
    assert E.verdict_core(sp, prove8) == E.verdict_prove(sp, prove8)


def test_prove_verdict_proved_capped_and_out_of_reach(prove8):
    sp = E.Settings("cluster", 8, 100020, 4, "prove", "normal")
    kind, text = E.verdict_prove(sp, prove8)
    assert kind == "success" and "bewiesen" in text and "Finden ist billig" in text and "Beweisen kostet" in text and "Gilmore–Lawler" in text and "Linearisierung" in text and "reine Zuordnung ohne Pads" in text
    capped = E.solve_prove("cluster", 8, 100020, cap=3)
    kind2, text2 = E.verdict_prove(sp, capped)
    assert kind2 == "warning" and "Obergrenze von 3 Knoten erreicht, nicht bewiesen" in text2
    far = E.solve_prove("cluster", 12, 100020, tree=False)
    kind3, text3 = E.verdict_prove(E.Settings("cluster", 12, 100020, 4, "prove", "normal"), far)
    assert kind3 == "info" and "nicht" in text3 and "Güte ist belegt, das Optimum nicht" in text3


def test_path_verdict_lists_the_questions():
    kind, text = E.verdict_path(E.Settings("cluster", 25, 1, 4, "find", "tight"), None)
    assert kind == "info" and "Ist n mindestens 20? ja" in text and "knapp" in text and "Abstieg aus der Schleife" in text and "nicht von Familie oder Pad-Zahl" in text
    _, tp = E.verdict_path(E.Settings("cluster", 8, 1, 4, "prove", "normal"), None)
    assert "Muss das Optimum bewiesen werden? ja" in tp and "Branch and Bound" in tp


def _rows12(neu_gap, n=12, exact=False):
    return [make_row(n, {"neu20": 100 * (1 + neu_gap), "sa_s": 103, "rund": 130, "schleife": 120, "elektro": 118, "elektro_b": 112, "abs_z": 108, "neu6": 101, "abs_r": 106, "abs_s": 104, "abs_e": 105},
                     {"neu20": 0.05, "sa_s": 0.1, "rund": 0.001, "schleife": 0.01, "elektro": 0.3, "elektro_b": 0.3, "abs_z": 0.002, "neu6": 0.02, "abs_r": 0.002, "abs_s": 0.011, "abs_e": 0.31},
                     exact=exact, opt=(99 if exact else None), p=p) for p in (2, 4, 8)]


def test_find_sweep_verdict_names_the_best_and_the_frontier():
    kind, text = E.verdict_find_sweep(12, _rows12(0.0))
    assert kind == "info" and "Bei n = 12, 3 Instanzen" in text and "Pads 2, 4, 8" in text and "20 Neustarts erreichen das Beste in 3 von 3" in text and "Kante" in text and "obere Grenze" in text
    assert "20 Neustarts 0,00 %" in text
    _, t2 = E.verdict_find_sweep(8, _rows12(0.02, 8, True))
    assert "obere Grenze" not in t2 and "20 Neustarts erreichen das Beste in 0 von 3" in t2


def test_cross_verdict_finds_the_first_size_where_annealing_wins():
    by_n = {16: [make_row(16, {"neu20": 100, "sa_s": 101}, {"neu20": 0.1, "sa_s": 0.2}), make_row(16, {"neu20": 100, "sa_s": 102}, {"neu20": 0.1, "sa_s": 0.2})],
            25: [make_row(25, {"neu20": 102, "sa_s": 100}, {"neu20": 1.0, "sa_s": 0.3}), make_row(25, {"neu20": 103, "sa_s": 100}, {"neu20": 1.0, "sa_s": 0.3})]}
    kind, text = E.verdict_cross(by_n)
    assert kind == "info" and "erstmals bei n = 25 besser" in text and "schneller in 2 von 2" in text and "schneller in 0 von 2" in text and "Standardfehler" in text
    swap = {16: by_n[25], 25: by_n[16]}
    assert "erstmals bei n = 16 besser" in E.verdict_cross(swap)[1]
    none = {16: by_n[16]}
    assert "in keiner gerechneten Größe besser" in E.verdict_cross(none)[1]


def test_rule_verdict_reports_the_loss_against_the_better_of_the_two():
    fixed = {12: [make_row(12, {"neu20": 100, "sa_s": 103}), make_row(12, {"neu20": 100, "sa_s": 98})], 25: [make_row(25, {"neu20": 104, "sa_s": 100}), make_row(25, {"neu20": 100, "sa_s": 100})]}
    fresh = {12: [make_row(12, {"neu20": 100, "sa_s": 99})], 25: [make_row(25, {"neu20": 100, "sa_s": 101})]}
    kind, text = E.verdict_rule(fixed, fresh)
    assert kind == "info" and "Feste Instanzen" in text and "Frische Instanzen" in text and "Seeds ab 200000" in text
    rr = [E.rule_regret(rows) for by_n in (fixed, fresh) for rows in by_n.values()]
    loss_fixed = max(r["rule"] - min(r["neu20"], r["sa_s"]) for r in rr) * 100
    loss_oracle = max(r["rule"] - r["oracle2"] for r in rr) * 100
    assert f"bessere der beiden festen Wahlen (im Mittel) verliert die Regel höchstens {E.de(loss_fixed, 2)} Prozentpunkte" in text and f"(im Voraus unbekannt) höchstens {E.de(loss_oracle, 2)}" in text and loss_oracle >= loss_fixed >= 0


def test_prove_sweep_verdict_has_a_clause_per_size():
    base = {"family": "cluster", "seed": 1, "ub20": 10, "ub200": 10, "sec": {"glb": 0.001, "da5": 0.05, "lp": 0.5, "ub20": 0.01, "ub200": 0.05}, "opt": 10, "ref": 10}
    mk = lambda n, nodes, lp=True: {**base, "n": n, "bound": {"glb": 8.0, "da5": 9.0, **({"lp": 10.0} if lp else {})}, "tree": {"glb": {"nodes": nodes, "best": 10, "capped": False, "sec": nodes / 1000}}}
    rows = {8: [mk(8, 100)], 12: [mk(12, 5000, False), mk(12, 7000, False)]}
    kind, text = E.verdict_prove_sweep(rows)
    assert kind == "info" and "n = 8 (1 Instanzen)" in text and "n = 12 (2 Instanzen)" in text and "Linearisierung 0,0 %" in text and "größter Fall 7 000 Knoten" in text and "Obergrenze" not in text
    rows[12][1]["tree"]["glb"]["capped"] = True
    assert "1 an der Obergrenze" in E.verdict_prove_sweep(rows)[1]
