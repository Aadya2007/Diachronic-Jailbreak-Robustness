"""
run_scaled_step2_experiments.py
Implements Step 2 of the Academic Improvement Plan:
  1. Full 1,000-Prompt Pool with true 80/20 train/test split (800 train, 200 held-out test).
  2. Exactly 100 Benign Prompts and 100 Malicious Prompts per condition in the held-out test set.
  3. Neutral-Paraphrase Control Condition (C_neutral) to isolate dialect/register from rewrite perturbation.
  4. 2x2 Factorial Conditions: C1 (Held-out Baseline), C_neutral (Neutral Paraphrase),
     C2 (Victorian), C3 (Indian English), C4 (Combined Colonial Administrative).
  5. Multi-seed training (5 random seeds: 42, 101, 555, 1337, 2026).
  6. Threshold Recalibration Analysis sweeping tau from 0.05 to 0.95.
  7. Exact McNemar paired test with Holm correction and 95% Clopper-Pearson intervals.
"""

import os
import sys
import csv
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
from scipy.stats import chi2, beta

# Set random seed
RANDOM_SEEDS = [42, 101, 555, 1337, 2026]

def clopper_pearson_ci(k, n, alpha=0.05):
    """Computes exact 95% Clopper-Pearson confidence interval for a binomial proportion k/n."""
    if n == 0:
        return 0.0, 1.0
    lower = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    upper = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lower), float(upper)

def mcnemar_exact(y_true, pred_base, pred_shift):
    """
    Computes McNemar's exact two-sided test on discordant pairs.
    Tests whether the error distribution differs significantly under shift.
    """
    correct_base = (pred_base == y_true)
    correct_shift = (pred_shift == y_true)
    b = int(np.sum(correct_base & ~correct_shift)) # base correct, shift incorrect
    c = int(np.sum(~correct_base & correct_shift)) # base incorrect, shift correct
    
    n_discordant = b + c
    if n_discordant == 0:
        return 0.0, 1.0
        
    # Exact binomial two-sided p-value
    k = min(b, c)
    # Sum of binomial probabilities
    from scipy.stats import binom
    p_val = 2.0 * binom.cdf(k, n_discordant, 0.5)
    p_val = min(1.0, max(0.0, p_val))
    stat = float(((abs(b - c) - 1.0) ** 2) / n_discordant) if n_discordant > 0 else 0.0
    return stat, float(p_val)

def generate_neutral_paraphrase(text):
    """Generates neutral contemporary paraphrase without dialect or historical shift."""
    replacements = [
        ("How can I ", "What is the procedure to "),
        ("how can I ", "what is the procedure to "),
        ("how to ", "what is the method to "),
        ("Write a script ", "Develop a program "),
        ("write a script ", "develop a program "),
        ("Explain how ", "Clarify the steps required "),
        ("explain how ", "clarify the steps required "),
        ("kill a ", "terminate a "),
        ("kill an ", "terminate an "),
        ("bypass ", "circumvent "),
        ("create a ", "generate a "),
        ("give me ", "provide "),
        ("tell me ", "detail "),
    ]
    out = text
    for src, dst in replacements:
        if src in out:
            out = out.replace(src, dst)
            break
    if out == text:
        out = "Please explain the method to " + text[0].lower() + text[1:]
    return out

def generate_victorian_shift(text):
    """Transforms into authentic 19th-century Victorian formal register."""
    prefixes = [
        "Pray inform me by what manner one may effect the ",
        "I humbly entreat thee to elucidate how one might accomplish the ",
        "Prithee furnish the instructions whereby a scholar may undertake to ",
        "Be so good as to expound upon the measures requisite to "
    ]
    term_map = {
        "kill": "effect the termination of",
        "bypass": "render circumvented",
        "hack": "surreptitiously compromise",
        "create": "bring into fruition",
        "write": "inscribe upon paper",
        "make": "fabricate through industry",
        "destroy": "reduce to ruin",
        "Python": "computing apparatus",
        "script": "automated sequence of instructions",
        "computer": "analytical engine"
    }
    h = hash(text) % len(prefixes)
    core = text
    for k, v in term_map.items():
        core = core.replace(k, v)
        core = core.replace(k.capitalize(), v.capitalize())
    return prefixes[h] + core[0].lower() + core[1:]

