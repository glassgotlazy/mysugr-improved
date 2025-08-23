import streamlit as st
import pandas as pd
import random
from datetime import datetime

# ---------------- Utility ----------------
def save_user_data(username, data):
    """Dummy save function (replace with real DB/file if needed)."""
    pass


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
            st.experimental_rerun()


# ---------------- Main App ----------------
def main_app():
    st.markdown("*Made by ~Glass*", unsafe_allow_html=True)
    st.title("💉 MySugr Improved App")
    st.write(f"👋 Welcome, **{st.session_state.username}**")

    # Tabs
    tabs = st.tabs([
        "📊 Dashboard", "🥗 Diet Tracking", "💉 Advanced Insulin Assistant",
        "🍎 Diet Recommendations", "📂 Data Upload", "📈 Reports"
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
        glucose = st.number_input("Current Glucose Level (mg/dL)", min_value=40, max_value=400)
        carbs = st.number_input("Carbohydrate Intake (grams)", min_value=0)
        sensitivity = st.slider("Insulin Sensitivity Factor", 10, 100, 50)

        if st.button("Calculate Insulin Dose"):
            recommended_dose = (glucose - 100) / sensitivity + (carbs / 10)
            recommended_dose = max(0, round(recommended_dose, 2))

            st.session_state.user_data.setdefault("insulin_recommendations", []).append({
                "glucose": glucose,
                "carbs": carbs,
                "dose": recommended_dose,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username, st.session_state.user_data)

            st.success(f"💉 Recommended Insulin Dose: **{recommended_dose} units**")

    # ---------------- Diet Recommendations ----------------
    with tabs[3]:
        st.header("🍎 Diet Recommendations")

        breakfast_options = ["Oatmeal with berries", "Scrambled eggs & spinach", "Greek yogurt with nuts"]
        lunch_options = ["Grilled chicken & quinoa", "Salmon salad", "Vegetable stir fry with tofu"]
        dinner_options = ["Grilled fish & sweet potato", "Turkey with veggies", "Lentil curry with rice"]

        diet_choice = st.radio("Choose your diet goal:", ["Balanced", "Low-Carb", "High-Protein"])

        if st.button("Generate Diet Plan"):
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

            st.success("✅ Diet plan generated!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Diet Plan (CSV)", csv, "diet_plan.csv", "text/csv")

        # History Viewer
        if st.session_state.user_data.get("diet_recommendations"):
            st.subheader("📜 Previous Diet Plans")
            for idx, record in enumerate(reversed(st.session_state.user_data["diet_recommendations"])): 
                st.markdown(
                    f"**Plan {len(st.session_state.user_data['diet_recommendations']) - idx}** "
                    f"({record.get('goal', 'N/A')}) - _{record.get('time', 'Unknown')}_"
                )

                plan_data = record.get("plan", [])
                if isinstance(plan_data, list) and len(plan_data) > 0:
                    df_hist = pd.DataFrame(plan_data)
                    st.dataframe(df_hist)
                else:
                    st.info("⚠️ This record has no valid plan data.")

    # ---------------- Data Upload ----------------
    with tabs[4]:
        st.header("📂 Data Upload")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
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
        st.experimental_rerun()


# ---------------- Run App ----------------
def run_app():
    if "username" not in st.session_state:
        login()  # ✅ first page (sign up/login) preserved
    else:
        main_app()


if __name__ == "__main__":
    run_app()
