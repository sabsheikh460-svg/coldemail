from crewai import Agent,Task,Crew,LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
import os

load_dotenv()


llm = LLM(model="gemini/gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"))


search_tool = SerperDevTool()

topic=input("Enter a topic you want to learn about: ")

researcher_agent = Agent(
    role = "researcher",
    goal = "gather accurate and relevant information on a given topic",
    backstory = "you are an expert researcher skilled at finding accurate and relevant information",
    llm = llm,
    tools = [search_tool]
)
researcher_task = Task(
    description = f'''conduct thorough research on the topic: {topic} using available tools''',
    expected_output = "a detailed report on including key facts, statistics, and insights",
    agent = researcher_agent
)
crew = Crew(
    agents=[researcher_agent],
    tasks= [researcher_task],
    verbose= True
)
result=crew.kickoff(inputs={"topic": topic})
print(result)

