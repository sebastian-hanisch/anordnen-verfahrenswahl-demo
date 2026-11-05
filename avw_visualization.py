"""Plotly-Abbildungen. Alle 2D-Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import avw_constants as C



def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend_below=True):
    legend = dict(orientation="h", yanchor="top", y=-0.22, x=0) if legend_below else dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    fig.update_layout(height=height + (40 if legend_below else 0), margin=dict(l=10, r=10, t=50, b=10), legend=legend, plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _slots(inst):
    return go.Scatter(x=inst.xy[:, 0].astype(float), y=-inst.xy[:, 1].astype(float), mode="markers", marker=dict(symbol="square", size=34, color="rgba(150,150,150,0.14)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False)


def _pads(pads):
    return go.Scatter(x=pads.pos[:, 0], y=-pads.pos[:, 1], mode="markers", name="Pads", marker=dict(symbol="diamond", size=12, color=C.COLORS["pad"], line=dict(width=1, color="white")), hovertemplate="Pad<extra></extra>")


def _region(fig, bins, row=None, col=None):
    x0, x1, y0, y1 = bins.region
    kw = {} if row is None else dict(row=row, col=col)
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=-y1, y1=-y0, line=dict(color="rgba(76,120,168,0.7)", width=1.5, dash="dot"), **kw)


def build_arrangement(inst, perm, title: str) -> go.Figure:
    """Die gerundete Anordnung: Bauteile auf den Plätzen, Verbindungen mit Fluss als Linien."""
    fig = go.Figure()
    xs, ys = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    pos = [(xs[int(perm[i])], ys[int(perm[i])]) for i in range(inst.n)]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(symbol="square", size=36, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False))
    lx, ly = [], []
    for a in range(inst.n):
        for b in range(a + 1, inst.n):
            if inst.F[a, b]:
                lx += [pos[a][0], pos[b][0], None]
                ly += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(width=1.5, color="rgba(76,120,168,0.35)"), hoverinfo="skip", name="Fluss"))
    fig.add_trace(go.Scatter(x=[q[0] for q in pos], y=[q[1] for q in pos], mode="markers+text", text=list(inst.names), textposition="middle center", showlegend=False, marker=dict(size=26, color=C.COLORS["best"]), textfont=dict(color="white", size=10)))
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[xs.min() - 0.7, xs.max() + 0.7], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[ys.min() - 0.7, ys.max() + 0.7])
    return _base(fig, height=300)


GROUP_COLORS = {"rel": "#9c755f", "elektro": "#b08a2e", "abs": "#8e6bb0", "neu": "#2F6B65", "sa": "#4c78a8"}
GROUP_OF = {"rund": "rel", "schleife": "rel", "elektro": "elektro", "elektro_b": "elektro", "abs_z": "abs", "abs_r": "abs", "abs_s": "abs", "abs_e": "abs", "neu6": "neu", "neu20": "neu", "sa_s": "sa"}
GROUP_NAMES = {"rel": "Relaxation und Rundung (Stück 9, 10)", "elektro": "Dichtestrafe (Stück 11)", "abs": "Tauschabstieg (Stück 12)", "neu": "Neustarts (Stück 12)", "sa": "Schleife und Annealing (Stück 10, 12)"}


SHORT = {"rund": "Runden", "schleife": "Schleife", "elektro": "Dichte, letzte", "elektro_b": "Dichte, billigste", "abs_z": "Abstieg Zufall", "abs_r": "Abstieg Rundung", "abs_s": "Abstieg Schleife", "abs_e": "Abstieg Dichte",
         "neu6": "6 Neustarts", "neu20": "20 Neustarts", "sa_s": "Schleife + Annealing"}


def _short(k: str) -> str:
    """Kurzer Name für die Beschriftung der Punkte."""
    return SHORT[k]


def _positions(n: int) -> list:
    """Beschriftungen abwechselnd über und unter dem Punkt, damit dicht liegende Punkte lesbar bleiben."""
    return ["top center" if i % 2 == 0 else "bottom center" for i in range(n)]


def build_methods(v: dict, rec: str, title: str) -> go.Figure:
    """Alle Verfahren auf einer Instanz: Rechenzeit (logarithmisch) gegen Bedauern in Prozent; die Empfehlung der Regel ist hervorgehoben."""
    fig = go.Figure()
    for g, color in GROUP_COLORS.items():
        ks = [k for k in C.FIND_KEYS if GROUP_OF[k] == g]
        fig.add_trace(go.Scatter(x=[max(v["sec"][k], 1e-4) for k in ks], y=[100 * v["gap"][k] for k in ks], mode="markers+text", text=[_short(k) for k in ks], textposition=_positions(len(ks)), name=GROUP_NAMES[g],
                                 marker=dict(size=12, color=color), customdata=[[v["cost"][k]] for k in ks], hovertemplate="%{text}<br>Zeit %{x:.3f} s<br>Bedauern %{y:.2f} %<br>Kosten %{customdata[0]:.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[max(v["sec"][rec], 1e-4)], y=[100 * v["gap"][rec]], mode="markers", name="Empfehlung der Regel", marker=dict(size=24, symbol="circle-open", color="#c0504d", line=dict(width=3))))
    fig.update_layout(title=title)
    fig.update_xaxes(type="log", title="Rechenzeit in s (Messung dieser Fassung)")
    fig.update_yaxes(title="Bedauern in %", rangemode="tozero")
    return _base(fig, height=420)


def build_restart_curve(v: dict) -> go.Figure:
    """Die besten Kosten nach 1 bis 20 Neustarts, dazu die Kosten von Schleife mit Annealing und der Vergleichswert."""
    fig = go.Figure()
    ks = list(range(1, len(v["curve"]) + 1))
    fig.add_trace(go.Scatter(x=ks, y=[b for _, b, _ in v["curve"]], mode="lines+markers", name="beste Kosten nach k Neustarts", line=dict(color=GROUP_COLORS["neu"]), marker=dict(size=7)))
    fig.add_hline(y=v["cost"]["sa_s"], line=dict(color=GROUP_COLORS["sa"], dash="dash"), annotation_text="Schleife mit Annealing", annotation_position="top right")
    fig.add_hline(y=v["best"], line=dict(color="#c0504d", dash="dot"), annotation_text="Vergleichswert", annotation_position="bottom right")
    fig.update_layout(title="Neustarts: beste Kosten nach k Abstiegen aus Zufall")
    fig.update_xaxes(title="Zahl der Neustarts", dtick=2)
    fig.update_yaxes(title="Kosten")
    return _base(fig, height=320)


def build_prove_bounds(v: dict, title: str) -> go.Figure:
    """Schranken gegen Optimum und beste Abstiege: je Schranke ein Balken, senkrechte Linien für das beste Abstiegsergebnis und das Optimum."""
    keys = [k for k in C.BOUND_KEYS if k in v["bound"]]
    fig = go.Figure(go.Bar(y=[C.BOUND_NAMES[k] for k in keys], x=[v["bound"][k] for k in keys], orientation="h", marker_color="#4c78a8", text=[f"{v['bound'][k]:.1f}" for k in keys], textposition="outside", name="Schranke"))
    fig.add_vline(x=v["ub200"], line=dict(color="#2F6B65", dash="dash"), annotation_text="beste von 200 Abstiegen", annotation_position="top")
    if v["opt"] is not None and v["opt"] != v["ub200"]:
        fig.add_vline(x=v["opt"], line=dict(color="#c0504d", dash="dot"), annotation_text="Optimum", annotation_position="bottom")
    lo = min(v["bound"].values())
    fig.update_xaxes(range=[lo * 0.8, max(v["ub200"], max(v["bound"].values())) * 1.08], title="Kosten")
    fig.update_layout(title=title, showlegend=False)
    return _base(fig, height=260, legend_below=False)


def build_prove_nodes(rows_by_n: dict, title: str) -> go.Figure:
    """Knoten des Baums je Instanz (logarithmisch), je Größe zwei Kästen: Gilmore–Lawler und lineare Knotenschranken (nur bis n = 9)."""
    fig = go.Figure()
    for art, color in (("glb", "#2F6B65"), ("lin", "#b08a2e")):
        xs, ys = [], []
        for n in sorted(rows_by_n):
            for r in rows_by_n[n]:
                if art in r["tree"]:
                    xs.append(f"n = {n}")
                    ys.append(max(r["tree"][art]["nodes"], 1))
        fig.add_trace(go.Box(x=xs, y=ys, name=C.TREE_NAMES[art], marker_color=color, boxpoints="all", jitter=0.4, pointpos=0))
    fig.update_layout(title=title, boxmode="group")
    fig.update_yaxes(type="log", title="bewertete Knoten")
    return _base(fig, height=380)


def build_bound_gaps(rows_by_n: dict, bound_gap, title: str) -> go.Figure:
    fig = go.Figure()
    for k, color in (("glb", "#4c78a8"), ("da5", "#8e6bb0"), ("lp", "#2F6B65")):
        ns = [n for n in sorted(rows_by_n) if any(k in r["bound"] for r in rows_by_n[n])]
        vals = [bound_gap(rows_by_n[n], k)["median"] for n in ns]
        fig.add_trace(go.Bar(x=[f"n = {n}" for n in ns], y=vals, name=C.BOUND_NAMES[k], marker_color=color, text=[f"{x:.1f} %" for x in vals], textposition="outside"))
    fig.update_layout(title=title, barmode="group")
    fig.update_yaxes(title="Lücke zum Optimum in % (Median)", rangemode="tozero")
    return _base(fig, height=340)


def build_regret_bars(rows: list, regret_stats, title: str) -> go.Figure:
    """Mittleres Bedauern je Verfahren (Balken) und Median (Raute)."""
    ks = list(C.FIND_KEYS)
    st = {k: regret_stats(rows, k) for k in ks}
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[C.FIND_NAMES[k] for k in ks], y=[100 * st[k]["mean"] for k in ks], name="Mittel", marker_color=[GROUP_COLORS[GROUP_OF[k]] for k in ks], text=[f"{100 * st[k]['mean']:.1f}" for k in ks], textposition="outside"))
    fig.add_trace(go.Scatter(x=[C.FIND_NAMES[k] for k in ks], y=[100 * st[k]["median"] for k in ks], mode="markers", name="Median", marker=dict(symbol="diamond", size=10, color="white", line=dict(width=2, color="#333"))))
    fig.update_layout(title=title)
    fig.update_yaxes(title="Bedauern in %", rangemode="tozero")
    fig.update_xaxes(tickangle=-35)
    return _base(fig, height=420)


def build_front(rows: list, regret_stats, front, title: str) -> go.Figure:
    """Mediane Zeit gegen mittleres Bedauern je Verfahren; die Kante (kein Verfahren zugleich schneller und besser) ist verbunden."""
    fig = go.Figure()
    st = {k: regret_stats(rows, k) for k in C.FIND_KEYS}
    kante = front(rows)
    for g, color in GROUP_COLORS.items():
        ks = [k for k in C.FIND_KEYS if GROUP_OF[k] == g]
        fig.add_trace(go.Scatter(x=[max(st[k]["sec"], 1e-4) for k in ks], y=[100 * st[k]["mean"] for k in ks], mode="markers+text", text=[_short(k) for k in ks], textposition=_positions(len(ks)), name=GROUP_NAMES[g], marker=dict(size=12, color=color)))
    fig.add_trace(go.Scatter(x=[max(st[k]["sec"], 1e-4) for k in kante], y=[100 * st[k]["mean"] for k in kante], mode="lines", line=dict(color="rgba(192,80,77,0.7)", dash="dot", shape="hv"), name="Kante", hoverinfo="skip"))
    fig.update_layout(title=title)
    fig.update_xaxes(type="log", title="Median der Rechenzeit in s (Messung dieser Fassung)")
    fig.update_yaxes(title="mittleres Bedauern in %", rangemode="tozero")
    return _base(fig, height=440)


def build_cross(rows_by_n: dict, regret_stats, title: str = "Neustarts gegen Schleife mit Annealing") -> go.Figure:
    """Oben das mittlere Bedauern, unten der Median der Zeit von 20 Neustarts und Schleife mit Annealing über die Größe."""
    ns = sorted(rows_by_n)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=("mittleres Bedauern in %", "Median der Rechenzeit in s (logarithmisch)"))
    for k, color in (("neu20", GROUP_COLORS["neu"]), ("sa_s", GROUP_COLORS["sa"])):
        st = [regret_stats(rows_by_n[n], k) for n in ns]
        fig.add_trace(go.Scatter(x=ns, y=[100 * s["mean"] for s in st], mode="lines+markers", name=C.FIND_NAMES[k], line=dict(color=color), legendgroup=k), row=1, col=1)
        fig.add_trace(go.Scatter(x=ns, y=[max(s["sec"], 1e-4) for s in st], mode="lines+markers", name=C.FIND_NAMES[k], line=dict(color=color), legendgroup=k, showlegend=False), row=2, col=1)
    fig.update_yaxes(type="log", row=2, col=1)
    fig.update_xaxes(title="Bauteile n", tickvals=ns, row=2, col=1)
    fig.update_layout(title=title)
    return _base(fig, height=520)


def build_rule_bars(by_n: dict, rule_regret, title: str) -> go.Figure:
    ns = sorted(by_n)
    rr = [rule_regret(by_n[n]) for n in ns]
    fig = go.Figure()
    for key, name, color in (("rule", "Regel", "#c0504d"), ("neu20", "immer 20 Neustarts", GROUP_COLORS["neu"]), ("sa_s", "immer Schleife mit Annealing", GROUP_COLORS["sa"]), ("oracle2", "bestes der beiden je Instanz", "#9aa0a6")):
        fig.add_trace(go.Bar(x=[f"n = {n}" for n in ns], y=[100 * r[key] for r in rr], name=name, marker_color=color))
    fig.update_layout(title=title, barmode="group")
    fig.update_yaxes(title="mittleres Bedauern in %", rangemode="tozero")
    return _base(fig, height=380)
