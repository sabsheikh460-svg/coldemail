from crewai import Agent,Task,Crew,LLM
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")

)


game_designer = Agent(
    role = "game designer",
    goal = "create engaging and fun game concepts",
    backstory = "you are a creative game designer with a knack for developing innovative game ideas",
    llm = llm

)

game_designer_task = Task(
    description = "design a unique and captivating game concept that will attract players",
    
    expected_output = "a detailed game concept including gameplay mechanics, storyline, and target audience",
    agent = game_designer


)

judge_agent = Agent(
    role = "game critic",
    goal = "evaluate game concepts based on creativity and feasibility",
    backstory = "you are a seasoned game critic known for your insightful reviews and evaluations",
    llm = llm

)

judge_task = Task(
    description = "evaluate the game concept from the game designer and provide constructive feedback",
    expected_output = "a comprehensive evaluation of the game concept, highlighting its strengths and potential improvements",
    agent = judge_agent


)

game_improver = Agent(
    role = "game improver",
    goal = "enhance game concepts based on feedback",
    backstory = "you are an experienced game developer skilled at refining and improving game ideas",
    llm = llm

)

game_improver_task = Task(
    description = "improve the game concept based on the feedback from the game critic",
    expected_output = "an enhanced game concept that addresses the critic's feedback and suggestions",
    agent = game_improver


)

crew = Crew(
    agents=[game_designer, judge_agent, game_improver],
    tasks= [game_designer_task, judge_task, game_improver_task],
    verbose= True
)

result=crew.kickoff()
print(result)

