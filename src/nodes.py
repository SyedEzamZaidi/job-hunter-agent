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
  Experince Summary: {state['experience_summary']}
  Skills: {state['skills']}
  Years of experience: {state['years_experience']}
  Work authorization: {state['work_authorization']}
  Work preference: {state['work_preference']}
  Willing to relocate: {state['willing_to_relocate']}
  Salary expectation: {state['salary_expectation']} {state['salary_currency']}

  INSTRUCTIONS
  - fit_score (0–100): rate ONLY how well the candidate's skills and experience match the role's
    requirements. Do NOT factor in eligibility, work authorization, visa, location, or salary —
    those must not change this number. This should always be an interger value and never string.
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

# def hitl_gate(state: JobApplicationState):
#     ask_human = interrupt(f"Do you approve? Fit Score = {state['fit_score']}, Eligibility = {state['eligible']}, Eligible Reason = {state['eligible_reason']} and Fit Reason = {state['fit_reason']}")
#     return {"status": ask_human["decision"] , "review_notes": ask_human["notes"]} 

def hitl_gate(state: JobApplicationState):
    payload = [{"name": "status","kind": "choice", "prompt": f"Fit Score = {state['fit_score']}\n Eligibility = {state['eligible']}\n Eligible Reason = {state['eligible_reason']}\n Fit Reason = {state['fit_reason']}\n"
                          "Do You Approve?","options": {"1":"Approved","2":"Rejected"}},{"name": "review_notes", "kind": "text", "prompt": "Please give the notes if needed", "required":False}]
    ask_human = interrupt(payload)
    
    return {"status": ask_human["status"], "review_notes": ask_human.get("review_notes")} 

class WriterContent(BaseModel):
    cv: str = Field(description="A complete, ATS-friendly CV tailored to this job, in plain text with "
                              "standard sections (Summary, Skills, Experience). Weave in keywords from "
                              "the job requirements; use ONLY the candidate's real information — invent nothing.")
    cover_letter: str = Field(description="A concise, tailored cover letter (3–4 short paragraphs) "
                                        "connecting the candidate's real experience to this job's "
                                        "requirements. Professional tone. No fabricated achievements.")

def writer(state: JobApplicationState):
    structured_llm = llm.with_structured_output(WriterContent, method="json_mode")
    request = f"""You are an expert career writer. Draft a tailored CV and a cover letter for this
  candidate applying to the job below.

  JOB
  Description: {state['pasted_jd']}
  Key requirements: {state['requirements']}

  CANDIDATE
  Name: {state['full_name']}
  Current title: {state['current_title']}
  Years of experience: {state['years_experience']}
  Skills: {state['skills']}
  Location: {state['location']}
  Contact: {state['email']} | {state['phone']} | {state['linkedin_url']} | {state['github_url']}

  REVIEWER FEEDBACK (apply this before anything else)
  Feedback: {state.get('critic_notes',"no feedback yet")}

  INSTRUCTIONS
  - If reviewer feedback is present above, treat addressing it as your TOP priority — revise the draft to resolve every point raised.
  - Tailor both documents to the job's requirements using ATS-friendly language and the requirement keywords.
  - Use ONLY the candidate's real experience and skills — do NOT fabricate employers, achievements, or qualifications.
  - CV: plain text, clear standard sections. Cover letter: concise, professional, 3–4 short paragraphs.
  - Use the candidate's REAL details from their experience above. Write out in full any section
    the resume actually supports (e.g. Education, Certifications, Projects). If the resume contains
    NO information for a section, OMIT that section entirely — never output placeholders, brackets,
    "[...]", "not specified", or "TBD", and never invent details to fill it.

  OUTPUT FORMAT
  Respond with ONLY a valid JSON object — no preamble, no markdown fences — with exactly these two keys:
  - "cv": a string containing the full CV text
  - "cover_letter": a string containing the full cover letter text
  """
    response = structured_llm.invoke(request)
    print(f"=============Writer Attempt: {state["wcloop_counter"]}=================")
    return {"cv": response.cv, "cover_letter": response.cover_letter, "wcloop_counter": state["wcloop_counter"] +1}


class CriticOutput(BaseModel):
    critic_score: int = Field(ge=0,le=10, description= "Overall quality of the draft (CV + cover letter) judged against the job's requirements, scored 0–10. A score of 7 or higher means it is ready to send.")
    critic_notes: str = Field(description="Specific, actionable revision feedback for the writer — exactly what to add, cut, or rephrase. Required on every pass, even when the score is high.")
    
def critic(state: JobApplicationState):
      structured_llm = llm.with_structured_output(CriticOutput, method="json_mode")
      request = f"""You are a strict senior hiring reviewer and ATS screener. Critically evaluate the
  candidate's CV and cover letter against the job below, and score how ready they are to send.

  JOB
  Description: {state['pasted_jd']}

  DRAFT TO REVIEW
  CV:
  {state['cv']}

  Cover letter:
  {state['cover_letter']}

  CANDIDATE'S REAL EXPERIENCE (ground truth — the ONLY facts that are true about this candidate)
  {state['experience_summary']}

  HOW TO SCORE (0-10)
  - How well the CV + cover letter match the job's requirements and use its keywords (ATS-friendly).
  - Clarity, structure, and professional tone.
  - Factual grounding: every claim must be supported by the candidate's real experience above.
  - Completeness: the draft should surface the candidate's MOST relevant real experience for THIS job.
    Flag important, relevant details from the candidate's real experience that the writer omitted,
    buried, or underplayed (e.g. a matching project, tool, or quantified achievement left out).
  - A 7 or higher means it is genuinely ready to send; below 7 means it still needs work.

  YOUR FEEDBACK (critic_notes — REQUIRED, even on a high score)
  - Be specific and actionable: name exactly what to add, cut, or rephrase, and where.
  - Flag any claim in the CV or cover letter NOT supported by the candidate's real experience above.
  - Call out relevant real experience that was omitted or underplayed and should be added.
  - Write the notes so the writer can act on them directly next revision — no vague praise.

  OUTPUT FORMAT
  Respond with ONLY a valid JSON object — no preamble, no markdown fences — with exactly these two keys:
  - "critic_score": an integer from 0 to 10
  - "critic_notes": a string with your actionable feedback
  """
      response = structured_llm.invoke(request)
      print(f"=============Critic score is {response.critic_score}=========================\n =====================Critic Notes are: {response.critic_notes}")
      return {"critic_score": response.critic_score, "critic_notes": response.critic_notes}


def hitl_gate_2(state: JobApplicationState):
    
    payload = [{"name": "cv_status","prompt": f"""The draft did NOT reach the quality bar (score >= 7) after {state['wcloop_counter']} revision attempts.
  A human decision is needed.

  Final critic score: {state['critic_score']}/10
  Critic's notes: {state['critic_notes']}

  --- CV ---
  {state['cv']}

  --- COVER LETTER ---
  {state['cover_letter']}

  Approve this draft for sending anyway, or reject it?""" , "kind": "choice", "options": {"1": "Approved", "2": "Rejected"}}]
    request = interrupt(payload)
    
    return {"cv_status": request["cv_status"]}






