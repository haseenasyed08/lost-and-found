import os
import sys
import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath('scripts'))
from features import DATA, get, pair_components, vector

P = pd.read_csv(DATA + 'candidate_pairs.csv')

def build(split):
    d = P[P.split == split].sort_values('lost_id')
    X, y, groups = [], [], []
    for _, grp in d.groupby('lost_id', sort=False):
        for r in grp.itertuples():
            X.append(vector(pair_components(get('lost', r.lost_id), get('found', r.found_id))))
            y.append(int(r.label == 'positive'))
        groups.append(len(grp))
    return np.array(X), np.array(y), groups

def train():
    print("Building training and validation sets...")
    Xtr, ytr, gtr = build('train')
    Xva, yva, gva = build('val')
    print(f"Train samples: {len(Xtr)} across {len(gtr)} query groups.")
    print(f"Val samples: {len(Xva)} across {len(gva)} query groups.")

    model = lgb.LGBMRanker(
        objective='lambdarank',
        n_estimators=150,
        learning_rate=0.05,
        num_leaves=15,
        random_state=42
    )

    model.fit(
        Xtr, ytr,
        group=gtr,
        eval_set=[(Xva, yva)],
        eval_group=[gva],
        eval_at=[1, 5]
    )

    out_path = os.path.abspath('backend/app/data/ranker.txt')
    model.booster_.save_model(out_path)
    importances = dict(zip(['text', 'image', 'color', 'brand', 'geo', 'time', 'ocr'], model.feature_importances_))
    print(f"Saved ranker to {out_path}")
    print("Feature importance:", importances)

if __name__ == '__main__':
    train()
