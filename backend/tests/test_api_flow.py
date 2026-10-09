import datetime as dt
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db import SessionLocal
from app.main import app
from app.models import Place

def signup(client, name):
    email = uuid.uuid4().hex[:8] + '@test.dev'
    r = client.post('/auth/register', json={'email': email, 'name': name, 'password': 'password123'})
    assert r.status_code == 200
    return {'Authorization': 'Bearer ' + r.json()['access_token']}

def test_full_recovery_flow():
    hidden = {
        'front_pocket_contents': 'two notebooks',
        'inner_lining_color': 'red',
        'tag_or_sticker': 'a yellow ribbon on the zip'
    }
    with TestClient(app) as client:
        db = SessionLocal()
        place = db.scalar(select(Place).limit(1))
        if place is None:
            place = Place(name='Test Main Library', latitude=12.9, longitude=77.5)
            db.add(place)
            db.commit()
            db.refresh(place)
            
        owner = signup(client, 'Owner User')
        finder = signup(client, 'Finder User')
        when = dt.datetime.utcnow() - dt.timedelta(hours=3)
        base = {'category': 'backpack', 'color': 'black', 'place_id': place.id}
        
        # 1. Finder creates found report with private details
        found = client.post(
            '/reports',
            headers=finder,
            data={
                **base,
                'type': 'found',
                'description': 'Found a black Nike backpack near the library front desk',
                'event_time': (when + dt.timedelta(hours=1)).isoformat(),
                'hidden_details': json.dumps(hidden)
            }
        )
        assert found.status_code == 200, found.text
        found_data = found.json()
        
        # 2. Owner creates lost report
        lost = client.post(
            '/reports',
            headers=owner,
            data={
                **base,
                'type': 'lost',
                'description': 'Lost my black Nike backpack with a white logo and padded straps',
                'event_time': when.isoformat()
            }
        )
        assert lost.status_code == 200, lost.text
        lost_data = lost.json()
        
        # 3. Check suggested matches
        matches_res = client.get(f"/reports/{lost_data['id']}/matches", headers=owner)
        assert matches_res.status_code == 200
        matches = matches_res.json()
        assert len(matches) > 0
        target_match = next(m for m in matches if m['other']['id'] == found_data['id'])
        mid = target_match['match_id']
        
        # 4. Start claim
        claim_res = client.post(f"/matches/{mid}/claim", headers=owner)
        assert claim_res.status_code == 200
        claim_data = claim_res.json()
        assert len(claim_data['questions']) == 3
        
        # 5. Submit correct answers
        ans_res = client.post(
            f"/claims/{claim_data['claim_id']}/answers",
            headers=owner,
            json={'answers': hidden}
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert ans_data['result'] == 'approved'
        assert ans_data['handover_code'] is not None
        code = ans_data['handover_code']
        
        # 6. Finder confirms handover with the code
        confirm_res = client.post(
            f"/claims/{claim_data['claim_id']}/confirm",
            headers=finder,
            json={'code': code}
        )
        assert confirm_res.status_code == 200
        assert confirm_res.json()['ok'] is True
        
        db.close()
