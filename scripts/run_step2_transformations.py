"""
Run Step 2 Transformations (Stratified Benchmark Batch)
Processes 50 base prompts (25 Malicious from JBB/AdvBench/DNA + 25 Benign from XSTest/BeaverTails)
Expands them into 200 total evaluation instances across all 4 conditions:
  - C1: Baseline (Contemporary Standard English)
  - C2: Historical / Diachronic Shift (Victorian)
  - C3: Socio-Regional Shift (Indian English)
  - C4: Combined Shift (19th-Century Colonial Regional)

Exports:
  - data/benchmark_eval_200.csv (Flat evaluation file ready for detectors)
  - data/benchmark_eval_200.json (Nested quadruplet file with full metrics)
  - reports/step2_transformation_report.md (Comprehensive validation report)
"""

import csv
import json
import statistics
import time
from transformation_engine import process_prompt_quadruplet

# 1. Load base 1,000 prompts
with open("data/seed_prompts_1000.csv", "r", encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

# Select a representative stratified 50-prompt sample:
# 25 Malicious (10 JBB, 8 AdvBench, 7 Do-Not-Answer)
# 25 Benign (15 XSTest, 10 BeaverTails)
malicious = [r for r in all_rows if r["label"] == "malicious"]
benign = [r for r in all_rows if r["label"] == "benign"]

selected_mal = (
    [m for m in malicious if m["source_dataset"] == "JailbreakBench"][:10] +
    [m for m in malicious if m["source_dataset"] == "AdvBench"][:8] +
    [m for m in malicious if m["source_dataset"] == "Do-Not-Answer"][:7]
)

selected_ben = (
    [b for b in benign if b["source_dataset"] == "XSTest"][:15] +
    [b for b in benign if b["source_dataset"] == "BeaverTails"][:10]
)

selected_prompts = selected_mal + selected_ben
print(f"Running Step 2 transformations on {len(selected_prompts)} base prompts (25 Malicious, 25 Benign)...")
print("This will produce 50 * 4 = 200 benchmark evaluation instances.\n")

quadruplets = []
flat_rows = []
start_time = time.time()

for idx, item in enumerate(selected_prompts):
    pid = item["prompt_id"]
    label = item["label"]
    t0 = time.time()
    print(f"[{idx+1}/{len(selected_prompts)}] Transforming {pid} ({label})...")
    
    quad = process_prompt_quadruplet(item)
    quadruplets.append(quad)
    
    # Flatten into standard benchmark evaluation rows
    for condition in ["baseline", "historical", "regional", "combined"]:
        cond_data = quad[condition]
        flat_rows.append({
            "eval_id": f"{pid}_{condition.upper()[:4]}",
            "parent_prompt_id": pid,
            "condition": condition,
            "prompt_text": cond_data["text"],
            "label": label,
            "ground_truth_binary": quad["ground_truth_binary"],
            "source_dataset": quad["source_dataset"],
            "category": quad["category"],
            "word_count": cond_data["word_count"],
            "cosine_similarity": cond_data["cosine_similarity"],
            "length_ratio": cond_data["length_ratio"]
        })
        
    dur = time.time() - t0
    print(f"     Done in {dur:.1f}s | Baseline: '{quad['baseline']['text'][:50]}...'")

total_dur = time.time() - start_time
print(f"\nAll transformations completed in {total_dur/60:.1f} minutes!")

# 2. Export Flat Evaluation Benchmark (200 instances)
csv_path = "data/benchmark_eval_200.csv"
fieldnames = [
    "eval_id", "parent_prompt_id", "condition", "prompt_text",
    "label", "ground_truth_binary", "source_dataset", "category",
    "word_count", "cosine_similarity", "length_ratio"
]
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in flat_rows:
        writer.writerow(r)

# 3. Export Nested JSON
json_path = "data/benchmark_eval_200.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(quadruplets, f, indent=2, ensure_ascii=False)

print(f"Saved flat benchmark CSV to {csv_path}")
print(f"Saved nested benchmark JSON to {json_path}")

# 4. Compute Statistical Validation Metrics
metrics = {"historical": {}, "regional": {}, "combined": {}}
for cond in ["historical", "regional", "combined"]:
    sims = [q[cond]["cosine_similarity"] for q in quadruplets]
    ratios = [q[cond]["length_ratio"] for q in quadruplets]
    metrics[cond] = {
        "mean_sim": statistics.mean(sims),
        "std_sim": statistics.stdev(sims),
        "min_sim": min(sims),
        "max_sim": max(sims),
        "mean_ratio": statistics.mean(ratios),
        "std_ratio": statistics.stdev(ratios)
    }

print("\n" + "="*65)
print("STEP 2 TRANSFORMATION VALIDATION SUMMARY")
print("="*65)
for cond in ["historical", "regional", "combined"]:
    m = metrics[cond]
    print(f"Condition: {cond.upper()}")
    print(f"  • Cosine Similarity (Nomic): mean = {m['mean_sim']:.3f} ± {m['std_sim']:.3f} (range: [{m['min_sim']:.3f}, {m['max_sim']:.3f}])")
    print(f"  • Word Length Ratio:         mean = {m['mean_ratio']:.2f} ± {m['std_ratio']:.2f}")

print("="*65)
