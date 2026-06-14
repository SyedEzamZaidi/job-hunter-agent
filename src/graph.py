from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from state import JobApplicationState
from nodes import extract_requirements, score_fit, hitl_gate, writer
from datetime import datetime
from langgraph.types import Command
from interrupt import collect_answers

def route_after_gate(state: JobApplicationState):
    if state["status"] == "Approved":
        return "writer"
    else:
        return END
    

builder = StateGraph(JobApplicationState)
builder.add_node("extract", extract_requirements)
builder.add_node("verdict", score_fit)
builder.add_node("gate", hitl_gate)
#builder.add_node("writer",writer)
builder.add_edge(START,"extract")
builder.add_edge("extract","verdict")
builder.add_edge("verdict","gate")
#builder.add_conditional_edges("gate",route_after_gate)
graph = builder.compile(checkpointer= InMemorySaver())

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
      "pasted_jd": sample_jd,
      "location": "Ghaziabad, Uttar Pradesh, India",
      "skills": ["Automation Anywhere", "Power Platform", "Python (learning)", "RPA", "BI"],
      "years_experience": 7.0,
      "work_authorization": "Indian citizen; No other legal permits for any other country",
      "work_preference": "Remote",
      "willing_to_relocate": "No",
      "salary_expectation": 2500000,
      "salary_currency": "INR"},config= config)

# print(result["__interrupt__"][0].value)

if "__interrupt__" in result:
    fields = result["__interrupt__"][0].value
    clean = collect_answers(fields)            
    final = graph.invoke(Command(resume= clean), config= config)

else:
    final = result

print(final)
