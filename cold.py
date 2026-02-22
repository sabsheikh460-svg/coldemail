import os
import json
import smtplib
import streamlit as st
import requests
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Page config - MUST be first Streamlit command
st.set_page_config(page_title="Cold Email Agent", page_icon="📧", layout="wide")

# Initialize session state with defaults
def init_session_state():
    defaults = {
        'smtp_config': {
            'server': os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            'port': int(os.getenv("SMTP_PORT", "587")),
            'email': os.getenv("SMTP_EMAIL", ""),
            'password': os.getenv("SMTP_PASSWORD", "")
        },
        'generated_email': '',
        'company_url': '',
        'sent_emails': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

st.title("📧 AI Cold Email Generator")
st.markdown("Generate and send personalized cold emails using Gemini AI")

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ Gemini API Configuration")
    api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    model = st.selectbox("Model", ["gemini-2.5-flash", "gemini-1.5-flash"])
    
    st.header("📧 Email Configuration (SMTP)")
    st.markdown("For sending emails directly")
    
    # SMTP inputs that save to session state
    smtp_server_input = st.text_input("SMTP Server", value=st.session_state['smtp_config']['server'], help="For Gmail: smtp.gmail.com")
    smtp_port_input = st.number_input("SMTP Port", value=st.session_state['smtp_config']['port'], help="For Gmail: 587")
    smtp_email_input = st.text_input("Your Email", value=st.session_state['smtp_config']['email'], type="password")
    smtp_password_input = st.text_input("Your Email Password/App Password", value=st.session_state['smtp_config']['password'], type="password", help="For Gmail: Use App Password, not your regular password!")
    
    # Save to session state when changed
    st.session_state['smtp_config']['server'] = smtp_server_input
    st.session_state['smtp_config']['port'] = int(smtp_port_input)
    st.session_state['smtp_config']['email'] = smtp_email_input
    st.session_state['smtp_config']['password'] = smtp_password_input
    
    # Test SMTP Connection
    if st.button("🧪 Test SMTP Connection"):
        if smtp_email_input and smtp_password_input:
            with st.spinner("Testing connection..."):
                try:
                    import smtplib
                    server = smtplib.SMTP(smtp_server_input, int(smtp_port_input), timeout=10)
                    server.starttls()
                    server.login(smtp_email_input, smtp_password_input)
                    server.quit()
                    st.success("✅ SMTP connection successful!")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
        else:
            st.warning("⚠️ Enter email and password first")
    
    st.header("🎯 Your Agency Services")
    agency_services = st.text_area(
        "List your services (one per line)",
        value="""Landing Page Optimization: Improve conversions without rebuilding the entire site.
CRM Setup & Automation: Automate sales pipelines using HubSpot, Zoho, or custom AI.
Website Speed & Core Web Vitals Optimization: Fix slow sites that lose Google rankings.""",
        height=150,
        help="Enter each service on a new line. Format: Service Name: Description"
    )

# Main input form
st.header("🎯 Target Company")
col1, col2, col3 = st.columns(3)
with col1:
    target_url = st.text_input("Company Website URL", placeholder="https://example.com")
with col2:
    recipient_name = st.text_input("Recipient Name", placeholder="CEO")
with col3:
    recipient_email = st.text_input("Recipient Email", placeholder="ceo@company.com")

# Validate API key
if not api_key:
    st.error("⚠️ Please enter your Gemini API Key in the sidebar")
    st.stop()

# Get SMTP config from sidebar inputs (stored in session state)
smtp_server = st.session_state['smtp_config']['server']
smtp_port = st.session_state['smtp_config']['port']
smtp_email = st.session_state['smtp_config']['email']
smtp_password = st.session_state['smtp_config']['password']

# Email sending function
def send_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email, subject, body):
    """Send email via SMTP"""
    try:
        # Validate inputs
        if not all([smtp_server, sender_email, sender_password, recipient_email]):
            return False, "Missing required fields: SMTP server, sender email, password, or recipient email"
        
        # Ensure port is integer
        port = int(smtp_port)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
        st.info(f"Connecting to {smtp_server}:{port}...")
        server = smtplib.SMTP(smtp_server, port, timeout=30)
        server.set_debuglevel(1)  # Enable debug output
        
        st.info("Starting TLS...")
        server.starttls()
        
        st.info("Logging in...")
        server.login(sender_email, sender_password)
        
        st.info("Sending email...")
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True, f"Email sent successfully to {recipient_email}!"
    except smtplib.SMTPAuthenticationError as e:
        return False, f"Authentication failed. Check your email/password. For Gmail, use App Password, not regular password. Error: {str(e)}"
    except smtplib.SMTPConnectError as e:
        return False, f"Could not connect to SMTP server. Check server address and port. Error: {str(e)}"
    except smtplib.SMTPRecipientsRefused as e:
        return False, f"Recipient address rejected: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Extract subject from email
