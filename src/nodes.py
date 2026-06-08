from llm import llm 
from state import JobApplicationState 

def extract_requirements(state: JobApplicationState):
    request = f"Here is a job description of a company : {state['pasted_jd']}. Please extract out the job requirements"
    llm_response = llm.invoke(request)
    
    return {"requirements": llm_response.content}






