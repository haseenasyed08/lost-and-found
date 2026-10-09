import json
import os
import shutil
import sys
import pandas as pd
from sqlalchemy import select, text

# Add backend directory to path
sys.path.insert(0, os.path.abspath('backend'))

from app.core.security import encrypt_json, hash_password
from app.core.config import settings
from app.db import SessionLocal, engine
from app.models import Base, Claim, HiddenDetail, Match, Place, Report, ReportImage, User, is_postgres
from app.services.embeddings import embed_clip_text, embed_image, embed_text
from app.services.imaging import ocr_text, save_image
from app.services.matching import run_matching
from app.services.verification import QUESTIONS

DATA_DIR = os.path.abspath('data/lost_found_dataset')
SPLIT = sys.argv[1] if len(sys.argv) > 1 else 'test'

COLORS = ['navy blue', 'black', 'grey', 'gray', 'red', 'green', 'maroon', 'blue', 'white', 'silver', 'brown', 'pink', 'orange']

def guess_color(desc):
    d = (desc or '').lower()
    return next((c.replace('gray', 'grey') for c in COLORS if c in d), 'black')

def seed():
    print(f"Starting seed process for split '{SPLIT}'...")
    if is_postgres:
        try:
            with engine.begin() as conn:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        except Exception as e:
            print("Notice on extension:", e)
            
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    # 1. Places
    places_df = pd.read_csv(os.path.join(DATA_DIR, 'campus_places.csv'))
    for r in places_df.itertuples():
        if not db.scalar(select(Place).where(Place.name == r.place)):
            db.add(Place(name=r.place, latitude=float(r.latitude), longitude=float(r.longitude)))
    db.commit()
    place_map = {p.name: p.id for p in db.scalars(select(Place)).all()}
    print(f"Loaded {len(place_map)} places.")
    
    # 2. Demo Admin User
    admin_user = db.scalar(select(User).where(User.email == 'admin@demo.test'))
    if not admin_user:
        admin_user = User(
            email='admin@demo.test',
            name='Moderator',
            role='moderator',
            password_hash=hash_password('admin12345')
        )
        db.add(admin_user)
        db.commit()
        print("Created moderator: admin@demo.test (password: admin12345)")
        
    # 3. Read dataset
    lost_df = pd.read_csv(os.path.join(DATA_DIR, 'lost_reports.csv'))
    found_df = pd.read_csv(os.path.join(DATA_DIR, 'found_reports.csv'))
    items_df = pd.read_csv(os.path.join(DATA_DIR, 'items_ground_truth.csv')).set_index('item_id')
    
    lost_split = lost_df[lost_df.split == SPLIT].copy()
    found_split = found_df[found_df.split == SPLIT].copy()
    
    # Ensure users exist
    all_users = sorted(set(lost_split.user_id) | set(found_split.user_id))
    user_map = {}
    for uid in all_users:
        email = f"{uid.lower()}@demo.test"
        u = db.scalar(select(User).where(User.email == email))
        if not u:
            u = User(
                email=email,
                name=f"Student {uid}",
                role='user',
                password_hash=hash_password('demo1234')
            )
            db.add(u)
            db.flush()
        user_map[uid] = u.id
    db.commit()
    print(f"Prepared {len(user_map)} user accounts (password: demo1234).")
    
    # 4. Insert Reports
    os.makedirs(os.path.join(settings.UPLOAD_DIR, 'private'), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, 'public'), exist_ok=True)
    
    lost_ids = []
    found_ids = []
    
    for kind, df in (('lost', lost_split), ('found', found_split)):
        print(f"Seeding {len(df)} {kind} reports...")
        for r in df.itertuples():
            cat = items_df.loc[r.item_id, 'category'] if kind == 'found' else r.category_reported
            group = QUESTIONS.get(cat, {}).get('group', 'other')
            when = pd.to_datetime(r.lost_time_reported if kind == 'lost' else r.found_time).to_pydatetime()
            
            p_name = r.place_reported
            p_id = place_map.get(p_name, list(place_map.values())[0])
            
            rep = Report(
                user_id=user_map[r.user_id],
                type=kind,
                category=cat,
                group=group,
                brand=str(getattr(r, 'brand', '') or '').strip(),
                color=guess_color(r.description),
                description=str(r.description).strip(),
                place_id=p_id,
                event_time=when,
                time_window_hours=float(getattr(r, 'time_window_hours', 1.0) or 1.0),
                txt_emb=embed_text(r.description),
                clip_txt_emb=embed_clip_text(r.description)
            )
            
            # Check image
            img_file = getattr(r, 'image_file', None)
            if pd.notna(img_file) and img_file:
                src_img = os.path.join('data/images', str(img_file))
                if os.path.exists(src_img):
                    with open(src_img, 'rb') as f_img:
                        priv, pub = save_image(f_img.read(), 'image/jpeg')
                    rep.img_emb = embed_image(priv)
                    rep.ocr_text = ocr_text(priv)
                    db.add(rep)
                    db.flush()
                    db.add(ReportImage(report_id=rep.id, private_path=priv, public_path=pub))
                else:
                    db.add(rep)
                    db.flush()
            else:
                db.add(rep)
                db.flush()
                
            if kind == 'found':
                try:
                    hidden = json.loads(r.hidden_details_json)
                    db.add(HiddenDetail(report_id=rep.id, payload=encrypt_json(hidden)))
                except Exception:
                    pass
                found_ids.append(rep.id)
            else:
                lost_ids.append(rep.id)
                
        db.commit()
        
    print(f"Running match engine across {len(lost_ids)} lost reports...")
    total_matches = 0
    for rid in lost_ids:
        ms = run_matching(db, rid)
        total_matches += len(ms)
    print(f"Generated {total_matches} suggested matches!")
    
    # 5. Create a sample claim in manual_review for the moderator queue demo
    any_match = db.scalar(select(Match).where(Match.status == 'suggested').limit(1))
    if any_match:
        test_claim = Claim(
            match_id=any_match.id,
            claimant_id=any_match.lost.user_id,
            decision='manual_review',
            n_correct=2,
            attempts=1,
            answers=encrypt_json({"q1": "black leather strap", "q2": "red logo tag", "q3": "small scratch on back"})
        )
        db.add(test_claim)
        db.commit()
        print("Created demo manual_review claim for moderator queue.")
        
    db.close()
    print("Seeding finished successfully!")

if __name__ == '__main__':
    seed()
