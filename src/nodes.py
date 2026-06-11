from llm import llm 
from state import JobApplicationState 
from pydantic import BaseModel, Field
from typing import Literal
from langgraph.types import interrupt, Command

def extract_requirements(state: JobApplicationState):
    request = f"Here is a job description of a company : {state['pasted_jd']}. Please extract out the job requirements"
    llm_response = llm.invoke(request)
    
    return {"requirements": llm_response.content}


class FitAssessment(BaseModel):
    fit_score: int = Field(ge=0,le=100,description="ONLY How well the candidate's skills and experience match the requirements."
                      "0 = no overlap, 100 = ideal match.  Do NOT factor in eligibility, visa, location, or salary.")
    fit_reason: str = Field(
                     description="One or two sentences justifying the fit_score: which skills/experience matched "
                      "the requirements, and which gaps lowered it. Skills/experience ONLY — not eligibility.",
                     examples=["Strong RPA and automation background matches the core requirements, but Python and "
                    "LLM-framework experience are still developing, which lowers the score."]
      )
    eligible: Literal["Yes","No","Unclear"] = Field(description= "'Yes' = candidate clearly meets the posting's stated eligibility constraints; "
                      "'No' = the posting states a requirement the candidate clearly fails; "
                      "'Unclear' = the posting doesn't state enough to decide.")
    eligible_reason: str = Field(description="One or two sentences. If 'Unclear' because the posting is silent on a restriction, "
                      "say so neutrally (e.g. 'No visa/location restriction stated — verify manually');"
                      "do not imply it is a problem.", 
                      examples=[ "Skills and experience align well with the requirements — Yes.",
              "No work-authorization restriction stated; nothing here disqualifies you — verify manually.",
              "Posting requires on-site work in the US and the candidate needs sponsorship — No."])


def score_fit(state: JobApplicationState):
    request =  f"""You are an impartial career advisor helping a candidate decide whether to apply to a job.
  Assess the candidate in two SEPARATE ways — fit and eligibility — and do not let one affect the other.

  JOB
  Description: {state['pasted_jd']}
  Extracted requirements: {state['requirements']}

  CANDIDATE
  Location: {state['location']}
  Skills: {state['skills']}
  Years of experience: {state['years_experience']}
  Work authorization: {state['work_authorization']}
  Work preference: {state['work_preference']}
  Willing to relocate: {state['willing_to_relocate']}
  Salary expectation: {state['salary_expectation']} {state['salary_currency']}

  INSTRUCTIONS
  - fit_score (0–100): rate ONLY how well the candidate's skills and experience match the role's
    requirements. Do NOT factor in eligibility, work authorization, visa, location, or salary —
    those must not change this number.
   - fit_reason: in one or two sentences, explain the fit_score — name which skills/experience matched
    and which gaps lowered it. Skills/experience only; do not mention eligibility here.
  - eligible (Yes / No / Unclear): judge ONLY against restrictions the posting EXPLICITLY states.
      • "No"  — the posting states a hard requirement the candidate clearly fails
                (e.g. "must be an EU citizen" and the candidate is not).
      • "Yes" — the posting states a relevant requirement and the candidate clearly meets it.
      • "Unclear" — the posting does NOT state the relevant restriction. This is NEUTRAL, not negative:
                absence of a stated restriction must NOT count against the candidate. Treat it as
                "nothing in the posting disqualifies you — verify directly if needed."
  - NEVER fabricate. Do not assume a restriction (visa, location, etc.) the posting doesn't state.
    If it isn't in the posting, the answer is "Unclear", never "No".
  """
    
    structured_llm = llm.with_structured_output(FitAssessment)
    response = structured_llm.invoke(request)
    return {"fit_score": response.fit_score, "eligible": response.eligible, "eligible_reason": response.eligible_reason, "fit_reason": response.fit_reason}

def hitl_gate(state: JobApplicationState):
    ask_human = interrupt(f"Do you approve? Fit Score = {state['fit_score']}, Eligibility = {state['eligible']}, Eligible Reason = {state['eligible_reason']} and Fit Reason = {state['fit_reason']}")
    return {"status": ask_human["decision"] , "review_notes": ask_human["notes"]}





