import os
import time
import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import ScrapeWebsiteTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="Cold Email Agent", page_icon="📧", layout="wide")

st.title("📧 AI Cold Email Generator")
st.markdown("Generate personalized cold emails by analyzing company websites")

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    model = st.selectbox("Model", ["gemini/gemini-2.5-flash", "gemini/gemini-1.5-flash"])
    
    st.header("🎯 Agency Services")
    agency_services = st.text_area(
        "Services",
        value="""1. Landing Page Optimization: Improve conversions without rebuilding the entire site.
2. CRM Setup & Automation: Automate sales pipelines using HubSpot, Zoho, or custom AI.
3. Website Speed & Core Web Vitals Optimization: Fix slow sites that lose Google rankings.""",
        height=150
    )

# Main input form
st.header("🎯 Target Company")
col1, col2 = st.columns(2)
with col1:
    target_url = st.text_input("Company Website URL", placeholder="https://example.com")
with col2:
    recipient_name = st.text_input("Recipient Name (optional)", placeholder="CEO")

# Initialize LLM
if not api_key:
    st.error("⚠️ Please enter your Gemini API Key in the sidebar or set GEMINI_API_KEY environment variable")
    st.stop()

llm = LLM(model=model, api_key=api_key)

# Create agents
def create_agents(services_text):
    scrape_tool = ScrapeWebsiteTool()
    
    researcher = Agent(
        role="Business Intelligence Analyst",
        goal="Analyze the target company's website to understand their business and identify weaknesses.",
        backstory=(
            "You are an expert at analyzing company websites. "
            "You identify what the company does, who they serve, "
            "and ONE clear operational or marketing weakness."
        ),
        tools=[scrape_tool],
        llm=llm,
        memory=True
    )
    
    strategist = Agent(
        role="Agency Strategist",
        goal="Select the SINGLE most relevant agency service for the client.",
        backstory=f"""You are a senior strategist at a digital agency.

AGENCY SERVICES:
{services_text}

Rules:
- Choose ONLY ONE service.
- The service must directly solve the client's biggest weakness.
- Clearly explain WHY this service is the best fit.""",
        llm=llm,
        memory=True
    )
    
    writer = Agent(
        role="Senior Sales Copywriter",
        goal="Write a short, personalized cold email that gets replies.",
        backstory=(
            "You write high-converting cold emails that sound human. "
            "You reference specific insights from the research to prove relevance. "
            "You are concise, confident, and professional."
        ),
        llm=llm,
    )
    
    auto_reply_agent = Agent(
        role="Auto-Reply Handler",
        goal="Generate appropriate responses to common email replies automatically.",
        backstory=(
            "You are an expert at handling email responses. "
            "You analyze the tone and intent of incoming replies and generate "
            "professional, contextually appropriate responses. You handle objections, "
            "schedule meetings, answer questions, and keep conversations moving forward."
        ),
        llm=llm,
        memory=True
    )
    
    workflow_manager = Agent(
        role="Sales Workflow Manager",
        goal="Manage the sales pipeline and recommend next steps after each interaction.",
        backstory=(
            "You are a strategic sales workflow manager. After each client interaction, "
            "you analyze the conversation history and recommend the optimal next steps. "
            "You suggest when to follow up, what content to send, when to schedule calls, "
            "or when to escalate to senior team members. You track deal progression."
        ),
        llm=llm,
        memory=True
    )
    
    return researcher, strategist, writer, auto_reply_agent, workflow_manager

# Generate button
if st.button("🚀 Generate Cold Email", type="primary", disabled=not target_url):
    if not target_url.startswith("http"):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("🤖 AI Agents are analyzing and writing..."):
            try:
                researcher, strategist, writer = create_agents(agency_services)
                
                # Create tasks
                task_analyze = Task(
                    description=(
                        f"Scrape and analyze the website {target_url}. "
                        "Summarize what the company does and identify ONE major weakness "
                        "(conversion, automation, or performance)."
                    ),
                    expected_output="A short company summary and one clear business weakness.",
                    agent=researcher
                )
                
                task_strategize = Task(
                    description=(
                        "Using the research findings, choose ONE agency service "
                        "that best solves the client's problem. Justify the choice."
                    ),
                    expected_output="Selected service name + explanation of why it fits.",
                    agent=strategist
                )
                
                recipient = recipient_name if recipient_name else "the CEO"
                task_write = Task(
                    description=(
                        f"Write a personalized cold email to {recipient} at the company. "
                        "Pitch the selected service. "
                        "Mention specific details from the website analysis. "
                        "Keep it under 150 words."
                    ),
                    expected_output="A ready-to-send cold email.",
                    agent=writer
                )
                
                # Create and run crew
                sales_crew = Crew(
                    agents=[researcher, strategist, writer],
                    tasks=[task_analyze, task_strategize, task_write],
                    process=Process.sequential,
                )
                
                result = sales_crew.kickoff()
                
                # Display result
                st.success("✅ Cold email generated successfully!")
                st.header("📨 Your Cold Email")
                st.text_area("Copy this email:", value=str(result), height=300)
                st.code(str(result), language="text")
                
                # Store result in session state for reply handling
                st.session_state['generated_email'] = str(result)
                st.session_state['company_url'] = target_url
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    st.error("⏱️ Rate limit exceeded. Please wait a minute and try again.")
                elif "quota" in error_msg.lower():
                    st.error("💳 API quota exceeded. Check your billing at https://ai.google.dev/")
                else:
                    st.error(f"❌ Error: {error_msg}")

