# ============================================================
# chunk_inspector.py
#
# HOW TO USE:
#   1. Run:  python chunk_inspector.py
#   2. A file called "chunk_map.txt" will be created.
#   3. Open chunk_map.txt and read through the chunks.
#   4. For each evaluation question, find which chunk(s) contain
#      the answer and note their IDs.
#   5. Use those real IDs in evaluation_dataset.json
# ============================================================

import os
from pdfreader import read_pdf
from chunker import chunk_pages

PDF_PATH = "./resources/InsurancePolicy.pdf"
OUTPUT_FILE = "chunk_map.txt"


def inspect_chunks():
    print("\n========== CHUNK INSPECTOR ==========\n")

    # -- Step 1: Read PDF -----------------------------------------
    print(f"[PDF] Reading: {PDF_PATH}")
    pages = read_pdf(PDF_PATH)
    print(f"   >> Extracted {len(pages)} pages\n")

    # -- Step 2: Chunk each page, tracking page numbers ----------
    # We chunk page-by-page so we know which page each chunk
    # came from. This matches what dataprocessor.py does.
    all_chunks = []       # list of (chunk_id, page_num, text)
    chunk_counter = 0

    for page_num, page_text in enumerate(pages, start=1):

        if not page_text or not page_text.strip():
            # Skip empty pages (some PDFs have blank pages)
            continue

        page_chunks = chunk_pages([page_text])

        for chunk_text in page_chunks:
            if chunk_text.strip():
                all_chunks.append((
                    f"chunk_{chunk_counter}",
                    page_num,
                    chunk_text
                ))
                chunk_counter += 1

    print(f"[CHUNKS] Total chunks created: {len(all_chunks)}\n")

    # -- Step 3: Print to console (brief view) -------------------
    print("Showing first 5 chunks as preview:\n")
    for chunk_id, page_num, text in all_chunks[:5]:
        print(f"  [{chunk_id}] (Page {page_num})")
        print(f"  {text[:120]}...")
        print()

    # -- Step 4: Save full map to a file -------------------------
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("CHUNK MAP — Use this to label evaluation_dataset.json\n")
        f.write("=" * 60 + "\n\n")

        for chunk_id, page_num, text in all_chunks:
            f.write(f"{'=' * 60}\n")
            f.write(f"ID   : {chunk_id}\n")
            f.write(f"Page : {page_num}\n")
            f.write(f"{'─' * 60}\n")
            f.write(f"{text}\n\n")

    print(f"[DONE] Full chunk map saved to: {OUTPUT_FILE}")
    print(f"   Open this file, read through the chunks,")
    print(f"   and note which chunk IDs contain answers")
    print(f"   to your evaluation questions.\n")
    print(f"   Total chunks to review: {len(all_chunks)}")
    print("\n=====================================\n")

    return all_chunks


if __name__ == "__main__":
    inspect_chunks()
