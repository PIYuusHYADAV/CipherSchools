# Build Plan — LLD Practice Platform

Goal: a working, explainable prototype in simple pieces. No over-engineering.
Priority order: (1) working features end-to-end, (2) clear domain design,
(3) tests for the important stuff, (4) docs. Code quality matters but isn't
the point of this assignment — the LLD thinking is.

## Stack (kept deliberately boring)
- Backend: Python + FastAPI (one process, no microservices)
- DB: SQLite via SQLAlchemy (file-based, zero setup)
- Frontend: plain HTML + vanilla JS, served by FastAPI (no build step, no React)
- AI: pluggable `Evaluator` interface. Default = a rule-based mock "LLM"
  evaluator that still gives real, structured, useful text. If an API key is
  set in env, a real Gemini call is used instead. Same interface either way.

## Phases

**Phase 0 — Skeleton**
- Project structure, FastAPI app boots, SQLite tables created, health check.

**Phase 1 — Problems**
- Seed 3 hand-written LLD problems (Parking Lot, Vending Machine, Elevator)
  with requirements + hints about expected entities (used later for eval).
- Endpoint + page to list and view a problem.

**Phase 2 — Attempts (the "think/design" step)**
- Learner starts an attempt on a problem.
- Attempt holds a draft: structured classes (name, fields, methods,
  relationships) + a free-text code/pseudo-code box. Autosave on submit only
  (keep it simple — no live autosave infra).

**Phase 3 — Submission + status**
- Submit an attempt -> creates a Submission snapshot, status = pending.
- Evaluation runs synchronously in the request for the mock evaluator
  (it's fast), but the state machine (pending/evaluating/completed/failed)
  is real, so swapping to a slow real LLM call or a queue later is a
  non-breaking change. On evaluator exception -> status = failed, learner can
  retry.

**Phase 4 — Evaluation & feedback (the core of the assignment)**
- DeterministicEvaluator: checks against each problem's expected-entity list,
  checks for at least one interface/abstraction where the problem needs
  varying behavior, flags obvious god-classes (too many responsibilities),
  flags missing relationships.
- MockLLMEvaluator: takes the deterministic findings + the learner's actual
  classes/code and produces narrative feedback (strengths, gaps, one
  alternative design, one trade-off question) — templated but genuinely
  reads the submission, not canned text.
- CompositeEvaluator: runs both, merges into one EvaluationResult shown to
  the learner (checklist + narrative).

**Phase 5 — History**
- Learner can see all past attempts/submissions for a problem, with status
  and score, and reopen an old submission's feedback.

**Phase 6 — Tests**
- Domain-level tests: deterministic evaluator against a good and a bad
  submission, submission state machine, failure/retry path, edge case of
  empty submission.

**Phase 7 — Docs**
- RESEARCH.md, DESIGN.md, README.md, AI_USAGE.md.

## What I'm deliberately NOT building
- Auth/login (single hardcoded demo learner) — not the point of the assignment.
- Real-time collaboration, diagram canvas/drawing UI — free-text + structured
  form covers "design expression" without a drag-and-drop diagram editor.
- Any queue/worker infra — the Evaluator interface is swappable later, that's
  the answer to "what if evaluation is slow," not an actual queue now.
- Multiple LLM providers, retries with backoff, rate limiting — out of scope
  for a 2-day LLD-focused prototype.
