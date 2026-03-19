# Regulatory Alignment Mapping

**How the frameworks and patterns in this repository map to NIST AI RMF, EU AI Act, and ISO/IEC 42001**

*Author: Sumit Kumar*

---

## Purpose

This document provides a detailed, verifiable mapping between the governance frameworks, implementation patterns, and case studies in this repository and three major AI governance standards:

1. **NIST AI Risk Management Framework (AI RMF 1.0)** — NIST AI 100-1, January 2023
2. **EU AI Act** — Regulation 2024/1689, effective August 2026
3. **ISO/IEC 42001:2023** — Artificial Intelligence Management System (AIMS)

Each mapping shows: the standard's requirement, where this repository addresses it, and what the implementation looks like in practice.

---

## 1. NIST AI RMF Alignment

The NIST AI RMF defines four core functions: **Govern, Map, Measure, Manage**. Below is how each function and its key categories map to this repository's frameworks and patterns.

### GOVERN — Culture, Policies, Accountability

| NIST Subcategory | Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **GOVERN 1.1** | Legal and regulatory requirements are understood, managed, and documented | [Compliance-by-Design](./compliance-by-design.md) — Separation of compliance domains (fair housing, fair lending, data privacy, advertising) | `ComplianceRulesRegistry` with per-domain rule management and versioning |
| **GOVERN 1.2** | Trustworthy AI characteristics integrated into organizational practices | [AI Governance Framework](./ai-governance-framework.md) — Four governance pillars (lifecycle, risk classification, controls, human oversight) | Framework embeds trustworthiness across lifecycle, not as a bolt-on |
| **GOVERN 1.3** | Processes to determine needed level of risk management based on risk tolerance | [AI Governance Framework](./ai-governance-framework.md) — Risk Classification (Pillar 2) with 4-tier system | Tier 1 (Critical) through Tier 4 (Low) with graduated governance requirements |
| **GOVERN 1.4** | Risk management process established through transparent policies | [Audit & Accountability](./audit-accountability.md) — Decision Specification format, governance documentation | 28+ documented decisions with rationale, alternatives, and review triggers |
| **GOVERN 1.5** | Ongoing monitoring and periodic review planned with clear roles | [Audit & Accountability](./audit-accountability.md) — Audit tiers with defined cadences | Tier 1: quarterly full audit, Tier 2: monthly functional, Tier 3: weekly regression |
| **GOVERN 1.6** | Mechanisms to inventory AI systems | [AI Governance Framework](./ai-governance-framework.md) — Phase 1 of implementation roadmap | AI system inventory and risk classification as foundation activity |
| **GOVERN 1.7** | Processes for decommissioning AI systems | [Validation Architecture](./validation-architecture.md) — Feature flag rollout pattern | Shadow mode → Advisory mode → Enforcement mode (reversible deployment) |
| **GOVERN 2.1** | Roles and responsibilities documented and clear | [AI Governance Framework](./ai-governance-framework.md) — Organizational Model | 5 defined roles: AI System Owner, Governance Lead, Validation Engineer, Audit Lead, Devil's Advocate |
| **GOVERN 2.2** | Personnel receive AI risk management training | [Audit & Accountability](./audit-accountability.md) — Scenario packs for structured testing | Pre-built adversarial test scenarios by domain for repeatable training |
| **GOVERN 2.3** | Executive leadership takes responsibility for AI risk decisions | [AI Governance Framework](./ai-governance-framework.md) — Escalation path | Defined escalation: Automated → Validation Engineer → Governance Lead → System Owner → Executive |
| **GOVERN 4.1** | Safety-first mindset in design and deployment | [Compliance-by-Design](./compliance-by-design.md) — "Post-processing over prompt engineering" principle | Deterministic compliance enforcement rather than probabilistic prompt instructions |
| **GOVERN 4.3** | Practices for AI testing and information sharing | [Audit & Accountability](./audit-accountability.md) — 4-phase audit protocol | Regression → Functional → Adversarial → Lead Auditor review |
| **GOVERN 6.1** | Policies for third-party AI risks | [Case Study: Multi-Agent Governance](../case-studies/multi-agent-governance.md) — Agent contracts, circuit breakers | Per-agent contracts define max LLM calls, cost ceilings, timeout, fallback behavior |

