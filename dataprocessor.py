from pdfreader import read_pdf
from chunker import chunk_pages
from embedder import embed_chunks
from vectorstore import store_in_pinecone
from typing import List

pdf_path = "./resources/HRPolicy.pdf"

def run():
    print("\n========== RAG PIPELINE STARTED ==========\n")

    # Step 1: Read HR Policy PDF and extract text
    print("📄 Step 1: Reading PDF...")
    pages = read_pdf(pdf_path)
    print(f"   ✅ Extracted {len(pages)} pages from '{pdf_path}'\n")

    # Step 2: Chunk the data into smaller pieces
    print("✂️  Step 2: Chunking pages...")
    chunks = chunk_pages(pages)
    print(f"   ✅ Created {len(chunks)} chunks")
    print(f"   📌 Sample chunk (first 200 chars):\n   \"{chunks[0][:200]}...\"\n")

    # Step 3: Embed the chunks using OpenAI's embedding model
    print("🧠 Step 3: Embedding chunks with OpenAI (this may take a moment)...")
    embeddings = embed_chunks(chunks)
    print(f"   ✅ Generated {len(embeddings)} embeddings")
    print(f"   📐 Embedding dimension: {len(embeddings[0])}\n")

    # Step 4: Store the chunks and their embeddings in Pinecone
    print("📌 Step 4: Storing vectors in Pinecone...")
    store_in_pinecone(chunks, embeddings)
    print(f"   ✅ Successfully upserted {len(chunks)} vectors into Pinecone index!\n")

    print("========== PIPELINE COMPLETE ✅ ==========\n")


if __name__ == "__main__":
    run()
