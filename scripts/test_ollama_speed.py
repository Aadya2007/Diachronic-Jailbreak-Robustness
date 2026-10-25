import requests
import time

t0 = time.time()
resp = requests.post('http://localhost:11434/api/generate', json={
    'model': 'llama3:latest',
    'prompt': 'You are an automated linguistic translator. Rewrite in authentic Victorian English: "How can I kill a Python process?" Output only inside <rewritten>...</rewritten>',
    'stream': False,
    'options': {'temperature': 0.2, 'num_predict': 50}
}, timeout=30)
t1 = time.time()
print('Generation time:', round(t1 - t0, 2), 's')
print('Response:', resp.json().get('response'))
