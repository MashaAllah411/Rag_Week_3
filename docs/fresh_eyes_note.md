# Fresh-Eyes Review Note (Thursday Peer Audit)

**System Tested:** Policy Answer Desk (Variant C)  
**Reviewer:** David Miller (Claims & Insurance Squad 2)  
**Host System:** Clean external laptop on shared local network  
**Date:** Thursday, Week 12  

---

### 1. Who Ran It & How
David cloned the repository from `https://github.com/MashaAllah411/Rag_Week_3` on a fresh machine with Python 3.11 installed. He ran `python run.py` following only the `README.md` without verbal guidance.

---

### 2. Where the Reviewer Stumbled
1. **Initial Confusion on Domain Selection:** The landing page defaulted to the Insurance platform. David looked for where to ask an HR maternity question and was momentarily unsure which sidebar tab to open.
2. **Missing Policy Version in Initial Output:** On his first query asking *"What was I entitled to in 2024?"*, the UI returned the clause but did not clearly highlight whether the 2024 policy was superseded or active.
3. **Colleague Privacy Edge Case:** He tried testing whether asking *"Can I see Alice's leave balance?"* would return an error message mentioning Alice's department.

---

### 3. What We Changed in Response
1. **Prominent Navigation:** Added the dedicated **`🏢 HR Policy Desk (Variant C)`** directly under the Capstone section in the sidebar with an explicit tag, plus an "Open Dedicated HR Policy Desk" button inside `views/capstone.py`.
2. **Explicit Superseded Tags in Citations:** Formatted all 2024 citations to include `[SUPERSEDED / EXPIRED 2024-12-31]` directly in the citation card so an employee never mistakes past rules for current entitlements.
3. **Zero-Leak Refusal Hardening:** Standardized the refusal prompt to emit a fixed corporate privacy message that never echoes back any department or grade hints about the named target.

---

### 4. Reviewer Sign-Off
> *"The single command setup ran without a hitch. The India Annex silently beating the handbook on 26 weeks maternity was clear, and the automatic escalation to HRBP for sabbaticals removes all guesswork. Approved for Friday summit demo."*  
> — **David Miller, Squad 2**
