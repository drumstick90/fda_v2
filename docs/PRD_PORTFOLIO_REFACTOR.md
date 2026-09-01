# PRD — FDA Drug Label Explorer: Portfolio-Grade Clinical AI Refactor

**Status:** Proposed
**Repository:** `drumstick90/fda_v2`
**Primary objective:** Transform an existing working clinical-data prototype into a credible, technically inspectable example of clinical AI product development, evaluation and deployment.

**Implementation runbook:** [`docs/hermes/README.md`](hermes/README.md) contains the successive, gated Hermes prompts for executing this PRD.

---

# 1. Product Thesis

FDA Drug Label Explorer is a clinician-oriented application for searching, comparing and analysing authoritative US FDA drug-label information.

The existing application already provides meaningful functionality:

- Single-drug search
- Batch drug search
- Historical label analysis
- Reverse indication search
- CSV export
- AI-generated indication summaries
- Multiple LLM providers
- React/TypeScript frontend
- FastAPI/Python backend
- Docker-based local deployment

The goal of this project is **not** to add large amounts of functionality.

The goal is to demonstrate that the product has been designed and engineered with appropriate attention to:

1. clinical usefulness
2. source provenance
3. AI reliability
4. evaluation
5. software quality
6. safety
7. reproducibility
8. pragmatic product decisions

The repository should communicate:

> A clinician identified a real information problem, built a working product around authoritative medical data, integrated LLMs where they add value, and created a rigorous evaluation system to determine when those LLMs are safe and useful.

---

# 2. Why This Refactor Exists

The current repository has good underlying product signal but several visible weaknesses.

## 2.1 Backend architecture

`backend/main.py` currently contains most application logic in a single large module of approximately 1,400+ lines.

This makes the project look like a prototype rather than an intentionally designed system.

## 2.2 Testing

There is some testing-related code, including `test_all_indications.py`, but the repository does not currently communicate a clear automated test strategy.

## 2.3 Infrastructure

Docker Compose currently defines PostgreSQL and Redis although the README states that neither is connected to the application.

Unused infrastructure increases apparent complexity without demonstrating capability.

## 2.4 AI functionality

AI summaries exist, including multi-provider support, but there is no visible systematic answer to:

> How do we know whether these generated clinical summaries are correct?

This is the most important gap.

## 2.5 Portfolio presentation

The repository explains features, but it does not yet clearly demonstrate:

- architectural judgement
- evaluation methodology
- clinical safety thinking
- model comparison
- technical trade-offs
- product decision-making

---

# 3. Target User

## Primary user

Clinician, researcher or medically knowledgeable analyst who needs to interrogate FDA drug labels efficiently.

Typical questions:

- What is this drug currently FDA-labelled for?
- Which indications appear across its labels?
- Which label is current?
- How has the label changed over time?
- Which drugs mention a given indication?
- Can a long FDA indication section be summarised accurately?

## Secondary user

Technical evaluator reviewing the repository as evidence of:

- clinical AI product development
- applied LLM engineering
- API/data engineering
- evaluation design
- safety reasoning
- product ownership

The product must remain useful to the first user while becoming legible to the second.

---

# 4. Product Principles

## P1. Authoritative data before generative output

OpenFDA label data remains the source of truth.

The LLM must never become the source of truth.

## P2. Deterministic before probabilistic

Extraction, metadata processing, label versioning and data transformation should remain deterministic whenever possible.

LLMs should only be used where semantic compression or interpretation adds meaningful value.

## P3. Provenance everywhere

A generated answer must remain traceable to the underlying label.

## P4. Evaluation is a product feature

AI quality must not be represented by anecdotes such as “the summaries look good.”

The repository must contain reproducible evidence.

## P5. Clinical usefulness over technical theatre

Do not introduce infrastructure merely to make the project appear sophisticated.

## P6. Explicit uncertainty

The product should distinguish:

- FDA source text
- deterministic interpretation
- heuristic classification
- LLM-generated content

## P7. Ship a small system well

This repository should demonstrate excellent judgment about scope.

---

# 5. Non-Goals

The following are explicitly out of scope for this refactor:

- Kubernetes
- microservices
- distributed event architecture
- user authentication
- user accounts
- PostgreSQL unless persistence becomes genuinely necessary
- Redis unless caching becomes genuinely necessary
- vector databases
- generic RAG frameworks
- autonomous agents
- fine-tuning models
- mobile applications
- replacing OpenFDA
- clinical decision support
- prescribing recommendations
- diagnosis
- patient-specific treatment recommendations
- turning the application into a regulated medical device

