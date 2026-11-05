"""Abbildungen: sie entstehen für jede Eingabe, Achsen sind gesperrt, Daten stimmen mit den Werten überein; PDF-Export."""

import numpy as np
import pytest

import avw_constants as C
import avw_evaluation as E
import avw_instance as I
import avw_visualization as V
from avw_pdf_export import build_pdf
from oracle import make_row


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


@pytest.fixture(scope="module")
def find12():
    return E.solve_find("cluster", 12, 100030, 4)


def test_arrangement_for_every_family_and_size():
    for fam in C.FAMILIES:
        for n in (6, 9, 12, 16, 25, 36):
            inst = I.make_instance(fam, n, 3)
            fig = V.build_arrangement(inst, list(range(n)), fam)
            assert len(fig.data[-1].x) == n and _locked(fig)


def test_methods_chart_has_one_marker_per_method_and_marks_the_recommendation(find12):
    fig = V.build_methods(find12, "neu20", "t")
    points = [(x, y, t) for tr in fig.data if tr.mode == "markers+text" for x, y, t in zip(tr.x, tr.y, tr.text)]
    assert sorted(t for _, _, t in points) == sorted(V.SHORT.values()) and set(V.SHORT) == set(C.FIND_KEYS) and fig.layout.xaxis.type == "log"
    ys = {t: y for _, y, t in points}
    assert ys["20 Neustarts"] == pytest.approx(100 * find12["gap"]["neu20"]) and ys["Runden"] == pytest.approx(100 * find12["gap"]["rund"])
    rec = fig.data[-1]
    assert rec.name == "Empfehlung der Regel" and rec.y[0] == pytest.approx(100 * find12["gap"]["neu20"]) and _locked(fig)


def test_restart_curve_is_monotone_and_has_two_reference_lines(find12):
    fig = V.build_restart_curve(find12)
    ys = list(fig.data[0].y)
    assert len(ys) == 20 and ys == sorted(ys, reverse=True) and ys[-1] == find12["cost"]["neu20"] and len(fig.layout.shapes) == 2 and _locked(fig)


def test_prove_charts():
    v = E.solve_prove("cluster", 8, 100031)
    fig = V.build_prove_bounds(v, "t")
    assert list(fig.data[0].y) == [C.BOUND_NAMES[k] for k in C.BOUND_KEYS] and list(fig.data[0].x) == [v["bound"][k] for k in C.BOUND_KEYS] and fig.layout.shapes
    rows = {8: [E.prove_row("cluster", 8, 100031), E.prove_row("star", 8, 100031)], 12: [E.prove_row("star", 12, 100031)]}
    nodes = V.build_prove_nodes(rows, "t")
    assert [t.name for t in nodes.data] == [C.TREE_NAMES["glb"], C.TREE_NAMES["lin"]] and len(nodes.data[0].y) == 3 and len(nodes.data[1].y) == 2 and nodes.layout.yaxis.type == "log"
    gaps = V.build_bound_gaps(rows, E.bound_gap, "t")
    assert [t.name for t in gaps.data] == [C.BOUND_NAMES["glb"], C.BOUND_NAMES["da5"], C.BOUND_NAMES["lp"]] and len(gaps.data[2].x) == 1 and len(gaps.data[0].x) == 2


def test_sweep_charts_regret_front_cross_and_rule():
    rows = [make_row(12, {"neu20": 100, "sa_s": 103, "rund": 120}, {"neu20": 0.05, "sa_s": 0.1, "rund": 0.001}), make_row(12, {"neu20": 101, "sa_s": 100, "rund": 125}, {"neu20": 0.05, "sa_s": 0.1, "rund": 0.001})]
    bars = V.build_regret_bars(rows, E.regret_stats, "t")
    assert len(bars.data[0].x) == len(C.FIND_KEYS) == len(bars.data[1].x) and bars.data[0].y[C.FIND_KEYS.index("neu20")] == pytest.approx(100 * E.regret_stats(rows, "neu20")["mean"]) and _locked(bars)
    fr = V.build_front(rows, E.regret_stats, E.front, "t")
    kante = fr.data[-1]
    assert kante.name == "Kante" and len(kante.x) == len(E.front(rows)) and fr.layout.xaxis.type == "log"
    by_n = {12: rows, 25: [make_row(25, {"neu20": 105, "sa_s": 100}, {"neu20": 1.0, "sa_s": 0.3})]}
    cross = V.build_cross(by_n, E.regret_stats)
    assert [list(t.x) for t in cross.data] == [[12, 25]] * 4 and cross.layout.yaxis2.type == "log"
    rule = V.build_rule_bars(by_n, E.rule_regret, "t")
    assert [t.name for t in rule.data] == ["Regel", "immer 20 Neustarts", "immer Schleife mit Annealing", "bestes der beiden je Instanz"] and list(rule.data[0].x) == ["n = 12", "n = 25"]


def test_pdf_export_for_both_tasks():
    sf = E.Settings("cluster", 8, 100032, 4, "find", "normal")
    pdf = build_pdf(sf, E.solve_find("cluster", 8, 100032, 4))
    assert pdf[:4] == b"%PDF" and len(pdf) > 1500
    sp = E.Settings("cluster", 8, 100032, 4, "prove", "tight")
    assert build_pdf(sp, E.solve_prove("cluster", 8, 100032))[:4] == b"%PDF"
    assert build_pdf(E.Settings("cluster", 12, 100032, 4, "prove", "normal"), E.solve_prove("cluster", 12, 100032, tree=False))[:4] == b"%PDF"
