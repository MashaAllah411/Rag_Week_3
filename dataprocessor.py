from pdfreader import read_pdf
from chunker import chunk_pages
from embedder import embed_chunks
from vectorstore import store_in_pinecone
from typing import List

pdf_path = "./resources/InsurancePolicy.pdf"

def run():
    print("\n========== RAG PIPELINE STARTED ==========\n")

    # Step 1: Read Insurance Policy PDF and extract text
    pages = read_pdf(pdf_path)


    # Step 2: Chunk the data into smaller pieces
    chunks = chunk_pages(pages)


    # Step 3: Embed the chunks using OpenAI's embedding model
    embeddings = embed_chunks(chunks)


    # Step 4: Store the chunks and their embeddings in Pinecone
    store_in_pinecone(chunks, embeddings)
 


if __name__ == "__main__":
    run()
