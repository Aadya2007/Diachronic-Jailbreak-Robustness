import json

with open('reports/scaled_threshold_recalibration.json', 'r') as f:
    recal = json.load(f)

print("="*95)
print("THRESHOLD RECALIBRATION FINDINGS (Default Tau=0.50 vs Optimal Tau*)")
print("Shows how recalibrating the decision threshold restores the Pareto frontier")
print("="*95)

for model_name, conds in recal.items():
    print(f"\nMODEL: {model_name}")
    print(f"{'Condition':<15} | {'Def FPR':<8} | {'Def Rec':<8} | {'Opt Tau*':<9} | {'Opt FPR':<8} | {'Opt Rec':<8} | {'Opt F1':<8}")
    print("-" * 80)
    for c_name, data in conds.items():
        print(f"{c_name:<15} | {data['default_fpr']:<8.3f} | {data['default_recall']:<8.3f} | {data['optimal_tau']:<9.2f} | {data['optimal_fpr']:<8.3f} | {data['optimal_recall']:<8.3f} | {data['optimal_f1']:<8.3f}")
