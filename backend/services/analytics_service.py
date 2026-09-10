from sqlalchemy.orm import Session
from backend.models import Candidate, Job, Application

def get_dashboard_metrics(db: Session):
    total_candidates = db.query(Candidate).count()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.status == "Published").count()
    total_applications = db.query(Application).count()

    # Stage breakdown
    stages = ["Applied", "Screening", "Interviewing", "Offered", "Hired", "Rejected"]
    pipeline_counts = {}
    for stage in stages:
        count = db.query(Candidate).filter(Candidate.status == stage).count()
        pipeline_counts[stage] = count

    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "pipeline_counts": pipeline_counts,
        "ai_matches_performed": total_candidates * active_jobs
    }
