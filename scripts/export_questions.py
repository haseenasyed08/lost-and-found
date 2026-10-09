import json
import os
import sys

# Ensure data directory is on python path
sys.path.insert(0, os.path.abspath('data/lost_found_dataset'))
from gen_dataset import CATS

out = {
    cat: {
        'group': spec['group'],
        'questions': {k: {'q': v[0], 'options': v[1]} for k, v in spec['hidden'].items()},
    }
    for cat, spec in CATS.items()
}

os.makedirs('backend/app/data', exist_ok=True)
with open('backend/app/data/questions.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)

print(f"Exported {len(out)} categories with questions to backend/app/data/questions.json")
