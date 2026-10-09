import os
import sys
from types import SimpleNamespace as NS
import pandas as pd

sys.path.insert(0, os.path.abspath('backend'))
from app.services.embeddings import embed_text
from app.services.matching import FEATURES, pair_components

DATA = os.path.abspath('data/lost_found_dataset') + os.sep
places = pd.read_csv(DATA + 'campus_places.csv').set_index('place')
L = pd.read_csv(DATA + 'lost_reports.csv').set_index('report_id')
F = pd.read_csv(DATA + 'found_reports.csv').set_index('report_id')

COLORS = ['navy blue', 'black', 'grey', 'gray', 'red', 'green', 'maroon', 'blue', 'white', 'silver', 'brown', 'pink', 'orange']
_cache = {}

def guess_color(desc):
    d = (desc or '').lower()
    return next((c.replace('gray', 'grey') for c in COLORS if c in d), '')

def get(kind, rid):
    key = (kind, rid)
    if key not in _cache:
        row = (L if kind == 'lost' else F).loc[rid]
        p = places.loc[row['place_reported']]
        when = row['lost_time_reported'] if kind == 'lost' else row['found_time']
        window = getattr(row, 'time_window_hours', 1.0) if kind == 'lost' else 1.0
        _cache[key] = NS(
            place=NS(latitude=float(p['latitude']), longitude=float(p['longitude'])),
            event_time=pd.to_datetime(when).to_pydatetime(),
            time_window_hours=float(window or 1.0),
            txt_emb=embed_text(str(row['description'])),
            img_emb=None,
            clip_txt_emb=None,
            color=guess_color(str(row['description'])),
            brand='',
            ocr_text=''
        )
    return _cache[key]

def vector(comp):
    return [-1.0 if comp.get(k) is None else comp[k] for k in FEATURES]
