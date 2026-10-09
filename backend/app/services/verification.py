import json
import os
import secrets
import numpy as np
from .embeddings import text_model, embed_text

_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')
try:
    with open(_path, 'r', encoding='utf-8') as f:
        QUESTIONS = json.load(f)
except Exception:
    QUESTIONS = {}

def question_text(category: str, key: str) -> str:
    cat_spec = QUESTIONS.get(category, {})
    q_spec = cat_spec.get('questions', {}).get(key, {})
    return q_spec.get('q', f"Verification question for {key}")

def norm(s) -> str:
    return ' '.join(str(s or '').lower().strip().split())

def is_correct(category: str, key: str, truth: str, answer: str) -> bool:
    a, t = norm(answer), norm(truth)
    if not a or not t:
        return False
    # Exact or substring containment
    if a == t or (' ' + t + ' ') in (' ' + a + ' ') or t in a or a in t:
        return True
    
    opts = QUESTIONS.get(category, {}).get('questions', {}).get(key, {}).get('options', [])
    if not opts:
        return False
        
    m = text_model()
    if m is not None:
        try:
            vecs = m.encode([answer] + opts, normalize_embeddings=True)
            sims = vecs[1:] @ vecs[0]
            best = int(np.argmax(sims))
            return norm(opts[best]) == t and float(sims[best]) >= 0.45
        except Exception:
            pass
            
    # Fallback option matching
    for opt in opts:
        if norm(opt) in a and norm(opt) == t:
            return True
    return False

def score_answers(category: str, hidden: dict, answers: dict) -> dict:
    return {k: is_correct(category, k, truth, answers.get(k, '')) for k, truth in hidden.items()}

def decision_from(n_correct: int, n_questions: int) -> str:
    if n_correct == n_questions:
        return 'approved'
    if n_questions >= 3 and n_correct == n_questions - 1:
        return 'manual_review'
    return 'rejected'

def new_handover_code() -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(6))
