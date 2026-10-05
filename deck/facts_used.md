# Munim Pitch Deck (v3) — Facts Used & Source Verification

This document provides complete traceability for every claim, metric, and architectural property presented in `munim_pitch_v3.pptx`. Every single statement maps directly to source code, automated test suites, or eval results within this repository.

---

## 1. Slide-by-Slide Traceability Matrix

| Slide | Claim / Metric / Feature | Source File / Implementation | Verification Method |
|---|---|---|---|
| **Slide 1: Overview** | Product Name: Munim (मुनीम) — Voice-first AI copilot | `README.md`, `backend/app/main.py` | Official project name and purpose |
| **Slide 1: Overview** | Hackathon Theme: AI business partner for Paytm merchants | `README.md` | Paytm AI Partner Hackathon 2026 problem statement |
| **Slide 1: Overview** | Operating Channel: Output-only Soundbox + Mobile App | `frontend/src/components/SoundboxSimulator.tsx`, `frontend/src/components/PhoneAppView.tsx` | Split-view UI architecture |
| **Slide 1: Overview** | 0 numeric errors on 50 financial QA benchmarks | `data/eval_results.json`, `backend/app/eval/qa_benchmark.py` | Benchmark metric `qa_50_hallucination_resistance_pct: 100.0%` |
| **Slide 2: Proposal** | 3 Stages: Understand, Recommend, Act & Measure | `backend/app/agent/loop.py`, `backend/app/services/` | End-to-end autonomous business loop |
| **Slide 2: Proposal** | Soundbox Speaks: Output-only audio broadcast | `frontend/src/components/SoundboxSimulator.tsx` | Hardware simulation policy |
| **Slide 2: Proposal** | Approval Gate: Zero external actions without mobile tap | `backend/app/agent/guardrails.py`, `frontend/src/components/ApprovalCard.tsx` | Guardrail state machine requirement |
| **Slide 2: Proposal** | Honest Limits: Simulated metrics explicitly labeled | `docs/demo_script.md`, UI `Simulated` pill badges | Transparency standard |
| **Slide 3: Technical** | Tech Stack: Python 3.12, TypeScript, React 18, FastAPI, SQLite | `backend/pyproject.toml`, `frontend/package.json` | Project manifest files |
| **Slide 3: Technical** | Analytics: scikit-learn GMM, NumPy, Combo Subset Solver | `backend/app/services/item_inference.py` | Inferred item clustering algorithms |
| **Slide 3: Technical** | Speech & Audio: Kokoro Neural TTS, Hinglish Voice Parser | `backend/app/services/tts.py`, `backend/app/services/voice_parser.py` | Voice synthesis & regex parser |
| **Slide 3: Technical** | 4 Parallel Engines: Inference, Ledger, Footfall, Munim Score | `backend/app/services/` | Service layer modular architecture |
| **Slide 3: Technical** | Prototype vs Production Rails (FastAPI->Cloud, WS->MQTT, Sim->Webhook, Score->NBFC) | `docs/architecture.md` | Architectural evolution roadmap |
| **Slide 4: Item Inference** | Clean baseline: F1 Score = 1.000 | `data/eval_results.json`, `backend/app/eval/inference_eval.py` | Baseline eval on clean 4-item menu |
| **Slide 4: Item Inference** | Hard-case stress test: F1 Score = 0.588 | `data/eval_results.json`, `backend/app/eval/inference_eval.py` | Evaluated with 2 price collisions, combos, noise, sparse item |
| **Slide 4: Item Inference** | Combinatorial subset clustering + domain priors | `backend/app/services/item_inference.py` | `BUSINESS_DOMAIN_PRIORS` mapping and combo solver |
| **Slide 4: Item Inference** | 1-Tap Merchant confirmation chips | `frontend/src/components/WhatISellScreen.tsx`, `backend/app/models/entities.py` | `PricePointHypothesis.confirmed_by_merchant` |
| **Slide 5: Bahi-Khata** | Daily True Profit = UPI + Cash In - Cash Outflow | `backend/app/services/analytics.py` (`get_daily_summary`) | Deterministic arithmetic formula |
| **Slide 5: Bahi-Khata** | 27 of 30 Hinglish test phrases accurately parsed (90%) | `data/eval_results.json`, `backend/app/eval/qa_benchmark.py` | `voice_30_extraction_accuracy_pct: 90.0%` (27/30) |
| **Slide 5: Bahi-Khata** | Tone selection: Polite, Formal, Firm | `frontend/src/components/UdhaarLedger.tsx`, `backend/app/services/udhaar.py` | Tone parameter in message drafting |
| **Slide 5: Bahi-Khata** | Customer Consent Boundary: No Soundbox debtor shaming | `frontend/src/components/SoundboxSimulator.tsx` | Architectural privacy guarantee |
| **Slide 6: Intelligence** | Footfall Detector: +2.8σ volume acceleration alert | `backend/app/services/proactive_triggers.py` | Statistical surge calculation |
| **Slide 6: Intelligence** | Proactive Soundbox broadcast: 'Chai aur bun maska tayyar' | `backend/app/services/tts.py`, `docs/demo_script.md` | Pre-recorded / synthesized Hinglish prompt |
| **Slide 6: Intelligence** | Cooldown window: 45 minutes | `backend/app/services/proactive_triggers.py` | Duplicate alert suppression |
| **Slide 6: Intelligence** | 'Don't Act' Decision: Suppresses discount during peaks | `backend/app/services/campaign_recommender.py` | Margin preservation policy rule |
| **Slide 7: Trust & Safety**| 3-Tier Risk Staircase: Tier 1 (Read), Tier 2 (Draft), Tier 3 (Gate) | `backend/app/agent/guardrails.py` | Execution permission tiers |
| **Slide 7: Trust & Safety**| Runtime Guardrail: Direct adapter calls raise PermissionError | `backend/app/adapters/mock_adapters.py`, `backend/tests/test_adapters.py` | Automated unit test verified |
| **Slide 7: Trust & Safety**| Single-use cryptographically secure execution token | `backend/app/agent/guardrails.py` | `secrets.token_urlsafe(32)` token gate |
| **Slide 7: Trust & Safety**| Append-only SQLite audit log with UTC timestamp | `backend/app/core/audit.py`, `backend/app/models/entities.py` | `AuditLogEntry` table |
| **Slide 8: Munim Score** | 5-Factor Scoring: Volume (25%), Expense (25%), Stability (20%), Recovery (15%), Margin (15%) | `backend/app/services/munim_score.py` | Deterministic 100-point scoring algorithm |
| **Slide 8: Munim Score** | Indicative credit limit band (₹78,000 - ₹106,000) labeled Simulated | `frontend/src/components/MunimScoreScreen.tsx` | Visual simulation pill and disclaimer |
| **Slide 8: Munim Score** | Regulatory disclaimer: Not a credit decision or loan offer | `frontend/src/components/MunimScoreScreen.tsx` | Mandatory regulatory compliance note |
| **Slide 9: Demo Flow** | 5-Act Demonstration Sequence (08:00 AM to 09:00 PM) | `docs/demo_script.md` | Standardized hackathon demonstration track |
| **Slide 9: Demo Flow** | +21.4% revenue increase labeled Simulated | `docs/demo_script.md` | Counterfactual model illustration |
| **Slide 10: Feasibility** | 4-Dimension Readiness (Data, Hardware, Compute, Control) | `README.md`, `docs/architecture.md` | Solution engineering feasibility analysis |
| **Slide 10: Feasibility** | Challenge vs Tested Mitigation Mapping (5 retail realities) | `backend/app/`, `backend/tests/` | Verified code implementations |
| **Slide 11: Impact** | Multi-sided ecosystem value (Merchants, Paytm, Soundbox, NBFCs) | `docs/architecture.md`, `README.md` | Ecosystem economics |
| **Slide 11: Impact** | Paradigm Shift Table (Manual Bookkeeping vs Munim Copilot) | `README.md` | Product contrast matrix |
| **Slide 11: Impact** | Empirical Proof: 50 QA tests (0 errors), 27/30 voice phrases | `data/eval_results.json` | Verifiable evaluation benchmarks |

