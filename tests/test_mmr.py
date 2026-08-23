from rag.core.retrieval.mmr import cosine_similarity


def test_cosine_similarity_handles_orthogonal_and_zero_vectors():
    assert cosine_similarity([1, 0], [0, 1]) == 0.0
    assert cosine_similarity([0, 0], [1, 0]) == 0.0
