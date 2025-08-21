import streamlit as st
import pandas as pd
import plotly.express as px

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
# Insulin Recommendations Tab
# -------------------------
with tabs[2]:
    st.header("💉 Insulin Recommendations")
    st.write("AI-assisted insulin dose guidance based on your blood sugar levels.")

    try:
        blood_sugar = st.number_input("Enter current blood sugar (mg/dL)", min_value=50, max_value=500, step=1)
        carbs = st.number_input("Enter meal carbs (grams)", min_value=0, max_value=200, step=1)
        insulin_sensitivity = st.slider("Insulin Sensitivity Factor (mg/dL per unit)", 10, 100, 50)
        carb_ratio = st.slider("Carb Ratio (grams per unit insulin)", 5, 30, 15)

        if st.button("💉 Get Recommendation"):
            correction_dose = (blood_sugar - 120) / insulin_sensitivity if blood_sugar > 120 else 0
            meal_dose = carbs / carb_ratio
            total_dose = max(0, correction_dose + meal_dose)

            st.success(f"💉 Recommended insulin dose: **{total_dose:.1f} units**")
            st.info(f"- Correction Dose: {correction_dose:.1f}\n- Meal Dose: {meal_dose:.1f}")

    except Exception as e:
        st.error(f"❌ Error in insulin recommendation: {e}")

import random
import streamlit as st

import streamlit as st
import random

# ----------------------
# Categorized Meals Dataset
# ----------------------
meals = {
    "Breakfast": [
        {
            "title": "Oatmeal with Berries",
            "img": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "250 kcal", "Carbs": "45 g", "Protein": "8 g", "Fat": "5 g"}
        },
        {
            "title": "Avocado Toast",
            "img": "https://images.unsplash.com/photo-1559628233-3ae08c0cd88d?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "280 kcal", "Carbs": "30 g", "Protein": "8 g", "Fat": "12 g"}
        },
        {
            "title": "Veggie Omelette",
            "img": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "300 kcal", "Carbs": "5 g", "Protein": "20 g", "Fat": "22 g"}
        },
    ],
    "Lunch": [
        {
            "title": "Grilled Chicken Salad",
            "img": "https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "350 kcal", "Carbs": "20 g", "Protein": "40 g", "Fat": "10 g"}
        },
        {
            "title": "Turkey Sandwich",
            "img": "https://images.unsplash.com/photo-1565958011703-44e9f3f31ef3?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "320 kcal", "Carbs": "40 g", "Protein": "25 g", "Fat": "12 g"}
        },
        {
            "title": "Quinoa Bowl with Veggies",
            "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "370 kcal", "Carbs": "55 g", "Protein": "15 g", "Fat": "10 g"}
        },
    ],
    "Dinner": [
        {
            "title": "Salmon with Veggies",
            "img": "https://images.unsplash.com/photo-1516685018646-549d9c0a7a48?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "400 kcal", "Carbs": "15 g", "Protein": "35 g", "Fat": "18 g"}
        },
        {
            "title": "Brown Rice & Grilled Fish",
            "img": "https://images.unsplash.com/photo-1512058564366-c9e1d31714af?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "450 kcal", "Carbs": "50 g", "Protein": "32 g", "Fat": "15 g"}
        },
        {
            "title": "Tofu Stir Fry",
            "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "350 kcal", "Carbs": "30 g", "Protein": "22 g", "Fat": "15 g"}
        },
    ],
    "Snacks": [
        {
            "title": "Greek Yogurt with Nuts",
            "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "200 kcal", "Carbs": "15 g", "Protein": "12 g", "Fat": "8 g"}
        },
        {
            "title": "Fruit Smoothie",
            "img": "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "180 kcal", "Carbs": "42 g", "Protein": "5 g", "Fat": "2 g"}
        },
        {
            "title": "Lentil Soup",
            "img": "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?auto=format&fit=crop&w=800&q=80",
            "nutrition": {"Calories": "220 kcal", "Carbs": "35 g", "Protein": "14 g", "Fat": "4 g"}
        },
    ]
}

# ----------------------
# Diet Tab
# ----------------------
st.subheader("🍴 Diet Recommendations")

category_tabs = st.tabs(list(meals.keys()))

# Loop through categories
for idx, category in enumerate(meals.keys()):
    with category_tabs[idx]:
        st.markdown(f"### 🍽 {category} Ideas")

        # Random meal button
        if st.button(f"🎲 Random {category} Meal", key=f"random_{category}"):
            meal = random.choice(meals[category])
            st.subheader(meal["title"])
            st.image(meal["img"], caption=meal["title"], use_container_width=True)

            st.write("**Nutrition Info:**")
            st.table(meal["nutrition"])

        # Manual selection
        choice = st.selectbox(f"👉 Pick a {category} meal:", [m["title"] for m in meals[category]], key=f"choice_{category}")
        meal = next(m for m in meals[category] if m["title"] == choice)
        st.image(meal["img"], caption=meal["title"], use_container_width=True)

        st.write("**Nutrition Info:**")
        st.table(meal["nutrition"])