---

## 2. Removed Claims and Rationale

The following claims from earlier drafts, brainstorms, or informal notes were strictly removed or relabeled to ensure 100% adherence to repository facts:

1. **Removed "30 Million Merchants" / "Over 30M Paytm merchants use Soundbox"**
   * *Rationale*: Macroeconomic statistic not originating from codebase data or benchmark files. Removed to keep claims strictly sourced from the repo.
2. **Removed "MQTT Gateway" and "4G SIM Embedded Driver"**
   * *Rationale*: The repo implements a simulated Soundbox via WebSocket and FastAPI (`backend/app/api/soundbox.py`). There is no physical SIM driver or active MQTT broker. Relabeled factually as "Simulated 4G Soundbox" and placed MQTT on the architectural roadmap.
3. **Removed "100% Zero-Math Safety Guarantee"**
   * *Rationale*: Unconditional claims are unverifiable marketing jargon. Replaced with the exact empirical benchmark: "0 numeric errors across 50 financial QA benchmarks".
4. **Removed "90% Accuracy" without context**
   * *Rationale*: Clarified the exact test denominator: "27 of 30 Hinglish test phrases accurately parsed".
5. **Removed "Cryptographic / Immutable Ledger / Unbypassable Guardrails"**
   * *Rationale*: The audit log is an append-only SQLite table by application convention, not an immutable blockchain. Replaced with factual descriptions: "Append-only SQLite audit log" and "Token-locked mock adapters raising PermissionError".
6. **Removed "Live Microphone Recording on Phone" as a working feature**
   * *Rationale*: Inspection of `frontend/src/components/BahiKhataScreen.tsx` revealed typed text input with a "Parse" button sending transcripts to `/api/bahi-khata/parse-voice`. There is no active WebSpeech microphone recorder. Labeled as typed text / voice transcript, and placed live browser WebSpeech recording on the Roadmap.
7. **Removed "Perfect 1.0 F1 Item Inference Score" as a standalone metric**
   * *Rationale*: The 1.000 F1 score only tested an easy 4-item menu with clean, unique price points. When subjected to our adversarial stress test (price collisions, combos, noise, sparse item), the model achieved F1 0.588. Both numbers are now honestly disclosed side by side.
8. **Removed Loan Approvals & Rupee Credit Guarantees**
   * *Rationale*: Munim is not an RBI-licensed NBFC or bank. It cannot disburse loans or promise credit lines. Framed strictly as an alternative behavioral underwriting signal for licensed lenders, accompanied by a prominent in-app disclaimer.
9. **Removed Unattributed "+21.4% Uplift"**
   * *Rationale*: The +21.4% figure was an illustrative narrative number from `docs/demo_script.md`. Explicitly tagged with the `Simulated` pill badge on all slides.
10. **Removed "Battle-Tested" and "localhost:8000" references**
    * *Rationale*: Replaced dev jargon with clear, professional engineering descriptions.
