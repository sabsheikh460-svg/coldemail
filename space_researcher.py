from crewai import Agent,Task,Crew,LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
import os

load_dotenv()


llm = LLM(model="groq/llama-3.1-8b-instant",
            api_key=os.getenv("GEMINI_API_KEY"))


search_tool = SerperDevTool()

topic=input("Enter a topic you want to learn about: ")

writer_agent = Agent(
    role = "space research writer",
    goal = "gather accurate and relevant information on space exploration and write a comprehensive article",
    backstory = "you are an expert space researcher and writer skilled at finding accurate and relevant information about space missions, discoveries, and technologies",
    llm = llm,
    tools = [search_tool]
)
writer_task = Task(
    description = f'''conduct thorough research on the topic: {topic} using available tools and write a comprehensive article''',
    expected_output = "a detailed article on space exploration including key facts, recent discoveries, and future missions",
    agent = writer_agent
)

editor_agent = Agent(
    role = "space research improver",
    goal = "review and enhance the article on space exploration for clarity, accuracy, and engagement",
    backstory = "you are an experienced editor with a keen eye for detail and a passion for space exploration",
    llm = llm
)
editor_task = Task(
    description = "review the article provided by the writer agent and suggest improvements for clarity, accuracy, and engagement",
    expected_output = "an improved version of the article with enhanced clarity, accuracy, and engagement",
    agent = editor_agent
)
enhancer_agent = Agent(
    role = "astorphysicist and space terminology expert",
    goal = "ensure the article uses accurate space terminology and concepts",
    backstory = "you are an astrophysicist with deep knowledge of space terminology and concepts",
    llm = llm

)

enhancer_task = Task(
    description = "review the article for accurate use of space terminology and concepts, making necessary corrections",
    expected_output = "a finalized article with accurate space terminology and concepts",
    agent = enhancer_agent
)

crew = Crew(
    agents=[writer_agent, editor_agent, enhancer_agent],
    tasks= [writer_task, editor_task, enhancer_task],
    verbose= True,
    memory=True 
)

result = crew.kickoff({"Topic": topic})

print(result)