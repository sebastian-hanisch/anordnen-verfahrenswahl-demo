"""Kennzahlen, feste Instanzen und Formatierung: an künstlichen Zeilen mit bekannten Antworten (ORACLE-PLAYBOOK §5, Eigenschaften)."""

import math

import numpy as np
import pytest

import avw_constants as C
import avw_evaluation as E
from oracle import make_row


def test_fixed_and_fresh_instance_counts():
    fixed = {n: len(E.find_jobs(n)) for n in C.FIND_SIZES}
    fresh = {n: len(E.find_jobs(n, True)) for n in C.FIND_SIZES}
    assert fixed == {8: 180, 12: 90, 16: 54, 20: 18, 25: 18, 36: 18}
    assert fresh == {8: 90, 12: 54, 16: 36, 20: 18, 25: 18, 36: 18}
    assert {n: len(C.FAMILIES) * C.SEEDS_PROVE[n] for n in C.PROVE_SIZES} == {8: 30, 9: 18, 12: 18}


def test_fixed_and_fresh_seeds_are_disjoint_and_pads_follow_the_size():
    for n in C.FIND_SIZES:
        fixed, fresh = E.find_jobs(n), E.find_jobs(n, True)
        assert {j[2] for j in fixed}.isdisjoint({j[2] for j in fresh}) and min(j[2] for j in fixed) == C.FIXED_SEED0 and min(j[2] for j in fresh) == C.FRESH_SEED0
        assert {j[3] for j in fixed} == ({2, 4, 8} if n <= 16 else {4}) and {j[0] for j in fixed} == set(C.FAMILIES)
        assert len(set(fixed)) == len(fixed) and all(j[1] == n for j in fixed)


def test_find_sweep_is_the_slice_of_one_family():
    jobs = E.find_jobs(8)
    assert [(j[2], j[3]) for j in jobs if j[0] == "star"] == [(s, p) for s in range(C.FIXED_SEED0, C.FIXED_SEED0 + C.SEEDS_FIND[8]) for p in C.PAD_CHOICES]


def test_regret_is_zero_for_the_best_and_positive_otherwise():
    r = make_row(12, {"neu20": 100, "sa_s": 102, "rund": 120})
    assert r["best"] == 100 and r["gap"]["neu20"] == 0 and r["gap"]["sa_s"] == pytest.approx(0.02) and r["hit"]["neu20"] and not r["hit"]["sa_s"]
    ro = make_row(8, {"neu20": 100, "sa_s": 102}, exact=True, opt=99)
    assert ro["best"] == 99 and ro["gap"]["neu20"] == pytest.approx(1 / 99) and not any(ro["hit"].values())


def test_regret_stats_front_and_paired_on_known_rows():
    rows = [make_row(12, {"neu20": 100, "sa_s": 104, "rund": 130}, {"neu20": 0.1, "sa_s": 0.3, "rund": 0.001}),
            make_row(12, {"neu20": 200, "sa_s": 196, "rund": 260}, {"neu20": 0.1, "sa_s": 0.3, "rund": 0.001}),
            make_row(12, {"neu20": 300, "sa_s": 300, "rund": 390}, {"neu20": 0.1, "sa_s": 0.3, "rund": 0.001})]
    s = E.regret_stats(rows, "neu20")
    assert s["count"] == 3 and s["hit"] == 2 and s["mean"] == pytest.approx((0 + 200 / 196 - 1 + 0) / 3) and s["sec"] == pytest.approx(0.1)
    assert E.regret_stats(rows, "sa_s")["median"] == pytest.approx(0.0) and E.regret_stats(rows, "rund")["mean"] == pytest.approx(0.3, abs=0.02)
    p = E.paired(rows, "sa_s", "neu20")
    d = np.array([100 * 4 / 100, 100 * -4 / 196, 0.0])
    assert p["mean"] == pytest.approx(d.mean()) and p["se"] == pytest.approx(d.std(ddof=1) / math.sqrt(3)) and (p["better"], p["worse"], p["equal"]) == (1, 1, 1)
    assert E.faster(rows, "rund", "neu20") == 3 and E.faster(rows, "sa_s", "neu20") == 0
    assert E.front(rows) == ["rund", "neu20"]                                # das Annealing ist langsamer und schlechter als die Neustarts


def test_front_contains_no_dominated_method():
    rows = [make_row(16, {k: c for k, c in zip(C.FIND_KEYS, (130, 125, 120, 118, 112, 110, 108, 107, 103, 101, 102))}, {k: t for k, t in zip(C.FIND_KEYS, (0.001, 0.01, 0.3, 0.3, 0.002, 0.002, 0.01, 0.3, 0.02, 0.09, 0.1))})]
    keys = E.front(rows)
    st = {k: E.regret_stats(rows, k) for k in C.FIND_KEYS}
    for k in keys:
        assert not any(st[o]["sec"] <= st[k]["sec"] and st[o]["mean"] < st[k]["mean"] - 1e-12 for o in C.FIND_KEYS)
    for k in set(C.FIND_KEYS) - set(keys):
        assert any(st[o]["sec"] <= st[k]["sec"] and st[o]["mean"] < st[k]["mean"] - 1e-12 for o in keys)
    assert "elektro" not in keys and "elektro_b" not in keys                    # teurer und schlechter als das Annealing und die Neustarts


