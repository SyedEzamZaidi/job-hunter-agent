# job-hunter-agent

LangGraph agent that screens a job posting, scores fit against my resume, and drafts a tailored CV and cover letter. Human approval gates so it doesn't spend tokens on jobs I don't want to pursue.

## What it does
- extracts the requirements from a job posting (LLM, structured output)
- scores fit and eligibility against my actual resume
- approval gate: I decide whether to pursue the job before anything gets drafted
- writer/critic loop: writer drafts, critic scores it 0-10 against the job + resume, loops back with feedback, hard cap on iterations then escalates to me
- critic checks each claim against my resume so it doesn't invent experience
- second approval gate on the final draft
- saves each run to Postgres, and uses a Postgres checkpointer so a run can pause and resume later

## Stack
Python, LangGraph, LangChain, Groq (Llama 3.3 70B), Pydantic, PostgreSQL (psycopg)

## Status
Working. Still tuning the scoring and prompts.

## Run
pip install -r requirements.txt
python main.py
