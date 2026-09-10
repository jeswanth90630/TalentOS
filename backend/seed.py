import json
from sqlalchemy.orm import Session
from backend.database import SessionLocal, Base, engine
from backend.models import Job, Candidate, Application, CandidateNote

def seed_db():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    # Check if already seeded
    if db.query(Job).count() > 0:
        db.close()
        return

    # Seed Jobs
    jobs_data = [
        {
            "title": "Senior AI / Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "job_type": "Full-time",
            "status": "Published",
            "description": "Building next-generation talent intelligence & AI matching workflows using FastAPI, Python, PostgreSQL, and vector databases.",
            "required_skills": json.dumps(["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "OpenAI", "System Design"]),
            "min_experience": 4,
            "salary_range": "$140,000 - $180,000"
        },
        {
            "title": "Lead Frontend Engineer (Next.js)",
            "department": "Engineering",
            "location": "San Francisco, CA / Remote",
            "job_type": "Full-time",
            "status": "Published",
            "description": "Crafting intuitive recruiter dashboards, interactive resume parsing views, and sleek design systems with Next.js and TailwindCSS.",
            "required_skills": json.dumps(["Next.js", "TypeScript", "React", "TailwindCSS", "HTML", "CSS", "UI/UX Design"]),
            "min_experience": 3,
            "salary_range": "$130,000 - $165,000"
        },
        {
            "title": "Machine Learning & NLP Specialist",
            "department": "AI Research",
            "location": "Remote",
            "job_type": "Full-time",
            "status": "Published",
            "description": "Developing domain-specific sentence embeddings, resume parsers, and semantic recommendation engines.",
            "required_skills": json.dumps(["Python", "Machine Learning", "NLP", "Sentence Transformers", "Qdrant", "Deep Learning", "PyTorch"]),
            "min_experience": 3,
            "salary_range": "$150,000 - $190,000"
        },
        {
            "title": "Technical Product Manager",
            "department": "Product",
            "location": "New York, NY",
            "job_type": "Full-time",
            "status": "Published",
            "description": "Defining candidate management, applicant pipeline features, and AI recruiter experience roadmap.",
            "required_skills": json.dumps(["Product Management", "Agile", "Scrum", "System Design", "Leadership"]),
            "min_experience": 5,
            "salary_range": "$145,000 - $175,000"
        }
    ]

    for j in jobs_data:
        db.add(Job(**j))
    db.commit()

    # Seed Candidates
    candidates_data = [
        {
            "name": "Sarah Chen",
            "email": "sarah.chen@example.com",
            "phone": "+1 (555) 234-5678",
            "location": "San Francisco, CA",
            "current_role": "Senior Staff Backend Engineer",
            "experience_years": 5.5,
            "education": "M.S. Computer Science, Stanford University",
            "summary": "Full-stack Python & AI backend engineer with expertise in distributed microservices, FastAPI, and vector databases.",
            "skills": json.dumps(["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "OpenAI", "System Design", "Git", "REST API"]),
            "status": "Interviewing",
            "resume_text": "Sarah Chen\nsarah.chen@example.com\n5.5 years experience in Python, FastAPI, PostgreSQL, Redis, Docker, and OpenAI."
        },
        {
            "name": "Marcus Vance",
            "email": "marcus.vance@example.com",
            "phone": "+1 (555) 876-5432",
            "location": "Austin, TX",
            "current_role": "Senior Frontend Developer",
            "experience_years": 4.0,
            "education": "B.S. Software Engineering, UT Austin",
            "summary": "Passionate frontend creator specializing in high-performance Web apps with Next.js, React, TypeScript, and responsive CSS styling.",
            "skills": json.dumps(["Next.js", "TypeScript", "React", "TailwindCSS", "HTML", "CSS", "UI/UX Design", "Git"]),
            "status": "Screening",
            "resume_text": "Marcus Vance\n4 years experience building UI applications with Next.js, React, TypeScript, and TailwindCSS."
        },
        {
            "name": "Elena Rostova",
            "email": "elena.rostova@example.com",
            "phone": "+1 (555) 432-1098",
            "location": "Boston, MA",
            "current_role": "AI Research Engineer",
            "experience_years": 3.5,
            "education": "Ph.D. Artificial Intelligence, MIT",
            "summary": "NLP research scientist focused on transformer models, embeddings, and intelligent candidate matching engines.",
            "skills": json.dumps(["Python", "Machine Learning", "NLP", "Sentence Transformers", "Qdrant", "Deep Learning", "OpenAI"]),
            "status": "Offered",
            "resume_text": "Elena Rostova\nPh.D. in AI from MIT. Expert in Python, NLP, Machine Learning, Sentence Transformers, and Qdrant."
        },
        {
            "name": "David Miller",
            "email": "david.m@example.com",
            "phone": "+1 (555) 998-1122",
            "location": "Seattle, WA",
            "current_role": "Full Stack Engineer",
            "experience_years": 2.5,
            "education": "B.S. Computer Science, University of Washington",
            "summary": "Versatile developer experienced with Python, React, JavaScript, SQL, and Docker deployment pipelines.",
            "skills": json.dumps(["Python", "React", "JavaScript", "SQL", "Docker", "Git", "REST API"]),
            "status": "Applied",
            "resume_text": "David Miller\n2.5 years experience in Python, React, JavaScript, SQL, and Docker."
        }
    ]

    for c in candidates_data:
        db.add(Candidate(**c))
    db.commit()

    # Seed Applications & Notes
    jobs = db.query(Job).all()
    cands = db.query(Candidate).all()

    if jobs and cands:
        # Sarah -> Senior AI Backend Engineer
        db.add(Application(candidate_id=cands[0].id, job_id=jobs[0].id, stage="Interviewing", match_score=96.5))
        db.add(CandidateNote(candidate_id=cands[0].id, author="Head of Engineering", note="Superb technical background. Passed initial system design screen with flying colors."))
        
        # Marcus -> Lead Frontend Engineer
        db.add(Application(candidate_id=cands[1].id, job_id=jobs[1].id, stage="Screening", match_score=92.0))
        db.add(CandidateNote(candidate_id=cands[1].id, author="Lead Recruiter", note="Great portfolio site and clean UI component design sample."))

        # Elena -> ML Specialist
        db.add(Application(candidate_id=cands[2].id, job_id=jobs[2].id, stage="Offered", match_score=98.0))
        db.add(CandidateNote(candidate_id=cands[2].id, author="VP of AI", note="Outstanding academic and practical research background. Offer extended!"))

        db.commit()

    db.close()

if __name__ == "__main__":
    seed_db()
