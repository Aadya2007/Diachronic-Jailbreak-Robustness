"""
Curate Scaled Seed Dataset (1,000 Base Prompts -> 4,000 Benchmark Instances)
Preserves 100% Ground-Truth Accuracy using Verified Published Benchmarks:

Malicious (500 Prompts):
  - 100 from JailbreakBench (NeurIPS 2024): 10 categories x 10 behaviors
  - 200 from AdvBench (USENIX/NeurIPS): high-severity malicious instructions
  - 200 from Do-Not-Answer (EMNLP 2023): question-form risk requests

Benign (500 Prompts):
  - 250 from XSTest (NAACL 2024): ALL 250 safe hard negatives across 10 categories
  - 250 from BeaverTails (NeurIPS 2023): verified safe assistance and educational queries

Total: Exactly 1,000 base prompts (50% Malicious, 50% Benign).
When expanded under 4-way factorial shift, produces 4,000 benchmark evaluation prompts.
"""

import os
import csv
import json
import gzip
import urllib.request
import io

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data", exist_ok=True)

print("Curating 1,000 high-accuracy seed prompts...")

# ==========================================
# 1. MALICIOUS (500 PROMPTS)
# ==========================================
malicious_prompts = []
mal_id = 1

# A. JailbreakBench (100 prompts)
jbb_path = "data/raw/jbb_harmful_behaviors.csv"
with open(jbb_path, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        goal = row["Goal"].strip()
        malicious_prompts.append({
            "prompt_id": f"MAL-{mal_id:04d}",
            "prompt": goal,
            "label": "malicious",
            "ground_truth_binary": 1,
            "source_dataset": "JailbreakBench",
            "category": row["Category"].strip(),
            "subcategory": row["Behavior"].strip(),
            "target_response_prefix": row.get("Target", "").strip(),
            "word_count": len(goal.split())
        })
        mal_id += 1
print(f"Added {len(malicious_prompts)} prompts from JailbreakBench.")

# B. AdvBench (200 prompts)
adv_raw_path = "data/raw/advbench_harmful_behaviors.csv"
if not os.path.exists(adv_raw_path):
    print("Downloading AdvBench...")
    req = urllib.request.Request(
        "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as resp:
        with open(adv_raw_path, "wb") as f:
            f.write(resp.read())

existing_prompts = set(m["prompt"].lower().strip() for m in malicious_prompts)
with open(adv_raw_path, "r", encoding="utf-8") as f:
    adv_count = 0
    for row in csv.DictReader(f):
        goal = row["goal"].strip()
        if goal.lower() not in existing_prompts and adv_count < 200:
            malicious_prompts.append({
                "prompt_id": f"MAL-{mal_id:04d}",
                "prompt": goal,
                "label": "malicious",
                "ground_truth_binary": 1,
                "source_dataset": "AdvBench",
                "category": "Imperative Harm",
                "subcategory": "Adversarial Goal",
                "target_response_prefix": row.get("target", "").strip(),
                "word_count": len(goal.split())
            })
            existing_prompts.add(goal.lower())
            mal_id += 1
            adv_count += 1
print(f"Added {adv_count} unique prompts from AdvBench.")

# C. Do-Not-Answer (200 prompts)
dna_raw_path = "data/raw/do_not_answer_data_en.csv"
if not os.path.exists(dna_raw_path):
    print("Downloading Do-Not-Answer...")
    req = urllib.request.Request(
        "https://huggingface.co/datasets/LibrAI/do-not-answer/raw/main/data_en.csv",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as resp:
        with open(dna_raw_path, "wb") as f:
            f.write(resp.read())

with open(dna_raw_path, "r", encoding="utf-8") as f:
    dna_count = 0
    for row in csv.DictReader(f):
        q = row["question"].strip()
        if q.lower() not in existing_prompts and dna_count < 200:
            malicious_prompts.append({
                "prompt_id": f"MAL-{mal_id:04d}",
                "prompt": q,
                "label": "malicious",
                "ground_truth_binary": 1,
                "source_dataset": "Do-Not-Answer",
                "category": row.get("risk_area", "Risk Area").strip(),
                "subcategory": row.get("types_of_harm", "").strip(),
                "target_response_prefix": "",
                "word_count": len(q.split())
            })
            existing_prompts.add(q.lower())
            mal_id += 1
            dna_count += 1
print(f"Added {dna_count} unique prompts from Do-Not-Answer.")
assert len(malicious_prompts) == 500, f"Expected 500 malicious, got {len(malicious_prompts)}"

# ==========================================
# 2. BENIGN (500 PROMPTS)
# ==========================================
benign_prompts = []
ben_id = 1

# A. XSTest Safe (ALL 250 prompts)
xstest_raw_path = "data/raw/xstest_prompts.csv"
with open(xstest_raw_path, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row.get("label") == "safe":
            p = row["prompt"].strip()
            focus = row.get("focus", "").strip()
            note = row.get("note", "").strip()
            benign_prompts.append({
                "prompt_id": f"BEN-{ben_id:04d}",
                "prompt": p,
                "label": "benign",
                "ground_truth_binary": 0,
                "source_dataset": "XSTest",
                "category": row["type"].strip(),
                "subcategory": f"Focus: {focus} | Note: {note}".strip(" |"),
                "target_response_prefix": "",
                "word_count": len(p.split())
            })
            ben_id += 1
print(f"Added {len(benign_prompts)} safe hard-negative prompts from XSTest.")

# B. BeaverTails Safe (250 prompts)
bt_raw_path = "data/raw/beavertails_30k_test.jsonl.gz"
if not os.path.exists(bt_raw_path):
    print("Downloading BeaverTails 30k test slice...")
    req = urllib.request.Request(
        "https://huggingface.co/datasets/PKU-Alignment/BeaverTails/resolve/main/round0/30k/test.jsonl.gz",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as resp:
        with open(bt_raw_path, "wb") as f:
            f.write(resp.read())

existing_benign = set(b["prompt"].lower().strip() for b in benign_prompts)
bt_count = 0
with gzip.GzipFile(bt_raw_path, "rb") as gz:
    for line in gz:
        item = json.loads(line.decode("utf-8"))
        if item.get("is_safe") is True:
            p = item["prompt"].strip()
            # Clean filtering: only well-formed prompts with 4 to 35 words
            words = p.split()
            if 4 <= len(words) <= 35 and p.lower() not in existing_benign and bt_count < 250:
                benign_prompts.append({
                    "prompt_id": f"BEN-{ben_id:04d}",
                    "prompt": p,
                    "label": "benign",
                    "ground_truth_binary": 0,
                    "source_dataset": "BeaverTails",
                    "category": "Everyday Assistance & Educational",
                    "subcategory": "Verified Safe Interaction",
                    "target_response_prefix": "",
                    "word_count": len(words)
                })
                existing_benign.add(p.lower())
                ben_id += 1
                bt_count += 1
print(f"Added {bt_count} verified safe prompts from BeaverTails.")
assert len(benign_prompts) == 500, f"Expected 500 benign, got {len(benign_prompts)}"

# ==========================================
# 3. COMBINE & EXPORT
# ==========================================
all_prompts = malicious_prompts + benign_prompts
assert len(all_prompts) == 1000, f"Expected 1,000 prompts, got {len(all_prompts)}"

# Verify uniqueness
all_texts = [p["prompt"].lower().strip() for p in all_prompts]
assert len(all_texts) == len(set(all_texts)), "Duplicate prompts detected across combined sets!"

csv_path = "data/seed_prompts_1000.csv"
json_path = "data/seed_prompts_1000.json"
fieldnames = [
    "prompt_id", "prompt", "label", "ground_truth_binary",
    "source_dataset", "category", "subcategory",
    "target_response_prefix", "word_count"
]

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for item in all_prompts:
        writer.writerow(item)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_prompts, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print(f"SUCCESS: Curated {len(all_prompts)} Base Prompts!")
print(f"CSV exported to:  {csv_path}")
print(f"JSON exported to: {json_path}")
print("Class Balance:")
print(f"  • Malicious: {len(malicious_prompts)} (50.0%) [100 JBB + 200 AdvBench + 200 Do-Not-Answer]")
print(f"  • Benign:    {len(benign_prompts)} (50.0%) [250 XSTest Safe + 250 BeaverTails Safe]")
print(f"Total Test Cases Under 4-Way Shift: {len(all_prompts) * 4:,} prompts")
print("="*60)
