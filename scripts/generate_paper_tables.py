"""
Generate Paper Tables (LaTeX and Markdown)
Reads reports/detector_robustness_results.json and produces publication-ready
LaTeX tables and Markdown comparison summaries for the research manuscript.
"""

import json
import os

results_path = "reports/detector_robustness_results.json"

def format_latex_tables():
    if not os.path.exists(results_path):
        print(f"Results file {results_path} not found yet. Run evaluate_detectors.py first.")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ----------------------------------------------------
    # Table 1: Main Performance Matrix (AUC, F1, FPR, FNR)
    # ----------------------------------------------------
    latex_table1 = []
    latex_table1.append(r"\begin{table*}[t]")
    latex_table1.append(r"\centering")
    latex_table1.append(r"\small")
    latex_table1.append(r"\begin{tabular}{llcccccc}")
    latex_table1.append(r"\toprule")
    latex_table1.append(r"\textbf{Detector Model} & \textbf{Evaluation Condition} & \textbf{AU-ROC} & \textbf{F1-Score} & \textbf{Precision} & \textbf{Recall} & \textbf{FPR (Over-refusal)} & \textbf{McNemar $p$} \\")
    latex_table1.append(r"\midrule")

    for model_name, conditions in data.items():
        latex_table1.append(f"\\multirow{{4}}{{*}}{{\\textbf{{{model_name}}}}} ")
        for cond_key, label in [
            ("baseline", "Condition 1: Baseline (Contemporary)"),
            ("historical", "Condition 2: Diachronic Shift (Victorian)"),
            ("regional", "Condition 3: Socio-Regional Shift (Indian Eng.)"),
            ("combined", "Condition 4: Combined Shift (Colonial Admin.)")
        ]:
            m = conditions.get(cond_key, {})
            auc = f"{m.get('auc', 0.0):.3f}"
            f1 = f"{m.get('f1', 0.0):.3f}"
            prec = f"{m.get('precision', 0.0):.3f}"
            rec = f"{m.get('recall', 0.0):.3f}"
            fpr = f"{m.get('fpr', 0.0):.3f}"
            pval = f"{m.get('mcnemar_pval', 1.0):.4f}" if cond_key != "baseline" else "---"
            latex_table1.append(f" & {label} & {auc} & {f1} & {prec} & {rec} & {fpr} & {pval} \\\\")
        latex_table1.append(r"\midrule")

    # Remove last midrule and close
    latex_table1.pop()
    latex_table1.append(r"\bottomrule")
    latex_table1.append(r"\end{tabular}")
    latex_table1.append(r"\caption{Jailbreak detector classification and false-positive performance across Contemporary, Historical, Regional, and Combined distribution shifts.}")
    latex_table1.append(r"\label{tab:main_results}")
    latex_table1.append(r"\end{table*}")

    out_tex_path = "reports/table_main_results.tex"
    with open(out_tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_table1))

    # ----------------------------------------------------
    # Table 2: Degradation Deltas (ΔAUC, ΔFPR, ΔFNR)
    # ----------------------------------------------------
    latex_table2 = []
    latex_table2.append(r"\begin{table}[t]")
    latex_table2.append(r"\centering")
    latex_table2.append(r"\small")
    latex_table2.append(r"\begin{tabular}{llccc}")
    latex_table2.append(r"\toprule")
    latex_table2.append(r"\textbf{Detector Model} & \textbf{Shift Type} & $\Delta$\textbf{AU-ROC} $\downarrow$ & $\Delta$\textbf{FPR (False Alarms)} $\uparrow$ & $\Delta$\textbf{FNR (Evasions)} $\uparrow$ \\")
    latex_table2.append(r"\midrule")

    for model_name, conditions in data.items():
        for cond_key, label in [
            ("historical", "Diachronic (Historical)"),
            ("regional", "Socio-Regional (Dialectal)"),
            ("combined", "Combined (Hist + Reg)")
        ]:
            m = conditions.get(cond_key, {})
            d_auc = f"{m.get('delta_auc', 0.0):+.3f}"
            d_fpr = f"{m.get('delta_fpr', 0.0):+.3f}"
            d_fnr = f"{m.get('delta_fnr', 0.0):+.3f}"
            latex_table2.append(f"{model_name} & {label} & {d_auc} & {d_fpr} & {d_fnr} \\\\")
        latex_table2.append(r"\midrule")

    latex_table2.pop()
    latex_table2.append(r"\bottomrule")
    latex_table2.append(r"\end{tabular}")
    latex_table2.append(r"\caption{Performance degradation deltas relative to contemporary baseline. Positive $\Delta$FPR indicates increased false alarms on benign prompts; positive $\Delta$FNR indicates increased adversarial evasion.}")
    latex_table2.append(r"\label{tab:degradation_deltas}")
    latex_table2.append(r"\end{table}")

    out_tex_path2 = "reports/table_degradation_deltas.tex"
    with open(out_tex_path2, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_table2))

    print(f"Generated LaTeX tables:\n  • {out_tex_path}\n  • {out_tex_path2}")

if __name__ == "__main__":
    format_latex_tables()
