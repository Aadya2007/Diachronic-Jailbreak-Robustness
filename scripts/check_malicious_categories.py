import csv
with open('data/benchmark_shifted_eval.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
base_rows = [r for r in rows if r['condition'] == 'baseline']
print(f'Total baseline rows: {len(base_rows)}')
for r in base_rows:
    if r['ground_truth_binary'] == '1':
        print(f"{r['eval_id']} | {r['parent_prompt_id']} | {r['source_dataset']} | {r['category']} | {r['prompt_text']}")
