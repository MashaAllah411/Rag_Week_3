# Resources

Policy PDFs live here. Any `*.pdf` in this folder is read, OCR'd where it has embedded images, chunked, embedded and indexed into ChromaDB (at startup if the store is empty, on upload, or via *Documents > Re-index*).

Shipped documents:

- `InsurancePolicy.pdf` - SBI General private car insurance policy wording (21 pages)
- `Commercial_Vehicles_Package_Policy_93ee460add.pdf` - Oriental Insurance commercial vehicles package policy

`RAG_Explainer.md` is a historical explainer written during Week 3; the current design is in [`docs/architecture.md`](../docs/architecture.md).
