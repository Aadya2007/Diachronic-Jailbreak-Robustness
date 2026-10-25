"""
Step 3: Benchmark Evaluation Harness for Jailbreak Detectors
Evaluates detector robustness degradation across:
  - Condition 1: Contemporary Baseline (In-Distribution Reference)
  - Condition 2: Historical / Diachronic Shift (Victorian English)
  - Condition 3: Socio-Regional Shift (Colloquial Indian English)
  - Condition 4: Combined Shift (Colonial Regional Administrative)

Detector Architectures Evaluated:
  1. Word N-gram TF-IDF + Logistic Regression (Lexical Surface Baseline)
  2. Word N-gram TF-IDF + LinearSVC (Linear Margin Support Vector Classifier)
  3. Subword Char N-gram (3-5) + Logistic Regression (Subword Tokenization Proxy)
  4. Subword Char N-gram + Linear Margin (Subword Margin Classifier)

Metrics Computed:
  - AU-ROC, F1-Score, Precision, Recall
  - False Positive Rate (FPR: Over-refusal on benign hard negatives)
  - False Negative Rate (FNR: Evasion on malicious jailbreaks)
  - Degradation Deltas (Delta_AUC, Delta_FPR, Delta_FNR relative to baseline)
  - McNemar's Paired Chi-Square Test (Statistical significance of prediction flip)
"""

import sys
import os
import csv
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
from scipy.stats import chi2

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def mcnemar_test(y_true, y_pred_base, y_pred_shifted):
    """Computes McNemar's test with continuity correction on paired binary predictions."""
    correct_base = (y_pred_base == y_true)
    correct_shift = (y_pred_shifted == y_true)
    
    b = np.sum(correct_base & ~correct_shift)
    c = np.sum(~correct_base & correct_shift)
    
    if (b + c) == 0:
        return 0.0, 1.0
    stat = ((abs(b - c) - 1.0) ** 2) / (b + c)
    p_val = chi2.sf(stat, 1)
    return float(stat), float(p_val)

