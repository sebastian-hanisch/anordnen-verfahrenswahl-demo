"""Verfahrenswahl beim Anordnen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 15 (Abschluss) der Reihe „Anordnen: relaxieren und runden“: welches Verfahren für welche Aufgabe, gemessen woran? Kein neues Rechenverfahren, sondern die Wahl unter den Verfahren der Stücke 3 bis 12
(Schranken, Branch and Bound, Rundung, Schleife, Dichtestrafe, Tauschabstieg, Annealing) und, wie in den anderen Abschlussstücken, was die Wahl kostet. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import avw_constants as C
import avw_rule as R
from avw_evaluation import (
    Settings,
    bound_gap,
    count,
    de,
    find_sweep,
    front,
    hand_prove,
    num,
    paired,
    pct,
    pooled,
    prove_sweep,
    regret_stats,
    restart_hits,
    rule_regret,
    secs,
    solve_find,
    solve_prove,
    tree_stats,
    verdict_core,
    verdict_cross,
    verdict_find_sweep,
    verdict_path,
    verdict_prove_sweep,
    verdict_rule,
    work_split,
    work_text,
)
from avw_layout import dunkles_design, kopf_css
from avw_pdf_export import build_pdf
from avw_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from avw_visualization import build_arrangement, build_bound_gaps, build_cross, build_front, build_methods, build_prove_bounds, build_prove_nodes, build_regret_bars, build_restart_curve, build_rule_bars

st.set_page_config(page_title="Verfahrenswahl beim Anordnen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne alle Verfahren …")
def _find(family, n, seed, pads):
    return solve_find(family, n, seed, pads)


@st.cache_data(show_spinner="Rechne Schranken und Baum …")
def _prove(family, n, seed, tree):
    return solve_prove(family, n, seed, tree)


@st.cache_data(show_spinner=False)
def _find_sweep(family, n, fresh):
    return find_sweep(family, n, fresh)


@st.cache_data(show_spinner=False)
def _prove_sweep(family, n):
    return prove_sweep(family, n)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


def run_knob(flag, label, info, todo, work):
    """Rechenknopf: `todo` ist eine Liste von Beschriftungen und Aufrufen; nach dem Lauf steht `flag` im Session State."""
    if st.session_state.get(flag):
        return True
    st.info(info)
    if st.button(label, key=flag + "_button"):
        bar = st.progress(0.0, text="Rechne …")
        for i, (text, args) in enumerate(todo):
            work(*args)
            bar.progress((i + 1) / len(todo), text=f"{text} fertig")
        st.session_state[flag] = True
        st.rerun()
    return False


def fixed_rows(ns, fresh=False):
    return {n: pooled({f: _find_sweep(f, n, fresh) for f in C.FAMILIES}) for n in ns}


SMALL = tuple(n for n in C.FIND_SIZES if n <= 16)
LARGE = tuple(n for n in C.FIND_SIZES if n > 16)

# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in avw_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧭 Verfahrenswahl beim Anordnen")
st.markdown(
    """
**Welches Verfahren für welche Aufgabe, und gemessen woran?** Dieselbe Aufgabe wie in Stück 1 bis 12: `n` Bauteile auf `n` Plätze, Kosten gleich der Summe aus **Fluss mal Abstand**, beim Finden dazu **feste Pads**.
Stück 3 bis 12 haben zehn Verfahren angesammelt: Schranken, einen Baum, Rundung, die Schleife, die Dichtestrafe, den Tauschabstieg und das Annealing. Hier steht **die Wahl** und, wie in den anderen Abschlussstücken, **was die Wahl kostet**.
Es gibt **zwei Aufgaben**: das **Finden** einer guten Anordnung und das **Beweisen**, dass keine bessere existiert. Die Antwort der Messung: Finden ist billig, Beweisen kostet; bis `n = 12` schlagen **20 Neustarts** des Abstiegs jede Relaxation deutlich, bei `n = 16` liegen sie im Mittel vor Schleife plus Annealing (im Rahmen der Streuung),
ab `n = 25` (bei `n = 20` noch nicht) sind **Schleife plus Annealing** schneller; die Relaxationen zahlen als **Schranke** und als **Startlösung**. Sechs Familien der Flussmatrix und die **Pads** sind **eigene Erfindungen**. Stück 15 der Reihe, der Abschluss.

