import streamlit as st
import pandas as pd
import os
import plotly.express as px
import random
from datetime import datetime

# ------------------------
# Page Config
# ------------------------
st.set_page_config(
    page_title="MySugr Improved",
    page_icon="💉",
    layout="wide"
)

# ------------------------
# User Authentication Utils
# ------------------------
USER_FILE = "users.csv"

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False  # User already exists
    users = pd.concat([users, pd.DataFrame([[username, password]], columns=["username", "password"])], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

def check_login(username, password):
    users = load_users()
    match = users[(users["username"] == username) & (users["password"] == password)]
    return not match.empty

# ------------------------
# Session State Init
# ------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# ------------------------
# Login / Signup Pages
# ------------------------
if not st.session_state.logged_in:
    st.title("🔐 Welcome to MySugr Improved")

    auth_choice = st.radio("Select Action", ["Login", "Sign Up"], key="auth_choice")

    if auth_choice == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    else:  # Signup
        st.subheader("Create a new account")
        new_username = st.text_input("Choose a username", key="signup_username")
        new_password = st.text_input("Choose a password", type="password", key="signup_password")
        if st.button("Sign Up", key="signup_button"):
            if save_user(new_username, new_password):
                st.success("🎉 Account created! Please log in.")
            else:
                st.error("⚠️ Username already exists. Try a different one.")

    st.stop()

# ------------------------
# If logged in → Continue App
# ------------------------
if st.sidebar.button("Logout", key="logout_button_sidebar"):
    st.session_state.clear()
    st.session_state["logged_in"] = False
    st.experimental_rerun()

# ------------------------
# Tabs Layout (ONLY ONCE)
# ------------------------
tabs = st.tabs([
    "📊 Dashboard",
    "🥗 Diet Tracking",
    "💉 Insulin Recommendations",
    "🍎 Diet Recommendations"
])

# -------------------------
# Dashboard Tab
# -------------------------
with tabs[0]:
    st.header("📊 Dashboard")
    uploaded_file = st.file_uploader("📂 Upload your CSV file", type="csv", key="dashboard_file_uploader")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.lower()

            if "date" in df.columns and "time" in df.columns:
                df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
            elif "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            else:
                st.error("❌ No 'datetime' column found.")
                st.stop()

            st.success("✅ File uploaded successfully!")
            st.dataframe(df.head())

            if "blood sugar measurement (mg/dl)" in df.columns:
                fig = px.line(df, x="datetime", y="blood sugar measurement (mg/dl)", title="Blood Sugar Over Time")
                st.plotly_chart(fig, use_container_width=True)

            insulin_cols = [col for col in df.columns if "insulin" in col]
            if insulin_cols:
                for col in insulin_cols:
                    fig = px.line(df, x="datetime", y=col, title=f"{col.title()} Over Time")
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    else:
        st.info("Upload a CSV file to see your dashboard.")

# -------------------------
# Diet Tracking Tab
# -------------------------
with tabs[1]:
    st.header("🥗 Diet Tracking")
    st.write("Keep track of whether you followed your diet plan today.")
    col1, col2 = st.columns([1, 2])
    with col1:
        diet_followed = st.checkbox("✅ Did you follow your diet today?", key="diet_followed_checkbox")
    with col2:
        if not diet_followed:
            st.text_input("❌ If not, what did you eat instead?", key="diet_not_followed_input")

# -------------------------
# Insulin Recommendation Tab
# -------------------------
with tabs[2]:
    st.header("💉 Insulin Assistant")
    st.markdown("This tool helps you calculate your **meal-time insulin dose** based on your carbs and blood sugar levels.")

    col1, col2 = st.columns(2)
    with col1:
        carbs = st.number_input("🍞 Carbs in your meal (grams)", min_value=0, max_value=200, value=50, key="carbs_input")
        carb_ratio = st.number_input("⚖️ Insulin-to-Carb Ratio (g/unit)", min_value=1, max_value=30, value=10, key="carb_ratio_input")
    with col2:
        glucose = st.number_input("🩸 Current Blood Sugar (mg/dL)", min_value=50, max_value=400, value=150, key="glucose_input")
        correction_factor = st.number_input("🔧 Correction Factor (mg/dL per unit)", min_value=10, max_value=100, value=50, key="correction_factor_input")

    target_glucose = st.number_input("🎯 Target Blood Sugar (mg/dL)", min_value=80, max_value=150, value=110, key="target_glucose_input")

    carb_insulin = carbs / carb_ratio if carb_ratio else 0
    correction_insulin = max((glucose - target_glucose) / correction_factor, 0) if correction_factor else 0
    total_dose = round(carb_insulin + correction_insulin, 1)

    st.subheader("📊 Insulin Dose Recommendation")
    st.metric("Carb Coverage", f"{carb_insulin:.1f} units", key="carb_metric")
    st.metric("Correction Dose", f"{correction_insulin:.1f} units", key="correction_metric")
    st.metric("✅ Total Recommended Dose", f"{total_dose:.1f} units", key="total_metric")

    st.markdown("### 📉 Dose Breakdown")
    st.progress(min(int((total_dose/20)*100), 100))
    st.bar_chart(pd.DataFrame({"Insulin Units": [carb_insulin, correction_insulin]}, index=["Carb Coverage", "Correction"]))

    st.markdown("💡 **Note:** This is a helper tool, not medical advice. Always confirm with your doctor before making insulin adjustments.")

# -------------------------
# Diet Recommendation Tab
# -------------------------
with tabs[3]:
    st.header("🍎 Diet Recommendations")
    st.write("Get personalized diet suggestions and track meal satisfaction.")

    meals = [
        "Grilled chicken with quinoa and vegetables",
        "Salmon with brown rice and steamed broccoli",
        "Tofu stir-fry with mixed veggies",
        "Lentil soup with whole-grain bread",
        "Egg omelet with spinach and avocado"
    ]
    suggestion = random.choice(meals)
    st.subheader("👉 Today's Meal Suggestion:")
    st.success(suggestion)

    # Per-user diet history file
    csv_file = f"diet_history_{st.session_state['username']}.csv"

    # Load existing history
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=["meal", "rating", "notes", "timestamp"])

    st.markdown("### 📝 Rate Your Meal")
    meal_choice = st.text_input("Meal you ate", value=suggestion, key="meal_choice_input")
    rating = st.slider("How satisfied are you with your meal?", 1, 5, 3, key="meal_rating_slider")
    notes = st.text_area("Additional notes", key="meal_notes_area")

    if st.button("Save Feedback", key="save_feedback_button"):
        new_entry = {
            "meal": meal_choice,
            "rating": rating,
            "notes": notes,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(csv_file, index=False)
        st.success("✅ Feedback saved!")

    if not df.empty:
        st.markdown("### 📖 Meal History")
        st.dataframe(df.tail(10))