### MAP — Context, Risk Identification

| NIST Subcategory | Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **MAP 1.1** | Intended purposes and prospective settings documented | [AI Governance Framework](./ai-governance-framework.md) — Risk Classification | Each AI system classified with documented purpose, risk tier, and deployment context |
| **MAP 1.5** | Organizational risk tolerances documented | [AI Governance Framework](./ai-governance-framework.md) — Health thresholds | First-pass clean rate ≥25% healthy, <15% danger; self-heal ≥85% target; production leaks 0% target |
| **MAP 2.2** | System behavior in unexpected conditions documented | [Validation Architecture](./validation-architecture.md) — Layer 4 (Hallucination Detection) | Claims verified against source data; unverified claims tracked with confidence scores |
| **MAP 3.2** | Potential costs from AI errors documented | [Cost Governance](../patterns/cost-governance/) — Per-operation cost tracking | `CostTracker` with per-user, per-operation, per-model cost attribution |
| **MAP 3.5** | Likelihood and magnitude of impacts documented | [Audit & Accountability](./audit-accountability.md) — Accepted Risk Register | AR-XXX format: severity, status, rationale, mitigation, review date, owner |
| **MAP 4.1** | Risks of third-party components mapped | [Case Study: Multi-Agent Governance](../case-studies/multi-agent-governance.md) — Agent governance | Circuit breakers, per-agent cost tracking, contract enforcement for third-party models |

### MEASURE — Assessment, Metrics, Monitoring

| NIST Subcategory | Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **MEASURE 1.1** | Metrics for AI risks selected and implemented | [AI Governance Framework](./ai-governance-framework.md) — Governance Metrics | Leading indicators (first-pass clean rate, catch rates, self-heal rate) and lagging indicators (violation rate, audit findings) |
| **MEASURE 2.3** | Performance demonstrated for deployment conditions | [Output Quality Scoring](../patterns/output-quality-scoring/) — Multi-dimensional scoring | 8 dimensions scored: completeness, clarity, relevance, originality, tone, accuracy, density, engagement |
| **MEASURE 2.5** | System validity and reliability demonstrated | [Case Study: Regulated Content](../case-studies/regulated-content-generation.md) — Production metrics | 98% publishable output, 0% compliance leaks, 84% first-pass clean rate |
| **MEASURE 2.6** | Safety risks evaluated, failure responses documented | [Self-Healing Pipelines](../patterns/self-healing-pipelines/) — Bounded retry with graceful degradation | Max 3 repair attempts → deterministic fix → targeted regen → full regen → graceful degrade → escalate |
| **MEASURE 2.7** | Security and resilience evaluated | [Audit & Accountability](./audit-accountability.md) — Devil's Advocate methodology | 8 adversarial attack categories including prompt injection, state corruption, logic bypass |
| **MEASURE 2.9** | AI output interpreted within context | [Hallucination Prevention](../patterns/hallucination-prevention/) — Factual routing | Claims classified by type (numeric, entity, temporal) and routed through type-specific verification |
| **MEASURE 2.11** | Fairness and bias evaluated and documented | [Compliance-by-Design](./compliance-by-design.md) — Domain-separated compliance scanning | 500+ banned phrases covering fair housing, fair lending, data privacy with per-domain rule management |
| **MEASURE 3.1** | Risk tracking approaches in place | [Audit & Accountability](./audit-accountability.md) — Regression anchors | 56+ permanent regression tests; every bug fix creates a new anchor; all anchors run before deployment |
| **MEASURE 3.3** | Feedback processes for end users established | [AI Governance Framework](./ai-governance-framework.md) — Continuous improvement cycle | Quality trend monitoring, drift detection, incident-driven rule updates |

### MANAGE — Response, Recovery, Communication

