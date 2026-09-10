from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- Skill Schemas ---
class SkillItem(BaseModel):
    name: str
    category: Optional[str] = "General"
    level: Optional[str] = "Intermediate"

# --- Job Schemas ---
class JobBase(BaseModel):
    title: str
    department: str
    location: Optional[str] = "Remote"
    job_type: Optional[str] = "Full-time"
    status: Optional[str] = "Published"
    description: str
    required_skills: List[str]
    min_experience: Optional[int] = 0
    salary_range: Optional[str] = "$80,000 - $120,000"

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    created_at: datetime
    applicant_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Note Schemas ---
class NoteCreate(BaseModel):
    note: str
    author: Optional[str] = "Recruiter"

class NoteResponse(BaseModel):
    id: int
    candidate_id: int
    author: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Candidate Schemas ---
class CandidateBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    current_role: Optional[str] = None
    experience_years: Optional[float] = 0.0
    education: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str]
    status: Optional[str] = "Applied"

class CandidateCreate(CandidateBase):
    resume_text: Optional[str] = None

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    resume_text: Optional[str] = None
    notes: Optional[List[NoteResponse]] = []

    class Config:
        from_attributes = True

# --- Resume Intelligence Schemas ---
class ResumeParseResponse(BaseModel):
    parsed_name: str
    parsed_email: str
    parsed_phone: str
    extracted_skills: List[str]
    experience_years: float
    extracted_education: List[str]
    summary_ai: str
    score: float
    filename: Optional[str] = "document.pdf"
    raw_character_count: Optional[int] = 0

# --- Matching Engine Schemas ---
class SkillGapResponse(BaseModel):
    candidate_id: int
    job_id: int
    candidate_name: str
    job_title: str
    candidate_skills: List[str]
    required_skills: List[str]
    matching_skills: List[str]
    missing_skills: List[str]
    fit_score: float
    recommendation: str
