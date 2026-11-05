"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import avw_constants as C
import avw_rule as R
from avw_evaluation import Settings, count, de, num, pct, secs, work_text

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "³": "3", "⁻": "-", "¹": "1", "½": "1/2", "⁴": "4", "λ": "lambda", "ρ": "rho", "ψ": "psi"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def _table(pdf, widths, header, rows):
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, header):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for row in rows:
        for w, x in zip(widths, row):
            pdf.cell(w, 5.5, _s(x), border=1)
        pdf.ln()


def build_pdf(s: Settings, v: dict) -> bytes:
    """`v`: das Ergebnis von `solve_find` (Aufgabe finden) oder `solve_prove` (Aufgabe beweisen)."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Verfahrenswahl beim Anordnen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    inst = v["inst"]
    adv = R.advise(s.n, s.task, s.budget)
    pads = "reine Zuordnung ohne Pads" if s.task == "prove" else f"{s.pads} Pads"
    pdf.multi_cell(0, 5, _s(f"Familie {C.FAMILY_NAMES[s.family]}, {s.n} Bauteile, {inst.rows}x{inst.cols}-Raster, Seed {s.seed}; {pads}; Aufgabe {C.TASK_NAMES[s.task]}; Zeitbudget {C.BUDGET_NAMES[s.budget]}. "
                            "Eine Instanz, kein Befund über die Familie. Erfundene Pads und Familien. Zeiten sind Messungen dieser Python-Fassung auf einem Rechner; Zählungen haben verschiedene Einheiten. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _s("Entscheidungsweg"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for st in adv.steps:
        pdf.multi_cell(0, 4.5, _s(f"- {st.question} {st.answer} ({st.piece})"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    if s.task == "find":
        rows = [(f"{C.FIND_NAMES[k]} ({C.FIND_PIECE[k]})", num(v["cost"][k]), pct(v["gap"][k], 1), secs(v["sec"][k]), work_text(v["work"][k])) for k in C.FIND_KEYS]
        _table(pdf, (58, 22, 22, 22, 66), ("Verfahren", "Kosten", "Bedauern", "Zeit", "Zählung"), rows)
        pdf.ln(3)
        ref = "Optimum (aufgezählt)" if v["exact"] else "Bestes Ergebnis aller Verfahren"
        pdf.multi_cell(0, 5, _s(f"{ref}: {num(v['best'])}. Empfehlung der Regel: {adv.label}, Kosten {num(v['cost'][adv.find])}, Bedauern {pct(v['gap'][adv.find], 1)}, {secs(v['sec'][adv.find])}."), new_x="LMARGIN", new_y="NEXT")
    else:
        rows = [(C.BOUND_NAMES[k], de(v["bound"][k], 1), pct((v["ref"] - v["bound"][k]) / v["ref"], 1), secs(v["sec"][k])) for k in C.BOUND_KEYS if k in v["bound"]]
        rows.append(("20 Abstiege aus Zufall", num(v["ub20"]), "", secs(v["sec"]["ub20"])))
        rows.append((f"{C.PROVE_STARTS} Abstiege aus Zufall", num(v["ub200"]), "", secs(v["sec"]["ub200"])))
        for art in v["tree"]:
            tr = v["tree"][art]
            rows.append((C.TREE_NAMES[art], num(tr["best"]) + (" (nicht bewiesen)" if tr["capped"] else ""), f"{count(tr['nodes'])} Knoten", secs(tr["sec"])))
        _table(pdf, (70, 40, 40, 30), ("Verfahren", "Wert", "Lücke / Knoten", "Zeit"), rows)
        pdf.ln(3)
        pdf.multi_cell(0, 5, _s("Optimum bewiesen: " + (num(v["opt"]) if v["opt"] is not None else "nein (Obergrenze erreicht oder nicht gerechnet)") + "."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: anordnen-verfahrenswahl-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