Do not add architecture solely for résumé signalling.

---

# 6. Target Architecture

Refactor the backend without changing core behaviour.

Target:

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routers/
│   │       ├── drugs.py
│   │       ├── labels.py
│   │       ├── indications.py
│   │       ├── ai.py
│   │       └── export.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── clients/
│   │   ├── openfda.py
│   │   └── llm/
│   │       ├── base.py
│   │       ├── openai.py
│   │       ├── gemini.py
│   │       └── deepseek.py
│   │
│   ├── services/
│   │   ├── drug_search.py
│   │   ├── label_analysis.py
│   │   ├── indication_search.py
│   │   └── summarisation.py
│   │
│   ├── schemas/
│   │   ├── drug.py
│   │   ├── label.py
│   │   └── summary.py
│   │
│   └── utils/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── evals/
    ├── datasets/
    ├── scorers/
    ├── runners/
    └── reports/
```

This architecture is deliberately conventional.

A reviewer should understand it immediately.

---

# 7. Backend Refactor Requirements

## 7.1 Thin application entry point

`app/main.py` should contain:

- FastAPI initialization
- middleware
- router registration
- startup configuration

It should not contain business logic.

Target: approximately 50–100 lines.

## 7.2 OpenFDA client

All OpenFDA HTTP interaction should live behind one explicit client.

Responsibilities:

- request construction
- timeouts
- response handling
- rate-limit handling
- upstream error translation
- retry behaviour where appropriate

Business logic must not make arbitrary HTTP calls directly.

## 7.3 Service layer

Separate:

**DrugSearchService**

- drug lookup
- label selection

**LabelAnalysisService**

- historical label processing
- version grouping
- current/superseded logic

**IndicationSearchService**

- reverse indication queries

**SummaryService**

- prompt construction
- LLM invocation
- structured response parsing
- provenance attachment

## 7.4 Structured schemas

Use explicit Pydantic models for API boundaries.

Avoid passing large untyped dictionaries through the system.

---

# 8. Infrastructure Simplification

Remove PostgreSQL and Redis from default Docker Compose.

Current product functionality does not require them.

Target:

```text
docker compose up
    ↓
frontend
backend
```

Nothing else.

If future persistence becomes justified, add it then with an Architecture Decision Record.

This demonstrates stronger engineering judgment than leaving speculative infrastructure in place.

---

# 9. AI Summary Redesign

The AI feature should become the technical centrepiece.

## 9.1 Input

The model receives only relevant FDA label content plus clearly defined task instructions.

## 9.2 Output

Move from unconstrained prose toward a structured response.

Example conceptual schema:

```json
{
  "summary": "...",
  "approved_indications": [],
  "population_qualifiers": [],
  "limitations": [],
  "source_set_id": "...",
  "source_effective_time": "...",
  "model": "...",
  "provider": "..."
}
```

Exact schema may change based on existing prompt behaviour.

## 9.3 Provenance

Every generated summary must expose:

- source label identifier
- effective date
- model
- provider

Where practical, generated claims should be linked back to supporting source passages.

Do not imply that an LLM-generated interpretation is itself FDA-authored.

---

# 10. LLM Provider Architecture

Preserve the current multi-provider capability.

Implement a small common interface:

```python
class LLMProvider:
    async def generate(self, request: SummaryRequest) -> SummaryResponse:
        ...
