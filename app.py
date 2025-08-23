import streamlit as st
import json
import os
import pandas as pd
import random
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

    tabs = st.tabs(["📊 Dashboard", "🥗 Diet Tracking", "💉 Advanced Insulin Assistant", "🍎 Diet Recommendations", "📂 Data Upload", "📈 Reports"])

    # ---------------- Dashboard ----------------
    with tabs[0]:
        st.header("📊 Dashboard")
        st.write("Welcome to your personalized dashboard,", st.session_state.username)

        st.metric("Total Meals Tracked", len(st.session_state.user_data.get("diet_tracking", [])))
        st.metric("Total Insulin Recs", len(st.session_state.user_data.get("insulin_recommendations", [])))

    # ---------------- Diet Tracking ----------------
    with tabs[1]:
        st.header("🥗 Diet Tracking")
        meal = st.text_input("Meal")
        calories = st.number_input("Calories", 0)
        if st.button("Add Meal"):
            new_meal = {"meal": meal, "calories": calories, "time": str(datetime.now())}
            st.session_state.user_data.setdefault("diet_tracking", []).append(new_meal)
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.success("Meal added!")

        if st.session_state.user_data.get("diet_tracking"):
            df = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.dataframe(df)

    # ---------------- Advanced Insulin Assistant ----------------
    with tabs[2]:
        st.header("💉 Advanced Insulin Assistant")
        glucose_level = st.number_input("Current Glucose Level (mg/dL)", 0)
        target_glucose = st.number_input("Target Glucose Level (mg/dL)", 100)
        carbs = st.number_input("Carbs in Meal (grams)", 0)
        insulin_ratio = st.number_input("Insulin-to-Carb Ratio (g/unit)", 10)
        correction_factor = st.number_input("Correction Factor (mg/dL per unit)", 50)

        if st.button("Calculate Dose"):
            meal_dose = carbs / insulin_ratio if insulin_ratio > 0 else 0
            correction_dose = (glucose_level - target_glucose) / correction_factor if correction_factor > 0 else 0
            total_dose = max(meal_dose + correction_dose, 0)

            recommendation = f"Meal Dose: {meal_dose:.1f}, Correction Dose: {correction_dose:.1f}, Total: {total_dose:.1f} units"

            st.session_state.user_data.setdefault("insulin_recommendations", []).append({
                "glucose": glucose_level,
                "carbs": carbs,
                "meal_dose": meal_dose,
                "correction_dose": correction_dose,
                "total_dose": total_dose,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.success(recommendation)

        if st.session_state.user_data.get("insulin_recommendations"):
            df = pd.DataFrame(st.session_state.user_data["insulin_recommendations"])
            st.dataframe(df)

    # ---------------- Diet Recommendations ----------------
    with tabs[3]:
        st.header("🍎 Diet Recommendations")

        diet_choice = st.selectbox("Choose your diet goal", ["Weight Loss", "Weight Gain", "Maintain Weight"])

        if st.button("Get Diet Plan") or st.button("Regenerate Diet Plan"):
            breakfast_options = ["Oatmeal with berries", "Greek yogurt with honey", "Vegetable omelette", "Smoothie bowl"]
            lunch_options = ["Grilled chicken with veggies", "Quinoa salad", "Fish tacos", "Chickpea curry"]
            dinner_options = ["Salmon with quinoa", "Stir fry with tofu", "Pasta with vegetables", "Lentil soup"]

            plan = []
            for day in range(1, 8):
                plan.append({"Day": f"Day {day}", "Meal": "Breakfast", "Recommendation": random.choice(breakfast_options)})
                plan.append({"Day": f"Day {day}", "Meal": "Lunch", "Recommendation": random.choice(lunch_options)})
                plan.append({"Day": f"Day {day}", "Meal": "Dinner", "Recommendation": random.choice(dinner_options)})

            df = pd.DataFrame(plan)
            st.session_state.user_data.setdefault("diet_recommendations", []).append({
                "goal": diet_choice,
                "plan": plan,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)

            st.success("Diet plan generated!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Diet Plan (CSV)", csv, "diet_plan.csv", "text/csv")

    # ---------------- Data Upload ----------------
    with tabs[4]:
        st.header("📂 Data Upload")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head())

            if st.button("Merge Data"):
                if "meal" in df.columns and "calories" in df.columns:
                    st.session_state.user_data.setdefault("diet_tracking", []).extend(df.to_dict(orient="records"))
                elif "glucose" in df.columns and "total_dose" in df.columns:
                    st.session_state.user_data.setdefault("insulin_recommendations", []).extend(df.to_dict(orient="records"))
                save_user_data(st.session_state.username, st.session_state.user_data)
                st.success("Data merged into your records!")

    # ---------------- Reports ----------------
    with tabs[5]:
        st.header("📈 Reports")
        if st.session_state.user_data.get("insulin_recommendations"):
            df = pd.DataFrame(st.session_state.user_data["insulin_recommendations"])
            st.line_chart(df.set_index("time")["glucose"])

        if st.session_state.user_data.get("diet_tracking"):
            df = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.bar_chart(df.set_index("meal")["calories"])

# ---------------------- Run App ----------------------
def run_app():
    if not st.session_state.logged_in:
        login_signup()
    else:
        main_app()

# Execute the app
if __name__ == "__main__":
    run_app()