| NIST Subcategory | Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **MANAGE 1.1** | Determination of whether AI system should proceed | [Case Study: Quality Gates](../case-studies/production-ai-quality-gates.md) — Finalization Principle | `FinalizeAsset()` is the only gate to production; blocked outputs never reach users |
| **MANAGE 1.2** | Risk treatment prioritized by impact and likelihood | [AI Governance Framework](./ai-governance-framework.md) — Control Architecture | Preventive → Detective → Corrective controls with severity-based prioritization |
| **MANAGE 1.3** | Responses to high-priority risks developed and documented | [Self-Healing Pipelines](../patterns/self-healing-pipelines/) — Repair engine | Strategy hierarchy: deterministic fix → targeted regen → full regen → graceful degrade → escalate |
| **MANAGE 2.2** | Mechanisms to sustain deployed AI system value | [Output Quality Scoring](../patterns/output-quality-scoring/) — First-pass clean rate tracking | `FirstPassCleanRateTracker` monitors system health over time with daily stats |
| **MANAGE 2.3** | Procedures for previously unknown risks | [Audit & Accountability](./audit-accountability.md) — Fix Closure Protocol | Root cause → fix → regression anchor → related area audit → documentation update |
| **MANAGE 2.4** | Mechanisms to disengage AI systems | [Case Study: Multi-Agent Governance](../case-studies/multi-agent-governance.md) — Circuit breakers | `AgentCircuitBreaker`: CLOSED → OPEN (bypass with fallback) → HALF_OPEN (test recovery) |
| **MANAGE 4.1** | Post-deployment monitoring plans implemented | [Validation Architecture](./validation-architecture.md) — Monitoring & Observability | Per-layer telemetry: failure rates, violation rates, quality score trends, hallucination rates |
| **MANAGE 4.3** | Incidents communicated and recovery processes documented | [Audit & Accountability](./audit-accountability.md) — Governance documentation | Decision Specification, Fix Closure Protocol, Accepted Risk Register, Regression Anchor Registry |

---

## 2. EU AI Act Alignment

The EU AI Act (Regulation 2024/1689) establishes risk-based regulation for AI systems. Below is how this repository's frameworks address the Act's key requirements.

### Risk Classification (Article 6, Annex III)

| EU AI Act Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|
| **4-tier risk classification** (Unacceptable, High, Limited, Minimal) | [AI Governance Framework](./ai-governance-framework.md) — Pillar 2: Risk Classification | 4-tier system (Critical, High, Moderate, Low) with graduated governance requirements per tier |
| **High-risk criteria** — AI in regulated domains requiring stringent controls | [Case Study: Regulated Content](../case-studies/regulated-content-generation.md) | Production system in regulated industry with full governance pipeline, 0% compliance leaks |
| **Risk assessment** for system classification | [AI Governance Framework](./ai-governance-framework.md) — Decision Framework | 5-criterion evaluation: Safety, Compliance, Quality, Auditability, Reversibility |

### High-Risk System Obligations (Articles 8-15)

