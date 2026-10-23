"""
Verify Scaled Dataset (1,000 Base Prompts)
Validates integrity, class balance, provenance, length statistics, and zero duplicates.
"""

import csv
import json
import statistics

csv_path = "data/seed_prompts_1000.csv"
json_path = "data/seed_prompts_1000.json"

with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open(json_path, "r", encoding="utf-8") as f:
    json_rows = json.load(f)

assert len(rows) == 1000, f"Expected 1,000 CSV rows, got {len(rows)}"
assert len(json_rows) == 1000, f"Expected 1,000 JSON rows, got {len(json_rows)}"

malicious = [r for r in rows if r["label"] == "malicious"]
benign = [r for r in rows if r["label"] == "benign"]

assert len(malicious) == 500, f"Expected 500 malicious, got {len(malicious)}"
assert len(benign) == 500, f"Expected 500 benign, got {len(benign)}"

# Uniqueness
prompts = [r["prompt"].lower().strip() for r in rows]
assert len(prompts) == len(set(prompts)), "Duplicate prompts detected!"

# Sources breakdown
mal_sources = {}
for m in malicious:
    mal_sources[m["source_dataset"]] = mal_sources.get(m["source_dataset"], 0) + 1

ben_sources = {}
for b in benign:
    ben_sources[b["source_dataset"]] = ben_sources.get(b["source_dataset"], 0) + 1

mal_words = [int(m["word_count"]) for m in malicious]
ben_words = [int(b["word_count"]) for b in benign]

print("="*65)
print("SCALED SEED DATASET VERIFICATION REPORT (1,000 PROMPTS)")
print("="*65)
print(f"Total Base Prompts: {len(rows)}")
print(f"Total Benchmark Instances under 4-Way Shift: {len(rows)*4:,}")
print(f"Malicious Ground Truth (y=1): {len(malicious)} (50.0%)")
print(f"Benign Ground Truth (y=0):    {len(benign)} (50.0%)")
print(f"Unique Prompts:               {len(set(prompts))} / {len(rows)}")

print("\n--- Malicious Sources (500 Total) ---")
for src, count in sorted(mal_sources.items()):
    print(f"  • {src:25s}: {count} prompts")

print("\n--- Benign Sources (500 Total) ---")
for src, count in sorted(ben_sources.items()):
    print(f"  • {src:25s}: {count} prompts")

print("\n--- Prompt Length Statistics (Words) ---")
print(f"Malicious Prompts: mean = {statistics.mean(mal_words):.1f}, "
      f"std = {statistics.stdev(mal_words):.1f}, min = {min(mal_words)}, max = {max(mal_words)}")
print(f"Benign Prompts:    mean = {statistics.mean(ben_words):.1f}, "
      f"std = {statistics.stdev(ben_words):.1f}, min = {min(ben_words)}, max = {max(ben_words)}")

print("\n--- Sample Prompts ---")
print("[MAL-0001] (JBB):        ", malicious[0]["prompt"])
print("[MAL-0101] (AdvBench):   ", malicious[100]["prompt"])
print("[MAL-0301] (Do-Not-Ans): ", malicious[300]["prompt"])
print("[BEN-0001] (XSTest):     ", benign[0]["prompt"])
print("[BEN-0251] (BeaverTails):", benign[250]["prompt"])
print("="*65)
print("ALL VERIFICATION CHECKS PASSED.")
