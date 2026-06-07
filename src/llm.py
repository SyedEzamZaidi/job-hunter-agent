from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model = "llama-3.3-70b-versatile", temperature= 0.2)

user_message = "Hi Llama ! How are you ? I just want to test if this shit is working or not"

response = llm.invoke(user_message)

print(response.content)