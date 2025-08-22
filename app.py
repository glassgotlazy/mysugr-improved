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

# ----------------------
# Meals categorized with nutrition (extended with more options)
import random
import streamlit as st

# ✅ Define days at top-level (no indent!)
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ✅ Define meals at top-level (no indent!)
meals = {
    "Breakfast": [
        {"name": "Oatmeal with Fruits",
         "img": "https://www.eatingwell.com/thmb/Q8N0K9j5Uv81f5q1mTtPizBVKpY=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/oatmeal-with-fruits-2000-5c9bb6b3c9e77c0001a6b3dd.jpg",
         "nutrition": {"Calories": 250, "Protein": 8, "Carbs": 45, "Fat": 5}},
        {"name": "Avocado Toast",
         "img": "https://cookieandkate.com/images/2012/08/best-avocado-toast-recipe-1-2.jpg",
         "nutrition": {"Calories": 300, "Protein": 10, "Carbs": 30, "Fat": 12}},
        {"name": "Smoothie Bowl",
         "img": "https://minimalistbaker.com/wp-content/uploads/2017/07/HEALTHY-Smoothie-Bowl-8-ingredients-10-minutes-healthy-fruits-nuts-vegan-glutenfree-plantbased-smoothiebowl-recipe-minimalistbaker-5.jpg",
         "nutrition": {"Calories": 280, "Protein": 9, "Carbs": 40, "Fat": 7}},
        {"name": "Idli with Sambar",
         "img": "https://www.cookwithmanali.com/wp-content/uploads/2021/07/Idli-Sambar.jpg",
         "nutrition": {"Calories": 320, "Protein": 11, "Carbs": 55, "Fat": 6}},
        {"name": "Vegetable Upma",
         "img": "https://www.indianhealthyrecipes.com/wp-content/uploads/2019/08/upma-recipe-500x500.jpg",
         "nutrition": {"Calories": 280, "Protein": 8, "Carbs": 48, "Fat": 7}},
    ],
    # ... keep the rest of the categories (Lunch, Dinner, Snack)
}
7}},
    ],
    "Lunch": [
        {"name": "Grilled Chicken Salad",
         "img": "https://www.cookingclassy.com/wp-content/uploads/2020/01/grilled-chicken-salad-21.jpg",
         "nutrition": {"Calories": 400, "Protein": 35, "Carbs": 20, "Fat": 15}},
        {"name": "Quinoa Bowl",
         "img": "https://simpleveganblog.com/wp-content/uploads/2020/09/Quinoa-buddha-bowl-4.jpg",
         "nutrition": {"Calories": 420, "Protein": 18, "Carbs": 55, "Fat": 12}},
        {"name": "Paneer Tikka Bowl",
         "img": "https://www.vegrecipesofindia.com/wp-content/uploads/2021/04/paneer-tikka-1.jpg",
         "nutrition": {"Calories": 450, "Protein": 25, "Carbs": 30, "Fat": 20}},
        {"name": "Rajma Chawal",
         "img": "https://www.secondrecipe.com/wp-content/uploads/2021/01/rajma-chawal.jpg",
         "nutrition": {"Calories": 480, "Protein": 18, "Carbs": 70, "Fat": 12}},
    ],
    "Dinner": [
        {"name": "Baked Salmon with Veggies",
         "img": "https://www.healthyseasonalrecipes.com/wp-content/uploads/2021/03/baked-salmon-013.jpg",
         "nutrition": {"Calories": 500, "Protein": 40, "Carbs": 25, "Fat": 22}},
        {"name": "Veggie Stir Fry",
         "img": "https://www.acouplecooks.com/wp-content/uploads/2020/02/Veggie-Stir-Fry-009.jpg",
         "nutrition": {"Calories": 350, "Protein": 12, "Carbs": 50, "Fat": 10}},
        {"name": "Dal with Brown Rice",
         "img": "https://www.indianhealthyrecipes.com/wp-content/uploads/2021/08/dal-tadka-recipe.jpg",
         "nutrition": {"Calories": 420, "Protein": 15, "Carbs": 65, "Fat": 8}},
        {"name": "Grilled Paneer with Veggies",
         "img": "https://www.funfoodfrolic.com/wp-content/uploads/2021/03/Grilled-Paneer-Tikka-Thumbnail.jpg",
         "nutrition": {"Calories": 460, "Protein": 30, "Carbs": 28, "Fat": 18}},
    ],
    "Snack": [
        {"name": "Greek Yogurt with Honey",
         "img": "https://www.cookingclassy.com/wp-content/uploads/2015/05/greek-yogurt-honey-walnuts-breakfast2-srgb..jpg",
         "nutrition": {"Calories": 180, "Protein": 12, "Carbs": 20, "Fat": 4}},
        {"name": "Mixed Nuts",
         "img": "https://www.heart.org/-/media/Images/News/2021/September-2021/0929MixedNuts_SC.jpg",
         "nutrition": {"Calories": 200, "Protein": 6, "Carbs": 8, "Fat": 18}},
        {"name": "Fruit Bowl",
         "img": "https://www.acouplecooks.com/wp-content/uploads/2021/05/Fruit-Salad-007.jpg",
         "nutrition": {"Calories": 150, "Protein": 3, "Carbs": 38, "Fat": 1}},
        {"name": "Sprout Salad",
         "img": "https://www.cookwithmanali.com/wp-content/uploads/2020/08/Moong-Sprouts-Salad.jpg",
         "nutrition": {"Calories": 160, "Protein": 10, "Carbs": 25, "Fat": 2}},
    ]
}



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