```

Adapters:

- OpenAI
- Gemini
- DeepSeek

The purpose is not sophisticated abstraction.

The purpose is to allow the same clinical task and evaluation dataset to be run against multiple models consistently.

---

# 11. Clinical AI Evaluation Lab

This is the highest-priority new capability.

Directory:

```text
backend/evals/
```

The evaluation system should answer:

> Given authoritative FDA label text, how reliably does each supported model produce a clinically faithful structured summary?

---

# 12. Evaluation Dataset

Create a version-controlled benchmark containing approximately **30–50 cases**.

Do not start with hundreds.

Cases should deliberately cover different difficulty classes.

Suggested strata:

### A. Simple indication

Straightforward single-indication label.

### B. Multiple indications

Drug approved across several conditions.

### C. Population qualifiers

Adult-only, paediatric, age-limited or other restricted indications.

### D. Adjunctive vs monotherapy

Cases where this distinction matters.

### E. Complex indication wording

Labels containing conditional or nuanced approval language.

### F. Multiple historical labels

Potential confusion between superseded and current information.

### G. Similar psychiatric drugs

Cases where model prior knowledge could contaminate source-grounded interpretation.

Initial emphasis should remain on psychiatry because this creates a credible link between domain expertise and evaluation design.

Each case should contain:

```json
{
  "case_id": "...",
  "drug": "...",
  "source": {...},
  "input_text": "...",
  "gold": {
    "approved_indications": [],
    "population_qualifiers": [],
    "limitations": []
  },
  "difficulty": "...",
  "clinical_notes": "..."
}
```

Gold-standard fields should be clinician-authored from the frozen source label.

---

# 13. Evaluation Dimensions

Each output should be scored independently across dimensions.

## 13.1 Factuality

Does the output make claims supported by the supplied label?

## 13.2 Completeness

Does it capture clinically important indication information?

## 13.3 Unsupported claims

Does it introduce plausible-sounding information not present in the source?

This is particularly important because medical language models may answer from prior knowledge rather than supplied evidence.

## 13.4 Population fidelity

Are age groups and other population restrictions preserved?

## 13.5 Therapeutic-context fidelity

Does the output preserve distinctions such as:

- adjunctive therapy
- monotherapy
- acute treatment
- maintenance treatment

where present in the source?

## 13.6 Source/version fidelity

Does the system use the correct label/version?

## 13.7 Schema compliance

Does the output satisfy the requested structured schema?

---

# 14. Scorers

Use layered evaluation.

## Layer 1 — deterministic

Examples:

- valid JSON
- required fields present
- expected indication terms present
- forbidden unsupported terms absent
- source identifiers preserved
- output parseable

## Layer 2 — clinician rubric

A clinician-authored rubric defines what constitutes:

- pass
- minor error
- major error
- clinically important failure

Store exemplars.

## Layer 3 — LLM-as-judge

Use an independent model to score outputs against:

- source label
- gold answer
- clinician rubric

Judge output should itself be structured.

Example:

```json
{
  "factuality": 4,
  "completeness": 5,
  "population_fidelity": 5,
  "unsupported_claim": false,
  "severity": "minor",
  "reason": "..."
}
```

The LLM judge must never be presented as ground truth.

---

# 15. Judge Calibration

Create a small manually reviewed subset.

For approximately 15–20 outputs:

1. score manually using the clinician rubric
2. score using the automated judge
3. compare agreement
4. document disagreements

Report:

- exact agreement
- adjacent-score agreement
- major-failure agreement

The point is to demonstrate awareness that **evaluation systems themselves require evaluation**.

---

# 16. Model Comparison

Run exactly the same frozen evaluation set across supported providers.

Produce a simple results table:

| Model | Factuality | Completeness | Unsupported Claims | Overall |
|---|---:|---:|---:|---:|
| Model A | | | | |
| Model B | | | | |
| Model C | | | | |

Also break failures down by case class.

Example:

```text
Population qualifiers      ███████░░
Multiple indications       █████████
Historical labels          ██████░░░
Adjunctive treatment       ████████░
```

The goal is not to prove one provider is globally superior.

The goal is to show that model selection can be informed by structured evaluation rather than intuition.

---

# 17. Regression Testing

Once the benchmark exists, it becomes a regression suite.

Prompt or model changes should be measurable.

Example:

```text
prompt_v1
↓
eval
↓
72% pass

prompt_v2
↓
eval
↓
86% pass
```

Store experiment metadata:

- prompt version
- model
- provider
- temperature/configuration
- timestamp
- dataset version
- scores

This turns prompting into an engineering process.

---

# 18. Automated Testing

Introduce `pytest`.

Minimum suite:

## Unit tests

Test deterministic logic:

- indication extraction
- label-date parsing
- version selection
- status heuristics
- malformed OpenFDA data
- missing fields
- schema validation

## Integration tests

Mock external APIs.

Test:

- OpenFDA client
- search endpoint
- batch endpoint
- label-analysis endpoint
- indication-search endpoint
- AI provider adapter

No paid LLM call should be required for normal CI.

## Smoke tests

Verify:

- application starts
- frontend builds
- backend health endpoint responds

---

# 19. Continuous Integration

Add:

```text
.github/workflows/ci.yml
```

Every push / pull request should run:

```text
backend
├── lint
├── tests
└── type checks

