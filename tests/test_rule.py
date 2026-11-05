"""Die Entscheidungsregel: eine reine Funktion von Größe, Aufgabe und Zeitbudget; jeder Zweig an festen Eingaben."""

import inspect

import pytest

import avw_constants as C
import avw_rule as R


@pytest.mark.parametrize("n", C.SIZES)
def test_find_rule_by_size_normal_budget(n):
    adv = R.advise(n, "find", "normal")
    assert adv.find == ("neu20" if n <= 16 else "sa_s") and adv.proof is None and adv.task == "find"
    assert R.rule_key(n) == adv.find and adv.label == C.FIND_NAMES[adv.find]


@pytest.mark.parametrize("n", C.SIZES)
def test_find_rule_by_size_tight_budget(n):
    assert R.advise(n, "find", "tight").find == ("neu6" if n <= 16 else "abs_s")


@pytest.mark.parametrize("n", (4, 8, 9, 12))
def test_prove_rule_within_reach_is_branch_and_bound_with_gilmore_lawler(n):
    adv = R.advise(n, "prove")
    assert adv.proof == "glb" and adv.find is None and "Branch and Bound" in adv.label
    assert [s.question for s in adv.steps][:2] == ["Muss das Optimum bewiesen werden?", f"Ist n höchstens {R.PROVE_MAX_N}?"] and [s.answer for s in adv.steps][:2] == ["ja", "ja"]


@pytest.mark.parametrize("n", (16, 20, 36))
def test_prove_rule_out_of_reach_falls_back_to_bound_and_finding(n):
    adv = R.advise(n, "prove", "normal")
    assert adv.proof is None and adv.find == R.rule_key(n) and adv.bounds == ("glb",)
    assert [s.answer for s in adv.steps][:2] == ["ja", "nein"]


def test_the_crossing_sits_between_sixteen_and_twenty():
    assert R.CROSS_N == 20 and R.advise(16, "find").find == "neu20" and R.advise(20, "find").find == "sa_s"


def test_bounds_follow_the_size_of_the_linear_program():
    assert R.advise(8, "prove").bounds == ("glb", "da5", "lp") and R.advise(9, "prove").bounds == ("glb", "da5", "lp")
    assert R.advise(12, "prove").bounds == ("glb", "da5") and R.advise(25, "find").bounds == ("glb",)


def test_every_step_names_its_piece_and_every_method_a_known_key():
    for n in C.SIZES:
        for task in C.TASKS:
            for budget in C.BUDGET_CHOICES:
                adv = R.advise(n, task, budget)
                assert all(s.question and s.answer and s.piece.startswith("Stück") for s in adv.steps)
                assert (adv.find in C.FIND_KEYS) == (adv.find is not None) and adv.steps[-1].answer


def test_the_rule_is_a_function_of_size_task_and_budget_only():
    assert list(inspect.signature(R.advise).parameters) == ["n", "task", "budget"]
    a = R.advise(12, "find", "normal")
    assert a == R.advise(12, "find", "normal")


def test_hand_example_path_for_four_places():
    prove = R.advise(4, "prove")
    assert [(s.question, s.answer) for s in prove.steps][:3] == [("Muss das Optimum bewiesen werden?", "ja"), ("Ist n höchstens 12?", "ja"), ("Welcher Beweis?", prove.steps[2].answer)]
    assert prove.proof == "glb" and R.advise(4, "find").find == "neu20"


def test_unknown_task_or_budget_is_refused():
    with pytest.raises(ValueError):
        R.advise(8, "raten")
    with pytest.raises(ValueError):
        R.advise(8, "find", "gemuetlich")
