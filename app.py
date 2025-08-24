import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# ---------------- Utility ----------------
def save_user_data(username, data):
    """Dummy save function (replace with DB or file persistence if needed)."""
    pass


# ---------------- USDA Integration ----------------
USDA_API_KEY = st.secrets.get("USDA_API_KEY", "")

def fetch_usda_foods(query, page_size=5):
    """Fetch foods from USDA API."""
    if not USDA_API_KEY:
        return []
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": USDA_API_KEY, "query": query, "pageSize": page_size}
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("foods", [])
    except Exception:
        return []
    return []


def generate_usda_diet_plan(goal="Balanced"):
    """Generate a 7-day diet plan using USDA foods."""
    categories = {
        "Breakfast": ["oatmeal", "eggs", "yogurt"],
        "Lunch": ["chicken", "salad", "tofu"],
        "Dinner": ["fish", "turkey", "lentils"]
    }

    plan = []
    for day in range(1, 8):
        for meal, queries in categories.items():
            foods = []
            for q in queries:
                foods.extend(fetch_usda_foods(q, page_size=3))
            if foods:
                choice = random.choice(foods)
                plan.append({
                    "Day": f"Day {day}",
                    "Meal": meal,
                    "Food": choice.get("description", "Unknown"),
                    "Calories": choice.get("foodNutrients", [{}])[0].get("value", "N/A")
                })
    return plan


# ---------------- Login Page ----------------
def login():
    st.title("🔑 Login / Sign Up Page")
    username = st.text_input("Enter Username")
    if st.button("Login / Sign Up"):
        if username.strip():
            st.session_state.username = username
            if "user_data" not in st.session_state:
                st.session_state.user_data = {}
            st.success(f"Welcome {username}!")
            st.rerun()   # modern rerun


# ---------------- Main App ----------------
def main_app():
    st.markdown("*Made by ~Glass*", unsafe_allow_html=True)
    st.title("💉 MySugr Improved App")
    st.write(f"👋 Welcome, **{st.session_state.username}**")

    # Tabs
    tabs = st.tabs([
        "📊 Dashboard", 
        "🥗 Diet Tracking", 
        "💉 Advanced Insulin Assistant",
        "🍎 Diet Recommendations", 
        "📂 Data Upload", 
        "📈 Reports"
    ])

    # ---------------- Dashboard ----------------
    with tabs[0]:
        st.header("📊 Dashboard")
        st.metric("Total Meals Tracked", len(st.session_state.user_data.get("diet_tracking", [])))
        st.metric("Total Insulin Recs", len(st.session_state.user_data.get("insulin_recommendations", [])))

    # ---------------- Diet Tracking ----------------
    with tabs[1]:
        st.header("🥗 Diet Tracking")
        meal = st.text_input("Meal Name")
        calories = st.number_input("Calories", min_value=0)
        if st.button("Add Meal"):
            st.session_state.user_data.setdefault("diet_tracking", []).append({
                "meal": meal,
                "calories": calories,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)
            st.success("Meal added!")

        if st.session_state.user_data.get("diet_tracking"):
            st.subheader("Tracked Meals")
            df_meals = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.dataframe(df_meals)

    # ---------------- Advanced Insulin Assistant ----------------
    with tabs[2]:
        st.header("💉 Advanced Insulin Assistant")

        glucose = st.number_input("Current Glucose Level (mg/dL)", min_value=40, max_value=400, key="glucose_input")
        carbs = st.number_input("Carbohydrate Intake (grams)", min_value=0, key="carbs_input")
        sensitivity = st.slider("Insulin Sensitivity Factor", 10, 100, 50, key="sensitivity_input")

        if st.button("Calculate Insulin Dose", key="insulin_button"):
            recommended_dose = (glucose - 100) / sensitivity + (carbs / 10)
            recommended_dose = max(0, round(recommended_dose, 2))

            st.session_state.last_insulin_dose = recommended_dose  # ✅ persist result

            st.session_state.user_data.setdefault("insulin_recommendations", []).append({
                "glucose": glucose,
                "carbs": carbs,
                "dose": recommended_dose,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)

        if "last_insulin_dose" in st.session_state:
            st.success(f"💉 Recommended Insulin Dose: **{st.session_state.last_insulin_dose} units**")

    # ---------------- Diet Recommendations ----------------
    with tabs[3]:
        st.header("🍎 Diet Recommendations")

        # --- Custom API Upload Section ---
        st.subheader("📤 Get Recommendations from Your API")
        uploaded_file = st.file_uploader("Upload your diet data file (CSV/JSON)", type=["csv", "json"])
        if uploaded_file is not None:
            api_url = "http://localhost:8000/recommend"  # <-- replace with your API endpoint
            files = {"file": uploaded_file.getvalue()}
            try:
                response = requests.post(api_url, files=files, timeout=30)
                if response.status_code == 200:
                    rec_data = response.json()
                    st.success("✅ Received recommendations from your API!")
                    if isinstance(rec_data, dict):
                        st.json(rec_data)
                    else:
                        st.write(rec_data)
                else:
                    st.error(f"API error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"❌ Failed to contact API: {e}")

        st.divider()

        # --- USDA Diet Plan Section ---
        st.subheader("🍎 Generate USDA-Based Plan")
        goal = st.radio("Choose your diet goal:", ["Balanced", "Low-Carb", "High-Protein"], horizontal=True)

        if st.button("Generate 7-Day Plan from USDA"):
            plan = generate_usda_diet_plan(goal)
            if plan:
                df_plan = pd.DataFrame(plan)
                st.session_state.user_data.setdefault("diet_recommendations", []).append({
                    "goal": goal,
                    "plan": plan,
                    "time": datetime.now().isoformat(timespec="seconds")
                })
                save_user_data(st.session_state.username, st.session_state.user_data)
                st.success("✅ USDA diet plan generated!")
                st.dataframe(df_plan, use_container_width=True)

                csv = df_plan.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Diet Plan (CSV)", csv, "usda_diet_plan.csv", "text/csv")
            else:
                st.error("⚠️ Could not generate plan from USDA API.")

    # ---------------- Data Upload ----------------
    with tabs[4]:
        st.header("📂 Data Upload")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="general_upload")
        if uploaded_file:
            df_upload = pd.read_csv(uploaded_file)
            st.write("✅ Uploaded Data:")
            st.dataframe(df_upload)

            st.session_state.user_data.setdefault("uploads", []).append({
                "filename": uploaded_file.name,
                "data": df_upload.to_dict(),
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)

    # ---------------- Reports ----------------
    with tabs[5]:
        st.header("📈 Reports")

        if st.session_state.user_data.get("insulin_recommendations"):
            df_insulin = pd.DataFrame(st.session_state.user_data["insulin_recommendations"])
            st.subheader("Glucose Level Trends")
            st.line_chart(df_insulin["glucose"])

        if st.session_state.user_data.get("diet_tracking"):
            df_calories = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.subheader("Calorie Intake")
            st.bar_chart(df_calories["calories"])

    # ---------------- Logout ----------------
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()


# ---------------- Run App ----------------
def run_app():
    if "username" not in st.session_state:
        login()
    else:
        main_app()


if __name__ == "__main__":
    run_app()
