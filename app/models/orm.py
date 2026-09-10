
from datetime import datetime, timezone

def _utcnow():
    return datetime.now(timezone.utc)
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db import Base


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(String, default="medium")
    description = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False)          # list[str]
    expected_entities = Column(JSON, nullable=False)      # list[str] - used by evaluator
    hints_for_variation = Column(JSON, default=list)      # list[str] - behaviors that vary
                                                            # -> hints an interface/strategy is expected

    attempts = relationship("Attempt", back_populates="problem")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    learner_id = Column(String, default="demo-learner")
    created_at = Column(DateTime, default=_utcnow)
    status = Column(String, default="in_progress")  # in_progress | submitted

    # the working draft the learner edits
    draft_classes = Column(JSON, default=list)          # list[{name, type, fields[], methods[]}]
    draft_relationships = Column(JSON, default=list)    # list[{from, to, kind}]
    draft_code = Column(Text, default="")

    problem = relationship("Problem", back_populates="attempts")
    submissions = relationship("Submission", back_populates="attempt")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    # snapshot of the design at submit time (never mutated afterwards)
    classes = Column(JSON, default=list)
    relationships = Column(JSON, default=list)
    code = Column(Text, default="")

    status = Column(String, default="pending")  # pending | evaluating | completed | failed
    score = Column(Integer, nullable=True)
    checklist = Column(JSON, nullable=True)      # list[{label, passed, detail}]
    narrative_feedback = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    attempt = relationship("Attempt", back_populates="submissions")
