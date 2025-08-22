import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime

# -------------------------
# Page Config
# -------------------------
st.set_page_config(
    page_title="MySugar Advanced",
    page_icon="💉",
    layout="wide"
)

st.title("🩸 MySugar - Diabetes Tracking Dashboard")

# -------------------------
# Tabs
# -------------------------
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

    uploaded_file = st.file_uploader("📂 Upload your CSV file", type="csv")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)

            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()

            # Merge date & time into datetime if available
            if "date" in df.columns and "time" in df.columns:
                df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
            elif "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            else:
                st.error("❌ No 'datetime' column found.")
                st.stop()

            # Show preview
            st.success("✅ File uploaded successfully!")
            st.dataframe(df.head())

            # Line chart for Blood Sugar
            if "blood sugar measurement (mg/dl)" in df.columns:
                fig = px.line(df, x="datetime", y="blood sugar measurement (mg/dl)", title="Blood Sugar Over Time")
                st.plotly_chart(fig, use_container_width=True)

            # Line chart for Insulin
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
        diet_followed = st.checkbox("✅ Did you follow your diet today?")

    with col2:
        if not diet_followed:
            st.text_input("❌ If not, what did you eat instead?")

# -------------------------
# 💉 Insulin Recommendation Tab
# -------------------------
with tabs[2]:
    st.header("💉 Insulin Assistant")

    st.markdown("This tool helps you calculate your **meal-time insulin dose** based on your carbs and blood sugar levels.")

    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        carbs = st.number_input("🍞 Carbs in your meal (grams)", min_value=0, max_value=200, value=50)
        carb_ratio = st.number_input("⚖️ Insulin-to-Carb Ratio (g/unit)", min_value=1, max_value=30, value=10)
    with col2:
        glucose = st.number_input("🩸 Current Blood Sugar (mg/dL)", min_value=50, max_value=400, value=150)
        correction_factor = st.number_input("🔧 Correction Factor (mg/dL per unit)", min_value=10, max_value=100, value=50)

    target_glucose = st.number_input("🎯 Target Blood Sugar (mg/dL)", min_value=80, max_value=150, value=110)

    # Calculations
    carb_insulin = carbs / carb_ratio if carb_ratio else 0
    correction_insulin = max((glucose - target_glucose) / correction_factor, 0) if correction_factor else 0
    total_dose = round(carb_insulin + correction_insulin, 1)

    # Results
    st.subheader("📊 Insulin Dose Recommendation")
    st.metric("Carb Coverage", f"{carb_insulin:.1f} units")
    st.metric("Correction Dose", f"{correction_insulin:.1f} units")
    st.metric("✅ Total Recommended Dose", f"{total_dose:.1f} units")

    # Visualization
    st.markdown("### 📉 Dose Breakdown")
    st.progress(min(int((total_dose/20)*100), 100))  # progress bar out of 20 units
    st.bar_chart(
        pd.DataFrame(
            {"Insulin Units": [carb_insulin, correction_insulin]},
            index=["Carb Coverage", "Correction"]
        )
    )

    # Notes
    st.markdown("💡 **Note:** This is a helper tool, not medical advice. Always confirm with your doctor before making insulin adjustments.")

# -------------------------
# 🍎 Diet Recommendations Tab
# -------------------------
with tabs[3]:
    st.header("🍎 Diet Recommendations")

    # Meals data
    meals = {
        "Breakfast": [
            {"name": "Oatmeal with Fruits", "nutrition": {"Calories": 250, "Protein": 8, "Carbs": 45, "Fat": 5}},
            {"name": "Avocado Toast", "nutrition": {"Calories": 300, "Protein": 10, "Carbs": 30, "Fat": 12}},
        ],
        "Lunch": [
            {"name": "Grilled Chicken Salad", "nutrition": {"Calories": 400, "Protein": 35, "Carbs": 20, "Fat": 15}},
            {"name": "Quinoa Bowl", "nutrition": {"Calories": 420, "Protein": 18, "Carbs": 55, "Fat": 12}},
        ],
        "Dinner": [
            {"name": "Baked Salmon with Veggies", "nutrition": {"Calories": 500, "Protein": 40, "Carbs": 25, "Fat": 22}},
            {"name": "Veggie Stir Fry", "nutrition": {"Calories": 350, "Protein": 12, "Carbs": 50, "Fat": 10}},
        ],
    }

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if "weekly_meals" not in st.session_state:
        st.session_state.weekly_meals = {}
        for i, day in enumerate(days):
            category = list(meals.keys())[i % len(meals)]
            st.session_state.weekly_meals[day] = random.choice(meals[category])

    # Weekly Plan
    st.subheader("🍽️ Auto-Balanced Weekly Diet Plan")
    weekly_totals = {"Calories": 0, "Protein": 0, "Carbs": 0, "Fat": 0}

    for day in days:
        meal = st.session_state.weekly_meals[day]
        st.markdown(f"### 📅 {day}")
        st.write(meal["name"])
        for k, v in meal["nutrition"].items():
            st.write(f"- {k}: {v}")
            weekly_totals[k] += v
        st.write("---")

    # Weekly Summary
    st.subheader("📅 Weekly Nutrition Summary")
    st.json(weekly_totals)