frontend
├── lint
├── typecheck
└── build
```

Suggested lightweight tooling:

Python:

- `pytest`
- `ruff`

TypeScript:

- existing ESLint
- `tsc`

Do not create an elaborate CI/CD platform.

A green GitHub Actions badge is sufficient portfolio evidence.

---

# 20. Observability and Failure Behaviour

External service failure should be explicit.

The application should distinguish:

- OpenFDA unavailable
- rate limited
- malformed upstream response
- LLM provider unavailable
- LLM malformed response
- evaluation failure

Use structured logging where useful.

Never silently convert a failed AI response into apparently valid clinical information.

---

# 21. Safety Positioning

Add:

`docs/SAFETY.md`

It should clearly state:

### Intended purpose

Research and exploration of public drug-label information.

### Not intended for

- diagnosis
- prescribing
- patient-specific clinical decisions
- emergency care
- replacement of official FDA documentation

### AI limitations

Generated summaries may:

- omit information
- misinterpret qualifiers
- hallucinate
- become outdated
- differ between models

### Mitigations

- source-grounded inputs
- visible provenance
- deterministic processing where possible
- structured outputs
- model evaluation
- regression testing
- explicit separation between source and generated content

Avoid making regulatory claims such as:

> FDA compliant  
> clinically validated  
> safe for clinical use

unless genuinely supported.

---

# 22. Architecture Decision Records

Create:

```text
docs/adr/
```

Only 3–4 short ADRs are needed.

### ADR-001: OpenFDA remains source of truth

Why authoritative retrieval is separated from generative summarisation.

### ADR-002: No database

Why live OpenFDA retrieval is currently sufficient.

### ADR-003: Multi-provider LLM interface

Why provider abstraction exists.

### ADR-004: Evaluation before additional AI features

Why reliability work was prioritised over expanding generative functionality.

These documents provide unusually strong product/engineering signal for relatively little work.

---

# 23. README Redesign

The README should become a portfolio landing page rather than internal documentation.

Top section:

```markdown
# FDA Drug Label Explorer

A clinician-built tool for exploring FDA drug labels and evaluating
source-grounded LLM summaries against authoritative medical evidence.
```

Immediately underneath:

- hero screenshot / GIF
- live demo if available
- CI badge
- short architecture diagram

Then:

## Why I built this

2–3 sentences describing the actual information problem.

## What it does

5–6 core capabilities.

## Clinical AI evaluation

Show actual benchmark results.

## Architecture

One diagram.

## Safety and provenance

Brief explanation.

## Quick start

Minimal commands.

## Technical details

Link deeper documentation rather than putting everything into the README.

---

# 24. Architecture Diagram

Include a simple diagram:

```text
                  ┌───────────────┐
                  │ React Client  │
                  └───────┬───────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   FastAPI   │
                   └──────┬──────┘
                          │
          ┌───────────────┴──────────────┐
          ▼                              ▼
 ┌────────────────┐             ┌────────────────┐
 │ OpenFDA Client │             │ Summary Service│
 └───────┬────────┘             └───────┬────────┘
         │                              │
         ▼                     ┌────────┼────────┐
      OpenFDA                  ▼        ▼        ▼
                            OpenAI   Gemini   DeepSeek
lo
                                   │
                                   ▼
                             Eval Harness
                                   │
                   ┌───────────────┼──────────────┐
                   ▼               ▼              ▼
              Deterministic    LLM Judge    Clinician Rubric
