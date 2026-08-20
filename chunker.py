import re
import numpy as np
from typing import List, Callable, Dict, Any

def chunk_pages(
    pages: List[str],
    chunk_size: int = 900,
    chunk_overlap: int = 150
) -> List[str]:
    """
    Fixed-size character chunking with overlap.
    Preserved for backward compatibility.
    """
    chunks: List[str] = []

    for text in pages:
        start = 0
        n = len(text)

        while start < n:
            end = min(start + chunk_size, n)
            chunk = text[start:end]

            last_period = chunk.rfind(". ")
            if last_period != -1 and end < n and (last_period > chunk_size * 0.5):
                end = start + last_period + 2
                chunk = text[start:end]

            chunks.append(chunk.strip())
            start = max(end - chunk_overlap, end)

    return chunks


def semantic_chunking(
    pages: List[str],
    embed_fn: Callable[[List[str]], List[List[float]]],
    threshold: float = 0.7,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1500
) -> List[str]:
    """
    Semantic chunking. Splits page content into sentences, calculates
    embeddings of neighboring sentences, and places boundaries where
    the similarity falls below the threshold.
    """
    chunks: List[str] = []
    
    for page_text in pages:
        if not page_text or not page_text.strip():
            continue
            
        # Split page into sentences using regex
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', page_text) if s.strip()]
        if not sentences:
            continue
            
        # Generate sentence embeddings using sentence-transformers (passed via embed_fn)
        embeddings = embed_fn(sentences)
        
        current_chunk_sentences = [sentences[0]]
        
        for i in range(len(sentences) - 1):
            vec1 = np.array(embeddings[i])
            vec2 = np.array(embeddings[i+1])
            norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            sim = float(np.dot(vec1, vec2) / norm) if norm > 0 else 0.0
            
            current_len = len(" ".join(current_chunk_sentences))
            
            # Boundary trigger: similarity < threshold (if long enough) or size exceeds max
            if (sim < threshold and current_len >= min_chunk_size) or (current_len >= max_chunk_size):
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = [sentences[i+1]]
            else:
                current_chunk_sentences.append(sentences[i+1])
                
        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
    return chunks


def keyword_chunking(
    pages: List[str],
    keyword_threshold: float = 0.2,
    min_chunk_size: int = 300,
    max_chunk_size: int = 1200
) -> List[str]:
    """
    Keyword-based chunking. Detects domain-specific keywords and splits
    boundaries when sentence keyword overlap is low, preserving context
    around related terminology.
    """
    chunks: List[str] = []
    
    # Standard English stopwords
    stopwords = {
        'the', 'and', 'of', 'in', 'to', 'for', 'a', 'is', 'that', 'on', 'it', 'with', 
        'as', 'by', 'at', 'an', 'be', 'this', 'are', 'from', 'or', 'have', 'your', 'will', 
        'shall', 'may', 'any', 'all', 'such', 'who', 'which', 'their', 'them', 'they', 
        'our', 'us', 'we', 'he', 'she', 'his', 'her', 'been', 'has', 'had', 'do', 'does'
    }
    
    for page_text in pages:
        if not page_text or not page_text.strip():
            continue
            
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', page_text) if s.strip()]
        if not sentences:
            continue
            
        # Extract keywords for this page
        words = re.findall(r'\b[a-zA-Z]{3,}\b', page_text.lower())
        freq = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1
                
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = {w for w, f in sorted_words[:15]}
        
        current_chunk = []
        current_keywords = set()
        
        for sentence in sentences:
            sent_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower()))
            sent_keywords = sent_words.intersection(top_keywords)
            
            current_len = len(" ".join(current_chunk + [sentence]))
            
            if not current_chunk:
                current_chunk.append(sentence)
                current_keywords = sent_keywords
                continue
                
            jaccard = 0.0
            if current_keywords and sent_keywords:
                jaccard = len(current_keywords.intersection(sent_keywords)) / len(current_keywords.union(sent_keywords))
                
            if current_len > max_chunk_size or (current_len >= min_chunk_size and jaccard < keyword_threshold):
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_keywords = sent_keywords
            else:
                current_chunk.append(sentence)
                current_keywords = current_keywords.union(sent_keywords)
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
    return chunks


def chunk_document(
    pages: List[str],
    strategy: str,
    embed_fn: Callable[[List[str]], List[List[float]]] = None,
    **kwargs
) -> List[str]:
    """
    Unified entry point for chunking a document using one of the three strategies.
    """
    if strategy == "fixed":
        chunk_size = kwargs.get("chunk_size", 900)
        chunk_overlap = kwargs.get("chunk_overlap", 150)
        return chunk_pages(pages, chunk_size, chunk_overlap)
        
    elif strategy == "semantic":
        if not embed_fn:
            raise ValueError("Embedding function is required for semantic chunking")
        threshold = kwargs.get("semantic_threshold", 0.7)
        return semantic_chunking(pages, embed_fn, threshold)
        
    elif strategy == "keyword":
        threshold = kwargs.get("keyword_threshold", 0.2)
        return keyword_chunking(pages, threshold)
        
    else:
        raise ValueError(f"Unknown chunking strategy: '{strategy}'")
