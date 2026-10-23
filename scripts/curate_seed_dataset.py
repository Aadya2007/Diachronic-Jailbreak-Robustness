"""
Curate Seed Dataset (Step 1)
Downloads JailbreakBench (100 harmful behaviors) and XSTest (250 safe prompts).
Selects:
  - 100 Malicious behaviors (all 100 JBB behaviors, 10 per category across 10 categories)
  - 100 Benign hard-negative prompts (10 stratified per category across 10 XSTest categories)
Total: 200 balanced seed prompts with standardized schema.
"""

import os
import urllib.request
import csv
import json
import io

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("scripts", exist_ok=True)

# 1. Download raw JailbreakBench harmful behaviors
jbb_url = "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/raw/main/data/harmful-behaviors.csv"
jbb_raw_path = "data/raw/jbb_harmful_behaviors.csv"
print(f"Downloading JailbreakBench from {jbb_url}...")
req = urllib.request.Request(jbb_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    jbb_bytes = resp.read()
    with open(jbb_raw_path, "wb") as f:
        f.write(jbb_bytes)
print(f"Saved JBB to {jbb_raw_path} ({len(jbb_bytes)} bytes)")

# 2. Download raw XSTest prompts
xstest_url = "https://raw.githubusercontent.com/paul-rottger/xstest/main/xstest_prompts.csv"
xstest_raw_path = "data/raw/xstest_prompts.csv"
print(f"Downloading XSTest from {xstest_url}...")
req = urllib.request.Request(xstest_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    xstest_bytes = resp.read()
    with open(xstest_raw_path, "wb") as f:
        f.write(xstest_bytes)
print(f"Saved XSTest to {xstest_raw_path} ({len(xstest_bytes)} bytes)")

# 3. Process JBB harmful behaviors (100 malicious)
malicious_items = []
with open(jbb_raw_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for idx, row in enumerate(reader):
        pid = f"MAL-{idx+1:03d}"
        goal = row["Goal"].strip()
        category = row["Category"].strip()
        behavior = row["Behavior"].strip()
        target = row.get("Target", "").strip()
        source = row.get("Source", "").strip()
        words = goal.split()
        
        malicious_items.append({
            "prompt_id": pid,
            "prompt": goal,
            "label": "malicious",
            "ground_truth_binary": 1,
            "source_dataset": "JailbreakBench",
            "category": category,
            "subcategory_or_behavior": behavior,
            "focus_or_note": f"Source: {source}" if source else "",
            "target_response_prefix": target,
            "word_count": len(words)
        })

print(f"Processed {len(malicious_items)} malicious prompts from JailbreakBench.")

# Verify distribution of malicious categories
mal_cat_counts = {}
for m in malicious_items:
    mal_cat_counts[m["category"]] = mal_cat_counts.get(m["category"], 0) + 1
print("Malicious counts by category:", mal_cat_counts)

# 4. Process XSTest safe prompts (10 per category across 10 categories = 100 benign)
with open(xstest_raw_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    safe_rows = [r for r in reader if r.get("label") == "safe"]

print(f"Total safe rows in XSTest: {len(safe_rows)}")

# Stratify by category (type) and select first 10 representative prompts from each
xstest_by_type = {}
for r in safe_rows:
    t = r["type"].strip()
    xstest_by_type.setdefault(t, []).append(r)

benign_items = []
ben_idx = 1
for t, rows in sorted(xstest_by_type.items()):
    selected = rows[:10]  # Take 10 prompts per category
    for r in selected:
        pid = f"BEN-{ben_idx:03d}"
        prompt = r["prompt"].strip()
        focus = r.get("focus", "").strip()
        note = r.get("note", "").strip()
        focus_note = f"Focus: {focus} | Note: {note}".strip(" |")
        words = prompt.split()
        
        benign_items.append({
            "prompt_id": pid,
            "prompt": prompt,
            "label": "benign",
            "ground_truth_binary": 0,
            "source_dataset": "XSTest",
            "category": t,
            "subcategory_or_behavior": focus if focus else t,
            "focus_or_note": focus_note,
            "target_response_prefix": "",
            "word_count": len(words)
        })
        ben_idx += 1

print(f"Selected {len(benign_items)} benign prompts from XSTest across {len(xstest_by_type)} categories.")

ben_cat_counts = {}
for b in benign_items:
    ben_cat_counts[b["category"]] = ben_cat_counts.get(b["category"], 0) + 1
print("Benign counts by category:", ben_cat_counts)

# 5. Combine and export
all_prompts = malicious_items + benign_items
assert len(all_prompts) == 200, f"Expected 200 prompts, got {len(all_prompts)}"

csv_path = "data/seed_prompts_200.csv"
fieldnames = [
    "prompt_id", "prompt", "label", "ground_truth_binary", 
    "source_dataset", "category", "subcategory_or_behavior", 
    "focus_or_note", "target_response_prefix", "word_count"
]

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for item in all_prompts:
        writer.writerow(item)

json_path = "data/seed_prompts_200.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_prompts, f, indent=2, ensure_ascii=False)

print(f"\nSuccessfully generated {csv_path} and {json_path} with 200 balanced seed prompts!")
