"""Pfade der App, die der Rauchtest nicht erreicht: die Experimente im Seiteninhalt, PDF, beide Aufgaben, jede Familie, große Instanzen, die Rechenknöpfe (DEMO-PLAYBOOK §1d)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import avw_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
KIND = {"family_select": "selectbox", "n_select": "select_slider", "seed_input": "number_input", "pads_select": "select_slider", "task_select": "radio", "budget_select": "radio"}
PROVE_METRICS = {"Optimum", "Beste von 200 Abstiegen", "Knoten des Beweises"}


def _app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    for key, value in state.items():
        getattr(at.sidebar, KIND[key])(key=key).set_value(value)
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.success) + list(at.info) + list(at.warning) + list(at.error) + list(at.markdown) + list(at.caption))


def test_default_page_shows_the_metrics_the_path_and_the_verdicts():
    at = _app()
    values = {m.label: m.value for m in at.metric}
    assert set(values) == {"Bedauern der Empfehlung", "Rechenzeit der Empfehlung", "Zählung der Empfehlung", "Optimum (aufgezählt)", "Pads"}
    assert values["Optimum (aufgezählt)"] == "300" and values["Pads"] == "4" and values["Bedauern der Empfehlung"] == "0,0 %" and values["Rechenzeit der Empfehlung"].endswith(" s") and values["Zählung der Empfehlung"].replace(" ", "").isdigit()
    assert next(m for m in at.metric if m.label == "Zählung der Empfehlung").delta == "Bewertungen"
    text = _texts(at)
    for part in ("Entscheidungsweg der Regel", "→ Empfehlung: **20 Neustarts**", "Familie **Zwei Cluster**, 8 Bauteile, Raster 2×4, Seed 48, 4 Pads", "Muss das Optimum bewiesen werden?", "fünf Experimente"):
        assert part in text, part
    assert len(at.get("plotly_chart")) == 4


def test_the_experiments_the_hand_example_the_limits_table_and_the_formulation_are_on_the_page():
    at = _app()
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬 Experiment")] == [f"🔬 Experiment {i}" for i in (1, 2, 3, 4, 5)] and "🚧 Wo die Annahmen enden" in headings
    assert [e.label for e in at.expander] == ["So funktioniert es", "Handbeispiel zum Nachrechnen", "📐 Mathematische Formulierung"]
    assert not at.error
    assert any("Gilmore–Lawler-Schranke der Wurzel ist **5**" in str(m.value) and "**4**" in str(m.value) and "**16**" in str(m.value) and "**64**" in str(m.value) for m in at.markdown)
    assert [b.label for b in at.button if "⏱️" in b.label] == ["⏱️ Schranken und Baum rechnen (n = 8, 9, 12)", "⏱️ Finden rechnen (n = 8, 12, 16)", "⏱️ Finden rechnen (n = 20, 25, 36)"]


def test_prove_task_shows_the_bounds_the_tree_and_the_path():
    at = _app(task_select="prove")
    values = {m.label: m.value for m in at.metric}
    assert set(values) == PROVE_METRICS and values["Optimum"].isdigit()
    text = _texts(at)
    assert "→ Empfehlung: **Branch and Bound mit Gilmore–Lawler**" in text and "reine Zuordnung ohne Pads" in text and "bewiesen" in text and len(at.get("plotly_chart")) == 1


def test_prove_twelve_waits_for_its_button_and_runs_with_a_cap(monkeypatch):
    monkeypatch.setattr(C, "PROVE_CAP", 400)                        # nur für die Geschwindigkeit des Tests
    at = _app(task_select="prove", n_select=12)
    assert "Beweis rechnen" in " ".join(b.label for b in at.button) and not at.metric and "Mit dem Knopf starten" in _texts(at)
    at.button(key="prove_button").click().run()
    assert not at.exception and {m.label for m in at.metric} == PROVE_METRICS and "Obergrenze von 400 Knoten erreicht" in _texts(at)


def test_prove_above_twelve_shows_only_the_bound_side():
    at = _app(task_select="prove", n_select=20)
    text = _texts(at)
    assert not at.exception and "→ Empfehlung: **Schleife und Annealing**" in text and "Güte ist belegt, das Optimum nicht" in text and {m.label for m in at.metric} == PROVE_METRICS


def test_every_family_every_size_and_pad_count_renders():
    for fam in C.FAMILIES:
        at = _app(family_select=fam, n_select=9)
        assert f"Familie **{C.FAMILY_NAMES[fam]}**" in _texts(at) and len(at.get("plotly_chart")) == 4
    for n in (12, 16, 20):
        at = _app(n_select=n)
        assert f"{n} Bauteile" in _texts(at) and len(at.get("plotly_chart")) == 4
    for p in C.PAD_CHOICES:
        assert not _app(pads_select=p, n_select=9).exception


def test_the_size_and_the_budget_change_the_recommendation():
    assert "→ Empfehlung: **Schleife und Annealing**" in _texts(_app(n_select=25))
    tight = _texts(_app(n_select=20, budget_select="tight"))
    assert "→ Empfehlung: **Abstieg aus der Schleife**" in tight and "Zeitbudget knapp" in tight
    assert "→ Empfehlung: **6 Neustarts**" in _texts(_app(budget_select="tight"))


def test_the_pdf_button_makes_a_download_for_both_tasks():
    for task in C.TASKS:
        at = _app(n_select=9, task_select=task)
        at.button(key="pdf_make").click().run()
        assert not at.exception and any(d.proto.label == "⬇️ PDF herunterladen" for d in at.get("download_button")), task


def test_the_comparison_buttons_fill_their_sections(monkeypatch):
    monkeypatch.setattr(C, "FIND_SIZES", (8, 12, 20, 25))                         # nur für die Geschwindigkeit des Tests: die echten Reihen stehen in test_claims.py
    monkeypatch.setattr(C, "SEEDS_FIND", {8: 1, 12: 1, 16: 1})
    monkeypatch.setattr(C, "SEEDS_LARGE", 1)
    monkeypatch.setattr(C, "SEEDS_FRESH", {8: 1, 12: 1, 16: 1, 20: 1, 25: 1, 36: 1})
    monkeypatch.setattr(C, "SEEDS_PROVE", {8: 1, 9: 1, 12: 1})
    monkeypatch.setattr(C, "PROVE_CAP", 300)
    at = _app()
    assert "Rechnen Sie in Experiment 3 mindestens zwei Größen" in _texts(at) and "Rechnen Sie zuerst beide Reihen" in _texts(at)
    at.button(key="prove_ok_button").click().run()
    text = _texts(at)
    assert not at.exception and "n = 8 (6 Instanzen)" in text and "n = 12 (6 Instanzen)" in text and "Obergrenze" in text and len(at.get("plotly_chart")) == 4 + 2
    at.button(key="find_small_ok_button").click().run()
    text = _texts(at)
    assert not at.exception and "Bei n = 8, 18 Instanzen (Pads 2, 4, 8)" in text and "n = 12: Neustarts" in text and len(at.get("plotly_chart")) == 6 + 3
    at.radio(key="n3_select").set_value(12).run()
    assert not at.exception and "Bei n = 12, 18 Instanzen" in _texts(at)
    at.button(key="find_large_ok_button").click().run()
    text = _texts(at)
    assert not at.exception and "n = 25: Neustarts" in text and "Rechnen Sie zuerst beide Reihen" not in text and len(at.get("plotly_chart")) == 6 + 3
    at.button(key="fresh_ok_button").click().run()
    text = _texts(at)
    assert not at.exception and "Frische Instanzen: n = 8" in text and "Feste Instanzen: n = 8" in text and len(at.get("plotly_chart")) == 6 + 3 + 1
