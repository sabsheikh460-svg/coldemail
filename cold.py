import os
import json
import streamlit as st
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="Cold Email Agent", page_icon="📧", layout="wide")

st.title("📧 AI Cold Email Generator")
st.markdown("Generate personalized cold emails using Gemini AI")

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    model = st.selectbox("Model", ["gemini-2.5-flash", "gemini-1.5-flash"])
    
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

# Validate API key
if not api_key:
    st.error("⚠️ Please enter your Gemini API Key in the sidebar")
    st.stop()

# Gemini API call function
def call_gemini(prompt, api_key, model):
    """Call Gemini API directly"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
    }
    
    response = requests.post(url, headers=headers, params=params, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# Generate cold email
if st.button("🚀 Generate Cold Email", type="primary", disabled=not target_url):
    if not target_url.startswith("http"):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("🤖 AI is analyzing and writing..."):
            try:
                # Step 1: Research
                research_prompt = f"""You are a Business Intelligence Analyst. Analyze the company at {target_url}.
                
                1. What does this company do?
                2. Who do they serve?
                3. Identify ONE major operational or marketing weakness (conversion, automation, or performance).
                
                Provide a concise summary."""
                
                research_result = call_gemini(research_prompt, api_key, model)
                
                # Step 2: Strategy
                strategy_prompt = f"""You are an Agency Strategist. Based on this company analysis:
                
                {research_result}
                
                Available Services:
                {agency_services}
                
                Choose ONLY ONE service that best solves their weakness. Explain why it's the best fit."""
                
                strategy_result = call_gemini(strategy_prompt, api_key, model)
                
                # Step 3: Write Email
                recipient = recipient_name if recipient_name else "the CEO"
                writer_prompt = f"""You are a Senior Sales Copywriter. Write a personalized cold email to {recipient}.
                
                Company Analysis: {research_result}
                Selected Service: {strategy_result}
                
                Write a concise, professional cold email that:
                - References specific details from the analysis
                - Pitches the selected service
                - Includes a clear call-to-action
                - Keep it under 150 words
                - Subject line included"""
                
                email_result = call_gemini(writer_prompt, api_key, model)
                
                # Display result
                st.success("✅ Cold email generated successfully!")
                st.header("📨 Your Cold Email")
                st.text_area("Copy this email:", value=email_result, height=300)
                st.code(email_result, language="text")
                
                # Store for later use
                st.session_state['generated_email'] = email_result
                st.session_state['company_url'] = target_url
                st.session_state['research'] = research_result
                st.session_state['strategy'] = strategy_result
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
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
                reply_prompt = f"""You are an expert at handling email responses.
                
                Original email we sent:
                {st.session_state['generated_email']}
                
                Prospect's reply:
                {prospect_reply}
                
                Generate a professional, contextually appropriate response that:
                - Addresses their concerns
                - Handles objections
                - Moves toward a meeting or next step
                - Keep it under 150 words"""
                
                reply_result = call_gemini(reply_prompt, api_key, model)
                
                st.success("✅ Reply generated!")
                st.subheader("📨 Your Response:")
                st.text_area("Copy this reply:", value=reply_result, height=250)
                st.code(reply_result, language="text")
                
                # Store conversation
                st.session_state['conversation'] = {
                    'original_email': st.session_state['generated_email'],
                    'prospect_reply': prospect_reply,
                    'our_reply': reply_result
                }
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Workflow Manager Section
st.header("📋 Workflow Manager")
st.markdown("Get recommendations for next steps based on the conversation")

if st.button("📊 Get Next Steps Recommendation", disabled=('conversation' not in st.session_state and 'generated_email' not in st.session_state)):
    with st.spinner("🤖 Analyzing and recommending next steps..."):
        try:
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
            
            workflow_prompt = f"""You are a strategic Sales Workflow Manager.
            
            Company URL: {st.session_state.get('company_url', 'N/A')}
            
            Conversation History:
            {conversation_history}
            
            Based on this sales interaction, provide:
            1. Current deal stage assessment
            2. Recommended next action (with specific timing)
            3. Suggested follow-up content or resources
            4. Risk factors to watch for
            5. Escalation recommendations if needed"""
            
            workflow_result = call_gemini(workflow_prompt, api_key, model)
            
            st.success("✅ Workflow recommendation generated!")
            st.subheader("📋 Next Steps:")
            st.markdown(workflow_result)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Instructions
with st.expander("📖 How to use"):
    st.markdown("""
    1. **Enter your Gemini API Key** in the sidebar
    2. **Enter the target company URL** (e.g., https://openai.com)
    3. **Optionally enter recipient name** (e.g., "CEO" or "John Smith")
    4. **Click "Generate Cold Email"** to create the initial email
    5. **When you get a reply**, paste it in "Auto-Reply Handler" and generate a response
    6. **Use "Workflow Manager"** to get recommendations on next steps anytime
    """)
