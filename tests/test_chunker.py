from rag.core.ingest.chunker import chunk_pages


def test_chunk_pages_applies_overlap():
    text = "a" * 30
    assert chunk_pages([text], chunk_size=20, chunk_overlap=5) == ["a" * 20, "a" * 15]
