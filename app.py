import streamlit as st
import datetime
import json
import os
import calendar

# --- 1. CONFIG & APP STYLING ---
st.set_page_config(page_title="MyRoutine", page_icon="🌱", layout="centered")

# Sleek CSS injection for modern, minimalist UI blocks and custom calendar coloring
st.markdown("""
    <style>
    .routine-card {
        background-color: #f9f9fb;
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid #eef0f3;
        margin-bottom: 8px;
    }
    .main-title { font-size: 26px; font-weight: 700; margin-bottom: 2px; }
    .subtitle { color: #8a8f99; font-size: 14px; margin-bottom: 20px; }
    
    /* Calendar Grid Styling */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 6px;
        margin-top: 10px;
    }
    .cal-header {
        font-weight: 600;
        text-align: center;
        font-size: 12px;
        color: #8a8f99;
        padding-bottom: 5px;
    }
    .cal-day {
        aspect-ratio: 1;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-center: center;
        font-size: 12px;
        font-weight: 500;
        color: #1e293b;
    }
    .day-blank { background-color: transparent; }
    .day-future { background-color: #f1f5f9; border: 1px dashed #cbd5e1; }
    .day-green { background-color: #bbf7d0; color: #166534; border: 1px solid #86efac; }
    .day-yellow { background-color: #fef08a; color: #854d0e; border: 1px solid #fde047; }
    .day-red { background-color: #fecaca; color: #991b1b; border: 1px solid #fca5a5; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "routine_history.json"

# --- 2. DATA PERSISTENCE LAYER ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": ["🧘 Stretch", "📚 Study Japanese", "💪 Workout", "💻 Code"], "history": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Initialize app state data
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
today_str = datetime.date.today().isoformat()

# --- 3. HEADER & DATE SELECTOR ---
today_display = datetime.date.today().strftime("%A, %b %d")
st.markdown(f'<div class="main-title">☀️ MyDaily Routine</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">{today_display} • Tailored Routine Engine</div>', unsafe_allow_html=True)

# --- 4. TASK MANAGEMENT (Add/Remove Custom Tasks) ---
with st.expander("🛠️ Customize My Tasks"):
    new_task = st.text_input("Add a brand new routine task:", placeholder="e.g., Read 10 pages")
    if st.button("Add Task") and new_task:
        if new_task not in data["tasks"]:
            data["tasks"].append(new_task)
            save_data(data)
            st.rerun()
            
    st.write("Current Tasks:")
    for index, task in enumerate(data["tasks"]):
        col_t, col_b = st.columns([4, 1])
        col_t.write(f"- {task}")
        if col_b.button("🗑️", key=f"del_{index}"):
            data["tasks"].remove(task)
            save_data(data)
            st.rerun()

# --- 5. THE DAILY TRACKER DASHBOARD ---
st.write("---")
st.markdown("### 📝 Today's Habits")

# Pull up previous completion status if saved earlier today
today_history = data["history"].get(today_str, {})
completed_tasks = []

if not data["tasks"]:
    st.info("No tasks added yet! Open the settings section above to add one.")
else:
    for task in data["tasks"]:
        st.markdown('<div class="routine-card">', unsafe_allow_html=True)
        # Match checkbox state with previously saved data if present
        is_checked = today_history.get(task, False)
        checked = st.checkbox(task, value=is_checked, key=f"check_{task}")
        if checked:
            completed_tasks.append(task)
        st.markdown('</div>', unsafe_allow_html=True)

# Calculate Daily Performance
total_tasks = len(data["tasks"])
score = len(completed_tasks) / total_tasks if total_tasks > 0 else 0.0

# Explicitly save current state automatically on every check interaction
new_today_status = {task: (task in completed_tasks) for task in data["tasks"]}
data["history"][today_str] = new_today_status
save_data(data)

# --- 6. INTricate MONTHLY CALENDAR GRID ---
st.write("---")
current_date = datetime.date.today()
st.markdown(f"### 📅 {current_date.strftime('%B %Y')} Habit Map")

# Calendar logic configurations
cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
month_days = cal.monthdayscalendar(current_date.year, current_date.month)

# Draw Calendar Days Header Titles
days_headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
hdr_cols = st.columns(7)
for idx, h in enumerate(days_headers):
    hdr_cols[idx].markdown(f'<div class="cal-header">{h}</div>', unsafe_allow_html=True)

# Render Rows of Calendar Boxes
for week in month_days:
    cols = st.columns(7)
    for index, day in enumerate(week):
        if day == 0:
            cols[index].markdown('<div class="cal-day day-blank"></div>', unsafe_allow_html=True)
        else:
            target_date = datetime.date(current_date.year, current_date.month, day)
            target_str = target_date.isoformat()
            
            # Determine color class mapping based on date constraints
            if target_date > current_date:
                bg_class = "day-future"
            else:
                day_history = data["history"].get(target_str, None)
                if day_history is None:
                    bg_class = "day-future"  # Unlogged or skipped day
                else:
                    # Calculate true completion percent ratio for that specific history date
                    day_total = len(day_history)
                    day_done = sum(1 for k, v in day_history.items() if v is True)
                    day_score = day_done / day_total if day_total > 0 else 0.0
                    
                    if day_score >= 0.70:
                        bg_class = "day-green"
                    elif day_score >= 0.30:
                        bg_class = "day-yellow"
                    else:
                        bg_class = "day-red"
            
            cols[index].markdown(f'<div class="cal-day {bg_class}">{day}</div>', unsafe_allow_html=True)