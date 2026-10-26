"""
save_prediction_artifacts.py
Saves the artifacts that the manuscript's statements depend on:

  reports/per_prompt_predictions_all.csv   per prompt x condition x model x weighting:
                                           score (P(malicious) or margin), prediction, correctness
  reports/vocabulary_coverage.json         token-coverage counts per condition, plus fitted
                                           intercepts and sigma(intercept) for the LogReg models
  reports/artifact_consistency_check.txt   comparison of recomputed numbers with those in the paper

Uses exactly the configuration described in the paper (data/benchmark_shifted_eval.csv, trained on C1,
seed 42, fixed thresholds 0.5 / 0.0). Run from the repository root:  python scripts/save_prediction_artifacts.py
"""

import csv
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import LinearSVC

CONDS = ["baseline", "historical", "regional", "combined"]


def sigmoid(z):
    return float(1.0 / (1.0 + np.exp(-z)))


def main():
    with open("data/benchmark_shifted_eval.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_cond = {c: [r for r in rows if r["condition"].lower() == c] for c in CONDS}
    base = by_cond["baseline"]
    base_texts = [r["prompt_text"] for r in base]
    base_y = np.array([int(r["ground_truth_binary"]) for r in base])

    word_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=1500, min_df=1)
    X_word = word_vec.fit_transform(base_texts)
    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=3000, min_df=1)
    X_char = char_vec.fit_transform(base_texts)

    configs = [
        ("Word_LogReg", word_vec, X_word, LogisticRegression, {"C": 1.0, "max_iter": 1000, "random_state": 42}, True),
        ("Word_LinearSVC", word_vec, X_word, LinearSVC, {"C": 1.0, "max_iter": 2000, "random_state": 42}, False),
        ("Char_LogReg", char_vec, X_char, LogisticRegression, {"C": 1.0, "max_iter": 1000, "random_state": 42}, True),
        ("Char_Ridge", char_vec, X_char, RidgeClassifier, {"alpha": 1.0, "random_state": 42}, False),
    ]

    out_rows = []
    intercepts = {}
    fp_counts = {}
    for weighting in ["unweighted", "balanced"]:
        for name, vec, X_fit, cls, params, has_prob in configs:
            kw = dict(params)
            if weighting == "balanced":
                kw["class_weight"] = "balanced"
            clf = cls(**kw)
            clf.fit(X_fit, base_y)
            if has_prob:
                b0 = float(clf.intercept_[0])
                intercepts[f"{name} ({weighting})"] = {"intercept": round(b0, 4), "sigmoid_intercept": round(sigmoid(b0), 3)}
            for cond in CONDS:
                texts = [r["prompt_text"] for r in by_cond[cond]]
                X = vec.transform(texts)
                if has_prob:
                    score = clf.predict_proba(X)[:, 1]
                    pred = (score >= 0.5).astype(int)
                else:
                    score = clf.decision_function(X)
                    pred = (score >= 0.0).astype(int)
                fp = 0
                for r, s, p in zip(by_cond[cond], score, pred):
                    y = int(r["ground_truth_binary"])
                    fp += int(y == 0 and p == 1)
                    out_rows.append({
                        "weighting": weighting, "model": name, "condition": cond,
                        "prompt_id": r["parent_prompt_id"], "source_dataset": r["source_dataset"],
                        "y_true": y, "score": round(float(s), 6), "pred": int(p),
                        "correct": int(p == y), "text": r["prompt_text"],
                    })
                fp_counts[(weighting, name, cond)] = fp

    with open("reports/per_prompt_predictions_all.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    # Vocabulary coverage (sklearn default token pattern (?u)\b\w\w+\b, lowercased, vs. C1 unigram vocabulary)
    uni = TfidfVectorizer(ngram_range=(1, 1), min_df=1).fit(base_texts)
    c1_unigrams = set(uni.vocabulary_.keys())
    tokenizer = uni.build_tokenizer()
    coverage = {"token_pattern": r"(?u)\b\w\w+\b", "c1_unigram_vocab_size": len(c1_unigrams), "conditions": {}}
    for cond in CONDS:
        toks = []
        for r in by_cond[cond]:
            toks.extend(tokenizer(r["prompt_text"].lower()))
        inv = sum(t in c1_unigrams for t in toks)
        coverage["conditions"][cond] = {
            "total_tokens": len(toks), "in_vocab_tokens": inv,
            "coverage_percent": round(100.0 * inv / len(toks), 1),
        }
    coverage["logreg_intercepts"] = intercepts
    coverage["training_prior_malicious"] = float(base_y.mean())
    with open("reports/vocabulary_coverage.json", "w", encoding="utf-8") as f:
        json.dump(coverage, f, indent=2)

    # Consistency check against numbers stated in the paper
    paper_fp = {
        "Word_LogReg": {"historical": 10, "regional": 10, "combined": 10},
        "Word_LinearSVC": {"historical": 5, "regional": 2, "combined": 8},
        "Char_LogReg": {"historical": 9, "regional": 8, "combined": 9},
        "Char_Ridge": {"historical": 5, "regional": 3, "combined": 8},
    }
    paper_fp_bal = {
        "Word_LogReg": {"historical": 3, "regional": 2, "combined": 7},
        "Word_LinearSVC": {"historical": 3, "regional": 2, "combined": 7},
        "Char_LogReg": {"historical": 3, "regional": 2, "combined": 5},
        "Char_Ridge": {"historical": 3, "regional": 2, "combined": 5},
    }
    paper_cov = {"baseline": (219, 219), "historical": (258, 474), "regional": (221, 333), "combined": (271, 600)}
    lines = []
    for weighting, table in [("unweighted", paper_fp), ("balanced", paper_fp_bal)]:
        for name, d in table.items():
            for cond, expected in d.items():
                got = fp_counts[(weighting, name, cond)]
                lines.append(f"{'OK  ' if got == expected else 'DIFF'} FP {weighting:10s} {name:15s} {cond:10s} paper={expected} recomputed={got}")
    for cond, (inv_p, tot_p) in paper_cov.items():
        c = coverage["conditions"][cond]
        ok = (c["in_vocab_tokens"], c["total_tokens"]) == (inv_p, tot_p)
        lines.append(f"{'OK  ' if ok else 'DIFF'} coverage {cond:10s} paper={inv_p}/{tot_p} recomputed={c['in_vocab_tokens']}/{c['total_tokens']}")
    for key, expected in [("Word_LogReg (unweighted)", (0.4770, 0.617)), ("Char_LogReg (unweighted)", (0.4451, 0.610))]:
        got = intercepts[key]
        lines.append(f"{'OK  ' if (abs(got['intercept']-expected[0]) < 5e-4 and abs(got['sigmoid_intercept']-expected[1]) < 5e-4) else 'DIFF'} intercept {key} paper={expected} recomputed=({got['intercept']}, {got['sigmoid_intercept']})")
    with open("reports/artifact_consistency_check.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