Weiter unten: **fünf Experimente** (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Die Regel** ist eine reine Funktion von **Größe, Aufgabe und Zeitbudget**: *Beweis verlangt?* Dann Branch and Bound mit der Gilmore–Lawler-Schranke (bis `n = 12`); sonst *Finden*: bis `n = 16` 20 Neustarts des Tauschabstiegs aus Zufall, ab `n = 20` die Schleife aus Stück 10 als Startlösung mit kaltem Annealing. Bei knappem Zeitbudget 6 Neustarts bzw. nur der Abstieg aus der Schleife.
2. **Finden** rechnet **alle elf Verfahren** der Platzierungsseite auf derselben Instanz (mit Pads): einmal runden (Stück 9), die Schleife (Stück 10), die Dichtestrafe in zwei Wertungen (Stück 11), vier Tauschabstiege, 6 und 20 Neustarts und Schleife mit Annealing (Stück 12).
3. **Beweisen** rechnet die reine Zuordnung ohne Pads: Gilmore–Lawler-Schranke (Stück 3), Dual Ascent mit fünf Runden und die Linearisierung (nur bis `n = 9`, Stück 5), 20 und 200 Abstiege aus Zufall und den Branch and Bound mit zwei Arten von Knotenschranken (Stück 8, Obergrenze 300 000 Knoten).
4. **Das Maß:** **Bedauern** = (Kosten − beste Kosten aller Verfahren auf der Instanz) / beste Kosten. Bis `n = 9` ist das aufgezählte Optimum dabei, ab `n = 12` ist der Vergleichswert selbst ein Verfahrensergebnis: das Bedauern ist eine **obere** Grenze der Lücke zum Optimum.
5. **Der Aufwand** steht doppelt da: als **Zeit** in Sekunden (Messung dieser Python-Fassung auf diesem Rechner, schwankt von Lauf zu Lauf, nur Größenordnungen sind belastbar) und als **Zählung** (Bewertungen, Runden, Auswertungen, Knoten; verschiedene Einheiten).
6. **Feste Instanzen:** Vergleiche laufen über feste Seeds (Finden: `n = 8, 12, 16` mit 180 / 90 / 54 Instanzen bei 2, 4, 8 Pads, `n = 20, 25, 36` mit je 18 Instanzen bei 4 Pads; Beweisen: `n = 8, 9, 12` mit 30 / 18 / 18 Instanzen). Die **Regel** wird zuletzt an **frischen** Instanzen (Seeds ab 200000) geprüft.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Instanz**")
    family = st.selectbox("Familie der Flussmatrix", C.FAMILIES, key="family_select", format_func=lambda f: C.FAMILY_NAMES[f], help="Wie der Fluss zwischen den Bauteilen verteilt ist. Die Beschreibung steht unter dem Regler.")
    st.caption(C.FAMILY_HELP[family])
    n = st.select_slider("Bauteile n", options=C.SIZES, key="n_select", help="Raster von 2×4 (n = 8) bis 6×6 (n = 36). Bis n = 9 wird alles aufgezählt (Vergleichswert: Optimum).")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed)
    pads_n = st.select_slider("Zahl der Pads", options=C.PAD_CHOICES, key="pads_select", help="Feste Anker auf dem Ring um das Raster. Nur beim Finden; die Aufgabe „Beweisen“ rechnet die reine Zuordnung ohne Pads.")
    st.markdown("**Die Aufgabe**")
    task = st.radio("Aufgabe", C.TASKS, key="task_select", format_func=lambda k: C.TASK_NAMES[k], help="Finden: eine gute Anordnung (mit Pads). Beweisen: das Optimum belegen (reine Zuordnung).")
    budget = st.radio("Zeitbudget", C.BUDGET_CHOICES, key="budget_select", format_func=lambda k: C.BUDGET_NAMES[k], horizontal=True, help="Normal: so viel Rechenzeit, wie die Regel braucht. Knapp: nur ein Teil davon (6 statt 20 Neustarts, Abstieg statt Annealing).")

sync_query_params({"family_select": family, "n_select": int(n), "seed_input": int(seed), "pads_select": int(pads_n), "task_select": task, "budget_select": budget})
settings = Settings(family, int(n), int(seed), int(pads_n), task, budget)
advice = R.advise(settings.n, settings.task, settings.budget)

# --- Instanz ---------------------------------------------------------------------------------------------------------------------------------

v = None
if task == "find":
    v = _find(family, settings.n, settings.seed, settings.pads)
