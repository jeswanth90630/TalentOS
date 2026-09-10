import json
from sqlalchemy.orm import Session
from backend.models import Candidate, CandidateNote, Application, Job
from backend.schemas import CandidateCreate, NoteCreate
from ai.parser import parse_resume, extract_text_from_file_bytes
from ai.matcher import compute_match_score

def get_candidates(db: Session, status: str = None):
    query = db.query(Candidate)
    if status:
        query = query.filter(Candidate.status == status)
    candidates = query.order_by(Candidate.id.desc()).all()

    result = []
    for c in candidates:
        skills = json.loads(c.skills) if c.skills else []
        notes = [{
            "id": n.id,
            "candidate_id": n.candidate_id,
            "author": n.author,
            "note": n.note,
            "created_at": n.created_at
        } for n in c.notes]

        result.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "location": c.location,
            "current_role": c.current_role,
            "experience_years": c.experience_years,
            "education": c.education,
            "summary": c.summary,
            "skills": skills,
            "status": c.status,
            "resume_text": c.resume_text,
            "created_at": c.created_at,
            "notes": notes
        })
    return result

def get_candidate_by_id(db: Session, candidate_id: int):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        return None
    skills = json.loads(c.skills) if c.skills else []
    notes = [{
        "id": n.id,
        "candidate_id": n.candidate_id,
        "author": n.author,
        "note": n.note,
        "created_at": n.created_at
    } for n in c.notes]

    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "location": c.location,
        "current_role": c.current_role,
        "experience_years": c.experience_years,
        "education": c.education,
        "summary": c.summary,
        "skills": skills,
        "status": c.status,
        "resume_text": c.resume_text,
        "created_at": c.created_at,
        "notes": notes
    }

def create_candidate(db: Session, candidate_data: CandidateCreate):
    db_cand = Candidate(
        name=candidate_data.name,
        email=candidate_data.email,
        phone=candidate_data.phone,
        location=candidate_data.location or "Remote",
        current_role=candidate_data.current_role or "Software Engineer",
        experience_years=candidate_data.experience_years or 0.0,
        education=candidate_data.education or "B.S. Computer Science",
        summary=candidate_data.summary or "",
        skills=json.dumps(candidate_data.skills),
        status=candidate_data.status or "Applied",
        resume_text=candidate_data.resume_text or ""
    )
    db.add(db_cand)
    db.commit()
    db.refresh(db_cand)
    return get_candidate_by_id(db, db_cand.id)

def apply_to_job_with_resume(
    db: Session,
    job_id: int,
    name: str,
    email: str,
    phone: str,
    location: str,
    current_role: str,
    experience_years: float,
    user_skills: list,
    file_bytes: bytes,
    filename: str
):
    """
    Job seeker application flow: parses PDF/DOCX resume, calculates backend ATS score,
    creates/updates candidate record, and links job application.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None

    # Parse resume PDF/DOCX file
    parsed_res = {}
    extracted_text = ""
    if file_bytes:
        extracted_text = extract_text_from_file_bytes(file_bytes, filename)
        parsed_res = parse_resume(extracted_text, filename)

    # Merge user skills with extracted skills
    combined_skills = set(user_skills)
    if parsed_res.get("extracted_skills"):
        combined_skills.update(parsed_res["extracted_skills"])

    if not combined_skills:
        combined_skills = {"Python", "Software Engineering"}

    # Calculate ATS Match Score
    job_req_skills = json.loads(job.required_skills) if job.required_skills else []
    match_data = compute_match_score(
        list(combined_skills),
        job_req_skills,
        experience_years,
        job.min_experience
    )
    ats_score = match_data["match_percentage"]

    # Check if candidate exists by email
    cand = db.query(Candidate).filter(Candidate.email == email).first()
    if not cand:
        cand = Candidate(
            name=name,
            email=email,
            phone=phone,
            location=location or "Remote",
            current_role=current_role or "Applicant",
            experience_years=experience_years or 0.0,
            education=parsed_res.get("extracted_education", ["Degree Holder"])[0] if parsed_res.get("extracted_education") else "B.S. Software Engineering",
            summary=parsed_res.get("summary_ai", f"Application for {job.title}"),
            skills=json.dumps(list(combined_skills)),
            status="Applied",
            resume_text=extracted_text[:3000] if extracted_text else f"Applied for {job.title}"
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)
    else:
        # Update existing candidate record with newest resume/skills
        cand.name = name
        cand.phone = phone or cand.phone
        cand.location = location or cand.location
        cand.current_role = current_role or cand.current_role
        cand.experience_years = max(experience_years, cand.experience_years or 0.0)
        cand.status = "Applied"
        if extracted_text:
            cand.resume_text = extracted_text[:3000]
        existing_skills = set(json.loads(cand.skills)) if cand.skills else set()
        existing_skills.update(combined_skills)
        cand.skills = json.dumps(list(existing_skills))
        db.commit()
        db.refresh(cand)

    # Delete any existing application for this same job to replace with newest score
    db.query(Application).filter(Application.candidate_id == cand.id, Application.job_id == job.id).delete()

    # Link Application with ATS score
    app_record = Application(
        candidate_id=cand.id,
        job_id=job.id,
        stage="Applied",
        match_score=ats_score
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    return {
        "success": True,
        "message": f"Application for {job.title} submitted successfully!",
        "application_id": app_record.id,
        "job_title": job.title,
        "candidate_name": cand.name,
        "candidate_id": cand.id
    }

def update_candidate_status(db: Session, candidate_id: int, status: str):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if c:
        c.status = status
        # Update stage on linked application records
        db.query(Application).filter(Application.candidate_id == candidate_id).update({"stage": status})
        db.commit()
        db.refresh(c)
    return get_candidate_by_id(db, candidate_id)

def delete_candidate(db: Session, candidate_id: int):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if c:
        # Delete associated Applications and Notes first
        db.query(Application).filter(Application.candidate_id == candidate_id).delete()
        db.query(CandidateNote).filter(CandidateNote.candidate_id == candidate_id).delete()
        db.delete(c)
        db.commit()
        return True
    return False

def add_candidate_note(db: Session, candidate_id: int, note_data: NoteCreate):
    note = CandidateNote(
        candidate_id=candidate_id,
        author=note_data.author or "Recruiter",
        note=note_data.note
    )
    db.add(note)
    db.commit()
    return get_candidate_by_id(db, candidate_id)
