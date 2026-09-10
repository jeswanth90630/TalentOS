from sqlalchemy.orm import Session
from backend.services.candidate_service import get_candidates, get_candidate_by_id
from backend.services.job_service import get_jobs, get_job_by_id
from ai.matcher import compute_match_score, rank_candidates_for_job

def get_job_candidate_rankings(db: Session, job_id: int):
    job = get_job_by_id(db, job_id)
    if not job:
        return []
    
    candidates = get_candidates(db)
    return rank_candidates_for_job(candidates, job)

def get_recommendations_for_candidate(db: Session, candidate_id: int):
    cand = get_candidate_by_id(db, candidate_id)
    if not cand:
        return []
    
    jobs = get_jobs(db, status="Published")
    recommendations = []
    
    cand_skills = cand.get("skills", [])
    cand_exp = cand.get("experience_years", 0)

    for j in jobs:
        req_skills = j.get("required_skills", [])
        min_exp = j.get("min_experience", 0)
        
        match_info = compute_match_score(cand_skills, req_skills, cand_exp, min_exp)
        
        recommendations.append({
            "job_id": j["id"],
            "job_title": j["title"],
            "department": j["department"],
            "location": j["location"],
            "match_percentage": match_info["match_percentage"],
            "matching_skills": match_info["matching_skills"],
            "missing_skills": match_info["missing_skills"]
        })
        
    recommendations.sort(key=lambda x: x["match_percentage"], reverse=True)
    return recommendations

def analyze_skill_gap(db: Session, candidate_id: int, job_id: int):
    cand = get_candidate_by_id(db, candidate_id)
    job = get_job_by_id(db, job_id)
    
    if not cand or not job:
        return None
        
    match_info = compute_match_score(
        cand.get("skills", []),
        job.get("required_skills", []),
        cand.get("experience_years", 0),
        job.get("min_experience", 0)
    )
    
    missing = match_info["missing_skills"]
    if not missing:
        recommendation_msg = "Outstanding fit! Candidate meets all required technical criteria for this position."
    elif len(missing) <= 2:
        recommendation_msg = f"Strong potential fit. Consider targeted upskilling in: {', '.join(missing)}."
    else:
        recommendation_msg = f"Moderate fit. Additional training recommended in: {', '.join(missing[:3])}."

    return {
        "candidate_id": cand["id"],
        "job_id": job["id"],
        "candidate_name": cand["name"],
        "job_title": job["title"],
        "candidate_skills": cand.get("skills", []),
        "required_skills": job.get("required_skills", []),
        "matching_skills": match_info["matching_skills"],
        "missing_skills": match_info["missing_skills"],
        "fit_score": match_info["match_percentage"],
        "recommendation": recommendation_msg
    }