def test_rule_regret_compares_the_rule_with_both_fixed_choices_and_the_better_of_the_two():
    small = [make_row(12, {"neu20": 100, "sa_s": 103}), make_row(12, {"neu20": 100, "sa_s": 97})]
    r = E.rule_regret(small)
    assert r["rule_key"] == "neu20" and r["rule"] == pytest.approx(E.regret_stats(small, "neu20")["mean"]) and r["oracle2"] == pytest.approx(0.0) and r["sa_s"] == pytest.approx(E.regret_stats(small, "sa_s")["mean"])
    big = [make_row(25, {"neu20": 100, "sa_s": 100}), make_row(25, {"neu20": 105, "sa_s": 100})]
    rb = E.rule_regret(big)
    assert rb["rule_key"] == "sa_s" and rb["rule"] == pytest.approx(0.0) and rb["neu20"] == pytest.approx(0.025)


def test_bound_gap_tree_stats_and_restart_hits_on_known_rows():
    base = {"family": "cluster", "n": 8, "seed": 1, "ub20": 10, "ub200": 10, "sec": {"glb": 0.001, "da5": 0.02, "lp": 0.5}, "tree": {"glb": {"nodes": 100, "best": 10, "capped": False, "sec": 0.1}}, "opt": 10, "ref": 10}
    rows = [{**base, "bound": {"glb": 8.0, "da5": 9.0, "lp": 10.0}}, {**base, "bound": {"glb": 9.0, "da5": 9.5}, "ub20": 11, "tree": {"glb": {"nodes": 300, "best": 10, "capped": True, "sec": 0.3}}, "opt": None}]
    g = E.bound_gap(rows, "glb")
    assert g["count"] == 2 and g["median"] == pytest.approx(15.0) and g["sharp"] == 0 and E.bound_gap(rows, "lp")["count"] == 1 and E.bound_gap(rows, "lp")["sharp"] == 1
    t = E.tree_stats(rows, "glb")
    assert t["median"] == 200 and t["max"] == 300 and t["capped"] == 1 and t["count"] == 2
    h = E.restart_hits(rows)
    assert h == {"proved": 1, "count": 2, "hit20": 1, "hit200": 1}


def test_formatting():
    assert E.de(-1.5, 1) == "−1,5" and E.pct(0.1234, 1) == "12,3 %" and E.num(27) == "27" and E.num(27.5) == "27,5" and E.count(1200) == "1 200"
    assert E.secs(0.0164) == "0,016 s" and E.secs(0.42) == "0,42 s" and E.secs(5.13) == "5,1 s" and E.secs(31.4) == "31 s"
    assert math.isnan(E.rel(5, 0)) and E.rel(0, 0) == 0.0 and E.rel(1 + 1e-13, 1) == 0.0
    assert E.work_text({"runden": 1}) == "1 Runde" and E.work_text({"runden": 16, "bewertungen": 1234}) == "16 Runden · 1 234 Bewertungen" and E.work_text({"auswertungen": 300, "stufen": 12}) == "12 Stufen · 300 Auswertungen"


def test_work_split_picks_the_main_unit_and_names_the_rest():
    assert E.work_split({"bewertungen": 3304}) == ("3 304", "Bewertungen") and E.work_split({"runden": 1}) == ("1", "Runden")
    assert E.work_split({"runden": 16, "bewertungen": 1234}) == ("1 234", "Bewertungen und 16 Runden") and E.work_split({"auswertungen": 300, "stufen": 12}) == ("300", "Auswertungen und 12 Stufen") and E.work_split({}) == ("–", "")


def test_counts_grow_with_the_work_done():
    v = E.solve_find("uniform", 12, 100016, 4)
    w = v["work"]
    assert w["neu6"]["bewertungen"] < w["neu20"]["bewertungen"] and w["abs_z"]["bewertungen"] < w["neu6"]["bewertungen"]
    assert w["rund"] == {"runden": 1} and w["schleife"]["runden"] == 16 and w["abs_s"]["runden"] == 16 and w["abs_s"]["bewertungen"] > 0
    assert w["elektro"] == w["elektro_b"] and w["elektro"]["stufen"] == C.STAGES and w["abs_e"]["auswertungen"] == w["elektro"]["auswertungen"]
    from avw_search import budget_for
    assert w["sa_s"]["bewertungen"] == budget_for(12) + 12 * 11 // 2 and w["sa_s"]["runden"] == 16
    assert all(v["sec"][k] >= 0 for k in C.FIND_KEYS) and v["sec"]["neu6"] <= v["sec"]["neu20"] and v["sec"]["abs_s"] >= v["sec"]["schleife"] and v["sec"]["sa_s"] >= v["sec"]["schleife"]
    assert v["curve"][-1][1] == v["cost"]["neu20"] and v["curve"][5][1] == v["cost"]["neu6"] and [b for _, b, _ in v["curve"]] == sorted((b for _, b, _ in v["curve"]), reverse=True)


def test_hand_example_prove():
    h = E.hand_prove()
    assert h["root"] == 5.0 and h["opt"] == 6.0 and (h["glb"].nodes, h["lin"].nodes, h["none"].nodes) == (4, 16, 64) and h["glb_free"].nodes == 10
