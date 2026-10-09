import datetime as dt
from types import SimpleNamespace as NS
from app.services.matching import pair_components, weighted_score

def mk(lat, lon, t, emb=(1.0, 0.0)):
    return NS(
        place=NS(latitude=lat, longitude=lon),
        event_time=t,
        time_window_hours=1.0,
        txt_emb=list(emb),
        img_emb=None,
        clip_txt_emb=None,
        color='black',
        brand='',
        ocr_text=''
    )

def test_near_and_recent_beats_far_and_old():
    t0 = dt.datetime(2026, 9, 1, 14, 0)
    lost = mk(12.9, 77.5, t0)
    near = mk(12.9001, 77.5001, t0 + dt.timedelta(minutes=30))
    far = mk(12.95, 77.55, t0 + dt.timedelta(days=4))
    
    s_near = weighted_score(pair_components(lost, near))
    s_far = weighted_score(pair_components(lost, far))
    assert s_near > s_far

def test_found_long_before_lost_gets_zero_time_score():
    t0 = dt.datetime(2026, 9, 1, 14, 0)
    lost = mk(12.9, 77.5, t0)
    found_earlier = mk(12.9, 77.5, t0 - dt.timedelta(hours=5))
    comp = pair_components(lost, found_earlier)
    assert comp['time'] == 0.0