| Article | Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **Art. 9: Risk Management** | Continuous, iterative risk management throughout lifecycle | [AI Governance Framework](./ai-governance-framework.md) — Pillar 1: Lifecycle Governance | 4-phase implementation roadmap: Foundation → Controls → Audit → Continuous Improvement |
| **Art. 9** | Risk mitigation in priority order (design → control → information) | [Compliance-by-Design](./compliance-by-design.md) — Layered controls | Input sanitization (design) → bounded generation (control) → compliance scanning (detection) → self-healing (correction) |
| **Art. 10: Data Governance** | Training data quality, bias detection, representativeness | [Hallucination Prevention](../patterns/hallucination-prevention/) — Extraction validation gate | `ExtractionValidator` with minimum quality (0.6) and coverage (0.5) thresholds; bad extraction → safe fallback |
| **Art. 10** | Special category data handling with safeguards | [Compliance-by-Design](./compliance-by-design.md) — PII scanning | `PIIScanner` in compliance validation layer; detection + auto-redaction |
| **Art. 11: Technical Documentation** | Documentation before market placement, kept up to date | [Audit & Accountability](./audit-accountability.md) — 6 governance documents | Decision Specification, Fix Closure Protocol, Audit Ownership, Accepted Risk Register, Regression Anchors, Evidence Minimums |
| **Art. 12: Record-Keeping** | Automatic logging for traceability | [Validation Architecture](./validation-architecture.md) — Pipeline telemetry | Every validation layer produces structured telemetry; per-layer metrics, per-claim verification records |
| **Art. 12** | Logs throughout system lifecycle | [Cost Governance](../patterns/cost-governance/) — `CostRecord` with full metadata | Timestamp, user, operation, model, tokens, cost, tier — every LLM call logged |
| **Art. 13: Transparency** | System capabilities and limitations communicated to deployers | [Output Quality Scoring](../patterns/output-quality-scoring/) — Multi-dimensional scoring | Per-dimension scores with evidence and confidence; weak dimensions explicitly identified |
| **Art. 13** | Information about accuracy, robustness, cybersecurity | [Validation Architecture](./validation-architecture.md) — 4-layer validation | Each layer has defined catch rates, monitoring thresholds, and alert conditions |
| **Art. 14: Human Oversight** | Effective human oversight to prevent automation bias | [AI Governance Framework](./ai-governance-framework.md) — Pillar 4: Human Oversight | "Automate the repeatable, escalate the ambiguous" — defined human decision points for quality standards, edge cases, compliance interpretation, ethical boundaries |
| **Art. 14** | Ability to override or reverse AI output | [Case Study: Quality Gates](../case-studies/production-ai-quality-gates.md) — Finalization Principle | `FinalizeAsset()` blocks any output that fails validation; human can reject at finalization gate |
| **Art. 14** | Ability to intervene or stop the system | [Case Study: Multi-Agent Governance](../case-studies/multi-agent-governance.md) — Circuit breakers | `AgentCircuitBreaker` with OPEN state that bypasses failing agents with safe fallback |
| **Art. 15: Accuracy** | Appropriate accuracy levels declared | [Output Quality Scoring](../patterns/output-quality-scoring/) — Composite scoring with thresholds | Configurable per-content-type thresholds; minimum composite score enforced at finalization |
| **Art. 15: Robustness** | Resilience against errors and inconsistencies | [Self-Healing Pipelines](../patterns/self-healing-pipelines/) — Automated repair | 92% self-heal success rate; bounded retries; graceful degradation for unfixable failures |
| **Art. 15: Cybersecurity** | Resilience against adversarial manipulation | [Audit & Accountability](./audit-accountability.md) — Devil's Advocate methodology | 8 attack categories including adversarial prompting, data poisoning, model evasion, prompt injection |

### Transparency (Article 50)

| Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|
| **AI interaction disclosure** | [AI Governance Framework](./ai-governance-framework.md) — Transparency requirements | Framework mandates disclosure when users interact with AI-generated content |
| **AI-generated content marking** | [Validation Architecture](./validation-architecture.md) — Finalization metadata | `FinalizedAsset` includes `finalization_version`, `finalized_at`, generation metadata — content is traceable as AI-generated |
| **Explainability of decisions** | [Output Quality Scoring](../patterns/output-quality-scoring/) — Evidence-based scoring | Every dimension score includes `evidence` (why this score) and `improvement_hints` (what to change) |

### Quality Management System (Article 17)

| QMS Component | Repository Alignment | Implementation Evidence |
|---|---|---|
| **Regulatory compliance strategy** | [Compliance-by-Design](./compliance-by-design.md) — Full compliance pipeline | Domain-separated rules, versioned updates, quarterly review cadence |
| **Design & development procedures** | [Validation Architecture](./validation-architecture.md) — Feature flag rollout | Shadow → Advisory → Enforcement deployment pattern |
| **Testing & validation** | [Audit & Accountability](./audit-accountability.md) — 4-phase audit protocol | 56+ regression anchors, adversarial testing, go/no-go gates |
| **Risk management integration** | [AI Governance Framework](./ai-governance-framework.md) — End-to-end framework | Risk classification drives governance intensity per system |
| **Post-market monitoring** | [Output Quality Scoring](../patterns/output-quality-scoring/) — Trend tracking | `FirstPassCleanRateTracker` with daily stats, health status (HEALTHY/ATTENTION/DANGER) |
| **Incident reporting** | [Audit & Accountability](./audit-accountability.md) — Fix Closure Protocol | Root cause → fix → regression anchor → related area audit → documentation |
| **Record-keeping** | [Cost Governance](../patterns/cost-governance/) + Validation telemetry | Every LLM call, every validation result, every repair attempt logged with full metadata |
| **Accountability framework** | [AI Governance Framework](./ai-governance-framework.md) — Organizational Model | 5 roles with defined responsibilities, escalation path with SLAs |
| **Change management** | [Compliance-by-Design](./compliance-by-design.md) — Rule versioning | `RuleVersioning` with supersedence tracking, effective dates, change reasons, audit log |