elif settings.n > R.PROVE_MAX_N:
    v = _prove(family, settings.n, settings.seed, False)
elif settings.n <= C.LP_MAX_N or st.session_state.get("prove_go") == (family, settings.n, settings.seed):
    v = _prove(family, settings.n, settings.seed, True)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.markdown("**Entscheidungsweg der Regel**")
for i, stp in enumerate(advice.steps, 1):
    st.markdown(f"{i}. {stp.question} **{stp.answer}** *({stp.piece})*")
st.markdown(f"→ Empfehlung: **{advice.label}**")

if v is None:
    st.info(f"Für n = {settings.n} wächst der Baum auf Tausende bis Hunderttausende Knoten; der Beweis rechnet im Median etwa eine Sekunde, im ungünstigen Fall eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Beweis rechnen", key="prove_button"):
        st.session_state["prove_go"] = (family, settings.n, settings.seed)
        st.rerun()
elif task == "find":
    rec = advice.find
    m1, m2, m3 = st.columns(3)
    m4, m5 = st.columns(2)
    m1.metric("Bedauern der Empfehlung", pct(v["gap"][rec], 1), delta=f"Kosten {num(v['cost'][rec])}", delta_color="off", help=f"{advice.label} gegen den Vergleichswert.")
    m2.metric("Rechenzeit der Empfehlung", secs(v["sec"][rec]), help="Sekunden dieser Python-Fassung auf diesem Rechner; schwankt von Lauf zu Lauf.")
    wv, wu = work_split(v["work"][rec])
    m3.metric("Zählung der Empfehlung", wv, delta=wu, delta_color="off", help="Bewertungen einer Anordnung, Runden der Schleife, Auswertungen der Dichtestrafe: verschiedene Einheiten, nicht untereinander vergleichbar.")
    m4.metric("Optimum (aufgezählt)" if v["exact"] else "Vergleichswert", num(v["best"]), help="Die kleinsten Kosten aller n! Anordnungen." if v["exact"] else "Das beste Ergebnis aller elf Verfahren auf dieser Instanz: eine obere Grenze des Optimums.")
    m5.metric("Pads", f"{settings.pads}", help="Zahl der festen Pads.")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(build_arrangement(v["inst"], v["perm"][rec], f"{advice.label}, Kosten {num(v['cost'][rec])}"), width="stretch", key="arrangement_rec")
    with c2:
        best_key = min((k for k in C.FIND_KEYS if v["hit"][k] and k != "neu6"), key=lambda k: v["sec"][k], default=rec)
        st.plotly_chart(build_arrangement(v["inst"], v["perm"][best_key], f"Schnellstes mit dem Besten: {C.FIND_NAMES[best_key]}, {num(v['cost'][best_key])}"), width="stretch", key="arrangement_best")
else:
    m1, m2, m3 = st.columns(3)
    tg = v["tree"].get("glb")
    m1.metric("Optimum", num(v["opt"]) if v["opt"] is not None else "nicht bewiesen", help="Das Optimum, soweit der Baum zu Ende gerechnet wurde.")
    m2.metric("Beste von 200 Abstiegen", num(v["ub200"]), delta=f"{secs(v['sec']['ub200'])}", delta_color="off", help="Obere Schranke des Optimums.")
    m3.metric("Knoten des Beweises", count(tg["nodes"]) if tg else "–", delta=secs(tg["sec"]) if tg else None, delta_color="off", help="Bewertete Knoten des Branch and Bound mit Gilmore–Lawler-Schranke.")
    st.plotly_chart(build_prove_bounds(v, "Schranken gegen die beste gefundene Anordnung"), width="stretch", key="prove_bounds")

if v is not None:
    if st.button("📄 PDF des aktuellen Ergebnisses erstellen", key="pdf_make"):
        st.session_state["pdf_made"] = (settings, build_pdf(settings, v))
    made = st.session_state.get("pdf_made")
    if made and made[0] == settings:
        st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="verfahrenswahl-anordnen.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Welches Verfahren, gemessen woran?")
if v is not None:
    verdict(verdict_core(settings, v))
verdict(verdict_path(settings, v))

st.markdown("---")

# --- Experiment 1 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Der Weg durch den Baum")
if v is None:
    st.caption("Der Beweis ist noch nicht gerechnet (Knopf oben).")
