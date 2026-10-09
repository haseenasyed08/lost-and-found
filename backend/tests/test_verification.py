from app.services.verification import decision_from, is_correct

def test_exact_and_embedded_answers_are_correct():
    assert is_correct('backpack', 'inner_lining_color', 'red', 'Red')
    assert is_correct('backpack', 'inner_lining_color', 'red', 'I think the lining is red')
    assert not is_correct('backpack', 'inner_lining_color', 'red', '')

def test_decision_bands():
    assert decision_from(3, 3) == 'approved'
    assert decision_from(2, 3) == 'manual_review'
    assert decision_from(1, 3) == 'rejected'
    assert decision_from(0, 3) == 'rejected'
