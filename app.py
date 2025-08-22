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

# ----------------------
# 💉 Insulin Recommendation Tab
# ----------------------
with tabs[1]:
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


import streamlit as st
import random
import pandas as pd
from datetime import datetime

# ----------------------
import random
import streamlit as st
import pandas as pd

# ----------------------
# Meals categorized with nutrition
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
    ],
    "Lunch": [
        {"name": "Grilled Chicken Salad",
         "img": "https://www.cookingclassy.com/wp-content/uploads/2020/01/grilled-chicken-salad-21.jpg",
         "nutrition": {"Calories": 400, "Protein": 35, "Carbs": 20, "Fat": 15}},
        {"name": "Quinoa Bowl",
         "img": "https://simpleveganblog.com/wp-content/uploads/2020/09/Quinoa-buddha-bowl-4.jpg",
         "nutrition": {"Calories": 420, "Protein": 18, "Carbs": 55, "Fat": 12}},
    ],
    "Dinner": [
        {"name": "Baked Salmon with Veggies",
         "img": "https://www.healthyseasonalrecipes.com/wp-content/uploads/2021/03/baked-salmon-013.jpg",
         "nutrition": {"Calories": 500, "Protein": 40, "Carbs": 25, "Fat": 22}},
        {"name": "Veggie Stir Fry",
         "img": "https://www.acouplecooks.com/wp-content/uploads/2020/02/Veggie-Stir-Fry-009.jpg",
         "nutrition": {"Calories": 350, "Protein": 12, "Carbs": 50, "Fat": 10}},
    ],
    "Snack": [
        {"name": "Greek Yogurt with Honey",
         "img": "https://www.cookingclassy.com/wp-content/uploads/2015/05/greek-yogurt-honey-walnuts-breakfast2-srgb..jpg",
         "nutrition": {"Calories": 180, "Protein": 12, "Carbs": 20, "Fat": 4}},
        {"name": "Mixed Nuts",
         "img": "https://www.heart.org/-/media/Images/News/2021/September-2021/0929MixedNuts_SC.jpg",
         "nutrition": {"Calories": 200, "Protein": 6, "Carbs": 8, "Fat": 18}},
    ]
}

days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
categories = ["Breakfast", "Lunch", "Dinner", "Snack"]

# Rotate through meals once
if "weekly_meals" not in st.session_state:
    st.session_state.weekly_meals = {}
    for i, day in enumerate(days):
        category = categories[i % len(categories)]
        st.session_state.weekly_meals[day] = random.choice(meals[category])

# ----------------------
# Tabs for Diet
# ----------------------
diet_tabs = st.tabs(["🥗 Diet Plan", "📊 History"])

# ----------------------
# Diet Plan Tab
# ----------------------
with diet_tabs[0]:
    st.title("🍽️ Auto-Balanced Weekly Diet Plan")

    # Track weekly totals
    weekly_totals = {"Calories": 0, "Protein": 0, "Carbs": 0, "Fat": 0}

    for day in days:
        meal = st.session_state.weekly_meals[day]
        st.markdown(f"### 📅 {day}")
        cols = st.columns([1, 2])  # Smaller image on left, details on right

        with cols[0]:
            st.image(meal["img"], caption=meal["name"], width=150)

        with cols[1]:
            st.subheader(meal["name"])
            st.markdown("**📊 Nutrition Breakdown:**")
            sub_cols = st.columns(4)
            for i, (k, v) in enumerate(meal["nutrition"].items()):
                sub_cols[i].metric(k, f"{v}{'g' if k!='Calories' else ''}")
                weekly_totals[k] += v

            # Replace option
            if st.button(f"🔄 Change {day}", key=f"change_{day}"):
                for cat, meal_list in meals.items():
                    if meal in meal_list:
                        st.session_state.weekly_meals[day] = random.choice(meal_list)
                st.rerun()

            # Rating + Notes
            st.slider(f"⭐ Rate {meal['name']}", 1, 5, 3, key=f"rating_{day}")
            st.text_area(f"📝 Notes for {meal['name']}", key=f"note_{day}")

        st.write("---")

    # 📊 Weekly Summary
    st.subheader("📅 Weekly Nutrition Summary")
    summary_cols = st.columns(4)
    for i, (k, v) in enumerate(weekly_totals.items()):
        summary_cols[i].metric(k, f"{v}{'g' if k!='Calories' else ''}")

# ----------------------
# History Tab
# ----------------------
with diet_tabs[1]:
    st.header("📊 Your Meal Rating History")
    try:
        df = pd.read_csv("diet_history.csv")
        st.dataframe(df)
        avg_ratings = df.groupby("meal")["rating"].mean().sort_values(ascending=False)
        st.bar_chart(avg_ratings)
    except FileNotFoundError:
        st.info("No ratings saved yet. Start rating meals to build your history!")



import streamlit as st
import pandas as pd
import random
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------
import pandas as pd
import streamlit as st

# ----------------------
# Export function (Excel with CSV fallback)
# ----------------------
def export_excel(df, doctor_name):
    safe_name = doctor_name.strip().replace(" ", "_")
    filename = f"{safe_name}_diet_plan.xlsx"
    try:
        df.to_excel(filename, index=False, engine="openpyxl")
    except ImportError:
        # Fallback to CSV if openpyxl not installed
        filename = f"{safe_name}_diet_plan.csv"
        df.to_csv(filename, index=False)
    return filename


# ----------------------
# Inside your Diet Tab (at the end after weekly summary)
# ----------------------
# Convert weekly diet plan into a DataFrame
diet_data = []
for day, meal in st.session_state.weekly_meals.items():
    row = {
        "Day": day,
        "Meal": meal["name"],
        "Calories": meal["nutrition"]["Calories"],
        "Protein (g)": meal["nutrition"]["Protein"],
        "Carbs (g)": meal["nutrition"]["Carbs"],
        "Fat (g)": meal["nutrition"]["Fat"]
    }
    diet_data.append(row)

df = pd.DataFrame(diet_data)

st.markdown("### 📥 Download Your Weekly Diet Plan")
doctor_name = st.text_input("Enter your name (for the file name):", "MyDiet")

if st.button("Generate Diet Report"):
    file = export_excel(df, doctor_name)
    with open(file, "rb") as f:
        st.download_button(
            label="⬇️ Download Diet Report",
            data=f,
            file_name=file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file.endswith("xlsx") else "text/csv"
        )

        st.info("No ratings saved yet. Start rating meals to build your history!")
