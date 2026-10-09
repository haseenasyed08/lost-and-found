import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath('scripts'))
sys.path.insert(0, os.path.abspath('backend'))

from features import DATA, F, get, pair_components
from app.services import matching

M = pd.read_csv(DATA + 'matches_ground_truth.csv')
M = M[M.split == 'test']
truth = dict(zip(M.lost_id, M.found_id))
found_ids = list(F[F.split == 'test'].index)

print(f"Evaluating on test split: {len(truth)} lost items with true matches against {len(found_ids)} candidates.")

comps = {
    lid: [pair_components(get('lost', lid), get('found', f)) for f in found_ids]
    for lid in truth
}

def report(name, scorer):
    ranks = []
    for lid, fid in truth.items():
        s = np.array([scorer(c) for c in comps[lid]])
        order = [found_ids[i] for i in np.argsort(-s)]
        if fid in order:
            ranks.append(order.index(fid) + 1)
        else:
            ranks.append(len(order) + 1)
    r = np.array(ranks)
    print('%-32s R@1 %.2f  R@5 %.2f  MRR %.3f' % (name, (r == 1).mean(), (r <= 5).mean(), (1.0 / r).mean()))

def only(keys):
    return lambda c: sum(matching.WEIGHTS[k] * (c[k] or 0.0) for k in keys if c.get(k) is not None)

print("--- Retrieval Baselines & Ablations ---")
report('TF-IDF / Text Only', only(['text']))
report('Geo & Time Only', only(['geo', 'time']))
report('Text + Geo + Time', only(['text', 'geo', 'time']))
report('Text + Geo + Time + Color', only(['text', 'geo', 'time', 'color']))
report('Weighted Multi-Factor (All)', matching.weighted_score)

ranker_path = os.path.abspath('backend/app/data/ranker.txt')
if os.path.exists(ranker_path):
    learned = matching.load_ranker(ranker_path)
    if learned:
        report('Learned Ranker (LightGBM)', learned)