---

## 3. ISO/IEC 42001 Alignment

ISO/IEC 42001:2023 provides a certifiable management system standard for AI. Below is how this repository's frameworks map to its clauses and Annex A controls.

### Main Clauses (4-10)

| ISO 42001 Clause | Requirement | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **Clause 4: Context** | Understand organizational context, stakeholders, and AIMS scope | [AI Governance Framework](./ai-governance-framework.md) — Pillar 2: Risk Classification | System inventory, risk classification, stakeholder identification as Phase 1 foundation |
| **Clause 5: Leadership** | AI policy, organizational roles, management commitment | [AI Governance Framework](./ai-governance-framework.md) — Organizational Model + Escalation | 5 defined roles; executive sponsor in escalation path; "governance is an accelerator" philosophy |
| **Clause 6: Planning** | AI risk assessment, impact assessment, objectives | [AI Governance Framework](./ai-governance-framework.md) — Decision Framework + Health Thresholds | 5-criterion decision framework (Safety, Compliance, Quality, Auditability, Reversibility); measurable health thresholds |
| **Clause 6.1.2: AI Risk Assessment** | Define AI-specific risk criteria and risk appetite | [AI Governance Framework](./ai-governance-framework.md) — Health Thresholds | First-pass clean rate ≥25%, self-heal ≥85%, production leaks = 0% — quantified risk tolerance |
| **Clause 6.1.4: AI Impact Assessment** | Evaluate impacts on individuals and society | [Case Study: Regulated Content](../case-studies/regulated-content-generation.md) | Fair housing/fair lending compliance preventing discriminatory impact on protected classes |
| **Clause 7: Support** | Resources, competence, awareness, documentation | [Audit & Accountability](./audit-accountability.md) — Scenario packs, evidence minimums | Pre-built adversarial scenarios for training; per-tier minimum evidence requirements |
| **Clause 8: Operation** | Operational planning, risk treatment execution | [Validation Architecture](./validation-architecture.md) — 4-layer pipeline | Structural → Compliance → Quality → Hallucination validation embedded in generation pipeline |
| **Clause 8.3: Risk Treatment** | Implement risk treatment plan | [Self-Healing Pipelines](../patterns/self-healing-pipelines/) — Repair engine | Deterministic fix → targeted regen → full regen → graceful degrade → escalate |
| **Clause 9: Performance Evaluation** | Monitoring, internal audit, management review | [Audit & Accountability](./audit-accountability.md) — Continuous monitoring + 4-phase audit | Automated monitors (per-deployment regression, daily violation rates, weekly quality trends); quarterly full audit |
| **Clause 9.2: Internal Audit** | Periodic audits of AIMS compliance | [Audit & Accountability](./audit-accountability.md) — 6-agent audit hierarchy | Regression Auditor, Functional Auditor, Stress Agent, Devil's Advocate, Validation Agent, Lead Auditor |
| **Clause 10: Improvement** | Nonconformity, corrective action, continual improvement | [Audit & Accountability](./audit-accountability.md) — Fix Closure Protocol + Regression Anchors | Every finding → root cause → fix → regression anchor → related area audit. System gets stronger from every failure |

### Annex A Controls

