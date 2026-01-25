from crewai import Agent, Task, Crew, LLM
from crewai.memory.storage.rag_storage import RAGStorage
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os


memory_storage = RAGStorage(type='chromadb')

question = input("ASK A QUESTION TO YOUR AI TEAM: ")

llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

friend = Agent(
    role="AI Best Friend",
    goal="Be friendly and remember user conversations to answer naturally that user ask in {topic}.",
    backstory="A loyal and chatty AI friend.",
    llm=llm
)

researcher = Agent(
    role="Researcher",
    goal="Provide accurate information when the question requires facts.",
    backstory="A smart AI who loves digging up information.",
    llm=llm
)

editor = Agent(
    role="Editor",
    goal="Polish the final answer in 2-3 lines after others provide input.",
    backstory="An expert editor who loves brevity and clarity.",
    llm=llm
)


remember_task = Task(
    description="Remember everything about the user for future conversation.",
    expected_output="Accurate memory storage of user info.",
    agent=friend
)

research_task = Task(
    description="Research any required facts or data for the answer.",
    expected_output="Factually accurate info.",
    agent=researcher
)

shorten_task = Task(
    description="Polish and shorten the final answer to 2-3 lines.",
    expected_output="Concise, clear, final answer.",
    agent=editor
)


crew = Crew(
    agents=[friend, researcher, editor], 
    tasks=[remember_task, research_task, shorten_task],  
    verbose=True,
    memory=True,
    memory_storage=memory_storage,
    embedder={
        "provider": "sentence-transformer",
        "config": {"model_name": "all-MiniLM-L6-v2"}
    }
)


result = crew.kickoff(inputs={"topic": question})
print("\n===== AI TEAM ANSWER =====")
print(result)