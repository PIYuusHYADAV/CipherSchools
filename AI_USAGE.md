# AI Usage

This was built with Claude doing the implementation from a plan we agreed on together.
Here are the decisions worth calling out specifically — what was suggested, what I
accepted or pushed back on, and why.

## 1. Splitting evaluation into deterministic + narrative layers

**Suggested:** Rather than one "AI evaluator" that reads the submission and returns a
score + feedback in one call, split it into a `DeterministicEvaluator` (objective checks,
no AI) and a narrative evaluator (LLM or LLM-shaped), merged by a `CompositeEvaluator`.

**Accepted, and it's the right call.** A single LLM-does-everything evaluator would make
scoring inconsistent between runs and hard to unit test (you can't assert "the score is
exactly X" against a live model). Splitting it means the checklist/score is deterministic
and testable with plain asserts, while the qualitative part — the thing that actually
needs an opinion — stays flexible. This became the core design answer for "which parts of
evaluation should be deterministic vs. benefit from an LLM," so it wasn't just an
implementation detail, it shaped the whole DESIGN.md answer.

## 2. Mock LLM evaluator instead of requiring a real API key by default

**Suggested:** Default to a rule-based "mock LLM" evaluator that still reads the actual
submission and produces different feedback for different inputs, with a real
Gemini-backed evaluator as an opt-in behind an env var.

**Accepted.** My first instinct was to just wire up the real API directly since I have
access to it. Claude pointed out that would mean the prototype (and its tests) depend on
network access and a paid key to run at all, which is a bad default for something meant to
be reviewed/graded. I agreed and kept the real LLM path but made it opt-in — this also
made the narrative evaluator's tests fast and deterministic instead of flaky.

## 3. Where domain objects live relative to the ORM

**Suggested:** Keep `ClassSpec`, `DesignSubmission`, `Evaluator`, etc. as plain dataclasses
in `domain.py`, completely separate from the SQLAlchemy models in `models/orm.py`, with
the FastAPI route layer doing the translation between them.

**Accepted.** This is the part of the assignment actually being graded (LLD/domain
design), so I wanted evaluators to be testable with zero DB or HTTP involved. This paid
off directly: `tests/test_evaluators.py` and `test_mock_llm_evaluator.py` don't touch the
database at all and run in milliseconds.

## 4. A real bug caught by the failure-path design, not by me reading the code

**What happened:** While building the "what if evaluation fails" behavior, I asked Claude
to test a submission with a malformed relationship (missing `source`/`target` keys) to
confirm it turns into a `failed` status instead of crashing. It actually crashed with a
500 — the domain-object construction (`RelationshipSpec(**r)`) was happening *outside* the
try/except in `_run_evaluation`, so a bad input skipped the "graceful failure" path
entirely.

**What I did with it:** Accepted the fix (move object construction inside the try block,
plus filter unexpected keys defensively) and asked for a regression test
(`test_evaluation_failure_is_recoverable_via_retry`) so this specific failure mode can't
silently regress. I'm calling this out because it's a good example of why the assignment
asks "what happens if evaluation fails" as a design question, not just an implementation
detail — the first version of the code answered that question incorrectly until it was
actually exercised.

## 5. Scope cuts I pushed back on / confirmed

Claude proposed (and I agreed to) explicitly **not** building: authentication, a drag-and-
drop diagram canvas, and any queue/worker infrastructure for evaluation — instead using a
single demo learner, a structured form + free-text code, and synchronous evaluation with
an explicit status field. I confirmed this was the right amount of scope for a 2-day
prototype focused on LLD rather than infra, rather than letting the build creep into a
bigger system. The one place I asked to keep a real (not fully mocked) path was the LLM
evaluator — I wanted an actual `RealLLMEvaluator` implementation behind a flag, not just a
description of how one would work, so the extensibility claim in DESIGN.md is backed by
working code, not just prose.
