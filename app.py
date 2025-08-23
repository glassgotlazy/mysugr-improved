import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# Page setup
st.set_page_config(page_title="MySugar Advanced", layout="wide")
st.markdown("<small><i>made by ~Glass</i></small>", unsafe_allow_html=True)

# File paths for authentication
auth_file = "auth.json"

# ---------------------- Authentication Functions ----------------------
def load_auth():
    if os.path.exists(auth_file):
        with open(auth_file, "r") as f:
            return json.load(f)
    return {}

def save_auth(auth_data):
    with open(auth_file, "w") as f:
        json.dump(auth_data, f)

# ---------------------- User Data Functions ----------------------
def get_user_file(username):
    return f"user_data_{username}.json"

def load_user_data(username):
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {
        "diet_tracking": [],
        "insulin_recommendations": [],
        "diet_recommendations": []
    }

def save_user_data(username, data):
    file_path = get_user_file(username)
    with open(file_path, "w") as f:
        json.dump(data, f)

# ---------------------- App State ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = {}

# ---------------------- Authentication UI ----------------------
def login_signup():
    st.title("🔐 MySugar Advanced - Login / Signup")
    auth_data = load_auth()

    choice = st.radio("Choose an option", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Signup":
        if st.button("Signup"):
            if username in auth_data:
                st.error("User already exists!")
            else:
                auth_data[username] = password
                save_auth(auth_data)
                st.success("Signup successful! Please login.")

    elif choice == "Login":
        if st.button("Login"):
            if username in auth_data and auth_data[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_data = load_user_data(username)
                st.success("Login successful!")
            else:
                st.error("Invalid username or password")

# ---------------------- Main App ----------------------
def main_app():
    st.sidebar.title("Navigation")

    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_data = {}
        st.rerun()

    tabs = st.tabs(["📊 Dashboard", "🥗 Diet Tracking", "💉 Insulin Recommendations", "🍎 Diet Recommendations"])

    with tabs[0]:
        st.header("📊 Dashboard")
        st.write("Welcome to your personalized dashboard,", st.session_state.username)

        if st.session_state.get("user_data", {}).get("diet_tracking"):
            df = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.dataframe(df)
        else:
            st.info("No meals tracked yet.")

    with tabs[1]:
        st.header("🥗 Diet Tracking")
        meal = st.text_input("Meal")
        calories = st.number_input("Calories", 0)
        if st.button("Add Meal"):
            new_meal = {"meal": meal, "calories": calories, "time": str(datetime.now())}
            st.session_state.user_data.setdefault("diet_tracking", []).append(new_meal)
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.success("Meal added!")

    with tabs[2]:
        st.header("💉 Insulin Recommendations")
        glucose_level = st.number_input("Current Glucose Level (mg/dL)", 0)
        if st.button("Get Recommendation"):
            recommendation = f"Take {glucose_level/50:.1f} units of insulin."
            st.session_state.user_data.setdefault("insulin_recommendations", []).append({
                "glucose": glucose_level,
                "recommendation": recommendation,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.info(recommendation)

        if st.session_state.get("user_data", {}).get("insulin_recommendations"):
            df = pd.DataFrame(st.session_state.user_data["insulin_recommendations"])
            st.dataframe(df)

    with tabs[3]:
        st.header("🍎 Diet Recommendations")
        diet_choice = st.selectbox("Choose your diet goal", ["Weight Loss", "Weight Gain", "Maintain Weight"])
        if st.button("Get Diet Plan"):
            plan = f"Recommended diet plan for {diet_choice}"
            st.session_state.user_data.setdefault("diet_recommendations", []).append({
                "goal": diet_choice,
                "plan": plan,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.success(plan)

        if st.session_state.get("user_data", {}).get("diet_recommendations"):
            df = pd.DataFrame(st.session_state.user_data["diet_recommendations"])
            st.dataframe(df)

# ---------------------- Run App ----------------------
def run_app():
    if not st.session_state.logged_in:
        login_signup()
    else:
        main_app()

# Execute the app
if __name__ == "__main__":
    run_app()