def evaluate_predictions(y_true, y_prob, y_pred):
    """Computes full suite of classification and calibration metrics."""
    try:
        auc = roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else 0.5
    except Exception:
        auc = 0.5
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return {
        "auc": round(float(auc), 4),
        "f1": round(float(f1), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "fpr": round(float(fpr), 4),
        "fnr": round(float(fnr), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    }

def run_evaluation(benchmark_csv_path="data/benchmark_shifted_eval.csv"):
    print("="*75)
    print("STEP 3: JAILBREAK DETECTOR ROBUSTNESS EVALUATION PIPELINE")
    print("="*75)
    
    with open(benchmark_csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    print(f"Loaded {len(rows)} benchmark instances from {benchmark_csv_path}")
    
    by_condition = {"baseline": [], "historical": [], "regional": [], "combined": []}
    for r in rows:
        cond = r["condition"].lower()
        if cond in by_condition:
            by_condition[cond].append(r)
            
    base_rows = by_condition["baseline"]
    print(f"Condition splits: Baseline={len(base_rows)}, Historical={len(by_condition['historical'])}, "
          f"Regional={len(by_condition['regional'])}, Combined={len(by_condition['combined'])}")
    
    base_texts = [r["prompt_text"] for r in base_rows]
    base_y = np.array([int(r["ground_truth_binary"]) for r in base_rows])
    
    print(f"Class distribution: {np.sum(base_y == 1)} Malicious, {np.sum(base_y == 0)} Benign Hard Negatives")
    
    # Feature Extractors & Detector Models
    print("\nFitting feature extractors on Condition 1 (Contemporary Baseline)...")
    
    word_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=1500, min_df=1)
    X_base_word = word_vec.fit_transform(base_texts)
    
    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=3000, min_df=1)
    X_base_char = char_vec.fit_transform(base_texts)
    
    models = {
        "Word TF-IDF + Logistic Regression": {
            "vec": word_vec,
            "clf": LogisticRegression(C=1.0, max_iter=1000, random_state=42),
            "fit_X": X_base_word,
            "has_prob": True
        },
        "Word TF-IDF + LinearSVC": {
            "vec": word_vec,
            "clf": LinearSVC(C=1.0, max_iter=2000, random_state=42),
            "fit_X": X_base_word,
            "has_prob": False
        },
        "Subword Char N-gram + Logistic Regression": {
            "vec": char_vec,
            "clf": LogisticRegression(C=1.0, max_iter=1000, random_state=42),
            "fit_X": X_base_char,
            "has_prob": True
        },
        "Subword Char N-gram + Linear Margin": {
            "vec": char_vec,
            "clf": RidgeClassifier(alpha=1.0, random_state=42),
            "fit_X": X_base_char,
            "has_prob": False
        }
    }
    
    for name, m_info in models.items():
        m_info["clf"].fit(m_info["fit_X"], base_y)
        
    print("All detector baselines successfully trained on contemporary distribution.\n")
    
    results = {}
    
    for name, m_info in models.items():
        print("="*75)
        print(f"EVALUATING MODEL: {name}")
        print("="*75)
        
        clf = m_info["clf"]
        vec = m_info["vec"]
        has_prob = m_info["has_prob"]
        
        clf_results = {}
        base_preds = None
        
        for condition in ["baseline", "historical", "regional", "combined"]:
            cond_data = by_condition[condition]
            texts = [r["prompt_text"] for r in cond_data]
            y_true = np.array([int(r["ground_truth_binary"]) for r in cond_data])
            
            X = vec.transform(texts)
            
            if has_prob:
                y_prob = clf.predict_proba(X)[:, 1]
                y_pred = (y_prob >= 0.5).astype(int)
            else:
                dec = clf.decision_function(X)
                y_prob = 1 / (1 + np.exp(-dec))
                y_pred = (dec >= 0).astype(int)
                
            eval_metrics = evaluate_predictions(y_true, y_prob, y_pred)
            
            if condition == "baseline":
                base_preds = y_pred
                eval_metrics["mcnemar_stat"] = 0.0
                eval_metrics["mcnemar_pval"] = 1.0
                eval_metrics["delta_auc"] = 0.0
                eval_metrics["delta_fpr"] = 0.0
                eval_metrics["delta_fnr"] = 0.0
            else:
                stat, pval = mcnemar_test(y_true, base_preds, y_pred)
                eval_metrics["mcnemar_stat"] = round(stat, 3)
                eval_metrics["mcnemar_pval"] = round(pval, 4)
                eval_metrics["delta_auc"] = round(clf_results["baseline"]["auc"] - eval_metrics["auc"], 4)
                eval_metrics["delta_fpr"] = round(eval_metrics["fpr"] - clf_results["baseline"]["fpr"], 4)
                eval_metrics["delta_fnr"] = round(eval_metrics["fnr"] - clf_results["baseline"]["fnr"], 4)
                
            clf_results[condition] = eval_metrics
            
            print(f"  Condition [{condition.upper():10s}]: "
                  f"AU-ROC = {eval_metrics['auc']:.3f} (d_AUC={eval_metrics.get('delta_auc', 0.0):+.3f}) | "
                  f"F1 = {eval_metrics['f1']:.3f} | "
                  f"FPR = {eval_metrics['fpr']:.3f} (d_FPR={eval_metrics.get('delta_fpr', 0.0):+.3f}) | "
                  f"FNR = {eval_metrics['fnr']:.3f} (d_FNR={eval_metrics.get('delta_fnr', 0.0):+.3f}) | "
                  f"McNemar p={eval_metrics.get('mcnemar_pval', 1.0):.4f}")
                  
        results[name] = clf_results
        
    os.makedirs("reports", exist_ok=True)
    out_json = "reports/detector_robustness_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "="*75)
    print(f"Step 3 complete! Empirical results saved to {out_json}")
    print("="*75)
    return results

if __name__ == "__main__":
    run_evaluation()
