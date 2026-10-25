import json

with open("reports/per_prompt_balanced_predictions.json", "r", encoding="utf-8") as f:
    preds = json.load(f)

for cond in ["historical", "regional", "combined"]:
    cond_preds = [p for p in preds if p["condition"] == cond]
    w_lr_flagged = [p["prompt_id"] for p in cond_preds if p["Word_LogReg"] == 1]
    w_svc_flagged = [p["prompt_id"] for p in cond_preds if p["Word_LinearSVC"] == 1]
    c_lr_flagged = [p["prompt_id"] for p in cond_preds if p["Char_LogReg"] == 1]
    c_rd_flagged = [p["prompt_id"] for p in cond_preds if p["Char_Ridge"] == 1]
    
    print(f"=== Condition: {cond.upper()} ===")
    print(f"Word LogReg:    {w_lr_flagged}")
    print(f"Word LinearSVC: {w_svc_flagged}")
    print(f"  Same Word prompts? {w_lr_flagged == w_svc_flagged}")
    print(f"Char LogReg:    {c_lr_flagged}")
    print(f"Char Ridge:     {c_rd_flagged}")
    print(f"  Same Char prompts? {c_lr_flagged == c_rd_flagged}")
    print(f"  Word vs Char same? {w_lr_flagged == c_lr_flagged}")
