  import os
  import uuid
  from fastapi import FastAPI
  from pydantic import BaseModel
  from psycopg_pool import ConnectionPool
  from langgraph.checkpoint.postgres import PostgresSaver
  from langgraph.types import Command
  from dotenv import load_dotenv

  from graph import builder

  # ===== ONE-TIME SETUP (runs once when the server loads this file) =====
  load_dotenv()
  DB_URI = os.getenv("DATABASE_URL")

  pool = ConnectionPool(DB_URI, max_size=10, kwargs={"autocommit": True})
  checkpointer = PostgresSaver(pool)
  checkpointer.setup()
  graph = builder.compile(checkpointer=checkpointer)   # compiled ONCE, reused by every request

  # read the résumé once (path relative to THIS file, so it works no matter where you run from)
  RESUME_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "resume.md")
  with open(RESUME_PATH, "r", encoding="utf-8") as f:
      EXPERIENCE_SUMMARY = f.read()

  app = FastAPI()

  SAMPLE_JD = """AI Automation Engineer — Remote (EU). Acme Remote GmbH.
  Build LLM workflows with LangGraph/LangChain, integrate via REST APIs, add human-in-the-loop
  approvals. Requirements: 3+ yrs automation/RPA/backend, strong Python, an LLM/agent framework,
  API integration + basic SQL/PostgreSQL."""

  def fresh_intake():
      return {
          "full_name": "Syed Ezam Zaidi", "email": "syedezamzaidi@gmail.com",
          "phone": "+91-9876543210", "location": "Ghaziabad, Uttar Pradesh, India",
          "linkedin_url": "https://linkedin.com/in/syed-ezam-zaidi",
          "github_url": "https://github.com/SyedEzamZaidi",
          "current_title": "RPA & Automation Architect", "years_experience": 8.0,
          "skills": ["Automation Anywhere", "Power Platform", "Python", "RPA", "BI"],
          "work_authorization": "Indian citizen; no other work permits",
          "work_preference": "Remote", "willing_to_relocate": "No",
          "salary_expectation": 4200000, "salary_currency": "INR",
          "company_name": "Acme Remote GmbH", "pasted_jd": SAMPLE_JD,
          "experience_summary": EXPERIENCE_SUMMARY, "status": "Pending", "wcloop_counter": 0,
      }

  class ResumeBody(BaseModel):
      answers: dict   # e.g. {"status": "Approved", "review_notes": "looks good"}

  def shape(thread_id, result):
      if "__interrupt__" in result:
          return {"thread_id": thread_id, "status": "paused",
                  "pending_question": result["__interrupt__"][0].value}
      return {"thread_id": thread_id, "status": "finished", "result": result}

  # ===== ENDPOINTS =====
  @app.get("/")
  def health():
      return {"message": "Job hunter API is alive"}

  @app.post("/runs")                                   # START a job
  def start_run():
      thread_id = str(uuid.uuid4())
      config = {"configurable": {"thread_id": thread_id}}
      result = graph.invoke(fresh_intake(), config=config)
      return shape(thread_id, result)

  @app.post("/runs/{thread_id}/resume")                # RESUME with the human's answer
  def resume_run(thread_id: str, body: ResumeBody):
      config = {"configurable": {"thread_id": thread_id}}
      result = graph.invoke(Command(resume=body.answers), config=config)
      return shape(thread_id, result)

  @app.get("/runs/{thread_id}")                        # CHECK status
  def get_status(thread_id: str):
      config = {"configurable": {"thread_id": thread_id}}
      snap = graph.get_state(config)
      return {"thread_id": thread_id, "next": snap.next, "values": snap.values}