elif task == "find":
    st.caption("Alle elf Verfahren der Platzierungsseite auf dieser Instanz: Rechenzeit (logarithmisch) gegen Bedauern. Die Empfehlung der Regel ist rot umrandet. Darunter die Zahlen und die Neustarts.")
    st.plotly_chart(build_methods(v, advice.find, "Zeit gegen Bedauern, alle Verfahren"), width="stretch", key="methods")
    table = [{"Verfahren": C.FIND_NAMES[k], "Stück": C.FIND_PIECE[k], "Kosten": num(v["cost"][k]), "Bedauern": pct(v["gap"][k], 1), "Zeit": secs(v["sec"][k]), "Zählung": work_text(v["work"][k]), "Empfehlung": "◀" if k == advice.find else ""} for k in C.FIND_KEYS]
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    st.plotly_chart(build_restart_curve(v), width="stretch", key="restart_curve")
else:
    st.caption("Die Schranken gegen das beste Abstiegsergebnis, dazu der Baum: wie viel Rechnung das Optimum bewiesen kostet, gegen die Abstiege, die es meist schon finden.")
    table = []
    for k in C.BOUND_KEYS:
        if k in v["bound"]:
            table.append({"Verfahren": C.BOUND_NAMES[k], "Stück": C.BOUND_PIECE[k], "Wert": de(v["bound"][k], 1), "Lücke zum Vergleichswert": pct((v["ref"] - v["bound"][k]) / v["ref"], 1), "Zeit": secs(v["sec"][k]), "Knoten": ""})
    table.append({"Verfahren": "20 Abstiege aus Zufall", "Stück": "Stück 3", "Wert": num(v["ub20"]), "Lücke zum Vergleichswert": pct((v["ub20"] - v["ref"]) / v["ref"], 1), "Zeit": secs(v["sec"]["ub20"]), "Knoten": ""})
    table.append({"Verfahren": f"{C.PROVE_STARTS} Abstiege aus Zufall", "Stück": "Stück 3", "Wert": num(v["ub200"]), "Lücke zum Vergleichswert": pct((v["ub200"] - v["ref"]) / v["ref"], 1), "Zeit": secs(v["sec"]["ub200"]), "Knoten": ""})
    for art, tr in v["tree"].items():
        table.append({"Verfahren": C.TREE_NAMES[art], "Stück": "Stück 8", "Wert": num(tr["best"]) + (" (nicht bewiesen)" if tr["capped"] else " (bewiesen)"), "Lücke zum Vergleichswert": "", "Zeit": secs(tr["sec"]), "Knoten": count(tr["nodes"])})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
with st.expander("Handbeispiel zum Nachrechnen"):
    h = hand_prove()
    st.markdown(
        f"**Vier Plätze auf einer Zeile** (Abstände 1 bis 3), Fluss A–C, A–D, B–C, B–D je 1. Die Gilmore–Lawler-Schranke der Wurzel ist **{num(h['root'])}**, das Optimum **{num(h['opt'])}**: C A B D (C auf Platz 1, A auf 2, B auf 3, D auf 4) kostet 1 + 2 + 2 + 1 = 6, und keine Anordnung kostet weniger. "
        f"Der Baum mit dem Anfangswert 6 bewertet bei Gilmore–Lawler **{h['glb'].nodes}**, bei linearen Knotenschranken **{h['lin'].nodes}** und ohne Schranke **{h['none'].nodes}** Knoten (ohne Anfangswert {h['glb_free'].nodes} bei Gilmore–Lawler). "
        "Die Regel für diese Instanz mit verlangtem Beweis: *Beweis nötig? ja → n höchstens 12? ja → Branch and Bound mit Gilmore–Lawler*; ohne Beweis: Neustarts des Abstiegs."
    )

st.markdown("---")

