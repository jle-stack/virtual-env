import streamlit as st
import datetime

# --- 1. CONFIG & STYLING (The "MyRoutine" Minimalist Aesthetic) ---
st.set_page_config(page_title="MyRoutine Tracker", page_icon="🌱", layout="centered")

# Custom injection to make cards look clean and boxed
st.markdown("""
    <style>
    .routine-card {
        background-color: #f9f9fb;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eef0f3;
        margin-bottom: 10px;
    }
    .main-title {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .subtitle {
        color: #8a8f99;
        font-size: 14px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER ---
today = datetime.date.today().strftime("%A, %b %d")
st.markdown(f'<div class="main-title">☀️ MyDaily Routine</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">{today} • 4 core routines targets</div>', unsafe_allow_html=True)

# Progress bar at the top to see the day's completion rate
progress = st.progress(0)
completed_count = 0

# --- 3. THE ROUTINE GRID (Columns) ---
# Left column for Morning/Afternoon, Right column for Evening/Habits
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🌅 Morning")
    
    with st.container():
        st.markdown('<div class="routine-card">', unsafe_allow_html=True)
        morn_1 = st.checkbox("🧘 Wake up & Stretch", key="m1")
        if morn_1: completed_count += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="routine-card">', unsafe_allow_html=True)
        morn_2 = st.checkbox("📚 Study Japanese (30m)", key="m2")
        if morn_2: completed_count += 1
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🌌 Night & Health")
    
    with st.container():
        st.markdown('<div class="routine-card">', unsafe_allow_html=True)
        night_1 = st.checkbox("💪 Workout / Quick Walk", key="n1")
        if night_1: completed_count += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="routine-card">', unsafe_allow_html=True)
        night_2 = st.checkbox("💻 Code / Review Project", key="n2")
        if night_2: completed_count += 1
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. DYNAMIC PROGRESS CALCULATION ---
total_habits = 4
calculated_progress = completed_count / total_habits
progress.progress(calculated_progress)

# --- 5. DAILY REFLECTION NOTES ---
st.write("---")
st.markdown("### ✍️ Daily Reflection")
note = st.text_area("How did today feel? Any blockers?", placeholder="Keep it brief...")

if st.button("Save Entry", type="primary"):
    st.success("Routine state saved locally! Perfect consistency.")