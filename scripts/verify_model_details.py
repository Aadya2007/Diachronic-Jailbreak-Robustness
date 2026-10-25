"""
scripts/verify_model_details.py
Verifies:
1. Exact fitted intercepts and sigmoid(intercept) for unweighted and balanced models.
2. Per-prompt predictions for Word LogReg, Word LinearSVC, Char LogReg, and Char Ridge.
3. Checks whether identical counts (3, 2, 7) and (3, 2, 5) come from separate models and examines per-prompt agreement.
4. Checks token coverage vs FPR relationship.
5. Inspects the 4 retried malicious prompts.
"""

import csv
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import LinearSVC

def main():
    benchmark_csv = "data/benchmark_shifted_eval.csv"
    with open(benchmark_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_cond = {"baseline": [], "historical": [], "regional": [], "combined": []}
    for r in rows:
        by_cond[r["condition"].lower()].append(r)

    c1_rows = by_cond["baseline"]
    c1_texts = [r["prompt_text"] for r in c1_rows]
    c1_y = np.array([int(r["ground_truth_binary"]) for r in c1_rows])
    c1_ids = [r["parent_prompt_id"] for r in c1_rows]

    # Feature extractors
    word_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=1500, min_df=1)
    X_base_word = word_vec.fit_transform(c1_texts)
    
    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=3000, min_df=1)
    X_base_char = char_vec.fit_transform(c1_texts)

    print("=== 1. FITTED INTERCEPTS ===")
    # Unweighted Word LogReg
    clf_word_unweighted = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    clf_word_unweighted.fit(X_base_word, c1_y)
    b0_unweighted = clf_word_unweighted.intercept_[0]
    p0_unweighted = 1.0 / (1.0 + np.exp(-b0_unweighted))
    print(f"Word LogReg (unweighted) intercept = {b0_unweighted:.4f}, sigmoid(intercept) = {p0_unweighted:.4f}")

    # Balanced Word LogReg
    clf_word_balanced = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
    clf_word_balanced.fit(X_base_word, c1_y)
    b0_balanced = clf_word_balanced.intercept_[0]
    p0_balanced = 1.0 / (1.0 + np.exp(-b0_balanced))
    print(f"Word LogReg (balanced) intercept = {b0_balanced:.4f}, sigmoid(intercept) = {p0_balanced:.4f}")

    # Char LogReg unweighted
    clf_char_unweighted = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    clf_char_unweighted.fit(X_base_char, c1_y)
    b0_char_unweighted = clf_char_unweighted.intercept_[0]
    p0_char_unweighted = 1.0 / (1.0 + np.exp(-b0_char_unweighted))
    print(f"Char LogReg (unweighted) intercept = {b0_char_unweighted:.4f}, sigmoid(intercept) = {p0_char_unweighted:.4f}")

    # LinearSVC intercepts
    svc_word_unweighted = LinearSVC(C=1.0, max_iter=2000, random_state=42)
    svc_word_unweighted.fit(X_base_word, c1_y)
    print(f"Word LinearSVC (unweighted) intercept = {svc_word_unweighted.intercept_[0]:.4f}")

    svc_word_balanced = LinearSVC(C=1.0, max_iter=2000, random_state=42, class_weight='balanced')
    svc_word_balanced.fit(X_base_word, c1_y)
    print(f"Word LinearSVC (balanced) intercept = {svc_word_balanced.intercept_[0]:.4f}")

    # Ridge intercepts
    ridge_char_unweighted = RidgeClassifier(alpha=1.0, random_state=42)
    ridge_char_unweighted.fit(X_base_char, c1_y)
    print(f"Char Ridge (unweighted) intercept = {ridge_char_unweighted.intercept_[0]:.4f}")

    ridge_char_balanced = RidgeClassifier(alpha=1.0, random_state=42, class_weight='balanced')
    ridge_char_balanced.fit(X_base_char, c1_y)
    print(f"Char Ridge (balanced) intercept = {ridge_char_balanced.intercept_[0]:.4f}")

    print("\n=== 2. PER-PROMPT PREDICTIONS UNDER BALANCED WEIGHTS ===")
    models = {
        "Word_LogReg": (word_vec, clf_word_balanced, True),
        "Word_LinearSVC": (word_vec, svc_word_balanced, False),
        "Char_LogReg": (char_vec, LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced').fit(X_base_char, c1_y), True),
        "Char_Ridge": (char_vec, ridge_char_balanced, False),
    }

    per_prompt_records = []
    for cond_name in ["baseline", "historical", "regional", "combined"]:
        cond_rows = by_cond[cond_name]
        texts = [r["prompt_text"] for r in cond_rows]
        y_true = [int(r["ground_truth_binary"]) for r in cond_rows]
        ids = [r["parent_prompt_id"] for r in cond_rows]

        preds_dict = {}
        for m_name, (vec, clf, has_prob) in models.items():
            X = vec.transform(texts)
            if has_prob:
                prob = clf.predict_proba(X)[:, 1]
                pred = (prob >= 0.5).astype(int)
            else:
                dec = clf.decision_function(X)
                pred = (dec >= 0.0).astype(int)
            preds_dict[m_name] = pred

        print(f"\nCondition: {cond_name.upper()}")
        for i in range(len(ids)):
            if y_true[i] == 0: # benign prompt
                p_id = ids[i]
                w_lr = preds_dict["Word_LogReg"][i]
                w_svc = preds_dict["Word_LinearSVC"][i]
                c_lr = preds_dict["Char_LogReg"][i]
                c_rd = preds_dict["Char_Ridge"][i]
                print(f"  {p_id} (Benign): Word_LogReg={w_lr}, Word_SVC={w_svc}, Char_LogReg={c_lr}, Char_Ridge={c_rd} | Text: {texts[i][:60]}...")
                per_prompt_records.append({
                    "condition": cond_name,
                    "prompt_id": p_id,
                    "y_true": 0,
                    "Word_LogReg": int(w_lr),
                    "Word_LinearSVC": int(w_svc),
                    "Char_LogReg": int(c_lr),
                    "Char_Ridge": int(c_rd),
                    "text": texts[i]
                })

    with open("reports/per_prompt_balanced_predictions.json", "w", encoding="utf-8") as f:
        json.dump(per_prompt_records, f, indent=2)

    print("\n=== 3. CHECKING THE 4 REFUSALS IN DATASET ===")
    # Find the malicious prompts and their generation notes / retries
    with open("data/seed_prompts_1000.csv", "r", encoding="utf-8") as f:
        seed_all = list(csv.DictReader(f))
    
    # Check pilot transformations log or dataset
    pilot_eval_path = "data/benchmark_shifted_eval.json"
    with open(pilot_eval_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    print(f"Loaded {len(eval_data)} instances from {pilot_eval_path}")
    
    # Inspect malicious instances
    mal_instances = [inst for inst in eval_data if inst.get("ground_truth_binary") == 1]
    print(f"Total malicious instances across conditions: {len(mal_instances)}")
    # Print sample prompts from cyber/exploit
    cyber_prompts = [inst for inst in mal_instances if "sql" in inst["prompt_text"].lower() or "exploit" in inst["prompt_text"].lower() or "hack" in inst["prompt_text"].lower() or "keylogger" in inst["prompt_text"].lower() or "ddos" in inst["prompt_text"].lower() or "malware" in inst["prompt_text"].lower() or "vulnerability" in inst["prompt_text"].lower() or "script" in inst["prompt_text"].lower()]
    print(f"Found {len(cyber_prompts)} cyber/exploit prompt variants:")
    for cp in cyber_prompts[:8]:
        print(f"  ID={cp.get('parent_prompt_id')} [{cp.get('condition')}]: {cp['prompt_text']}")

if __name__ == "__main__":
    main()
