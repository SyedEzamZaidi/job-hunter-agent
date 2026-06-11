from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from state import JobApplicationState
from nodes import extract_requirements, score_fit, hitl_gate
from datetime import datetime
from langgraph.types import Command

builder = StateGraph(JobApplicationState)
builder.add_node("extract", extract_requirements)
builder.add_node("verdict", score_fit)
builder.add_node("gate", hitl_gate)
builder.add_edge(START,"extract")
builder.add_edge("extract","verdict")
builder.add_edge("verdict","gate")
builder.add_edge("gate",END)
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

#print(result)

final = graph.invoke(Command(resume={"decision": "Approved", "notes": "looks Good"}), config= config)

print(final)