import os
from fastapi import FastAPI, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.config import settings
from backend.database import get_db, Base, engine
from backend.schemas import (
    JobCreate, JobResponse, CandidateCreate, CandidateResponse,
    NoteCreate, ResumeParseResponse, SkillGapResponse
)
from backend.services import (
    job_service, candidate_service, resume_service, matching_service, analytics_service
)
from backend.seed import seed_db

Base.metadata.create_all(bind=engine)
try:
    seed_db()
except Exception as e:
    print(f"Seed info: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Open-source AI-powered Talent Intelligence & Hiring Infrastructure"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HEALTH CHECK ---
@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}

# --- RECRUITER AUTH API ---
@app.post(f"{settings.API_V1_STR}/auth/recruiter-login")
def recruiter_login(passcode: str = Form(...)):
    if passcode.strip() in ["admin123", "recruiter", "talentOS"]:
        return {"authenticated": True, "token": "recruiter-auth-token-12345", "role": "Recruiter"}
    raise HTTPException(status_code=401, detail="Invalid recruiter access passcode.")

# --- ANALYTICS API ---
@app.get(f"{settings.API_V1_STR}/analytics/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    return analytics_service.get_dashboard_metrics(db)

# --- JOB MANAGEMENT APIs ---
@app.get(f"{settings.API_V1_STR}/jobs", response_model=List[JobResponse])
def list_jobs(status: Optional[str] = None, db: Session = Depends(get_db)):
    return job_service.get_jobs(db, status=status)

@app.post(f"{settings.API_V1_STR}/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_new_job(job: JobCreate, db: Session = Depends(get_db)):
    return job_service.create_job(db, job)

@app.get(f"{settings.API_V1_STR}/jobs/{{job_id}}", response_model=JobResponse)
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return job

@app.patch(f"{settings.API_V1_STR}/jobs/{{job_id}}/status", response_model=JobResponse)
def update_job_status(job_id: int, status: str = Query(...), db: Session = Depends(get_db)):
    return job_service.update_job_status(db, job_id, status)

# --- PUBLIC JOB SEEKER APPLICATION API ---
@app.post(f"{settings.API_V1_STR}/jobs/{{job_id}}/apply")
async def apply_to_job(
    job_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(""),
    location: Optional[str] = Form("Remote"),
    current_role: Optional[str] = Form("Applicant"),
    experience_years: float = Form(0.0),
    skills: Optional[str] = Form(""),
    resume_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    file_bytes = b""
    filename = "resume.pdf"
    if resume_file:
        file_bytes = await resume_file.read()
        filename = resume_file.filename or "resume.pdf"

    user_skills_list = [s.trim() if hasattr(s, 'trim') else s.strip() for s in skills.split(',') if s.strip()] if skills else []

    res = candidate_service.apply_to_job_with_resume(
        db=db,
        job_id=job_id,
        name=name,
        email=email,
        phone=phone,
        location=location,
        current_role=current_role,
        experience_years=experience_years,
        user_skills=user_skills_list,
        file_bytes=file_bytes,
        filename=filename
    )

    if not res:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    return res

# --- CANDIDATE MANAGEMENT APIs ---
@app.get(f"{settings.API_V1_STR}/candidates", response_model=List[CandidateResponse])
def list_candidates(status: Optional[str] = None, db: Session = Depends(get_db)):
    return candidate_service.get_candidates(db, status=status)

@app.post(f"{settings.API_V1_STR}/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_new_candidate(candidate: CandidateCreate, db: Session = Depends(get_db)):
    return candidate_service.create_candidate(db, candidate)

@app.get(f"{settings.API_V1_STR}/candidates/{{candidate_id}}", response_model=CandidateResponse)
def get_candidate_detail(candidate_id: int, db: Session = Depends(get_db)):
    cand = candidate_service.get_candidate_by_id(db, candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return cand

@app.patch(f"{settings.API_V1_STR}/candidates/{{candidate_id}}/status", response_model=CandidateResponse)
def update_candidate_status(candidate_id: int, status: str = Query(...), db: Session = Depends(get_db)):
    return candidate_service.update_candidate_status(db, candidate_id, status)

@app.delete(f"{settings.API_V1_STR}/candidates/{{candidate_id}}")
def delete_candidate_profile(candidate_id: int, db: Session = Depends(get_db)):
    success = candidate_service.delete_candidate(db, candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully", "id": candidate_id}

@app.post(f"{settings.API_V1_STR}/candidates/{{candidate_id}}/notes", response_model=CandidateResponse)
def add_candidate_note(candidate_id: int, note: NoteCreate, db: Session = Depends(get_db)):
    return candidate_service.add_candidate_note(db, candidate_id, note)

# --- RESUME INTELLIGENCE FILE UPLOAD API ---
@app.post(f"{settings.API_V1_STR}/resume/parse", response_model=ResumeParseResponse)
async def parse_resume_file(file: UploadFile = File(...)):
    filename = file.filename or "resume.pdf"
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty resume file provided")
    return resume_service.process_resume_file(file_bytes, filename)

# --- CANDIDATE MATCHING ENGINE APIs ---
@app.get(f"{settings.API_V1_STR}/matching/job/{{job_id}}/rankings")
def get_job_rankings(job_id: int, db: Session = Depends(get_db)):
    return matching_service.get_job_candidate_rankings(db, job_id)

@app.get(f"{settings.API_V1_STR}/matching/candidate/{{candidate_id}}/recommendations")
def get_candidate_recommendations(candidate_id: int, db: Session = Depends(get_db)):
    return matching_service.get_recommendations_for_candidate(db, candidate_id)

@app.get(f"{settings.API_V1_STR}/matching/skill-gap")
def get_skill_gap_analysis(candidate_id: int = Query(...), job_id: int = Query(...), db: Session = Depends(get_db)):
    result = matching_service.analyze_skill_gap(db, candidate_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Candidate or job record not found")
    return result

# --- SERVE FRONTEND APPLICATION ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "TalentOS API is running. Frontend static files not found."})
