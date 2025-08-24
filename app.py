import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime

# ================== CONFIG ==================
USER_DATA_FILE = "users.json"
USDA_API_KEY = st.secrets["usda"]["api_key"]
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# ================== USER MANAGEMENT ==================
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

def save_user_data(username, data):
    users = load_users()
    users[username] = data
    save_users(users)

def load_user_data(username):
    return load_users().get(username, {})

# ================== USDA API ==================
def search_usda_food(query, page_size=5):
    """Search USDA API for foods."""
    params = {"api_key": USDA_API_KEY, "query": query, "pageSize": page_size}
    response = requests.get(USDA_SEARCH_URL, params=params)
    if response.status_code == 200:
        foods = response.json().get("foods", [])
        return [
            {
                "name": f["description"],
                "calories": next((n["value"] for n in f.get("foodNutrients", []) if n["nutrientName"] == "Energy"), 0),
                "protein": next((n["value"] for n in f.get("foodNutrients", []) if n["nutrientName"] == "Protein"), 0),
                "carbs": next((n["value"] for n in f.get("foodNutrients", []) if n["nutrientName"] == "Carbohydrate, by difference"), 0),
                "fat": next((n["value"] for n in f.get("foodNutrients", []) if n["nutrientName"] == "Total lipid (fat)"), 0),
            }
            for f in foods
        ]
    return []

def generate_usda_diet_plan(goal):
    """Generate a 7-day plan from USDA API foods based on diet goal."""
    if goal == "Balanced":
        queries = ["chicken breast", "brown rice", "broccoli", "salmon", "quinoa", "oatmeal"]
    elif goal == "Low-Carb":
        queries = ["eggs", "avocado", "chicken", "spinach", "tofu", "salmon"]
    elif goal == "High-Protein":
        queries = ["chicken breast", "turkey", "lentils", "greek yogurt", "fish", "eggs"]
    else:
        queries = ["vegetables", "fruit", "rice", "beans"]

    plan = []
    for day in range(1, 8):
        for meal_type, q in zip(["Breakfast", "Lunch", "Dinner"], queries[:3]):
            foods = search_usda_food(q, page_size=1)
            if foods:
                food = foods[0]
                plan.append({
                    "Day": f"Day {day}",
                    "Meal": meal_type,
                    "Recommendation": food["name"],
                    "Calories": food["calories"],
                    "Protein": food["protein"],
                    "Carbs": food["carbs"],
                    "Fat": food["fat"]
                })
    return plan

# ================== STREAMLIT APP ==================
st.set_page_config(page_title="Health & Diet App", layout="wide")

# Session state init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ---------------- Login/Register ----------------
st.title("🏥 Health & Diet Tracker")

if not st.session_state.logged_in:
    choice = st.radio("Login / Register", ["Login", "Register"])

    if choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            users = load_users()
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_data = users[username]
                st.success(f"Welcome back, {username}!")
            else:
                st.error("Invalid username or password")

    else:  # Register
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        if st.button("Register"):
            users = load_users()
            if username in users:
                st.error("Username already exists")
            else:
                users[username] = {"password": password, "diet_tracking": [], "diet_recommendations": []}
                save_users(users)
                st.success("Account created! Please login.")
else:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Tabs
    tabs = st.tabs(["🏠 Home", "🥗 Diet Tracking", "📊 Reports", "🍎 Diet Recommendations"])

    # ---------------- Home ----------------
    with tabs[0]:
        st.header("Welcome to Your Health Tracker!")
        st.write("Use the tabs to track your meals, view reports, and generate diet plans.")

    # ---------------- Diet Tracking ----------------
    with tabs[1]:
        st.header("🥗 Diet Tracking")

        food_query = st.text_input("Search food (via USDA Database)")
        if food_query and st.button("🔍 Search Food"):
            results = search_usda_food(food_query, page_size=5)
            if results:
                for food in results:
                    if st.button(f"Add {food['name']} ({food['calories']} kcal)"):
                        st.session_state.user_data["diet_tracking"].append({
                            "meal": food["name"],
                            "calories": food["calories"],
                            "protein": food["protein"],
                            "carbs": food["carbs"],
                            "fat": food["fat"],
                            "time": str(datetime.now())
                        })
                        save_user_data(st.session_state.username, st.session_state.user_data)
                        st.success(f"{food['name']} added!")
            else:
                st.warning("No results from USDA.")

        st.subheader("Manual Entry")
        meal = st.text_input("Meal Name")
        calories = st.number_input("Calories", min_value=0)
        protein = st.number_input("Protein (g)", min_value=0)
        carbs = st.number_input("Carbs (g)", min_value=0)
        fat = st.number_input("Fat (g)", min_value=0)
        if st.button("Add Meal Manually"):
            st.session_state.user_data["diet_tracking"].append({
                "meal": meal,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.success("Meal added manually!")

        if st.session_state.user_data["diet_tracking"]:
            st.subheader("Tracked Meals")
            df_meals = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.dataframe(df_meals)

    # ---------------- Reports ----------------
    with tabs[2]:
        st.header("📊 Reports")

        if st.session_state.user_data["diet_tracking"]:
            df = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.write("### Nutrition Summary")
            st.write(df.describe())

            st.write("### Calories Over Time")
            df["time"] = pd.to_datetime(df["time"])
            st.line_chart(df.set_index("time")["calories"])
        else:
            st.info("No meals logged yet!")

    # ---------------- Diet Recommendations ----------------
    with tabs[3]:
        st.header("🍎 Diet Recommendations (USDA)")

        diet_choice = st.radio("Choose your diet goal:", ["Balanced", "Low-Carb", "High-Protein"])
        if st.button("Generate USDA Diet Plan"):
            plan = generate_usda_diet_plan(diet_choice)
            if plan:
                df_plan = pd.DataFrame(plan)
                st.session_state.user_data["diet_recommendations"].append({
                    "goal": diet_choice,
                    "plan": plan,
                    "time": str(datetime.now())
                })
                save_user_data(st.session_state.username, st.session_state.user_data)
                st.success("✅ USDA diet plan generated!")
                st.dataframe(df_plan)

                csv = df_plan.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Diet Plan (CSV)", csv, "usda_diet_plan.csv", "text/csv")
            else:
                st.error("⚠️ Could not generate plan from USDA API.")
