# AI Use Declaration
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  
**Date:** October 2026  

---

## 1. Purpose of This Declaration

The COEN838 exam instructions (item F) require students to *"ensure responsible and ethical use of AI."* This document fulfils that requirement by transparently disclosing:

1. **Where** AI assistance was used in this project.
2. **How** it was used (as a learning aid, not as a substitute for engineering judgement).
3. **What was NOT delegated** to AI.
4. **How** the final work reflects the candidate's own understanding.

---

## 2. AI Tool Used

| Tool | Version / Access | Purpose |
|------|------------------|---------|
| **Claude (Anthropic)** | Web interface, October 2026 | Conversational coding tutor and design reviewer |

No other AI tools were used. No code generation services (e.g., GitHub Copilot, ChatGPT, Cursor) were used to author source files directly.

---

## 3. Nature of Assistance Provided

AI was used in the following **supporting** capacities:

| Area | Assistance Type | Candidate's Responsibility |
|------|----------------|---------------------------|
| **Learning environment setup** | Step-by-step guidance on installing Python, Conda, Git, VS Code on Windows | Candidate executed every command and verified each result |
| **Code scaffolding** | Example patterns for FastAPI routers, SQLAlchemy models, Pydantic schemas | Candidate reviewed, understood, and where necessary modified each snippet |
| **Debugging** | Explaining error messages (import errors, encoding issues, path issues) | Candidate applied fixes and confirmed behaviour |
| **Documentation drafting** | Structuring SRS, RTM, Design, Security, and Technical Report sections | Candidate filled in project-specific details and validated factual accuracy |
| **Test case generation** | Suggesting edge cases for pytest | Candidate ran tests and inspected failures |
| **Architecture review** | Discussing trade-offs (monolith vs microservices, SQLite vs PostgreSQL, JWT vs sessions) | Candidate made the final design decisions |

---

## 4. What Was NOT Delegated to AI

The following engineering decisions and artefacts were **the candidate's own work**:

1. **Requirements interpretation** — the decision to answer Question 7 (ABU-SSO) and the scope boundary drawn for the prototype.
2. **Design choices** — selecting a modular monolith with clear growth path, choosing JWT + bcrypt over sessions, choosing lazy wallet creation.
3. **Testing strategy** — the decision to use three test layers (unit, service, integration) with a temp database, and to run Bandit SAST.
4. **Deployment** — the decision to split hosting (Render for app, Neon for DB) after discovering Render's free-tier DB expiry.
5. **Written narrative** — the analysis in the Technical Report, Risk Register, and Maintenance Plan reflects the candidate's own understanding of Sommerville and Pressman course material.
6. **Verification** — every code path was executed, every test was run, every deployment was manually verified in a browser.

---

## 5. Ethical Use Principles Applied

The following principles guided AI use in this project:

| Principle | How it was upheld |
|-----------|-------------------|
| **Transparency** | Every AI interaction is disclosed in this document |
| **Accountability** | The candidate takes full responsibility for the correctness, security, and originality of the final submission |
| **Understanding over copying** | AI output was treated as a starting point for learning, never as a substitute for comprehension |
| **Verification** | Every AI-suggested fix or pattern was tested locally before being accepted into the codebase |
| **Academic integrity** | No AI was used to write exam-critical narrative without candidate review; no AI was used during timed exams |
| **Attribution** | Where AI assistance shaped a design (e.g., the RBAC pattern), the choice was justified on its engineering merits, not on AI authority |

---

## 6. Reflection on AI-Assisted Learning

Working with an AI tutor accelerated my learning of:
- FastAPI dependency injection and router patterns
- SQLAlchemy ORM design and session lifecycle
- JWT issuance, verification, and expiry handling
- Test isolation using a temporary database
- Cloud deployment (Render + Neon) and separation of compute vs storage

It did **not** replace the need to:
- Read error messages carefully
- Understand *why* a fix works, not just *that* it works
- Design the system to solve the *stated* problem, not merely to compile
- Write honest documentation that reflects what was actually built

This project demonstrates that AI can be a **legitimate productivity multiplier** when used with discipline, verification, and disclosure.

---

## 7. Declaration

I, **Idris Muhammad Abubakar (P25EGCP9003)**, declare that:

1. The AI use described above is complete and honest.
2. The final software, documentation, and design decisions are my own responsibility.
3. I have verified every component of the submitted system and can defend it orally.
4. This declaration is made in accordance with COEN838 exam instruction F.

**Signature:** _______________________  
**Date:** October 2026

---

*End of AI Use Declaration.*