def extract_subject(email_text):
    """Extract subject line from email text"""
    lines = email_text.split('\n')
    for line in lines:
        if line.lower().startswith('subject:'):
            return line.replace('Subject:', '').replace('subject:', '').strip()
    return "Introduction - Agency Services"

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
                st.text_area("Copy this email:", value=email_result, height=300, key="email_display")
                st.code(email_result, language="text")
                
                # Store for later use
                st.session_state['generated_email'] = email_result
                st.session_state['company_url'] = target_url
                st.session_state['research'] = research_result
                st.session_state['strategy'] = strategy_result
                st.session_state['recipient_email'] = recipient_email
                
                # Send Email Button
                if recipient_email and smtp_email and smtp_password:
                    # Debug info
                    with st.expander("🔧 Debug SMTP Settings"):
                        st.write(f"Server: {smtp_server}")
                        st.write(f"Port: {smtp_port}")
                        st.write(f"From: {smtp_email}")
                        st.write(f"To: {recipient_email}")
                    
                    if st.button("📤 Send Email Now", type="primary"):
                        with st.spinner("Sending email..."):
                            subject = extract_subject(email_result)
                            st.write(f"Debug: Attempting to send to {recipient_email}")
                            success, message = send_email(
                                smtp_server, smtp_port, smtp_email, smtp_password,
                                recipient_email, subject, email_result
                            )
                            if success:
                                # Store in sent mailbox
                                if 'sent_emails' not in st.session_state:
                                    st.session_state['sent_emails'] = []
                                
                                email_record = {
                                    'to': recipient_email,
                                    'to_name': recipient_name,
                                    'subject': subject,
                                    'body': email_result,
                                    'company_url': target_url,
                                    'timestamp': st.session_state.get('_timestamp', 'Just now')
                                }
                                st.session_state['sent_emails'].insert(0, email_record)
                                
                                # Notification Agent
                                st.balloons()
                                st.success(f"✅ {message}")
                                
                                # Generate notification message
                                notification_prompt = f"""You are a Notification Agent. Create a friendly, professional confirmation message.
                                
                                Email sent to: {recipient_name} at {recipient_email}
                                Subject: {subject}
                                Company: {target_url}
                                
                                Write a brief, celebratory notification confirming the email was sent successfully.
                                Include next steps suggestion. Keep it under 3 sentences."""
                                
                                try:
                                    notification = call_gemini(notification_prompt, api_key, model)
                                    st.info(f"📢 **Notification:** {notification}")
                                except:
                                    st.info(f"📧 Email sent to **{recipient_name}** at **{recipient_email}** successfully!")
                                
                            else:
                                st.error(f"❌ Failed to send: {message}")
                elif not recipient_email:
                    st.info("💡 Enter recipient email to enable sending")
                elif not smtp_email or not smtp_password:
                    st.info("💡 Configure SMTP settings in sidebar to send emails")
                
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

# Mailbox Section - View Sent Emails
st.header("📬 Mailbox - Sent Emails")

if 'sent_emails' in st.session_state and st.session_state['sent_emails']:
    for idx, email in enumerate(st.session_state['sent_emails']):
        with st.expander(f"📧 To: {email['to_name']} ({email['to']}) - {email['subject'][:50]}..."):
            st.markdown(f"**To:** {email['to_name']} <{email['to']}>")
            st.markdown(f"**Company:** {email['company_url']}")
            st.markdown(f"**Subject:** {email['subject']}")
            st.markdown("**Body:**")
            st.text_area(f"Email Content {idx}", value=email['body'], height=200, key=f"sent_email_{idx}")
            
            # Resend button
            if st.button(f"🔄 Resend", key=f"resend_{idx}"):
                with st.spinner("Resending..."):
                    success, message = send_email(
                        smtp_server, smtp_port, smtp_email, smtp_password,
                        email['to'], email['subject'], email['body']
                    )
                    if success:
                        st.success("✅ Resent successfully!")
                    else:
                        st.error(f"❌ Failed: {message}")
else:
    st.info("📭 No emails sent yet. Generate and send an email to see it here.")

# Instructions
with st.expander("📖 How to use"):
    st.markdown("""
    ### Setup
    1. **Enter your Gemini API Key** in the sidebar
    2. **Configure SMTP settings** (for Gmail: use App Password from Google Account settings)
    3. **Enter your Agency Services** in the sidebar (one per line)
    
    ### Generate & Send Email
    4. **Enter target company URL**, **recipient name**, and **recipient email**
    5. **Click "Generate Cold Email"** to create the email
    6. **Click "Send Email Now"** to send directly (or copy manually)
    
    ### Manage Replies
    7. **When you get a reply**, paste it in "Auto-Reply Handler" and generate a response
    8. **Use "Workflow Manager"** to get recommendations on next steps
    """)
    
with st.expander("⚙️ SMTP Setup Guide"):
    st.markdown("""
    ### Gmail Setup
    1. Go to Google Account → Security → 2-Step Verification → Enable
    2. Go to Google Account → Security → App passwords
    3. Select "Mail" and your device, click Generate
    4. Copy the 16-character password and paste it in the sidebar
    
    ### Other Email Providers
    - **Outlook**: smtp.office365.com, port 587
    - **Yahoo**: smtp.mail.yahoo.com, port 587
    - **Custom**: Check with your email provider
    """)