| Annex A Domain | Control Objective | Repository Alignment | Implementation Evidence |
|---|---|---|---|
| **A.2: Policies for AI** | Management direction for AI | [AI Governance Framework](./ai-governance-framework.md) — Core Philosophy | "Governance is an accelerator" — documented philosophy with 4 governance pillars |
| **A.3: Internal Organization** | Accountability structure for AI governance | [AI Governance Framework](./ai-governance-framework.md) — Organizational Model | 5 roles with clear mandates; escalation path with defined authority at each level |
| **A.3** | Reporting procedures for AI concerns | [Audit & Accountability](./audit-accountability.md) — Escalation path | Automated Detection → Self-Heal → Validation Engineer → Governance Lead → System Owner → Executive |
| **A.4: Resources for AI** | AI system inventory and tooling | [AI Governance Framework](./ai-governance-framework.md) — Phase 1: Inventory & Classify | Risk-classified AI system inventory as foundation; per-system governance requirements |
| **A.4** | Personnel competence | [Audit & Accountability](./audit-accountability.md) — Audit hierarchy | Each audit role has defined mandate and perspective; scenario packs for skill development |
| **A.5: Assessing Impacts** | AI impact assessment process | [Compliance-by-Design](./compliance-by-design.md) — Domain-separated compliance | Per-domain impact assessment: fair housing, fair lending, data privacy, advertising, accessibility |
| **A.5** | Ongoing monitoring of impacts | [Output Quality Scoring](../patterns/output-quality-scoring/) — Trend tracking | First-pass clean rate tracking with health status; daily stats; drift detection |
| **A.6: AI System Lifecycle** | Design and development processes | [Validation Architecture](./validation-architecture.md) — Feature flag rollout | Shadow → Advisory → Enforcement; per-asset isolation; extraction validation gate |
| **A.6** | Testing and validation | [Audit & Accountability](./audit-accountability.md) — 4-phase protocol + regression anchors | 56+ regression anchors; adversarial testing; 1,000+ governance-specific tests |
| **A.6** | Operation and monitoring | [Self-Healing Pipelines](../patterns/self-healing-pipelines/) — Pipeline telemetry | Per-component status tracking (completed/degraded/blocked); repair attempt logging |
| **A.7: Data for AI** | Data quality requirements | [Hallucination Prevention](../patterns/hallucination-prevention/) — Extraction validation gate | `ExtractionValidator` with minimum quality and coverage thresholds; fallback on bad extraction |
| **A.7** | Data provenance and preparation | [Compliance-by-Design](./compliance-by-design.md) — Input sanitization | `InputSanitizer` cleans source data before generation; audit trail of violations found and remediated |
| **A.8: Transparency** | Explainability of AI decisions | [Output Quality Scoring](../patterns/output-quality-scoring/) — Evidence-based scoring | Every quality dimension includes evidence (why this score) and improvement hints |
| **A.8** | Communication about AI monitoring | [AI Governance Framework](./ai-governance-framework.md) — Governance Metrics | Leading and lagging indicators with defined health thresholds; dashboard recommendations |
| **A.9: Use of AI** | Intended use documentation | [AI Governance Framework](./ai-governance-framework.md) — Risk Classification | Each risk tier has documented governance requirements, controls, and review cadence |
| **A.9** | Human oversight mechanisms | [Case Study: Quality Gates](../case-studies/production-ai-quality-gates.md) — Finalization Principle | `FinalizeAsset()` is the only gate to production; human oversight at quality standard and edge case decision points |
| **A.9** | Monitoring for misuse | [Audit & Accountability](./audit-accountability.md) — Devil's Advocate methodology | Adversarial prompting attack category; prompt injection detection in user-controllable fields |
| **A.10: Third-Party** | Supplier responsibilities and accountability | [Case Study: Multi-Agent Governance](../case-studies/multi-agent-governance.md) — Agent contracts | `AgentContract` defines max LLM calls, cost ceiling, timeout, required I/O, error budget, fallback behavior per third-party model |

---

## Cross-Standard Alignment Matrix

This matrix shows how key governance concepts are addressed across all three standards and where this repository provides implementation:

