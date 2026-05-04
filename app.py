# app.py
import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import base64
from datetime import datetime
import json
import pandas as pd
import random
import time
from gtts import gTTS
import os
import plotly.express as px
from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(
    page_title="Doubt Solver Pro - AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }
    
    /* Animated header */
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    
    .live-badge {
        background: #ff0000;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        animation: blink 1s infinite;
        display: inline-block;
    }
    
    /* Card styling */
    .answer-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 30px;
        font-weight: bold;
        transition: transform 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
    }
    
    /* Mode selector */
    .mode-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .mode-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: scale(1.05);
    }
    
    /* Chat bubble */
    .chat-bubble {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(0, 0, 0, 0.5);
    }
    
    /* Points counter */
    .points-counter {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'points' not in st.session_state:
    st.session_state.points = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'daily_count' not in st.session_state:
    st.session_state.daily_count = 0
if 'last_date' not in st.session_state:
    st.session_state.last_date = datetime.now().date()
if 'language' not in st.session_state:
    st.session_state.language = 'English'

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCIqDZLHu_ibGtb23S0UxUJgSvfGb8e93Q"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Mode configurations
MODES = {
    "Bollywood Style": {
        "prompt": "You are a Bollywood movie hero giving answers. Use dramatic Hindi movie dialogue style with 'Yaara', 'Mastikhor', 'Bhidu' etc. Add filmy expressions and be overly dramatic but funny!",
        "emoji": "🎬",
        "voice_pitch": "medium",
        "sound_effect": "drama"
    },
    "Meme Teacher": {
        "prompt": "You are a funny internet meme teacher. Use Gen Z slang, memes, and super casual style. Say things like 'no cap', 'that's sus', 'bruh moment', 'let me cook now', 'absolute sigma'. Be funny but still give correct answer!",
        "emoji": "😎",
        "voice_pitch": "high",
        "sound_effect": "meme"
    },
    "Little Kid": {
        "prompt": "You are a 5-year-old genius kid explaining things super simply. Use cute words 'oooh', 'wow', 'magical', 'sparkly'. Make it fun like a cartoon character but still correct!",
        "emoji": "🧒",
        "voice_pitch": "high",
        "sound_effect": "cute"
    },
    "Punjabi Paaji": {
        "prompt": "You are a friendly Punjabi uncle. Use Punjabi slang like 'Oye hoye', 'Kiddan', 'Chak de phatte', 'Bahut vadiya'. Be warm and funny with mix of Hindi/English/Punjabi!",
        "emoji": "🪘",
        "voice_pitch": "low"
    },
    "South Indian Anna": {
        "prompt": "You are a South Indian 'Anna'. Use 'Enna rascala', 'Super', 'Dialogue maaru', 'Maja aayitu'. Mix Tamil/Telugu style with English. Be dramatic like Rajinikanth!",
        "emoji": "🐅",
        "voice_pitch": "low"
    }
}

# Subject detection function
def detect_subject(query_text, image_desc=""):
    subject_prompt = f"""Analyze this query and tell me the subject category (Math, Science, History, Geography, English, Other) and confidence level (0-1).
    Query: {query_text}
    Image description: {image_desc}
    
    Return in format: "Subject: X, Confidence: Y" """
    
    try:
        response = model.generate_content(subject_prompt)
        text = response.text
        # Simple parsing
        if "Math" in text:
            return "Math"
        elif "Science" in text:
            return "Science"
        elif "History" in text:
            return "History"
        elif "Geography" in text:
            return "Geography"
        elif "English" in text:
            return "English"
        else:
            return "Other"
    except:
        return "Other"

# Generate funny badges
def get_badge(subject, points):
    badges = {
        "Math": ["🧮 The Newton of Memes", "📐 Algebra Avenger", "➕ Math Magician"],
        "Science": ["🔬 Science Superstar", "⚗️ Lab Legend", "🧪 Einstein's Heir"],
        "History": ["🏺 Time Traveller", "📜 History Hacker", "🗿 Past Master"],
        "Geography": ["🌍 Globe Trotter", "🗺️ Map Master", "🏔️ Mountain Mover"],
        "English": ["📖 Shakespeare's Sidekick", "✍️ Grammar Guru", "📚 Literary Legend"],
        "Other": ["🎯 Knowledge Ninja", "💡 Bright Spark", "🧠 Brain Champion"]
    }
    return random.choice(badges.get(subject, badges["Other"]))

# Generate meme card
def create_meme_card(question, answer, mode_emoji):
    # Create image
    img = Image.new('RGB', (800, 600), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for i in range(600):
        color_value = int(30 + (i/600)*100)
        draw.rectangle([(0, i), (800, i+1)], fill=(color_value, color_value, color_value+20))
    
    # Add mode emoji
    try:
        # Try to use a default font
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Draw title
    draw.text((50, 50), f"{mode_emoji} Doubt Solver Pro", fill=(255, 255, 255), font=title_font)
    draw.text((50, 100), "Question:", fill=(255, 200, 100), font=title_font)
    
    # Wrap text
    question_words = question[:200].split()
    question_lines = [' '.join(question_words[i:i+15]) for i in range(0, len(question_words), 15)]
    y_offset = 130
    for line in question_lines[:3]:
        draw.text((70, y_offset), line, fill=(200, 200, 200), font=text_font)
        y_offset += 30
    
    draw.text((50, y_offset+20), "🤣 Answer:", fill=(100, 255, 100), font=title_font)
    
    answer_words = answer[:300].split()
    answer_lines = [' '.join(answer_words[i:i+15]) for i in range(0, len(answer_words), 15)]
    y_offset += 60
    for line in answer_lines[:6]:
        draw.text((70, y_offset), line, fill=(255, 255, 255), font=text_font)
        y_offset += 30
    
    # Add footer
    draw.text((50, 550), "🔍 Generated by Doubt Solver Pro", fill=(150, 150, 150), font=text_font)
    draw.text((50, 570), "📅 " + datetime.now().strftime("%Y-%m-%d %H:%M"), fill=(150, 150, 150), font=text_font)
    
    return img

# Text-to-speech
def text_to_speech(text, mode):
    try:
        tts = gTTS(text[:500], lang='hi' if st.session_state.language != 'English' else 'en', slow=False)
        audio_file = "temp_audio.mp3"
        tts.save(audio_file)
        return audio_file
    except:
        return None

# Main header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🎓 Doubt Solver Pro")
    st.markdown('<div class="live-badge">🔴 LIVE NOW</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🏆 Your Stats")
    
    # Reset daily counter
    current_date = datetime.now().date()
    if st.session_state.last_date != current_date:
        st.session_state.daily_count = 0
        st.session_state.last_date = current_date
    
    # Points display
    st.markdown(f"""
    <div class="points-counter">
        <h3>⭐ Brain Points</h3>
        <h1>{st.session_state.points}</h1>
        <p>Today: {st.session_state.daily_count} doubts solved</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get badge
    if st.session_state.points > 0:
        badge = get_badge("Other", st.session_state.points)
        st.markdown(f"🏅 **Your Badge:** {badge}")
    
    # Language selector
    st.markdown("### 🌐 Language")
    lang = st.selectbox("Select Language", ["English", "Hinglish", "Pure Hindi"], key="lang_select")
    if lang != st.session_state.language:
        st.session_state.language = lang
    
    # Subject analytics
    if st.session_state.history:
        st.markdown("### 📊 Subject Analytics")
        subjects = [h.get('subject', 'Other') for h in st.session_state.history]
        if subjects:
            df = pd.DataFrame(subjects, columns=['Subject'])
            fig = px.pie(df, names='Subject', title='Your Study Pattern', color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    
    # Leaderboard
    st.markdown("### 🏅 Study Leaderboard")
    leaderboard_data = [
        {"Name": "You", "Points": st.session_state.points},
        {"Name": "Top Student", "Points": 1250},
        {"Name": "Quiz Master", "Points": 980},
        {"Name": "Homework Hero", "Points": 750}
    ]
    for idx, user in enumerate(sorted(leaderboard_data, key=lambda x: x['Points'], reverse=True)[:5], 1):
        st.markdown(f"{idx}. {user['Name']} - {user['Points']} pts")
    
    # History
    st.markdown("### 📜 History")
    if st.session_state.history:
        for idx, item in enumerate(reversed(st.session_state.history[-5:])):
            with st.expander(f"Q{len(st.session_state.history)-idx}: {item['question'][:40]}..."):
                st.write(f"**Mode:** {item['mode']}")
                st.write(f"**Answer:** {item['answer'][:150]}...")
                if st.button(f"🔊 Listen", key=f"listen_{idx}"):
                    audio_file = text_to_speech(item['answer'], item['mode'])
                    if audio_file:
                        st.audio(audio_file)
    else:
        st.info("No history yet. Upload a photo to start!")

# Main content area
tab1, tab2, tab3 = st.tabs(["📸 Solve Doubt", "💬 Chat with AI", "🏆 Wall of Fame"])

with tab1:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Mode selection
        st.markdown("### 🎭 Choose Your Style")
        mode_cols = st.columns(3)
        selected_mode = None
        
        for idx, (mode_name, mode_info) in enumerate(MODES.items()):
            col = mode_cols[idx % 3]
            with col:
                if st.button(f"{mode_info['emoji']} {mode_name}", key=f"mode_{idx}", use_container_width=True):
                    selected_mode = mode_name
                    st.session_state.selected_mode = mode_name
        
        if 'selected_mode' not in st.session_state:
            st.session_state.selected_mode = "Bollywood Style"
        
        st.markdown(f"**Current Mode:** {MODES[st.session_state.selected_mode]['emoji']} {st.session_state.selected_mode}")
        
        # File uploader
        uploaded_file = st.file_uploader("Upload your doubt image 📸", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Question", use_container_width=True)
            
            # Process button
            if st.button("🤖 Solve My Doubt!", use_container_width=True):
                with st.spinner("✨ AI is analyzing your question..."):
                    # Show thinking animation
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Convert image to text
                    img_io = io.BytesIO()
                    image.save(img_io, format='PNG')
                    img_io.seek(0)
                    
                    # Get answer from Gemini
                    mode_prompt = MODES[st.session_state.selected_mode]["prompt"]
                    language_instruction = f"Respond in {st.session_state.language} style. " if st.session_state.language != "English" else ""
                    
                    full_prompt = f"""{mode_prompt}
                    {language_instruction}
                    The user has uploaded an image containing a academic question/doubt.
                    Please analyze the image and provide a funny, engaging answer in your assigned style.
                    Make it educational but entertaining! Keep response under 200 words.
                    Start directly with your answer."""
                    
                    try:
                        # For image processing with Gemini
                        response = model.generate_content([full_prompt, image])
                        answer = response.text
                        
                        # Extract question text from image
                        question_prompt = "Extract the main question text from this image. Keep it concise."
                        question_response = model.generate_content([question_prompt, image])
                        question = question_response.text[:200]
                        
                        # Detect subject
                        subject = detect_subject(question, "")
                        
                        # Store in history
                        history_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "question": question,
                            "answer": answer,
                            "mode": st.session_state.selected_mode,
                            "subject": subject
                        }
                        st.session_state.history.append(history_entry)
                        
                        # Update points
                        points_earned = random.randint(10, 30)
                        st.session_state.points += points_earned
                        st.session_state.daily_count += 1
                        
                        # Display answer
                        st.markdown(f"""
                        <div class="answer-card">
                            <h3>{MODES[st.session_state.selected_mode]['emoji']} Answer in {st.session_state.selected_mode} Style:</h3>
                            <p>{answer}</p>
                            <hr>
                            <small>📚 Subject: {subject} | ⭐ +{points_earned} points</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Generate audio
                        audio_file = text_to_speech(answer, st.session_state.selected_mode)
                        if audio_file:
                            st.audio(audio_file)
                            st.markdown("🔊 **Listen to answer above!**")
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            # Download as image
                            meme_card = create_meme_card(question, answer, MODES[st.session_state.selected_mode]['emoji'])
                            buf = io.BytesIO()
                            meme_card.save(buf, format='PNG')
                            st.download_button(
                                label="📸 Download as Image (Share on Instagram!)",
                                data=buf.getvalue(),
                                file_name=f"doubt_solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png"
                            )
                        
                        with col2:
                            # Download as text
                            st.download_button(
                                label="📝 Download as Text",
                                data=f"Question: {question}\n\nAnswer: {answer}",
                                file_name=f"solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                        
                        # Show follow-up option
                        st.markdown("### 💬 Need more explanation?")
                        follow_up = st.text_input("Ask a follow-up question...")
                        if follow_up:
                            follow_prompt = f"Previous question: {question}\nPrevious answer: {answer}\nFollow-up: {follow_up}\nAnswer in the same style: {st.session_state.selected_mode}"
                            follow_response = model.generate_content(follow_prompt)
                            st.markdown(f"""
                            <div class="chat-bubble">
                                <strong>🤖 {st.session_state.selected_mode}:</strong> {follow_response.text}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "user": follow_up,
                                "bot": follow_response.text,
                                "mode": st.session_state.selected_mode
                            })
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}. Please check your API key.")
                        st.info("Make sure to replace 'YOUR_GEMINI_API_KEY_HERE' with your actual Gemini API key")

with tab2:
    st.markdown("### 🤖 Chat with Your AI Buddy")
    st.markdown("Ask anything, get funny answers in your preferred style!")
    
    # Chat interface
    chat_mode = st.selectbox("Chat Mode", list(MODES.keys()))
    user_input = st.text_input("Your question:", key="chat_input")
    
    if user_input:
        with st.spinner("Thinking..."):
            chat_prompt = f"{MODES[chat_mode]['prompt']} Answer this: {user_input}"
            chat_response = model.generate_content(chat_prompt)
            
            st.markdown(f"""
            <div class="chat-bubble">
                <strong>{MODES[chat_mode]['emoji']} {chat_mode}:</strong> {chat_response.text}
            </div>
            """, unsafe_allow_html=True)
            
            # Add to history
            st.session_state.chat_history.append({"user": user_input, "bot": chat_response.text, "mode": chat_mode})
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 📜 Chat History")
        for chat in st.session_state.chat_history[-10:]:
            st.markdown(f"""
            **You:** {chat['user']}
            **{chat['mode']}:** {chat['bot']}
            ---
            """)

with tab3:
    st.markdown("### 🏆 Wall of Fame - Funniest Doubts")
    
    # Sample wall of fame entries
    wall_entries = [
        {"user": "Math_Wizard", "question": "Why is 6 afraid of 7?", "answer": "Because 7 8 9! Classic math horror story! 😱", "likes": 234},
        {"user": "ScienceGeek", "question": "Why did the physics teacher break up with biology?", "answer": "There was no chemistry! *ba dum tss* 🥁", "likes": 189},
        {"user": "HistoryBuff", "question": "Why was the math book sad?", "answer": "Because it had too many problems! 📚😢", "likes": 156}
    ]
    
    for entry in wall_entries:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                **👤 {entry['user']}**
                ❓ {entry['question']}
                💡 {entry['answer']}
                """)
            with col2:
                if st.button(f"❤️ {entry['likes']} likes", key=f"like_{entry['user']}"):
                    st.balloons()
                    st.success("Thanks for liking!")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    st.markdown("""
    <div style="text-align: center;">
        <p>🎓 Doubt Solver Pro - Making Learning Fun!</p>
        <p>Share your funny answers on Instagram and tag #DoubtSolverPro</p>
    </div>
    """, unsafe_allow_html=True)