```

Keep it understandable.

---

# 25. Demo

Create a **45–60 second demo**.

Suggested sequence:

1. Search `risperidone`
2. Show authoritative FDA label information
3. Show historical labels
4. Generate AI summary
5. Show provenance
6. Open Eval view/report
7. Show model comparison / failure analysis

This tells a complete story:

**data → product → AI → evaluation → safety**

---

# 26. Optional Eval UI

Only implement if inexpensive after the backend evaluation pipeline works.

Possible route:

`/evals`

Display:

- dataset version
- models compared
- overall scores
- error categories
- example failure cases

Do not spend significant time creating dashboard polish before the evaluation methodology itself is sound.

---

# 27. Repository Hygiene

Before positioning the project publicly:

- remove dead code
- remove unused dependencies
- remove unused infrastructure
- remove secrets
- verify `.env.example`
- remove generated artifacts that do not belong in Git
- standardise naming
- remove commented-out experimental code
- add licence if appropriate
- add repository description
- add GitHub topics

Suggested topics:

```text
clinical-ai
health-ai
llm-evaluation
fastapi
react
openfda
medical-data
python
typescript
```

---

# 28. Success Metrics

This refactor succeeds when an external reviewer can verify all of the following within approximately five minutes:

### Product

- Real health-data product exists
- Clear user/problem definition
- Application runs

### Engineering

- Backend is modular
- External APIs are isolated
- tests exist
- CI passes
- configuration is clean

### AI

- Multiple LLM providers are supported
- prompts are explicit/versioned
- outputs are structured
- model behaviour can be compared

### Evaluation

- benchmark dataset exists
- clinician-authored rubric exists
- deterministic scorers exist
- LLM judge exists
- judge is calibrated against human scoring
- regression results are reproducible

### Clinical safety

- authoritative source is explicit
- provenance is retained
- limitations are documented
- generated and source material are visually/conceptually separated

### Product judgement

- unnecessary infrastructure has been removed
- scope is intentionally constrained
- trade-offs are documented

---

# 29. Definition of Done

The portfolio version is complete when:

- [ ] Existing core functionality still works
- [ ] `main.py` is reduced to application bootstrap/routing
- [ ] OpenFDA access lives behind a client abstraction
- [ ] AI providers implement one common interface
- [ ] PostgreSQL removed unless genuinely used
- [ ] Redis removed unless genuinely used
- [ ] Automated backend tests exist
- [ ] Frontend build/type checking is automated
- [ ] GitHub Actions CI is green
- [ ] 30–50-case frozen eval dataset exists
- [ ] Clinician-authored gold answers exist
- [ ] Deterministic scoring exists
- [ ] LLM-as-judge scoring exists
- [ ] Human/judge calibration experiment exists
- [ ] At least two models have been benchmarked
- [ ] Results report is committed
- [ ] `SAFETY.md` exists
- [ ] ADRs document major design decisions
- [ ] README rewritten
- [ ] architecture diagram added
- [ ] screenshot/GIF added
- [ ] demo video created
- [ ] repository metadata/topics cleaned up

---

# 30. Execution Order

## Phase 1 — Clean the foundation

1. Baseline current behaviour.
2. Add tests around important existing deterministic logic.
3. Split `main.py`.
4. Isolate OpenFDA client.
5. Remove unused Postgres/Redis.
6. Add CI.

**Do not change product behaviour significantly during this phase.**

## Phase 2 — Professionalise AI integration

1. Formalise LLM provider interface.
2. Create structured summary schema.
3. Version prompts.
4. Attach model/source provenance.
5. Improve failure handling.

## Phase 3 — Build evaluation system

1. Define clinical rubric.
2. Build first 10 benchmark cases.
3. Implement deterministic scorers.
4. Implement LLM judge.
5. Manually score calibration subset.
6. Expand benchmark to 30–50 cases.
7. Run model comparison.
8. Produce report.

## Phase 4 — Portfolio polish

1. Rewrite README.
2. Add architecture diagram.
3. Add safety documentation.
4. Add ADRs.
5. Add screenshot/GIF.
6. Record short demo.
7. Clean GitHub repository metadata.

---

# 31. Priority Rules

If time becomes constrained:

### Must have

1. modular backend
2. tests
3. CI
4. clean Docker
5. 30-case eval set
6. clinician rubric
7. deterministic + LLM scoring
8. model comparison
9. excellent README

### Should have

10. provenance UI
11. architecture diagram
12. safety document
13. ADRs
14. demo GIF/video

### Nice to have

15. dedicated eval dashboard
16. additional providers
17. larger benchmark

Never sacrifice evaluation quality to build more UI.

---

# 32. Explicit Anti-Goals for Coding Agents

Agents working on this repository must NOT:

- rewrite the application from scratch
- introduce a new framework without necessity
- introduce databases merely for sophistication
- add vector search
- add generic agent frameworks
- add authentication
- add Kubernetes
- add cloud-specific dependencies
- expand the clinical scope
- change label interpretation heuristics without tests
- claim medical validation
- claim regulatory compliance
- manufacture benchmark results
- generate “gold” clinical answers without clinician review
- hide model failures from reports

Prefer small, reviewable pull requests.

Every architectural change must answer:

> What concrete problem does this solve?

---

# 33. Portfolio Narrative

Once complete, this repository should support the following truthful claim:

> Built a full-stack clinical AI product using React, FastAPI and OpenFDA, with multi-model LLM summarisation and a clinician-designed evaluation framework measuring factuality, completeness, source fidelity and clinically significant failure modes. Developed reproducible model comparisons, automated regression tests and calibrated LLM-based scoring against expert review.

That statement should only be used after the corresponding components actually exist.

---

# 34. Strategic Outcome

FDA_v2 should not attempt to prove that its author is a senior software engineer.

It should prove something more relevant:

> The author can move fluently between clinical reasoning, product definition, data/API engineering, LLM prototyping, evaluation, safety and shipping.

That is the target state.
