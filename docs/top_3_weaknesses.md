# Top 3 Known System Weaknesses (Unprompted)

**Author:** MashaAllah411  
**Date Authored:** Wednesday, Week 12 (Prior to Evaluation Panel Review)  
**System:** Policy Answer Desk (Variant C)  

> *"A demo where nothing ever fails means you are hiding the failures. Showing real limits and how to handle them proves engineering maturity."*

---

### Weakness 1: Rule-Based PII Scrubber Vulnerability to Obfuscated Colleague Names
* **The Weakness:** Our PII scrubber in `tracer.py` relies on deterministic regex matching for Grade bands (`Grade [1-7]`), currency amounts, and recognized employee directory names. If an employee queries a colleague using phonetic misspelling, leetspeak, or indirect hints (e.g., *"the female director who sits next to the printer in London"*), the regex scrubber will not flag the inquiry, potentially leaking context into developer logs.
* **Severity:** **HIGH**
* **The First Fix to Try:** Deploy a secondary, lightweight local Named Entity Recognition (NER) model (e.g. `gliner` or `spacy-en_core_web_sm`) run synchronously inside the span serializer to redact non-standard person entities.

---

### Weakness 2: Context Over-Compression in the Cross-Encoder Reranker
* **The Weakness:** When an employee asks a composite query involving multiple topics (e.g., *"What is my maternity entitlement, and can I carry over unused leave into next year?"*), the cross-encoder reranker scores high on the maternity clause and deprioritizes the annual leave carryover chunk, causing the second half of the question to fall back into a general summary.
* **Severity:** **MEDIUM**
* **The First Fix to Try:** Implement sub-query decomposition in the Query Rewriter: split conjunction queries into two atomic queries, retrieve top-2 chunks for each independently, and union the sets before synthesis.

---

### Weakness 3: Single-Instance Ollama Queue Saturation Under Concurrency
* **The Weakness:** Our local inference backend runs Ollama with a concurrency depth of 1 request at a time. While average latency is ~750ms on single requests, if 3 employees query simultaneously, request #3 waits over 2.2 seconds in FIFO queue.
* **Severity:** **MEDIUM**
* **The First Fix to Try:** Add an asynchronous Celery task queue with a Redis broker, or point `OLLAMA_HOST` to a multi-worker cluster with load balancing across dual GPUs.
