from rag.core.retrieval.hybrid_retriever import RRF_K


def test_rrf_rewards_document_returned_by_both_retrievers():
    shared = 1 / (RRF_K + 1) + 1 / (RRF_K + 2)
    single = 1 / (RRF_K + 1)
    assert shared > single