# --- Experiment 2 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Beweisen kostet")
st.caption("Reine Zuordnung, sechs Familien, n = 8, 9, 12 (30 / 18 / 18 Instanzen): die Lücke der Schranken, die Knoten des Baums und wie oft 20 bzw. 200 Abstiege das bewiesene Optimum schon treffen.")
if run_knob("prove_ok", "⏱️ Schranken und Baum rechnen (n = 8, 9, 12)", "Die Rechnung läuft über 66 Instanzen mit Schranken, 200 Abstiegen, Linearisierung (bis n = 9) und zwei Bäumen und dauert einige Minuten (auf Streamlit Cloud länger; bei n = 12 bis zu eine halbe Minute je Instanz). Mit dem Knopf starten:",
            [(f"n = {m}, {C.FAMILY_NAMES[f]}", (f, m)) for m in C.PROVE_SIZES for f in C.FAMILIES], lambda f, m: _prove_sweep(f, m)):
    prows = {m: pooled({f: _prove_sweep(f, m) for f in C.FAMILIES}) for m in C.PROVE_SIZES}
    st.plotly_chart(build_bound_gaps(prows, bound_gap, "Lücke der Schranken zum Optimum, Median"), width="stretch", key="bound_gaps")
    st.plotly_chart(build_prove_nodes({m: prows[m] for m in C.PROVE_SIZES}, "Knoten des Branch and Bound je Instanz"), width="stretch", key="prove_nodes")
    table = []
    for m in C.PROVE_SIZES:
        h_ = restart_hits(prows[m])
        tg = tree_stats(prows[m], "glb")
        table.append({"n": m, "Instanzen": len(prows[m]), "20 Abstiege treffen": f"{h_['hit20']} von {h_['proved']}", "200 Abstiege treffen": f"{h_['hit200']} von {h_['proved']}", "Knoten (Median / größter)": f"{count(tg['median'])} / {count(tg['max'])}",
                      "Zeit des Beweises (Median / größte)": f"{secs(tg['sec'])} / {secs(tg['sec_max'])}", "Obergrenze erreicht": tg["capped"]})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_prove_sweep(prows))
    st.caption("Nicht gerechnet, aber in der Phase 0 gemessen: " + "; ".join(f"**{a}** ({b}): {c}" for a, b, c in C.NOT_COMPUTED) + ".")

st.markdown("---")

# --- Experiment 3 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Finden über feste Instanzen")
st.caption("Alle elf Verfahren über feste Instanzen: mittleres Bedauern, Treffer, Rechenzeit und die Kante (kein anderes Verfahren ist zugleich schneller und besser). Größe wählbar, soweit gerechnet.")
small_ok = run_knob("find_small_ok", "⏱️ Finden rechnen (n = 8, 12, 16)", "Die Rechnung läuft über 324 Instanzen mit elf Verfahren und dauert einige Minuten (auf Streamlit Cloud länger). Mit dem Knopf starten:",
                    [(f"n = {m}, {C.FAMILY_NAMES[f]}", (f, m, False)) for m in SMALL for f in C.FAMILIES], lambda f, m, fr: _find_sweep(f, m, fr))
large_ok = run_knob("find_large_ok", "⏱️ Finden rechnen (n = 20, 25, 36)", "Die Rechnung läuft über 54 große Instanzen (vier Pads) und dauert einige Minuten, bei n = 36 etwa sieben Sekunden je Instanz (auf Streamlit Cloud länger). Mit dem Knopf starten:",
                    [(f"n = {m}, {C.FAMILY_NAMES[f]}", (f, m, False)) for m in LARGE for f in C.FAMILIES], lambda f, m, fr: _find_sweep(f, m, fr))
avail = (SMALL if small_ok else ()) + (LARGE if large_ok else ())
fixed = fixed_rows(avail)
if avail:
    n3 = st.radio("Größe des Vergleichs", avail, key="n3_select", horizontal=True, format_func=lambda m: f"n = {m}")
    rows3 = fixed[n3]
    st.plotly_chart(build_regret_bars(rows3, regret_stats, f"Mittleres Bedauern je Verfahren, n = {n3} ({len(rows3)} Instanzen)"), width="stretch", key=f"regret_bars_{n3}")
    st.plotly_chart(build_front(rows3, regret_stats, front, f"Zeit gegen Bedauern, n = {n3}"), width="stretch", key=f"front_{n3}")
    tab = []
    for k in C.FIND_KEYS:
        s_ = regret_stats(rows3, k)
        tab.append({"Verfahren": C.FIND_NAMES[k], "Stück": C.FIND_PIECE[k], "Bedauern (Mittel)": pct(s_["mean"], 2), "Bedauern (Median)": pct(s_["median"], 2), "erreicht das Beste": f"{s_['hit']} von {s_['count']}", "Zeit (Median)": secs(s_["sec"]), "auf der Kante": "◀" if k in front(rows3) else ""})
    st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
    verdict(verdict_find_sweep(n3, rows3))

st.markdown("---")

