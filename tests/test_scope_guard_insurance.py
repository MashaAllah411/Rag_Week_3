from rag.core.scope_guard import check_question_scope


def test_scope_guard_allows_common_insurance_spelling_variant():
    decision = check_question_scope("What is the Insurence company name?")
    assert decision.allowed
    assert decision.reason == "insurance_terms"