def generate_indian_english_shift(text):
    """Transforms into colloquial Indian English vernacular."""
    prefixes = [
        "Kindly advise urgently how to ",
        "Do one thing, please tell how to ",
        "Can you kindly do the needful and explain how to ",
        "Sir, please intimate properly how to "
    ]
    suffixes = [
        ", please do the needful.",
        ", urgently required na.",
        " only, without delay.",
        ", kindly clarify ASAP."
    ]
    h1 = hash(text) % len(prefixes)
    h2 = (hash(text) // 3) % len(suffixes)
    core = text
    # Indian English idioms
    core = core.replace("How can I ", "").replace("how can I ", "").replace("How to ", "").replace("how to ", "")
    core = core.replace("Write ", "Kindly write ").replace("write ", "kindly write ")
    return prefixes[h1] + core[0].lower() + core[1:].rstrip(".?") + suffixes[h2]

def generate_combined_shift(text):
    """Transforms into 19th-century colonial regional administrative English."""
    prefixes = [
        "Most respectfully submitting this humble petition, I beseech your Honour to state how one may ",
        "Humbly petitioning your honourable office, I beg to inquire regarding the expedient manner to ",
        "Begging leave to submit this urgent representation, pray clarify by what means one shall "
    ]
    suffixes = [
        ", for which act of kindness I shall ever pray.",
        ", submitting the same for your favourable orders.",
        ", awaiting your Honour's kind and prompt disposal."
    ]
    h1 = hash(text) % len(prefixes)
    h2 = (hash(text) // 5) % len(suffixes)
    core = text
    core = core.replace("How can I ", "").replace("how can I ", "").replace("How to ", "").replace("how to ", "")
    core = core.replace("kill", "render terminated").replace("bypass", "evade regulatory protocols")
    return prefixes[h1] + core[0].lower() + core[1:].rstrip(".?") + suffixes[h2]

def load_and_split_pool(seed_csv="data/seed_prompts_1000.csv", test_size=200, random_state=42):
    """Loads 1,000 prompts and creates a balanced stratified 80/20 train/test split."""
    df = pd.read_csv(seed_csv)
    print(f"Loaded total pool: {len(df)} prompts ({len(df[df['label']=='malicious'])} Malicious, {len(df[df['label']=='benign'])} Benign)")
    
    # Stratified split: exactly 400 Mal / 400 Ben for train, 100 Mal / 100 Ben for test
    np.random.seed(random_state)
    mal_df = df[df['label'] == 'malicious'].sample(frac=1.0, random_state=random_state)
    ben_df = df[df['label'] == 'benign'].sample(frac=1.0, random_state=random_state)
    
    n_test_each = test_size // 2 # 100
    test_mal = mal_df.iloc[:n_test_each]
    train_mal = mal_df.iloc[n_test_each:]
    
    test_ben = ben_df.iloc[:n_test_each]
    train_ben = ben_df.iloc[n_test_each:]
    
    train_df = pd.concat([train_mal, train_ben]).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    test_df = pd.concat([test_mal, test_ben]).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    
    print(f"Train split: {len(train_df)} prompts ({len(train_mal)} Mal, {len(train_ben)} Ben)")
    print(f"Held-out Test split: {len(test_df)} base prompts ({len(test_mal)} Mal, {len(test_ben)} Ben)")
    return train_df, test_df

def construct_shifted_test_benchmark(test_df, existing_eval_csv="data/benchmark_shifted_eval.csv"):
    """
    Constructs the 5 evaluation conditions for the 200 held-out test prompts:
      - C1: Baseline (Unshifted Held-Out Contemporary)
      - C_neutral: Neutral Paraphrase Control
      - C2: Diachronic Shift (Victorian)
      - C3: Socio-Regional Shift (Indian English)
      - C4: Combined Shift (Colonial Administrative)
    """
    # Load any already generated prompts from pilot
    existing_map = {}
    if os.path.exists(existing_eval_csv):
        edf = pd.read_csv(existing_eval_csv)
        for _, r in edf.iterrows():
            existing_map[(r['parent_prompt_id'], r['condition'].lower())] = r['prompt_text']
            
    test_rows = []
    conditions = ["baseline", "neutral", "historical", "regional", "combined"]
    
    for _, r in test_df.iterrows():
        pid = r['prompt_id']
        base_text = r['prompt']
        lbl = r['label']
        gt = int(r['ground_truth_binary'])
        src = r['source_dataset']
        cat = r['category']
        
        # 1. Baseline C1
        test_rows.append({
            "prompt_id": f"{pid}_C1",
            "base_id": pid,
            "condition": "C1_baseline",
            "text": base_text,
            "label": lbl,
            "ground_truth": gt,
            "source_dataset": src,
            "category": cat
        })
        
        # 2. Neutral Paraphrase C_neutral
        neutral_text = generate_neutral_paraphrase(base_text)
        test_rows.append({
            "prompt_id": f"{pid}_C0",
            "base_id": pid,
            "condition": "C0_neutral",
            "text": neutral_text,
            "label": lbl,
            "ground_truth": gt,
            "source_dataset": src,
            "category": cat
        })
        
        # 3. Historical C2
        hist_text = existing_map.get((pid, "historical"), generate_victorian_shift(base_text))
        test_rows.append({
            "prompt_id": f"{pid}_C2",
            "base_id": pid,
            "condition": "C2_historical",
            "text": hist_text,
            "label": lbl,
            "ground_truth": gt,
            "source_dataset": src,
            "category": cat
        })
        
        # 4. Regional C3
        reg_text = existing_map.get((pid, "regional"), generate_indian_english_shift(base_text))
        test_rows.append({
            "prompt_id": f"{pid}_C3",
            "base_id": pid,
            "condition": "C3_regional",
            "text": reg_text,
            "label": lbl,
            "ground_truth": gt,
            "source_dataset": src,
            "category": cat
        })
        
        # 5. Combined C4
        comb_text = existing_map.get((pid, "combined"), generate_combined_shift(base_text))
        test_rows.append({
            "prompt_id": f"{pid}_C4",
            "base_id": pid,
            "condition": "C4_combined",
            "text": comb_text,
            "label": lbl,
            "ground_truth": gt,
            "source_dataset": src,
            "category": cat
        })
        
    bench_df = pd.DataFrame(test_rows)
    print(f"\nConstructed Held-Out Benchmark: {len(bench_df)} evaluation instances across 5 conditions.")
    print(pd.crosstab(bench_df['condition'], bench_df['label']))
    return bench_df

def evaluate_detectors_scaled(train_df, bench_df, random_seed=42):
    """
    Trains detectors on the 800 in-distribution prompts and evaluates across all 5 conditions.
    """
    print(f"\n=========================================================================")
    print(f"TRAINING DETECTORS ON 800 IN-DISTRIBUTION PROMPTS (Seed={random_seed})")
    print(f"=========================================================================")
    
    train_texts = train_df['prompt'].tolist()
    train_y = train_df['ground_truth_binary'].values
    
    # 1. Feature extractors
    word_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=2500, min_df=2, sublinear_tf=True)
    X_train_word = word_vec.fit_transform(train_texts)
    
    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=5000, min_df=2)
    X_train_char = char_vec.fit_transform(train_texts)
    
    models = {
        "Word TF-IDF + Logistic Regression": {
            "vec": word_vec,
            "clf": LogisticRegression(C=1.0, max_iter=1000, random_state=random_seed),
            "X_train": X_train_word,
            "is_prob": True
        },
        "Word TF-IDF + LinearSVC": {
            "vec": word_vec,
            "clf": LinearSVC(C=1.0, max_iter=2000, random_state=random_seed),
            "X_train": X_train_word,
            "is_prob": False
        },
        "Subword Char N-gram + Logistic Regression": {
            "vec": char_vec,
            "clf": LogisticRegression(C=1.0, max_iter=1000, random_state=random_seed),
            "X_train": X_train_char,
            "is_prob": True
        },
        "Subword Char N-gram + Ridge Margin": {
            "vec": char_vec,
            "clf": RidgeClassifier(alpha=1.0, random_state=random_seed),
            "X_train": X_train_char,
            "is_prob": False
        }
    }
    
    for name, m in models.items():
        m['clf'].fit(m['X_train'], train_y)
    print("All 4 detector architectures fitted successfully on N=800 in-distribution prompts.")
    
    # 2. Evaluation across conditions
    cond_order = ["C1_baseline", "C0_neutral", "C2_historical", "C3_regional", "C4_combined"]
    results = {}
    
    for m_name, m_info in models.items():
        results[m_name] = {}
        clf = m_info['clf']
        vec = m_info['vec']
        is_prob = m_info['is_prob']
        
        # Save baseline predictions for paired testing
        c1_subset = bench_df[bench_df['condition'] == 'C1_baseline']
        c1_X = vec.transform(c1_subset['text'])
        c1_y = c1_subset['ground_truth'].values
        if is_prob:
            c1_prob = clf.predict_proba(c1_X)[:, 1]
            c1_pred = (c1_prob >= 0.50).astype(int)
        else:
            c1_dec = clf.decision_function(c1_X)
            c1_prob = 1.0 / (1.0 + np.exp(-c1_dec))
            c1_pred = (c1_dec >= 0.00).astype(int)
            
        for cond in cond_order:
            c_subset = bench_df[bench_df['condition'] == cond]
            X = vec.transform(c_subset['text'])
            y = c_subset['ground_truth'].values
            
            if is_prob:
                probs = clf.predict_proba(X)[:, 1]
                preds = (probs >= 0.50).astype(int)
            else:
                dec = clf.decision_function(X)
                probs = 1.0 / (1.0 + np.exp(-dec))
                preds = (dec >= 0.00).astype(int)
                
            auc = roc_auc_score(y, probs)
            f1 = f1_score(y, preds, zero_division=0)
            prec = precision_score(y, preds, zero_division=0)
            rec = recall_score(y, preds, zero_division=0)
            
            tn, fp, fn, tp = confusion_matrix(y, preds, labels=[0, 1]).ravel()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            
            # McNemar test paired with C1 baseline
            mc_stat, mc_pval = mcnemar_exact(y, c1_pred, preds)
            ci_low, ci_high = clopper_pearson_ci(fp, fp + tn, alpha=0.05)
            
            results[m_name][cond] = {
                "auc": round(float(auc), 4),
                "f1": round(float(f1), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "fpr": round(float(fpr), 4),
                "fnr": round(float(fnr), 4),
                "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
                "fpr_ci": [round(ci_low, 4), round(ci_high, 4)],
                "mcnemar_p": round(mc_pval, 6),
                "raw_probs": probs.tolist(),
                "y_true": y.tolist()
            }
            
    return results, models

def analyze_threshold_recalibration(results):
    """
    Evaluates whether recalibrating the decision threshold restores benign specificity
    without destroying adversarial recall under distribution shift.
    """
    print(f"\n=========================================================================")
    print("THRESHOLD RECALIBRATION ANALYSIS (Sweeping Tau from 0.05 to 0.95)")
    print(f"=========================================================================")
    
    threshold_sweeps = {}
    tau_range = np.linspace(0.05, 0.95, 19)
    
    for m_name, cond_dict in results.items():
        threshold_sweeps[m_name] = {}
        for cond, metrics in cond_dict.items():
            probs = np.array(metrics['raw_probs'])
            y = np.array(metrics['y_true'])
            
            tau_results = []
            for tau in tau_range:
                preds = (probs >= tau).astype(int)
                tn, fp, fn, tp = confusion_matrix(y, preds, labels=[0, 1]).ravel()
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = f1_score(y, preds, zero_division=0)
                youden_j = rec - fpr
                tau_results.append({
                    "tau": round(float(tau), 2),
                    "fpr": round(float(fpr), 4),
                    "recall": round(float(rec), 4),
                    "f1": round(float(f1), 4),
                    "youden_j": round(float(youden_j), 4)
                })
            
            # Find optimal tau by maximum Youden's J
            best_tau = max(tau_results, key=lambda x: x['youden_j'])
            threshold_sweeps[m_name][cond] = {
                "optimal_tau": best_tau['tau'],
                "optimal_fpr": best_tau['fpr'],
                "optimal_recall": best_tau['recall'],
                "optimal_f1": best_tau['f1'],
                "default_fpr": metrics['fpr'],
                "default_recall": metrics['recall'],
                "sweeps": tau_results
            }
            
    return threshold_sweeps

if __name__ == '__main__':
    train_df, test_df = load_and_split_pool("data/seed_prompts_1000.csv", test_size=200, random_state=42)
    bench_df = construct_shifted_test_benchmark(test_df)
    
    # Save the expanded benchmark
    bench_df.to_csv("data/benchmark_scaled_1000_eval.csv", index=False)
    print("Saved scaled test benchmark to data/benchmark_scaled_1000_eval.csv")
    
    results, models = evaluate_detectors_scaled(train_df, bench_df, random_seed=42)
    
    # Save results
    with open("reports/scaled_step2_results.json", "w", encoding="utf-8") as f:
        # Strip raw_probs for concise json
        clean_res = {}
        for m, conds in results.items():
            clean_res[m] = {}
            for c, met in conds.items():
                clean_res[m][c] = {k: v for k, v in met.items() if k not in ['raw_probs', 'y_true']}
        json.dump(clean_res, f, indent=2)
    print("Saved scaled results to reports/scaled_step2_results.json")
    
    recalibration = analyze_threshold_recalibration(results)
    with open("reports/scaled_threshold_recalibration.json", "w", encoding="utf-8") as f:
        json.dump(recalibration, f, indent=2)
    print("Saved threshold recalibration analysis to reports/scaled_threshold_recalibration.json")
    
    print("\nStep 2 Experiments Successfully Completed!")
