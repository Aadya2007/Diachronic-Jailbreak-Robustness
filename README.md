# Beyond Contemporary Standard English: A Pilot Study of False-Alarm Fragility in Lightweight Jailbreak Classifiers Under Diachronic and Dialectal Shift

[![Paper PDF](https://img.shields.io/badge/Paper-IEEE%20Format-blue.svg)](paper/ieee_conference_paper.tex)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Official research repository and empirical benchmarking harness for the paper:
> **"Beyond Contemporary Standard English: A Pilot Study of False-Alarm Fragility in Lightweight Jailbreak Classifiers Under Diachronic and Dialectal Shift"**  
> *Authors:* Anjali Ajith, Aishwarya Upadhyay, and Aadya Singh  
> *Affiliation:* Department of Computer Science and Engineering, Dronacharya College of Engineering (affiliated with Gurugram University), Gurugram, Haryana, India.

---

## 📌 Abstract Overview

Input-filtering classifiers are widely deployed as perimeter defenses for large language models (LLMs), yet they are conventionally evaluated on contemporary standard English. We present a controlled pilot study investigating detector behavior under:
1. **Diachronic Shift ($\tau$):** Victorian formal English register.
2. **Socio-Regional Shift ($\rho$):** Colloquial Indian English dialect.
3. **Combined Dual Shift ($\tau \times \rho$):** Colonial-administrative register.

Using a $2 \times 2$ factorial evaluation design across 25 base prompts (15 malicious from JailbreakBench, AdvBench, Do-Not-Answer; 10 benign hard-negative homonyms from XSTest) rewritten under strict cosine similarity ($\ge 0.70$) and length ratio controls, we evaluate four linear classifier architectures (Word TF-IDF + LogReg, Word TF-IDF + LinearSVC, Char n-gram + LogReg, Char n-gram + Ridge).

### Key Findings
* **Preserved Attack Recall:** Recall on malicious prompts remained strictly $1.000$ ($15/15$, $95\%$ CI $[0.78, 1.00]$) across all shifts.
* **False-Alarm Inflation:** Unweighted models showed marked false-positive inflation on technical benign homonyms, with five increases surviving multiple-comparison correction.
* **Prior-Bias & Sparsity Artifact:** Exploratory balanced re-weighting (`class_weight='balanced'`) demonstrated that part of the false alarms in unweighted models is associated with majority-class prior bias (substantially for logistic models, modestly for LinearSVC and Ridge), though residual elevations persist in the combined condition ($C_4$).
* **Thresholding vs. Ranking:** High AU-ROC ($\ge 0.973$) under shift indicates that decision thresholds, rather than fundamental ranking capability, drive over-refusal behavior.

---

## 📁 Repository Structure

```text
├── data/
│   ├── benchmark_shifted_eval.csv        # Evaluated 100-instance pilot benchmark (4 conditions x 25 prompts)
│   ├── benchmark_scaled_1000_eval.csv     # Scaled 4,000-instance evaluation dataset
│   └── seed_prompts_1000.csv             # 1,000 curated base prompts (500 malicious / 500 benign)
├── paper/
│   ├── ieee_conference_paper.tex         # Complete IEEE conference LaTeX manuscript
│   ├── references.bib                    # 21 verified BibTeX references
│   ├── fig1.pdf                          # 2x2 Factorial experimental design diagram
│   ├── fig2.pdf                          # False-positive rate bar chart with 95% Clopper-Pearson CIs
│   ├── ieee_paper_overleaf.zip           # 1-click ready-to-upload Overleaf package
│   └── overleaf_package/                 # Unpacked Overleaf source files
├── reports/
│   ├── balanced_weight_experiment_results.json # 4-model balanced-weight empirical data
│   ├── detector_robustness_results.json        # Main classification metrics & McNemar tests
│   └── per_prompt_balanced_predictions.json    # Exact prompt-by-prompt model predictions
├── scripts/
│   ├── evaluate_detectors.py             # Benchmark evaluation harness
│   ├── run_balanced_weight_experiments.py # Balanced-weight exploratory experiments
│   ├── update_figures.py                 # Vector PDF figure generation (fig1 & fig2)
│   └── verify_prompt_matches.py          # Per-prompt error breakdown across feature spaces
└── README.md                             # Repository documentation
```

---

## 🚀 Reproduction Quickstart

### 1. Requirements
* Python 3.10+
* `scikit-learn`, `scipy`, `numpy`, `pillow`

```bash
pip install scikit-learn scipy numpy pillow
```

### 2. Run Robustness Evaluation
Evaluate the four detector architectures on the contemporary baseline ($C_1$) and shifted conditions ($C_2, C_3, C_4$):
```bash
python scripts/evaluate_detectors.py
```

### 3. Run Balanced-Weight Experiment
Reproduce the multi-model balanced weighting experiment and token-level vocabulary coverage diagnostics:
```bash
python scripts/run_balanced_weight_experiments.py
```

### 4. Regenerate Figures
Generate publication-ready vector figures (`fig1.pdf` and `fig2.pdf`):
```bash
python scripts/update_figures.py
```

---

## 📄 LaTeX Paper & Overleaf Compilation

The paper is typeset using the official IEEE conference template (`\documentclass[conference]{IEEEtran}`).
* To compile on Overleaf: upload [`paper/ieee_paper_overleaf.zip`](paper/ieee_paper_overleaf.zip) via **New Project $\rightarrow$ Upload Project**.

---

## ⚖️ Ethics & Responsible Disclosure

This repository releases benign evaluation quadruplets, feature extraction harnesses, classifier configurations, and full statistical logs. In compliance with AI safety best practices, access to raw adversarial attack prompts is restricted to credentialed academic researchers upon request to prevent misuse in filter evasion.

## 📜 Citation

```bibtex
@inproceedings{ajith2026beyond,
  title={Beyond Contemporary Standard English: A Pilot Study of False-Alarm Fragility in Lightweight Jailbreak Classifiers Under Diachronic and Dialectal Shift},
  author={Ajith, Anjali and Upadhyay, Aishwarya and Singh, Aadya},
  booktitle={IEEE Conference Proceedings},
  year={2026}
}
```
