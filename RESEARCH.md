# Research Note

## The learner problem

Practicing Low-Level Design is easy to *start* and hard to *know if you're doing well*.
A learner can sketch a Parking Lot or Elevator design in twenty minutes, but LLD rarely
has one correct answer — so unlike a LeetCode problem with a pass/fail test suite, the
learner has no signal on whether their class boundaries, abstractions, and relationships
are actually good, or just "compiles in my head."

The gap isn't access to problems (plenty of LLD problem lists exist online). The gap is
**feedback loops**: something that looks at an actual design and says, specifically,
"here's what's solid, here's what will hurt you when requirements change, here's an
alternative you didn't consider."

## Existing approaches, briefly

- **LeetCode / HackerRank style judges** — excellent for DSA because correctness is
  binary and testable. LLD doesn't fit this: there's no single "expected output" for a
  Parking Lot class diagram.
- **Educative / DesignGurus "Grokking LLD" style courses** — good structured content and
  model answers, but the learner reads a model solution rather than getting feedback on
  *their own* solution. Practice happens by comparison, not by submission.
- **Mock interview platforms (Pramp, interviewing.io)** — real feedback from a human, but
  synchronous, scheduled, and not repeatable on demand. Not really "practice loop" tooling.
- **Generic "paste your code into ChatGPT" workflows** — flexible but unstructured: no
  problem bank, no history, no consistent rubric, and feedback quality depends entirely on
  how well the learner happens to prompt it that day.

## The gap

Nothing sits in the middle: a **repeatable, structured practice loop** where a learner
picks a known problem, submits a design in a consistent shape, gets feedback that mixes
objective checks (did you actually model the entities the problem needs?) with
qualitative reasoning (trade-offs, alternatives), and can look back at how their designs
improved over multiple attempts.

## Product direction

A small, focused practice platform built around one loop:

**Choose problem → design → submit → get feedback → review → try again.**

Key product decisions this research led to:

1. **Submission format should capture structure, not just prose.** If a learner just
   pastes free text, evaluation degrades into "read this essay." Asking for a lightweight
   structured shape (classes, fields, methods, relationships) — while still allowing free
   text/code alongside it — gives the objective half of evaluation something concrete to
   check, without forcing the learner into a full diagramming tool.
2. **Feedback needs an objective layer, not just an LLM opinion.** LLMs are good at
   *nuance* (trade-offs, alternatives) but inconsistent at *facts* (did they define a
   Vehicle class? is there a god class?). Splitting these into a deterministic evaluator
   and a narrative evaluator makes the feedback both trustworthy and rich — this is the
   core design bet of the MVP (see DESIGN.md).
3. **History matters more than a single attempt.** The value of practice is improvement
   across attempts, not one good/bad verdict. So attempt history is a first-class feature,
   not an afterthought.
4. **Scope discipline.** A full diagram editor, real-time collaboration, or a large
   rubric/LMS system would take the two days away from the part that actually matters:
   the domain design and the evaluation approach. The MVP intentionally uses a simple
   structured form + free text instead of a canvas.