| Governance Concept | NIST AI RMF | EU AI Act | ISO 42001 | Repository Implementation |
|---|---|---|---|---|
| **Risk Classification** | MAP 1.5 (risk tolerance) | Art. 6 (4-tier classification) | Clause 6.1.2 (risk criteria) | [AI Governance Framework](./ai-governance-framework.md) — 4-tier risk classification |
| **Lifecycle Governance** | GOVERN 1.1-1.7 | Art. 9 (continuous risk management) | Clause 8 + A.6 (lifecycle controls) | [AI Governance Framework](./ai-governance-framework.md) — Pillar 1 |
| **Human Oversight** | GOVERN 3.2 (human-AI roles) | Art. 14 (override, intervene, stop) | A.9 (human oversight mechanisms) | Finalization Principle + circuit breakers |
| **Data Governance** | MAP 2.1 (data documented) | Art. 10 (quality, bias, representativeness) | A.7 (quality, provenance, preparation) | Extraction validation gate + input sanitization |
| **Transparency** | MEASURE 2.8-2.9 (accountability, explainability) | Art. 13 + Art. 50 (disclosure, marking) | A.8 (explainability, communication) | Evidence-based quality scoring + finalization metadata |
| **Bias & Fairness** | MEASURE 2.11 (fairness evaluated) | Art. 10.5 (special category data) | A.5 (impact assessment) | 500+ banned phrases, domain-separated compliance scanning |
| **Robustness & Safety** | MEASURE 2.6 (safety risks, fail safely) | Art. 15 (accuracy, robustness, cybersecurity) | A.6 (testing, operation) | Self-healing pipelines, 92% auto-recovery, graceful degradation |
| **Audit & Accountability** | GOVERN 2.1 (roles clear) | Art. 17 (QMS, record-keeping) | Clause 9 (audit, management review) | 6-agent audit hierarchy, 4-phase protocol, 56+ regression anchors |
| **Incident Management** | MANAGE 4.3 (incidents communicated) | Art. 17 (incident reporting) | Clause 10 (corrective action) | Fix Closure Protocol + regression anchor creation |
| **Third-Party Risk** | GOVERN 6.1, MANAGE 3.1 | Art. 17 (supply chain) | A.10 (supplier accountability) | Agent contracts, circuit breakers, per-agent cost tracking |
| **Continuous Improvement** | MANAGE 4.2 (continual improvements) | Art. 9 (iterative risk management) | Clause 10.2 (continual improvement) | First-pass clean rate trending, drift detection, adversarial findings as improvement fuel |
| **Cost Governance** | MAP 3.2 (costs documented) | Art. 17 (resource management) | A.4 (resources for AI) | Per-user, per-operation LLM cost tracking with budget controls |

---

## Maturity Alignment

This repository demonstrates governance maturity that maps to established maturity models:

| Maturity Level | NIST AI RMF Profile | ISO 42001 Readiness | EU AI Act Readiness | Repository Evidence |
|---|---|---|---|---|
| **Level 1: Ad Hoc** | Partial | No AIMS | Non-compliant | — |
| **Level 2: Reactive** | Partial | Planning | Awareness only | — |
| **Level 3: Systematic** | Current state | Core clauses addressed | Requirements understood | Governance framework, risk classification, audit methodology |
| **Level 4: Automated** | Target state | Annex A controls implemented | Conformity assessment ready | Automated validation pipelines, self-healing, continuous monitoring, 1,000+ tests |
| **Level 5: Predictive** | Aspirational | Full AIMS certification | Full compliance | Drift detection, trend analysis (partially implemented via first-pass clean rate tracking) |

**Current maturity: Level 4 (Automated)** — Governance controls are embedded in AI pipelines, self-healing is operational, continuous monitoring is in place. Level 5 (Predictive) is partially addressed through trend analysis and health monitoring.

---

## How to Use This Document

**For AI governance practitioners:** Use this mapping as a template for aligning your own governance implementations to regulatory standards. The pattern is: identify the requirement → map to your control → document the implementation evidence.

**For auditors and reviewers:** Each mapping in this document can be verified by examining the referenced framework document or code pattern in this repository. Every claim is traceable to a specific artifact.

**For organizations preparing for regulatory compliance:** This mapping demonstrates that production-grade AI governance — built from practical implementation experience — naturally aligns with major regulatory frameworks. The standards codify what good governance practitioners already do.

---

## References

- [NIST AI 100-1: AI Risk Management Framework (AI RMF 1.0)](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) — January 2023
- [EU AI Act (Regulation 2024/1689)](https://artificialintelligenceact.eu/) — Published July 2024, fully applicable August 2026
- [ISO/IEC 42001:2023](https://www.iso.org/standard/81230.html) — Artificial Intelligence Management System
- [NIST AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/) — Practical guidance for each subcategory
- [EU AI Act High-Level Summary](https://artificialintelligenceact.eu/high-level-summary/)

---

*This regulatory alignment mapping is maintained alongside the governance frameworks it references. As standards evolve and new regulations emerge, this document will be updated to reflect current alignment.*
