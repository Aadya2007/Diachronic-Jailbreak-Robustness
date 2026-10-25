import json

with open('reports/scaled_step2_results.json', 'r') as f:
    res = json.load(f)

print("="*95)
print("SCALED EXPERIMENTAL RESULTS (N=100 Benign, N=100 Malicious per condition)")
print("Training Set: 800 prompts (400 Malicious, 400 Benign)")
print("Held-out Test: 200 base prompts x 5 conditions = 1,000 evaluated instances")
print("="*95)

for model_name, conds in res.items():
    print(f"\nMODEL: {model_name}")
    print(f"{'Condition':<18} | {'AU-ROC':<7} | {'F1':<7} | {'Prec':<7} | {'Recall':<7} | {'FPR':<7} | {'95% CI':<16} | {'McNemar p':<10}")
    print("-" * 95)
    for c_name, m in conds.items():
        ci_str = f"[{m['fpr_ci'][0]:.2f}, {m['fpr_ci'][1]:.2f}]"
        print(f"{c_name:<18} | {m['auc']:<7.3f} | {m['f1']:<7.3f} | {m['precision']:<7.3f} | {m['recall']:<7.3f} | {m['fpr']:<7.3f} | {ci_str:<16} | {m['mcnemar_p']:<10}")
