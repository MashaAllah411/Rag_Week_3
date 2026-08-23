from rag.core.scope_guard import _is_gibberish


def test_scope_guard_detects_gibberish_without_an_llm_call():
    assert _is_gibberish("jsadbjhbd")
    assert _is_gibberish("jdbhb msansquwdh")
    assert _is_gibberish("1234 !!!")
    assert not _is_gibberish("What does the policy cover?")