# Auto-Reply Handler Section
st.header("💬 Auto-Reply Handler")
st.markdown("Paste the prospect's reply to generate an appropriate response")

prospect_reply = st.text_area("Prospect's Reply:", placeholder="Paste the email reply you received here...", height=150)

if st.button("🤖 Generate Auto-Reply", disabled=not prospect_reply):
    if 'generated_email' not in st.session_state:
        st.error("Please generate a cold email first!")
    else:
        with st.spinner("🤖 AI is crafting a response..."):
            try:
                _, _, _, auto_reply_agent, _ = create_agents(agency_services)
                
                task_reply = Task(
                    description=(
                        f"Original email sent: {st.session_state['generated_email']}\n\n"
                        f"Prospect's reply: {prospect_reply}\n\n"
                        "Generate a professional, contextually appropriate response. "
                        "Address their concerns, answer questions, handle objections, "
                        "and move the conversation toward a meeting or next step. "
                        "Keep it under 150 words."
                    ),
                    expected_output="A professional email response.",
                    agent=auto_reply_agent
                )
                
                reply_crew = Crew(
                    agents=[auto_reply_agent],
                    tasks=[task_reply],
                    process=Process.sequential,
                )
                
                reply_result = reply_crew.kickoff()
                
                st.success("✅ Reply generated!")
                st.subheader("📨 Your Response:")
                st.text_area("Copy this reply:", value=str(reply_result), height=250)
                st.code(str(reply_result), language="text")
                
                # Store conversation for workflow manager
                st.session_state['conversation'] = {
                    'original_email': st.session_state['generated_email'],
                    'prospect_reply': prospect_reply,
                    'our_reply': str(reply_result)
                }
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Workflow Manager Section
st.header("📋 Workflow Manager")
st.markdown("Get recommendations for next steps based on the conversation")

if st.button("📊 Get Next Steps Recommendation", disabled=('conversation' not in st.session_state and 'generated_email' not in st.session_state)):
    with st.spinner("🤖 Analyzing conversation and recommending next steps..."):
        try:
            _, _, _, _, workflow_manager = create_agents(agency_services)
            
            conversation_history = ""
            if 'conversation' in st.session_state:
                conv = st.session_state['conversation']
                conversation_history = f"""
Original Email: {conv['original_email']}

Prospect Reply: {conv['prospect_reply']}

Our Response: {conv['our_reply']}
"""
            else:
                conversation_history = f"Original Email (no reply yet): {st.session_state['generated_email']}"
            
            task_workflow = Task(
                description=(
                    f"Company URL: {st.session_state.get('company_url', 'N/A')}\n\n"
                    f"Conversation History:\n{conversation_history}\n\n"
                    "Based on this sales interaction, provide:\n"
                    "1. Current deal stage assessment\n"
                    "2. Recommended next action (with specific timing)\n"
                    "3. Suggested follow-up content or resources\n"
                    "4. Risk factors to watch for\n"
                    "5. Escalation recommendations if needed"
                ),
                expected_output="A detailed workflow recommendation report.",
                agent=workflow_manager
            )
            
            workflow_crew = Crew(
                agents=[workflow_manager],
                tasks=[task_workflow],
                process=Process.sequential,
            )
            
            workflow_result = workflow_crew.kickoff()
            
            st.success("✅ Workflow recommendation generated!")
            st.subheader("📋 Next Steps:")
            st.markdown(str(workflow_result))
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Instructions
with st.expander("📖 How to use"):
    st.markdown("""
    1. **Enter your Gemini API Key** in the sidebar (or set GEMINI_API_KEY env variable)
    2. **Enter the target company URL** (e.g., https://openai.com)
    3. **Optionally enter recipient name** (e.g., "CEO" or "John Smith")
    4. **Click "Generate Cold Email"** to create the initial email
    5. **When you get a reply**, paste it in "Auto-Reply Handler" and generate a response
    6. **Use "Workflow Manager"** to get recommendations on next steps anytime
    """)
