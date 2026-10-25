"""
run_balanced_weight_experiments.py
Runs the balanced class weight experiment across all four classifiers:
1. Word TF-IDF + Logistic Regression (class_weight='balanced')
2. Word TF-IDF + LinearSVC (class_weight='balanced')
3. Char n-gram + Logistic Regression (class_weight='balanced')
4. Char n-gram + RidgeClassifier (class_weight='balanced')

Also recomputes the vocabulary overlap metric properly using the exact tokenizer of TfidfVectorizer.
Computes exact binomial Clopper-Pearson CIs and two-sided McNemar p-values for all conditions.
"""

import csv
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import LinearSVC
from scipy.stats import binom, beta

def clopper_pearson(k, n, alpha=0.05):
    """Computes exact Clopper-Pearson 95% confidence interval for k successes in n trials."""
    if k == 0:
        low = 0.0
    else:
        low = beta.ppf(alpha / 2, k, n - k + 1)
    if k == n:
        high = 1.0
    else:
        high = beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(low), float(high)

def exact_mcnemar(b, c=0):
    """
    Two-sided exact McNemar test (binomial test under H0: p=0.5).
    Since C1 has FP=0, b is the number of false positives in shifted condition, c=0.
    """
    n = b + c
    if n == 0:
        return 1.0
    # Two-sided p-value is 2 * P(X <= min(b, c)) where X ~ Binomial(n, 0.5)
    # When c=0, 2 * (0.5)^b
    p = 2.0 * binom.cdf(min(b, c), n, 0.5)
    return min(1.0, float(p))

