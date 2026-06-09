from typing import TypedDict

class JobApplicationState(TypedDict):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin_url: str
    github_url: str
    current_title: str
    work_preference: str
    willing_to_relocate: str
    salary_expectation: int
    salary_currency: str
    work_authorization: str
    years_experience: float
    skills: list[str]
    company_name: str
    pasted_jd: str
    requirements: str
    fit_score: int
    eligible: str
    eligible_reason: str
    fit_reason: str

