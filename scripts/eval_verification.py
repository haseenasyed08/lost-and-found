import json
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('scripts'))

from features import DATA
from app.services.verification import decision_from, is_correct

def evaluate_claims():
    claims = pd.read_csv(DATA + 'verification_claims.csv')
    found = pd.read_csv(DATA + 'found_reports.csv').set_index('report_id')
    items = pd.read_csv(DATA + 'items_ground_truth.csv').set_index('item_id')

    name = {'approved': 'approve', 'manual_review': 'manual_review', 'rejected': 'reject'}
    rows = []
    
    print(f"Evaluating verification engine on {len(claims)} claim samples...")
    for c in claims.itertuples():
        f = found.loc[c.found_id]
        cat = items.loc[f['item_id'], 'category']
        n = 0
        hidden_details = json.loads(f['hidden_details_json'])
        for i, (key, truth) in enumerate(list(hidden_details.items())[:3], 1):
            ans = getattr(c, 'a%d' % i)
            n += int(is_correct(cat, key, truth, str(ans) if pd.notna(ans) else ''))
            
        rows.append({
            'claim_type': c.claim_type,
            'label': c.decision_label,
            'pred': name[decision_from(n, 3)]
        })
        
    df = pd.DataFrame(rows)
    print("\n--- Verification Confusion Matrix ---")
    ct = pd.crosstab(df.label, df.pred)
    print(ct)
    
    imp = df[df.claim_type == 'impostor']
    false_approval = (imp.pred == 'approve').mean()
    genuine_full = (df[df.claim_type == 'genuine_full'].pred == 'approve').mean()
    
    print("\n--- Key Verification Metrics ---")
    print(f"False Approval Rate (Impostors Approved): {false_approval:.1%}")
    print(f"Genuine Full Claims Approved:            {genuine_full:.1%}")

if __name__ == '__main__':
    evaluate_claims()
