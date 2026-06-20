from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from state import JobApplicationState
from nodes import extract_requirements, score_fit, hitl_gate, writer, critic, hitl_gate_2
from datetime import datetime
from langgraph.types import Command
from interrupt import collect_answers

import os
from dotenv import load_dotenv
load_dotenv()
DB_URI = os.getenv("DATABASE_URL")

def route_after_gate(state: JobApplicationState):
    if state["status"] == "Approved":
        return "writer"
    else:
        return END
    
def route_after_critic(state: JobApplicationState):
    if state["critic_score"] >=7:
       return END
    elif state["wcloop_counter"] < 5:
        return "writer"
    else:
        return "gate_2"
        
            
    
    

builder = StateGraph(JobApplicationState)
builder.add_node("extract", extract_requirements)
builder.add_node("verdict", score_fit)
builder.add_node("gate", hitl_gate)
builder.add_node("writer",writer)
builder.add_node("critic",critic)
builder.add_node("gate_2",hitl_gate_2)
builder.add_edge(START,"extract")
builder.add_edge("extract","verdict")
builder.add_edge("verdict","gate")
builder.add_conditional_edges("gate",route_after_gate)
builder.add_edge("writer","critic")
builder.add_conditional_edges("critic",route_after_critic)


sample_jd = """
  AI Automation Engineer — Remote (EU time zones)
  Acme Remote GmbH

  About the role:
  We're hiring an AI Automation Engineer to design and ship LLM-powered workflows that
  automate internal business processes. You'll build multi-step agentic pipelines, integrate
  them with our existing tools via APIs, and own them from prototype to production.

  Responsibilities:
  - Design and build LLM workflows using frameworks like LangGraph or LangChain
  - Integrate workflows with internal systems through REST APIs
  - Add human-in-the-loop approval steps for sensitive actions
  - Monitor, evaluate, and improve prompt quality and output reliability

  Requirements:
  - 3+ years in software automation, RPA, or backend engineering
  - Strong Python; comfortable building and debugging from scratch
  - Experience with at least one LLM/agent framework (LangGraph, LangChain, or similar)
  - Familiarity with API integration and basic SQL/PostgreSQL
  - Clear written communication; able to work independently in a remote team

  Nice to have:
  - Background in RPA tools (UiPath, Automation Anywhere, Power Automate)
  - Experience with prompt engineering and evaluation
  - Exposure to cloud deployment

  We offer a fully remote role, flexible hours, and a learning budget.
  """

thread_id = datetime.now().strftime("Job_%d_%m_%Y__%H_%M_%S")

config = {"configurable": {"thread_id": thread_id}}

with open("data/resume.md", "r", encoding="utf-8") as f:
      experience_summary = f.read()

# full_name = input("What's your full name?\n")
# email = input("Your email?\n")
# phone = input("Your phone number?\n")
# location = input("Your location?\n")
# linkedin_url = input("Your LinkedIn URL?\n")
# github_url = input("Your GitHub URL?\n")
# current_title = input("Your current job title?\n")
# years_experience = float(input("Years of experience (e.g. 7 or 7.5)?\n"))   # float()
# skills = input("Your skills, comma-separated (e.g. RPA,Python,BI)?\n").split(",")  # → list
# work_authorization = input("Your work authorization?\n")
# work_preference = input("Work preference (Remote/Hybrid/Onsite)?\n")
# willing_to_relocate = input("Willing to relocate? (Yes/No)\n")
# salary_expectation = int(input("Salary expectation (number only)?\n"))       # int()
# salary_currency = input("Salary currency (e.g. INR)?\n")
# company_name = input("Company name (from the JD)?\n")
# pasted_jd = input("Paste the full job description:\n")


with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer= checkpointer)
    # result = graph.invoke({
    #       "full_name": full_name,
    #       "email": email,
    #       "phone": phone,
    #       "location": location,
    #       "linkedin_url": linkedin_url,
    #       "github_url": github_url,
    #       "current_title": current_title,
    #       "years_experience": years_experience,
    #       "skills": skills,
    #       "work_authorization": work_authorization,
    #       "work_preference": work_preference,
    #       "willing_to_relocate": willing_to_relocate,
    #       "salary_expectation": salary_expectation,
    #       "salary_currency": salary_currency,
    #       "company_name": company_name,
    #       "pasted_jd": pasted_jd,
    #       "status": "Pending",
    #      }, config=config)



    result = graph.invoke({
            "full_name": "Syed Ezam Zaidi",
            "email": "syedezamzaidi@gmail.com",
            "phone": "+91-9876543210",
            "location": "Ghaziabad, Uttar Pradesh, India",
            "linkedin_url": "https://linkedin.com/in/syed-ezam-zaidi",
            "github_url": "https://github.com/SyedEzamZaidi",
            "current_title": "RPA & Automation Architect",
            "years_experience": 7.0,
            "skills": ["Automation Anywhere", "Power Platform", "Python", "RPA", "BI"],
            "work_authorization": "Indian citizen; No other legal permits for any other country",
            "work_preference": "Remote",
            "willing_to_relocate": "No",
            "salary_expectation": 4200000,
            "salary_currency": "INR",
            "company_name": "Acme Remote GmbH",
            "pasted_jd": sample_jd,
            "status": "Pending",
            "experience_summary": experience_summary,
            "wcloop_counter": 0
        }, config=config)

    # print(result["__interrupt__"][0].value)

    while "__interrupt__" in result:
        fields = result["__interrupt__"][0].value
        clean = collect_answers(fields)            
        result = graph.invoke(Command(resume= clean), config= config)
    
    final= result



print(final["cv"])


import psycopg

with psycopg.connect(DB_URI) as conn:
      with conn.cursor() as cur:
          cur.execute(
              """INSERT INTO applications
                 (thread_id, company, fit_score, fit_reason, eligible, eligible_reason,
                  status, review_notes, cv, cover_letter, critic_score, critic_notes,
                  iterations, cv_status)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
              (
                  thread_id,                      # from the variable, not final
                  final["company_name"],          # column 'company'
                  final["fit_score"],
                  final["fit_reason"],
                  final["eligible"],
                  final["eligible_reason"],
                  final["status"],
                  final["review_notes"],
                  final.get("cv"),                # .get() → None → NULL on a rejected run
                  final.get("cover_letter"),
                  final.get("critic_score"),
                  final.get("critic_notes"),
                  final.get("wcloop_counter"),    # column 'iterations'
                  final.get("cv_status"),
              )
          )