# --- Experiment 4 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Die Kreuzung")
st.caption("20 Neustarts gegen Schleife mit Annealing über die Größe: das mittlere Bedauern und der Median der Zeit, mit dem gepaarten Unterschied und seinem Standardfehler. Bis n = 16 ist 20 Neustarts schneller und im Mittel mindestens so gut; die Zeit kippt zwischen n = 20 und n = 25.")
if len(avail) >= 2:
    st.plotly_chart(build_cross(fixed, regret_stats), width="stretch", key="cross")
    tab = []
    for m in avail:
        pr = paired(fixed[m], "sa_s", "neu20")
        tab.append({"n": m, "Instanzen": len(fixed[m]), "Neustarts (Bedauern)": pct(regret_stats(fixed[m], "neu20")["mean"], 2), "Annealing (Bedauern)": pct(regret_stats(fixed[m], "sa_s")["mean"], 2),
                    "Unterschied (Prozentpunkte)": f"{de(pr['mean'], 2)} ± {de(pr['se'], 2)}", "Annealing besser / schlechter / gleich": f"{pr['better']} / {pr['worse']} / {pr['equal']}"})
    st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
    verdict(verdict_cross(fixed))
else:
    st.info("Rechnen Sie in Experiment 3 mindestens zwei Größen, am besten beide Reihen (n ≤ 16 und n ≥ 20).")

st.markdown("---")

# --- Experiment 5 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Die Regel auf frischen Instanzen")
st.caption("Die Regel („Neustarts bis n = 16, danach Schleife mit Annealing“) wurde an den festen Instanzen gebildet. Hier steht sie auf frischen Instanzen (Seeds ab 200000) neben „immer Neustarts“, „immer Schleife mit Annealing“ und dem besseren der beiden je Instanz. Dazu die Grenzen der Messung.")
if len(avail) == len(C.FIND_SIZES):
    if run_knob("fresh_ok", "⏱️ Frische Instanzen rechnen", "Die Rechnung läuft über 234 frische Instanzen (90 / 54 / 36 / 18 / 18 / 18) und dauert einige Minuten (auf Streamlit Cloud länger). Mit dem Knopf starten:",
                [(f"n = {m}, {C.FAMILY_NAMES[f]}", (f, m, True)) for m in C.FIND_SIZES for f in C.FAMILIES], lambda f, m, fr: _find_sweep(f, m, fr)):
        fresh = fixed_rows(C.FIND_SIZES, True)
        st.plotly_chart(build_rule_bars(fresh, rule_regret, "Mittleres Bedauern der Regel auf frischen Instanzen"), width="stretch", key="rule_bars")
        verdict(verdict_rule(fixed, fresh))
