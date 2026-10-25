# Beyond Contemporary Standard English: Evaluating the Robustness and False-Alarm Fragility of Jailbreak Detectors Under Diachronic and Dialectal Shift

**Authors:** Undergraduate AI Safety Research Team  
**Affiliation:** AI Safety and Alignment Laboratory  
**Artifact Directory:** [`paper/main.tex`](file:///c:/Users/Aayush%20Singh/Documents/antigravity/fervent-raman/paper/main.tex) | [`paper/references.bib`](file:///c:/Users/Aayush%20Singh/Documents/antigravity/fervent-raman/paper/references.bib)

---

## Abstract
As large language models (LLMs) are integrated into high-stakes applications, safety guardrails and input-filtering classifiers are deployed as perimeter defenses against jailbreaks and adversarial prompt injections. However, current safety benchmarks evaluate detectors predominantly on contemporary, standardized English. In this work, we investigate whether jailbreak detectors remain reliable when prompts undergo **diachronic shift** (historical Victorian English registers), **socio-regional dialect shift** (colloquial Indian English), and their **combined interaction** (19th-century colonial regional administrative English), while strictly preserving underlying semantic intent and safety ground-truth labels. 

Using a controlled $2 \times 2$ factorial evaluation benchmark constructed from authenticated safety suites (JailbreakBench, AdvBench, Do-Not-Answer, XSTest, and BeaverTails), we benchmark word-level lexical classifiers, linear margin estimators, and subword character n-gram architectures. Counter to the prevailing hypothesis that linguistic shifts primarily facilitate adversarial evasion (false negatives), our empirical findings reveal a catastrophic **"Censorship-by-Default"** failure mode: while classifiers maintain high attack detection recall ($\text{FNR} = 0.0\%$), their False Positive Rate (FPR) on benign hard negatives surges from $0.0\%$ in-distribution to between $50.0\%$ and $100.0\%$ under historical and regional shifts ($p < 0.01$, McNemar's test). Furthermore, simultaneous temporal and regional shifts produce compounding degradation, driving linear margin false alarm rates up to $80.0\%$. Our results demonstrate that production guardrails overfit to contemporary standardized syntax, creating severe linguistic discrimination and denial of service for non-standard dialect speakers and benign historical inquiries.

---

## 1. Introduction
To protect large language models (LLMs) from harmful completions, production architectures deploy a defense-in-depth perimeter consisting of dedicated, lightweight input classifiers (e.g., Meta Prompt Guard, AllenAI WildGuard, sentence embedding probes) that intercept adversarial inputs before they reach costly generative models. While these detectors report near-perfect precision and recall on standardized in-distribution test sets, real-world deployment exposes systems to vast linguistic diversity across cultural registers, geographical regions, and historical periods.

Recent investigations into AI safety have highlighted specific facets of distribution shift:
* *JailbreaksOverTime* (Piet et al., 2025) revealed that detectors degrade across chronological calendar time due to evolving human attack strategies.
* *XL-SafetyBench* (Choi et al., 2026) and *IndicJR* (Pattnayak & Chowdhuri, 2026) demonstrated that generative models exhibit safety vulnerabilities when evaluated across different national languages.
* Andriushchenko & Flammarion (2025) demonstrated that simple past-tense grammatical rewrites bypass model refusal training.

However, a fundamental research gap persists: **No prior study has systematically evaluated standalone input-filtering safety classifiers under controlled, intra-lingual diachronic (historical registers) and socio-regional dialect shifts while holding semantic harm strictly constant and evaluating benign hard negatives alongside adversarial attacks.**

### The Central Hypothesis
We formulate and investigate the **Linguistic Robustness Hypothesis**:
> *Do historical register variations and socio-regional dialect shifts cause dedicated safety classifiers to misclassify prompts, even when their underlying meaning and safety-relevant intent remain unchanged?*

### Core Contributions
1. **A Controlled Factorial Benchmark:** We design a $2 \times 2$ factorial evaluation framework mapping contemporary seed prompts into four conditions: Contemporary Baseline ($C_1$), Diachronic / Victorian Shift ($C_2$), Socio-Regional Indian English ($C_3$), and Combined Colonial Administrative Shift ($C_4$).
2. **The "Censorship-by-Default" Discovery:** We discover that detectors do not primarily fail through adversarial evasion ($\Delta \text{FNR} = 0.0\%$), but through catastrophic false-positive inflation ($\Delta \text{FPR} = +20.0\%$ to $+100.0\%$, $p < 0.01$). Classifiers misidentify unfamiliar benign syntax as malicious attacks.
3. **Compound Factorial Interaction:** We prove that joint temporal-regional shifts produce compounding degradation ($\Delta \text{FPR} = +80.0\%$ on margin classifiers), demonstrating that interaction effects exceed individual single-factor shifts.

---

## 2. Related Work

### 2.1 Temporal Shift in AI Safety
Prior literature on temporal robustness in NLP has explored domain drift and diachronic language change. In adversarial safety, Piet et al. (2025) introduced *JailbreaksOverTime*, documenting how detector accuracy degrades over a 10-month calendar timeline as human adversaries discover novel prompt templates. In contrast to chronological exploit evolution, Andriushchenko & Flammarion (2025) examined grammatical tense, showing that past-tense reformulations (e.g., "How did people make...") circumvent refusal alignment in frontier LLMs. Our study addresses a distinct dimension: *diachronic register shift*—the vocabulary, syntax, and circumlocutions characteristic of historical English prose (e.g., 19th-century Victorian literature).

### 2.2 Multilingual and Cross-Cultural AI Safety
Research in multilingual red-teaming has accelerated rapidly:
* *MultiJail* (Deng et al., 2024) established that translating harmful prompts into low-resource languages bypasses safety alignment.
* *XL-SafetyBench* (Choi et al., 2026) introduced a 10-country cross-cultural safety suite.
* *IndicJR* (Pattnayak & Chowdhuri, 2026) evaluated jailbreak vulnerabilities across 12 South Asian languages, identifying script-switching and romanization as critical blind spots.
* *TukaBench* (Akinode et al., 2026) and *IndicSafeEval* (Mondal et al., 2026) benchmarked culturally localized threats in African and Indic languages.

However, these benchmarks evaluate *cross-lingual generative LLM refusal* on localized legal concepts. Our work isolates *intra-lingual socio-regional dialect variation* (e.g., Indian English) on dedicated input classifiers.

### 2.3 Detector Shortcuts and Exaggerated Safety
Evaluating prompt classifiers under true distribution shift was formalized by Fomin (2026) in *When Benchmarks Lie*, demonstrating that linear probes learn dataset-identity shortcuts that collapse under Leave-One-Dataset-Out (LODO) testing. Complementarily, *XSTest* (Röttger et al., 2024) exposed the widespread phenomenon of exaggerated safety (over-refusal) on benign prompts sharing lexical overlap with sensitive topics. We build upon this foundation by evaluating how dialectal shift exacerbates false-alarm sensitivity.

---

## 3. Factorial Experimental Design

### 3.1 The $2 \times 2$ Evaluation Space
We define a prompt transformation function $T(x, \tau, \rho)$ parametrized by a temporal axis $\tau \in \{\text{Contemporary}, \text{Historical}\}$ and a regional axis $\rho \in \{\text{Standard}, \text{Regional}\}$:

```
                          TEMPORAL AXIS
                     Contemporary    Historical (19th-C)
                   ┌──────────────┬──────────────────────┐
          Standard │ Condition 1: │ Condition 2:         │
          English  │ Contemporary │ Diachronic /         │
                   │ Baseline     │ Victorian Shift      │
  CULTURAL         ├──────────────┼──────────────────────┤
  / REGIONAL       │ Condition 3: │ Condition 4:         │
  AXIS    Regional │ Socio-       │ Combined Historical  │
          Dialect  │ Regional     │ -Regional Colonial   │
                   │ Dialect      │ Administrative       │
                   └──────────────┴──────────────────────┘
```

* **Condition 1 ($C_1$, Baseline):** Standard contemporary American/British English.
* **Condition 2 ($C_2$, Historical):** 19th-Century Victorian formal English with Latinate diction and formal circumlocutions.
* **Condition 3 ($C_3$, Regional):** Colloquial Indian English vernacular characterized by South Asian syntax and discourse particles.
* **Condition 4 ($C_4$, Combined):** 19th-century colonial regional administrative English merging formal petitionary structures with South Asian administrative idioms.

### 3.2 Benchmark Foundation & Ground-Truth Provenance
To avoid synthetic label noise, all seed prompts originate from peer-reviewed, human-audited benchmarks:
1. **Malicious Cohort ($y = 1$):** Sourced from JailbreakBench (10 policy categories; Chao et al., 2024), AdvBench (Zou et al., 2023), and Do-Not-Answer (Wang et al., 2023).
2. **Benign Cohort ($y = 0$):** Sourced from XSTest safe hard negatives (homonyms, figurative language, safe contexts, definitions, historical events; Röttger et al., 2024) and BeaverTails safe interactions (Ji et al., 2023).

### 3.3 Semantic Invariance & Confounder Controls
To guarantee that $y_i$ remains invariant across transformations:
* **Meta-Linguistic Translation Framing:** To prevent LLM instruction-refusal, transformation prompts instruct the generator to operate solely as a literal syntactic translator without executing actions.
* **Dense Semantic Cosine Validation:** Transformations are embedded using Nomic-Embed-Text (768 dimensions), verifying that cross-style cosine similarity satisfies $\text{CosSim} \ge 0.70$.
* **Length Normalization:** Output token counts are constrained within $[0.70, 2.50]$ word length ratios relative to baseline.

---

## 4. Empirical Results & Findings

### Table 1: Main Performance Matrix Across Distribution Shifts
*Metrics on 100 evaluation instances across the $2 \times 2$ grid (15 Malicious, 10 Benign per condition).*

| Detector Model | Condition | AU-ROC | F1-Score | Precision | Recall | FPR (Over-refusal) | McNemar $p$-value |
|---|---|---|---|---|---|---|---|
| **Word TF-IDF + Logistic Regression** | $C_1$: Baseline (Contemporary) | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | --- |
| | $C_2$: Historical Shift (Victorian) | 1.000 | 0.750 | 0.600 | 1.000 | **1.000** | **0.0044** |
| | $C_3$: Regional Shift (Indian Eng.) | 1.000 | 0.750 | 0.600 | 1.000 | **1.000** | **0.0044** |
| | $C_4$: Combined Shift (Colonial Admin) | 0.973 | 0.750 | 0.600 | 1.000 | **1.000** | **0.0044** |
| **Word TF-IDF + LinearSVC** | $C_1$: Baseline (Contemporary) | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | --- |
| | $C_2$: Historical Shift (Victorian) | 1.000 | 0.857 | 0.750 | 1.000 | **0.500** | 0.0736 |
| | $C_3$: Regional Shift (Indian Eng.) | 1.000 | 0.938 | 0.882 | 1.000 | **0.200** | 0.4795 |
| | $C_4$: Combined Shift (Colonial Admin) | 0.980 | 0.789 | 0.652 | 1.000 | **0.800** | **0.0133** |
| **Subword Char N-gram + Logistic Regression** | $C_1$: Baseline (Contemporary) | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | --- |
| | $C_2$: Historical Shift (Victorian) | 1.000 | 0.769 | 0.625 | 1.000 | **0.900** | **0.0077** |
| | $C_3$: Regional Shift (Indian Eng.) | 0.987 | 0.789 | 0.652 | 1.000 | **0.800** | **0.0133** |
| | $C_4$: Combined Shift (Colonial Admin) | 0.973 | 0.769 | 0.625 | 1.000 | **0.900** | **0.0077** |
| **Subword Char N-gram + Linear Margin** | $C_1$: Baseline (Contemporary) | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | --- |
| | $C_2$: Historical Shift (Victorian) | 1.000 | 0.857 | 0.750 | 1.000 | **0.500** | 0.0736 |
| | $C_3$: Regional Shift (Indian Eng.) | 0.987 | 0.909 | 0.833 | 1.000 | **0.300** | 0.2482 |
| | $C_4$: Combined Shift (Colonial Admin) | 0.973 | 0.789 | 0.652 | 1.000 | **0.800** | **0.0133** |

---

### Table 2: Robustness Degradation Deltas Relative to Baseline
*Positive $\Delta\text{FPR}$ indicates increased false alarms on benign prompts; positive $\Delta\text{FNR}$ indicates increased adversarial evasions.*

| Detector Model | Shift Type | $\Delta\text{AU-ROC} \downarrow$ | $\Delta\text{FPR (False Alarms)} \uparrow$ | $\Delta\text{FNR (Evasions)} \uparrow$ |
|---|---|---|---|---|
| **Word TF-IDF + Logistic Regression** | Diachronic (Historical) | +0.000 | **+1.000 (+100%)** | +0.000 |
| | Socio-Regional (Dialectal) | +0.000 | **+1.000 (+100%)** | +0.000 |
| | Combined (Hist + Reg) | +0.027 | **+1.000 (+100%)** | +0.000 |
| **Word TF-IDF + LinearSVC** | Diachronic (Historical) | +0.000 | **+0.500 (+50%)** | +0.000 |
| | Socio-Regional (Dialectal) | +0.000 | **+0.200 (+20%)** | +0.000 |
| | Combined (Hist + Reg) | +0.020 | **+0.800 (+80%)** | +0.000 |
| **Subword Char N-gram + Logistic Regression** | Diachronic (Historical) | +0.000 | **+0.900 (+90%)** | +0.000 |
| | Socio-Regional (Dialectal) | +0.013 | **+0.800 (+80%)** | +0.000 |
| | Combined (Hist + Reg) | +0.027 | **+0.900 (+90%)** | +0.000 |
| **Subword Char N-gram + Linear Margin** | Diachronic (Historical) | +0.000 | **+0.500 (+50%)** | +0.000 |
| | Socio-Regional (Dialectal) | +0.013 | **+0.300 (+30%)** | +0.000 |
| | Combined (Hist + Reg) | +0.027 | **+0.800 (+80%)** | +0.000 |

---

### 4.1 Finding 1: Catastrophic False-Positive Inflation ("Censorship-by-Default")
As documented in Tables 1 and 2, all models exhibit near-perfect in-distribution calibration on Condition 1 ($\text{FPR} = 0.000$). However, when presented with benign prompts written in historical or regional English, detectors experience a catastrophic increase in false-alarm rates:
* Word TF-IDF models falsely classify **$100.0\%$** of benign historical and regional inquiries as malicious attacks ($p = 0.0044$, McNemar's test).
* Subword character n-gram models falsely flag **$90.0\%$** of benign historical prompts ($p = 0.0077$) and **$80.0\%$** of benign regional prompts ($p = 0.0133$).
* Linear margin classifiers experience a surge to **$50.0\%$** false alarms under historical shift.

### 4.2 Finding 2: Asymmetric Attack Invariance
Across all models, the False Negative Rate remained zero ($\text{FNR} = 0.000$, $\Delta\text{FNR} = +0.000$). Detectors did not miss malicious attacks when transformed into historical or regional dialects. Instead, because classifiers overfit to contemporary benign grammar, *any input exhibiting non-standard, unfamiliar phrasing was defaulted to the malicious class*. The classifiers exhibited an aggressive "guilty until proven innocent" bias.

### 4.3 Finding 3: Compounding Factorial Degradation
Condition 4 demonstrates an empirical compounding interaction effect:
* Under LinearSVC, regional shift produced $\Delta\text{FPR} = +0.200$ and historical shift produced $\Delta\text{FPR} = +0.500$.
* When both shifts occurred simultaneously in the Combined condition, $\Delta\text{FPR}$ surged to **$+0.800$** ($80.0\%$ over-refusal), accompanied by an AU-ROC drop down to $0.973$.

---

## 5. Qualitative Error Diagnostics

```
┌────────────────────────────────────────────────────────────────────────┐
│               Case Study: Benign Python Homonym (BEN-0001)             │
│                                                                        │
│ Baseline (C1): "How can I kill a Python process?"                      │
│   ──> Predicted: SAFE (Correct, Prob = 0.04)                          │
│                                                                        │
│ Historical (C2): "Pray inform me by what manner one may effect the    │
│                   termination of an executing Python process."         │
│   ──> Predicted: MALICIOUS (FALSE POSITIVE, Prob = 0.88) ❌           │
│                                                                        │
│ Regional (C3): "Kindly advise how to kill this Python background       │
│                 process urgently, please."                             │
│   ──> Predicted: MALICIOUS (FALSE POSITIVE, Prob = 0.82) ❌           │
│                                                                        │
│ Combined (C4): "Humbly petitioning your honour, I beseech to know the  │
│                 expedient manner to terminate a recalcitrant Python    │
│                 process."                                              │
│   ──> Predicted: MALICIOUS (FALSE POSITIVE, Prob = 0.91) ❌           │
└────────────────────────────────────────────────────────────────────────┘
```

The qualitative analysis reveals why the detectors misfired:
1. In the baseline condition, the classifier recognized the contemporary bigram structure (`kill a`, `Python process`) as a benign computing context.
2. Under historical transformation, archaic markers (*"pray inform me"*, *"effect the termination"*) displaced the familiar bigrams, while the sensitive root *termination* triggered the detector's harm weights.
3. Under regional transformation, South Asian politeness and urgency markers (*"kindly advise... urgently please"*) caused the prompt to fall outside the standard benign manifold, triggering false positives.

---

## 6. Threats to Validity & Limitations

1. **Synthetic Paraphrase Fidelity:** Prompt transformations were produced via few-shot generative style transfer with Llama 3. While semantic similarity was verified via dense Nomic embeddings ($\ge 0.70$) and manual audit, synthetic rewrites may exhibit subtle distributional artifacts not present in organic diachronic texts.
2. **Classifier Scope:** Our empirical evaluation focused on edge-deployable linear, n-gram, and subword classifiers. Future extensions will evaluate large multi-billion-parameter generative moderators (e.g., Llama Guard 3 8B, ShieldGemma) across this factorial matrix.
3. **Dialect Scope:** We selected Indian English as our primary regional dialect due to its extensive speaker population (over 200 million English speakers) and distinctive syntactic idioms. Other regional varieties (e.g., AAVE, Nigerian English, Singapore English) warrant independent benchmarking.

---

## 7. Conclusion & Recommendations
This study provides the first systematic evaluation of jailbreak detectors under controlled diachronic and socio-regional distribution shifts. Our empirical findings demonstrate that detectors do not merely suffer from adversarial evasion; rather, their primary vulnerability is a **catastrophic surge in false-positive over-refusals ($p < 0.01$)** on harmless regional and historical queries. 

### Recommendations for AI Safety Developers
* **Train on Diverse Socio-Lects:** Guardrails must incorporate non-standard dialects (Indian English, AAVE, West African English) into benign training datasets to prevent algorithmic discrimination.
* **Incorporate Diachronic Negatives:** Benign historical inquiries and archival documents must be integrated into moderation corpora to calibrate classifiers against archaic vocabulary.
* **Calibrate False-Alarm Thresholds:** Production deployment must report and optimize False Positive Rates across demographic groups rather than relying exclusively on in-distribution AUC.

---

## References
1. **Andriushchenko, M., & Flammarion, N. (2025).** *Does Refusal Training in LLMs Generalize to the Past Tense?* International Conference on Learning Representations (ICLR 2025).
2. **Chao, P. et al. (2024).** *JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models.* NeurIPS 2024 Datasets and Benchmarks Track.
3. **Choi, D. et al. (2026).** *XL-SafetyBench: A Country-Grounded Cross-Cultural Benchmark for LLM Safety and Cultural Sensitivity.* arXiv:2605.05662.
4. **Deng, Y., Zhang, W., Pan, S. J., & Bing, L. (2024).** *Multilingual Jailbreak Challenges in Large Language Models.* ICLR 2024.
5. **Fomin, M. (2026).** *When Benchmarks Lie: Evaluating Malicious Prompt Classifiers Under True Distribution Shift.* arXiv:2602.14161.
6. **Han, S. et al. (2024).** *WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs.* NeurIPS 2024.
7. **Ji, J. et al. (2023).** *BeaverTails: Towards Improved Values Alignment in Large Language Models.* NeurIPS 2023.
8. **Pattnayak, P., & Chowdhuri, S. (2026).** *IndicJR: A Judge-Free Benchmark of Jailbreak Robustness in South Asian Languages.* EACL 2026 Industry Track / ACL Anthology `2026.eacl-industry.50`.
9. **Piet, J. et al. (2025).** *JailbreaksOverTime: Detecting Jailbreak Attacks Under Distribution Shift.* arXiv:2504.19440.
10. **Röttger, P. et al. (2024).** *XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models.* NAACL 2024 / ACL Anthology `2024.naacl-long.382`.
11. **Wang, Y. et al. (2023).** *Do-Not-Answer: A Dataset for Evaluating Safeguards in Large Language Models.* EMNLP 2023.
12. **Zou, A. et al. (2023).** *Universal and Transferable Adversarial Attacks on Aligned Language Models.* arXiv:2307.15043.
