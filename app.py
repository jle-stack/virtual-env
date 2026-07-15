import streamlit as st

st.title("🥤 Daily Tracker")
st.write("A simple app to track your daily goals.")

glasses = st.slider("How many glasses of water have you had today?", 0, 12, 4)

if glasses >= 8:
    st.success(f"Great job! {glasses} glasses is plenty of hydration! 🎉")
else:
    st.info(f"You've had {glasses} glasses. Keep drinking!")