from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    location = Column(String(100), default="Remote")
    job_type = Column(String(50), default="Full-time") # Full-time, Part-time, Contract
    status = Column(String(50), default="Published") # Published, Draft, Closed
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=False) # JSON or comma-separated string
    min_experience = Column(Integer, default=0)
    salary_range = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    current_role = Column(String(150), nullable=True)
    experience_years = Column(Float, default=0.0)
    education = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=False) # JSON or comma-separated string
    status = Column(String(50), default="Applied") # Applied, Screening, Interviewing, Offered, Rejected, Hired
    resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    notes = relationship("CandidateNote", back_populates="candidate", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    stage = Column(String(50), default="Applied") # Applied, Screening, Interviewing, Offered, Rejected, Hired
    match_score = Column(Float, default=0.0) # 0 to 100 percentage
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")

class CandidateNote(Base):
    __tablename__ = "candidate_notes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    author = Column(String(100), default="Recruiter")
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="notes")