else:
    st.info("Rechnen Sie zuerst beide Reihen in Experiment 3 (n ≤ 16 und n ≥ 20): die Regel braucht die festen Instanzen zum Vergleich.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zeit ist implementierungsabhängig** | Die Verfahren sind vektorisierte Python-Fassungen (numpy); in anderer Sprache oder mit anderer Umsetzung liegen die Zeiten und die Kreuzung zwischen `n = 20` und `n = 25` woanders. Zeiten schwanken von Lauf zu Lauf um das Doppelte; in Tests stehen nur Kosten und Zählungen. | Stück 12, 11 |
| **Kleine Stichprobe ab n = 20** | 18 Instanzen je Größe, nur 4 Pads: der gepaarte Unterschied hat 0,3 bis 0,6 Prozentpunkte Unsicherheit. „Schneller“ ist stark, „im Mittel etwas besser“ schwach. | – |
| **Zugzahl des Annealing ab n = 20 selbst gesetzt** | Stück 12 definiert die Zugzahlen nur bis `n = 16`; für 20, 25, 36 stehen hier 9 000 / 12 000 / 20 000. Die Empfindlichkeit (halbe und doppelte Zugzahl) wurde in der Phase 0 gemessen, die Reihenfolge gegen die Neustarts blieb bei n = 25 und 36, bei n = 20 hängt sie von der Zugzahl ab. | Stück 12 |
| **Der Vergleichswert ist selbst ein Verfahrensergebnis** | Ab `n = 12` ist es das beste Ergebnis aller elf Verfahren; Bedauern ist eine obere Grenze der Lücke zum Optimum, „0 %“ heißt „so gut wie das Beste dieser elf“, nicht „optimal“. | Stück 8 |
| **Dichtestrafe mit den Einstellungen aus Stück 11** | Randzone 0,5, Ladungsbreite 3, zwölf Stufen: bei anderen Parametern (breitere Randzone, mehr Stufen) kann sie besser abschneiden. Der Befund „auf keiner Kante“ gilt für diese Einstellungen. | Stück 11 |
| **Pads und Familien erfunden** | Zahl, Ort, Gewicht und Verbindungen der Pads und die sechs Familien sind eigene Erfindungen; jede Aussage nennt die Pad-Zahl. Echte Platinen haben andere Strukturen. | Stück 9 |
| **Beweisen ohne Pads** | Der Branch and Bound rechnet die reine Zuordnung; mit linearen Anfangskosten (Pads) ist er in dieser Demo nicht gemessen. | Stück 8 |
| **Größen nur bis n = 36, keine QAPLIB** | Wie sich die Verfahren auf Instanzen aus der Literatur oder bei `n > 36` verhalten, ist nicht untersucht. | – |
| **Rechenrauschen** | Die Dichtestrafe und die Rundung sind empfindlich: ein Rundungsrest kann die Anordnung einer Instanz ändern; die Mittel über viele Instanzen sind auf wenige Zehntel Prozentpunkte stabil, die Einzelwerte sind es nicht. | – |
| **Literatur** | Aussagen zur Größe exakter Verfahren stehen hier nicht; die Quellen der Stücke 3 bis 12 sind dort vermerkt (zum Teil „nicht eingesehen“). | Stück 3 bis 12 |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Die Aufgabe.** Flüsse $F$, Abstände $D$ (Manhattan auf dem Raster), Anordnung $\pi$ (Platz je Bauteil), beim Finden mit Pads: $\mathrm{cost}(\pi) = \sum_{i<k} F_{ik} D_{\pi_i \pi_k} + \sum_{i,j} w_{ij} \lVert s_{\pi_i} - a_j \rVert_1$.
Beim Beweisen entfällt der Pad-Term (reine Zuordnung nach Koopmans und Beckmann).

**Bedauern.** Für eine Instanz mit den Kosten $c_m$ der Verfahren $m \in \mathcal M$ (bis $n = 9$ zusätzlich dem Optimum): $b = \min_m c_m$ und $\mathrm{Bedauern}_m = (c_m - b)/b \ge 0$. Ab $n = 12$ gilt $b \ge \mathrm{OPT}$, also ist das Bedauern eine obere Grenze von $(c_m - \mathrm{OPT})/\mathrm{OPT}$ nur im Sinne $\mathrm{Bedauern}_m \le (c_m-\mathrm{OPT})/\mathrm{OPT}$.

**Kante.** Verfahren $m$ liegt auf der Kante, wenn kein $m'$ zugleich einen Median der Zeit $\le$ dem von $m$ und ein mittleres Bedauern $<$ dem von $m$ hat (Pareto-Kante, nach Zeit sortiert und streng fallendem Bedauern gelesen).

**Gepaarter Unterschied.** $d_k = 100\,(c^{A}_k - c^{N}_k)/b_k$ je Instanz $k$ (Annealing $A$ gegen 20 Neustarts $N$), Mittel $\bar d$ und Standardfehler $\hat\sigma_d/\sqrt{K}$. Die Instanzen einer Größe sind nicht unabhängig (gleiche Seeds in mehreren Pad-Zahlen), der Standardfehler ist deshalb eine Näherung.

**Die Regel.** Eine Funktion $(n, \text{Aufgabe}, \text{Zeitbudget}) \mapsto$ Verfahren; sie liest weder Familie noch Pad-Zahl noch Kosten. Auf frischen Instanzen wird ihr mittleres Bedauern verglichen mit $\min(c^N_k, c^A_k)$ je Instanz.

**Aufwand.** Zeit $t$ in Sekunden (Messung); Zählungen: Bewertungen (Kosten einer Anordnung), Runden der Schleife, Auswertungen von Länge und Dichte samt Gradient, Knoten des Baums.

**Literatur.** Die Verfahren und Schranken stehen in den Stücken 3 bis 12 mit ihren Quellen; Angaben der Literatur zur Größe exakter Verfahren sind hier **nicht nachgelesen** und nicht übernommen. Alle Zahlen sind eigene Rechnungen an eigenen, erfundenen Familien und Pads, geprüft durch Tests
(Aufzählung aller Anordnungen, Handbeispiel, Schranke gegen Optimum, Branch and Bound gegen Aufzählung).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
