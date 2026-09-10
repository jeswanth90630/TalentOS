from typing import List, Dict, Any

def compute_match_score(
    candidate_skills: List[str],
    job_required_skills: List[str],
    candidate_exp: float = 0.0,
    job_min_exp: float = 0.0
) -> Dict[str, Any]:
    """
    Computes candidate-job match score, identifying matching vs missing skills,
    experience alignment, and percentage breakdown.
    """
    cand_set = {s.lower().strip() for s in candidate_skills}
    job_set = {s.lower().strip() for s in job_required_skills}

    if not job_set:
        skill_match_ratio = 1.0
        matching = list(cand_set)
        missing = []
    else:
        matching_set = cand_set.intersection(job_set)
        missing_set = job_set.difference(cand_set)
        
        matching = [s for s in job_required_skills if s.lower().strip() in matching_set]
        missing = [s for s in job_required_skills if s.lower().strip() in missing_set]
        
        skill_match_ratio = len(matching) / len(job_set)

    # Experience fit calculation
    if candidate_exp >= job_min_exp:
        exp_score = 100.0
        exp_fit = True
    else:
        exp_score = max(50.0, (candidate_exp / max(1.0, job_min_exp)) * 100.0)
        exp_fit = False

    # Weighted final match percentage: 70% skills, 30% experience
    final_score = (skill_match_ratio * 70.0) + (exp_score * 0.30)
    final_score = round(min(max(final_score, 10.0), 99.0), 1)

    return {
        "match_percentage": final_score,
        "matching_skills": matching,
        "missing_skills": missing,
        "experience_fit": exp_fit,
        "score_breakdown": {
            "skill_match_score": round(skill_match_ratio * 100, 1),
            "experience_score": round(exp_score, 1)
        }
    }

def rank_candidates_for_job(candidates: List[Dict[str, Any]], job: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ranks a list of candidates for a given job by overall match percentage.
    """
    ranked = []
    required_skills = job.get("required_skills", [])
    min_exp = job.get("min_experience", 0)

    for cand in candidates:
        cand_skills = cand.get("skills", [])
        cand_exp = cand.get("experience_years", 0)
        
        match_info = compute_match_score(cand_skills, required_skills, cand_exp, min_exp)
        
        ranked.append({
            "candidate_id": cand.get("id"),
            "candidate_name": cand.get("name"),
            "current_role": cand.get("current_role"),
            "match_percentage": match_info["match_percentage"],
            "matching_skills": match_info["matching_skills"],
            "missing_skills": match_info["missing_skills"],
            "experience_fit": match_info["experience_fit"],
            "score_breakdown": match_info["score_breakdown"]
        })

    # Sort descending by match_percentage
    ranked.sort(key=lambda x: x["match_percentage"], reverse=True)
    return ranked
