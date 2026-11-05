"""Orakel für das Portfolio (ORACLE-PLAYBOOK §5): jede ausgegebene Anordnung ist eine Permutation, ihre Kosten werden einzeln neu gerechnet (zweite, unabhängige Rechnung),
und kein Verfahren liegt unter dem aufgezählten Optimum; die Schranken liegen darunter, der Baum belegt es."""

import numpy as np
import pytest

import avw_constants as C
import avw_evaluation as E
import avw_landscape as L
import avw_place as Pl
from oracle import brute_force, independent_cost


@pytest.mark.parametrize("family", C.FAMILIES)
@pytest.mark.parametrize("n", (6, 8))
def test_every_arrangement_is_a_permutation_and_its_cost_is_recomputed_independently(family, n):
    v = E.solve_find(family, n, 100008, 4)
    assert set(v["cost"]) == set(C.FIND_KEYS) == set(v["perm"]) == set(v["sec"]) == set(v["work"])
    for k in C.FIND_KEYS:
        assert sorted(int(x) for x in v["perm"][k]) == list(range(n)), k
        assert v["cost"][k] == pytest.approx(independent_cost(v["perm"][k], v["inst"], v["pads"])), k


@pytest.mark.parametrize("family", C.FAMILIES)
def test_no_method_beats_the_enumerated_optimum(family):
    v = E.solve_find(family, 6, 100009, 2)
    opt, _ = brute_force(v["inst"], v["pads"])
    assert v["exact"] and v["opt"] == pytest.approx(opt) and v["best"] == pytest.approx(opt)
    assert all(c >= opt - 1e-9 for c in v["cost"].values()) and all(g >= 0 for g in v["gap"].values())


def test_the_optimum_of_eight_places_is_the_enumerated_one():
    v = E.solve_find("cluster", 8, 100010, 4)
    P, costs = Pl.all_costs(v["inst"], v["c"])
    k = int(costs.argmin())
    assert v["opt"] == pytest.approx(float(costs[k])) and independent_cost([int(x) for x in P[k]], v["inst"], v["pads"]) == pytest.approx(v["opt"])


@pytest.mark.parametrize("n", (12, 16))
def test_above_nine_the_comparison_value_is_the_best_method(n):
    v = E.solve_find("netlist", n, 100011, 4)
    assert not v["exact"] and v["opt"] is None and v["best"] == min(v["cost"].values())
    assert any(v["hit"].values()) and all(g >= 0 for g in v["gap"].values())
    for k in C.FIND_KEYS:
        assert v["cost"][k] == pytest.approx(independent_cost(v["perm"][k], v["inst"], v["pads"])), k


def test_the_run_is_deterministic_in_costs_and_counts():
    a, b = E.solve_find("star", 8, 100012, 4), E.solve_find("star", 8, 100012, 4)
    assert a["cost"] == b["cost"] and a["perm"] == b["perm"] and a["work"] == b["work"] and a["best"] == b["best"]


@pytest.mark.parametrize("family", ("uniform", "cluster"))
def test_prove_side_bounds_below_the_optimum_and_the_tree_proves_it(family):
    v = E.solve_prove(family, 8, 100013)
    P = L.all_perms(8)
    opt = int(L.costs_of(P, v["inst"].F, v["inst"].D).min())
    assert v["opt"] == opt and v["ref"] == opt and v["ub20"] >= opt and v["ub200"] >= opt and v["ub200"] <= v["ub20"]
    assert all(b <= opt + 1e-6 for b in v["bound"].values()) and set(v["bound"]) == {"glb", "da5", "lp"}
    assert v["bound"]["da5"] >= v["bound"]["glb"] - 1e-9
    assert {a: t["best"] for a, t in v["tree"].items()} == {"glb": opt, "lin": opt} and not any(t["capped"] for t in v["tree"].values())
    assert independent_cost(v["ub_perm"], v["inst"]) == v["ub200"]


def test_prove_without_the_tree_and_with_a_cap():
    v = E.solve_prove("sparse", 12, 100014, tree=False)
    assert v["tree"] == {} and v["opt"] is None and v["ref"] == v["ub200"] and set(v["bound"]) == {"glb"}
    w = E.solve_prove("sparse", 8, 100014, cap=3)
    assert w["tree"]["glb"]["capped"] and w["opt"] is None and w["ref"] == w["ub200"] and w["cap"] == 3
    assert "lin" in w["tree"] and "lp" in w["bound"]


def test_the_linear_nodes_and_the_lp_are_left_out_above_nine():
    v = E.solve_prove("sparse", 12, 100015, cap=200)
    assert set(v["tree"]) == {"glb"} and set(v["bound"]) == {"glb", "da5"}