def analyze():
    benchmark_csv = "data/benchmark_shifted_eval.csv"
    with open(benchmark_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_cond = {"baseline": [], "historical": [], "regional": [], "combined": []}
    for r in rows:
        by_cond[r["condition"].lower()].append(r)

    c1_texts = [r["prompt_text"] for r in by_cond["baseline"]]
    c1_y = np.array([int(r["ground_truth_binary"]) for r in by_cond["baseline"]])

    # 1. Exact Vocabulary Overlap Analysis
    # Let's inspect default TfidfVectorizer tokenizer
    vec_word = TfidfVectorizer(ngram_range=(1, 2), max_features=1500, min_df=1)
    vec_word.fit(c1_texts)
    
    tokenizer = vec_word.build_tokenizer()
    c1_vocab_words = set(vec_word.vocabulary_.keys()) # includes 1-grams and 2-grams
    
    # Let's check token-level unigram vocabulary
    vec_unigram = TfidfVectorizer(ngram_range=(1, 1), min_df=1)
    vec_unigram.fit(c1_texts)
    c1_unigrams = set(vec_unigram.vocabulary_.keys())

    print("--- VOCABULARY OVERLAP METRIC INSPECTION ---")
    print(f"C1 total unigram features: {len(c1_unigrams)}")
    print(f"C1 total (1,2)-gram features: {len(c1_vocab_words)}")

    for cond_name in ["baseline", "historical", "regional", "combined"]:
        texts = [r["prompt_text"] for r in by_cond[cond_name]]
        
        # Tokenizer-based word tokens (using sklearn default tokenizer: (?u)\b\w\w+\b)
        all_tokens = []
        in_vocab_tokens = []
        for t in texts:
            toks = tokenizer(t.lower())
            all_tokens.extend(toks)
            in_vocab_tokens.extend([tok for tok in toks if tok in c1_unigrams])
        
        token_coverage = len(in_vocab_tokens) / len(all_tokens) * 100 if all_tokens else 0.0
        
        # Also check whitespace/punct split tokens to see why 73.7% appeared previously
        raw_words = []
        for t in texts:
            # simple whitespace split stripping punct
            wds = [w.strip(".,!?;:\"'()[]{}") for w in t.lower().split() if w.strip(".,!?;:\"'()[]{}")]
            raw_words.extend(wds)
        raw_in_vocab = [w for w in raw_words if w in c1_unigrams]
        raw_coverage = len(raw_in_vocab) / len(raw_words) * 100 if raw_words else 0.0
        
        print(f"Condition: {cond_name:10s} | Tokenizer tokens: {len(all_tokens)} | In C1 unigram vocab: {len(in_vocab_tokens)} ({token_coverage:.2f}%) | Raw words: {len(raw_words)} | In vocab: {len(raw_in_vocab)} ({raw_coverage:.2f}%)")

    # 2. Balanced Weight Experiment Across All 4 Models
    print("\n--- BALANCED WEIGHT EXPERIMENT ACROSS 4 MODELS ---")
    
    # Feature vectors
    word_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=1500, min_df=1)
    X_base_word = word_vec.fit_transform(c1_texts)
    
    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=3000, min_df=1)
    X_base_char = char_vec.fit_transform(c1_texts)
    
    # Unweighted vs Balanced models
    model_configs = [
        ("Word TF-IDF + LogReg", word_vec, X_base_word, LogisticRegression, {"C": 1.0, "max_iter": 1000, "random_state": 42}, True),
        ("Word TF-IDF + LinearSVC", word_vec, X_base_word, LinearSVC, {"C": 1.0, "max_iter": 2000, "random_state": 42}, False),
        ("Char n-gram + LogReg", char_vec, X_base_char, LogisticRegression, {"C": 1.0, "max_iter": 1000, "random_state": 42}, True),
        ("Char n-gram + Ridge", char_vec, X_base_char, RidgeClassifier, {"alpha": 1.0, "random_state": 42}, False),
    ]

    all_results = {}

    for name, vec, X_base, clf_cls, kwargs, has_prob in model_configs:
        print(f"\nModel: {name}")
        for weighting in ["unweighted", "balanced"]:
            clf_kwargs = dict(kwargs)
            if weighting == "balanced":
                clf_kwargs["class_weight"] = "balanced"
            
            clf = clf_cls(**clf_kwargs)
            clf.fit(X_base, c1_y)
            
            res_by_cond = {}
            for cond_name in ["baseline", "historical", "regional", "combined"]:
                cond_rows = by_cond[cond_name]
                texts = [r["prompt_text"] for r in cond_rows]
                y_true = np.array([int(r["ground_truth_binary"]) for r in cond_rows])
                
                X = vec.transform(texts)
                if has_prob:
                    probs = clf.predict_proba(X)[:, 1]
                    preds = (probs >= 0.5).astype(int)
                else:
                    dec = clf.decision_function(X)
                    preds = (dec >= 0.0).astype(int)
                
                benign_mask = (y_true == 0)
                malicious_mask = (y_true == 1)
                
                fp = int(np.sum(preds[benign_mask] == 1))
                tn = int(np.sum(preds[benign_mask] == 0))
                fn = int(np.sum(preds[malicious_mask] == 0))
                tp = int(np.sum(preds[malicious_mask] == 1))
                
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                ci_low, ci_high = clopper_pearson(fp, fp + tn)
                exact_p = exact_mcnemar(fp, 0) if cond_name != "baseline" else 1.0
                
                res_by_cond[cond_name] = {
                    "fp": fp,
                    "n_benign": fp + tn,
                    "fpr": fpr,
                    "recall": recall,
                    "ci_95": [round(ci_low, 3), round(ci_high, 3)],
                    "exact_p": exact_p
                }
                print(f"  [{weighting:10s}] {cond_name:10s}: FP={fp}/{fp+tn} (FPR={fpr:.2f}, 95% CI [{ci_low:.2f}, {ci_high:.2f}]), Recall={recall:.2f}, exact p={exact_p:.4f}")
            
            # Interaction contrast: FPR(C4) - FPR(C2) - FPR(C3) + FPR(C1)
            c1_fpr = res_by_cond["baseline"]["fpr"]
            c2_fpr = res_by_cond["historical"]["fpr"]
            c3_fpr = res_by_cond["regional"]["fpr"]
            c4_fpr = res_by_cond["combined"]["fpr"]
            interaction = c4_fpr - c2_fpr - c3_fpr + c1_fpr
            print(f"  [{weighting:10s}] Interaction contrast: {interaction:+.2f}")
            
            all_results[f"{name} ({weighting})"] = res_by_cond

    with open("reports/balanced_weight_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print("\nSaved all results to reports/balanced_weight_experiment_results.json")

if __name__ == "__main__":
    analyze()
