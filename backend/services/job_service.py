import json
from sqlalchemy.orm import Session
from backend.models import Job, Application
from backend.schemas import JobCreate

def get_jobs(db: Session, status: str = None):
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    jobs = query.order_by(Job.id.desc()).all()
    
    result = []
    for j in jobs:
        req_skills = json.loads(j.required_skills) if j.required_skills else []
        app_count = db.query(Application).filter(Application.job_id == j.id).count()
        result.append({
            "id": j.id,
            "title": j.title,
            "department": j.department,
            "location": j.location,
            "job_type": j.job_type,
            "status": j.status,
            "description": j.description,
            "required_skills": req_skills,
            "min_experience": j.min_experience,
            "salary_range": j.salary_range,
            "created_at": j.created_at,
            "applicant_count": app_count
        })
    return result

def get_job_by_id(db: Session, job_id: int):
    j = db.query(Job).filter(Job.id == job_id).first()
    if not j:
        return None
    req_skills = json.loads(j.required_skills) if j.required_skills else []
    app_count = db.query(Application).filter(Application.job_id == j.id).count()
    return {
        "id": j.id,
        "title": j.title,
        "department": j.department,
        "location": j.location,
        "job_type": j.job_type,
        "status": j.status,
        "description": j.description,
        "required_skills": req_skills,
        "min_experience": j.min_experience,
        "salary_range": j.salary_range,
        "created_at": j.created_at,
        "applicant_count": app_count
    }

def create_job(db: Session, job_data: JobCreate):
    db_job = Job(
        title=job_data.title,
        department=job_data.department,
        location=job_data.location or "Remote",
        job_type=job_data.job_type or "Full-time",
        status=job_data.status or "Published",
        description=job_data.description,
        required_skills=json.dumps(job_data.required_skills),
        min_experience=job_data.min_experience or 0,
        salary_range=job_data.salary_range or "$80,000 - $120,000"
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return get_job_by_id(db, db_job.id)

def update_job_status(db: Session, job_id: int, status: str):
    j = db.query(Job).filter(Job.id == job_id).first()
    if j:
        j.status = status
        db.commit()
        db.refresh(j)
    return get_job_by_id(db, job_id)
