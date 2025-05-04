import streamlit as st
import re

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="FakeNews Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
import database as db
from datetime import datetime
import sqlite3

# Initialize database
db.init_db()

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #0A0A0A;
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Navigation bar */
    .navbar {
        background-color: rgba(10, 10, 10, 0.95);
        padding: 1rem 3rem;
        color: white;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        backdrop-filter: blur(10px);
        height: 70px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Logo and brand */
    .brand {
        font-size: 2rem;
        font-weight: 700;
        color: #E50914;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Navigation container */
    .nav-container {
        display: flex;
        align-items: center;
        gap: 30px;
        margin-right: 20px;
    }
    
    /* Navigation links */
    .nav-link {
        color: #FFFFFF;
        text-decoration: none;
        padding: 0.7rem 1.2rem;
        border-radius: 6px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-weight: 500;
        font-size: 1.1rem;
        white-space: nowrap;
        position: relative;
    }
    
    .nav-link:hover {
        color: #E50914;
        background-color: rgba(229, 9, 20, 0.1);
        transform: translateY(-2px);
    }
    
    /* Logout button */
    .logout-btn {
        background-color: #E50914;
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1.1rem;
        white-space: nowrap;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(229, 9, 20, 0.3);
    }
    
    .logout-btn:hover {
        background-color: #FF0F1A;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(229, 9, 20, 0.4);
    }

    /* Cards */
    .card {
        background-color: rgba(20, 20, 20, 0.95);
        border-radius: 12px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }

    /* Hero section */
    .hero {
        background: linear-gradient(45deg, #1a1a1a, #2a2a2a);
        padding: 120px 20px;
        text-align: center;
        margin-top: 70px;
        position: relative;
    }

    /* Forms */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        padding: 12px;
        transition: all 0.3s ease;
    }

    .stTextInput>div>div>input:focus {
        border-color: #E50914;
        box-shadow: 0 0 0 2px rgba(229, 9, 20, 0.2);
    }

    /* Password input specific styling */
    .stTextInput>div>div>input[type="password"],
    .stTextInput>div>div>input[type="text"] {
        color: black !important;
        background-color: white !important;
        -webkit-text-fill-color: black !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #E50914;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 2px 5px rgba(229, 9, 20, 0.3);
    }
    
    .stButton>button:hover {
        background-color: #FF0F1A;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(229, 9, 20, 0.4);
    }

    /* Footer */
    .footer {
        background-color: rgba(10, 10, 10, 0.95);
        color: #999;
        padding: 20px;
        text-align: center;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Hidden navigation */
    .hidden-nav {
        display: none;
    }

    /* Page content */
    .page-content {
        margin-top: 90px;
        margin-bottom: 80px;
        padding: 0 40px;
    }

    /* Headings */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Links */
    a {
        color: #E50914;
        text-decoration: none;
        transition: all 0.3s ease;
    }

    a:hover {
        color: #FF0F1A;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Please set your GEMINI_API_KEY in the .env file or as an environment variable")
    st.stop()

def initialize_gemini():
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        system_instruction=(
            "You are a fact-checking expert. Analyze news articles for potential fake news indicators. "
            "Consider these factors:\n"
            "1. Source credibility\n"
            "2. Emotional language and sensationalism\n"
            "3. Lack of evidence or sources\n"
            "4. Inconsistencies in the story\n"
            "5. Clickbait headlines\n"
            "6. Political bias\n"
            "7. Grammar and spelling errors\n"
            "8. Unusual timing or context\n"
            "Provide a clear and concise analysis with:\n"
            "- Final Verdict (REAL or FAKE)\n"
            "- Trust Score (0-100)\n"
            "- Fake News Probability (0-100%)\n"
            "- Key Points\n"
            "- Explanation"
        ),
    )
    return model.start_chat(history=[])

def get_gemini_response(chat_session, description, retries=3, delay=10):
    try:
        response = chat_session.send_message(description)
        return response
    except Exception as e:
        if "RATE_LIMIT_EXCEEDED" in str(e):
            st.warning(f"Rate limit exceeded. Waiting for {delay} seconds...")
            time.sleep(delay)
            if retries > 0:
                return get_gemini_response(chat_session, description, retries - 1, delay * 2)
            st.error("Max retries reached. Please try again later.")
            return None
        st.error(f"Error: {str(e)}")
        if retries > 0:
            time.sleep(5)
            return get_gemini_response(chat_session, description, retries - 1, delay)
        st.error("Max retries reached. Skipping this request.")
        return None

def extract_scores(response_text):
    try:
        # Extract trust score
        trust_score_match = re.search(r'Trust Score:\s*(\d+)', response_text)
        trust_score = int(trust_score_match.group(1)) if trust_score_match else 50
        
        # Extract fake probability
        fake_prob_match = re.search(r'Fake News Probability:\s*(\d+)', response_text)
        fake_probability = int(fake_prob_match.group(1)) if fake_prob_match else 50
        
        return trust_score, fake_probability
    except Exception as e:
        print(f"Error extracting scores: {e}")
        return 50, 50  # Default values if extraction fails

def navigation():
    st.markdown("""
    <div class="navbar">
        <div class="brand">🔍 FakeNews Detector</div>
        <div class="nav-container">
            <div class="nav-link" onclick='document.getElementById("home").click()'>Home</div>
            <div class="nav-link" onclick='document.getElementById("about").click()'>About</div>
            <div class="nav-link" onclick='document.getElementById("login").click()'>Login</div>
            <button class="logout-btn" onclick='document.getElementById("logout").click()'>Logout</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def home_page():
    st.markdown("""
    <div class="hero" style="background: linear-gradient(45deg, #1a1a1a, #2a2a2a);">
        <h1 style='font-size: 3.5rem; margin-bottom: 20px;'>Fake News Detection System</h1>
        <p style='font-size: 1.5rem; color: #999; margin-bottom: 30px;'>Your AI-Powered Shield Against Misinformation</p>
    </div>
    
    <div style='padding: 40px 20px;'>
        <div class="card">
            <h2 style='color: #E50914; text-align: center; margin-bottom: 30px;'>The Growing Threat of Fake News</h2>
            <p style='color: #999; line-height: 1.8; margin-bottom: 20px;'>
                In today's digital landscape, fake news has become a significant threat to society. Misinformation spreads six times faster than real news on social media platforms, making it crucial to have reliable tools for fact-checking. Our AI-powered platform uses advanced natural language processing and machine learning to detect patterns commonly associated with fake news.
            </p>
            <p style='color: #999; line-height: 1.8; margin-bottom: 20px;'>
                We analyze multiple dimensions of news content, including source credibility, emotional language, factual consistency, and evidence quality. Our system can identify subtle patterns that might indicate misinformation, such as sensationalist headlines, lack of credible sources, or manipulative language.
            </p>
            <div style='text-align: center; margin-top: 30px;'>
                <button onclick='document.getElementById("get-started").click()' style='background-color: #E50914; color: white; border: none; padding: 15px 30px; border-radius: 4px; font-size: 1.2rem; cursor: pointer;'>Get Started</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Get Started", key="get-started"):
        if 'user_id' in st.session_state:
            st.session_state.page = "main"
        else:
            st.session_state.page = "login"
        st.rerun()

def about_page():
    st.markdown("""
    <div style="margin-top: 80px; padding: 40px 20px;">
        <div class="card">
            <h1 style='text-align: center; color: #E50914; font-size: 2.5rem; margin-bottom: 20px;'>About Our News Analysis Project</h1>
            <p style='text-align: center; color: #999; font-size: 1.2rem; margin-bottom: 40px;'>Empowering Users with AI-Powered News Verification</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def login_page():
    st.markdown("""
    <div style="margin-top: 80px;">
        <h1 style='text-align: center; color: #E50914;'>Welcome Back</h1>
        <p style='text-align: center; color: #999;'>Sign in to continue analyzing news</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if submit:
            if not username or not password:
                st.error("Please fill in all fields")
            else:
                user = db.verify_user(username, password)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.page = "main"
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    # Add a button for signup instead of a link
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Don't have an account? Sign up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

def signup_page():
    st.markdown("""
    <div style="margin-top: 80px;">
        <h1 style='text-align: center; color: #E50914;'>Create Account</h1>
        <p style='text-align: center; color: #999;'>Join our community of fact-checkers</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("signup_form"):
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if submit:
            if not username or not email or not password or not confirm_password:
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    if db.register_user(username, password, email):
                        st.success("Account created successfully! Please login.")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("Username or email already exists")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    # Add a button to go back to login
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Already have an account? Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

def main_page():
    st.markdown("""
    <div style="margin-top: 80px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
            <h1 style='color: #E50914;'>Welcome, {}</h1>
        </div>
    </div>
    """.format(st.session_state.username), unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h2 style='text-align: center; color: #E50914;'>News Analysis</h2>
        <p style='text-align: center; color: #999;'>Enter news content to analyze for authenticity</p>
    </div>
    """, unsafe_allow_html=True)
    
    chat_session = initialize_gemini()
    
    article_content = st.text_area("News Content", height=200)
    
    if st.button('Analyze', type="primary", use_container_width=True):
        if article_content:
            with st.spinner('Analyzing...'):
                prompt = f"""
                Content: {article_content}
                
                Please analyze this news content for potential fake news indicators and provide a detailed fact-checking report.
                Consider these factors:
                1. Source credibility
                2. Emotional language and sensationalism
                3. Lack of evidence or sources
                4. Inconsistencies in the story
                5. Clickbait headlines
                6. Political bias
                7. Grammar and spelling errors
                8. Unusual timing or context
                
                Provide a clear and concise analysis with:
                - Final Verdict (REAL or FAKE)
                - Trust Score (0-100)
                - Fake News Probability (0-100%)
                - Key Points
                - Explanation
                """
                response = get_gemini_response(chat_session, prompt)
                
                if response:
                    # Extract trust score and fake probability from response
                    trust_score, fake_probability = extract_scores(response.text)
                    
                    # Save analysis to database
                    db.save_analysis(
                        st.session_state.user_id,
                        article_content,
                        response.text,
                        trust_score,
                        fake_probability
                    )
                    
                    # Display results
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown("### Analysis Results")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Trust Score", f"{trust_score}%")
                    with col2:
                        st.metric("Fake News Probability", f"{fake_probability}%")
                    
                    st.markdown("#### Detailed Analysis")
                    st.markdown(response.text)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error("Failed to analyze the content. Please try again.")
        else:
            st.warning("Please enter content to analyze.")
    
    # Show analysis history
    st.markdown("""
    <div class="card">
        <h2 style='color: #E50914;'>Your Analysis History</h2>
    </div>
    """, unsafe_allow_html=True)
    
    history = db.get_user_history(st.session_state.user_id)
    
    for i, (content, result, trust_score, fake_prob, date) in enumerate(history):
        with st.expander(f"Analysis from {date}"):
            col1, col2 = st.columns([0.95, 0.05])
            with col1:
                st.markdown(f"**Content:** {content[:200]}...")
                st.markdown(f"**Result:** {result}")
                st.markdown(f"**Trust Score:** {trust_score}%")
                st.markdown(f"**Fake Probability:** {fake_prob}%")
            with col2:
                if st.button("🗑️", key=f"delete_{i}"):
                    try:
                        if db.delete_analysis(st.session_state.user_id, str(date)):
                            st.success("Analysis deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete analysis")
                    except Exception as e:
                        st.error(f"Error deleting analysis: {str(e)}")

def main():
    navigation()
    
    # Navigation buttons (hidden)
    st.markdown('<div class="hidden-nav">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        if st.button("Home", key="home"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("About", key="about"):
            st.session_state.page = "about"
            st.rerun()
    with col3:
        if st.button("Login", key="login"):
            st.session_state.page = "login"
            st.rerun()
    with col4:
        if st.button("Logout", key="logout"):
            if 'user_id' in st.session_state:
                st.session_state.clear()
                st.session_state.page = "home"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Page content wrapper
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    # Show different pages based on login state
    if 'user_id' in st.session_state:
        if st.session_state.page == "home":
            home_page()
        elif st.session_state.page == "about":
            about_page()
        elif st.session_state.page == "main":
            main_page()
    else:
        if st.session_state.page == "home":
            home_page()
        elif st.session_state.page == "about":
            about_page()
        elif st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "signup":
            signup_page()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer">
        <p>© 2024 FakeNews Detector. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
