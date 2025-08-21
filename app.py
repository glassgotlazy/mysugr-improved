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

import streamlit as st
import pandas as pd
import plotly.express as px
import random

# ----------------------------
# Sample Diet Plans
# ----------------------------
diet_plans = {
    "Breakfast": [
        {"name": "Oats with Fruits", "image": "https://source.unsplash.com/400x300/?oats,fruits",
         "description": "High fiber breakfast with fresh fruits.",
         "nutrition": {"calories": 250, "carbs": 45, "protein": 8, "fat": 5}},
        {"name": "Vegetable Omelette", "image": "https://source.unsplash.com/400x300/?omelette",
         "description": "Egg omelette with spinach and vegetables.",
         "nutrition": {"calories": 200, "carbs": 3, "protein": 14, "fat": 12}},
        {"name": "Smoothie Bowl", "image": "https://source.unsplash.com/400x300/?smoothie",
         "description": "Mixed fruit smoothie bowl with nuts.",
         "nutrition": {"calories": 300, "carbs": 50, "protein": 10, "fat": 7}},
    ],
    "Lunch": [
        {"name": "Grilled Chicken Salad", "image": "https://source.unsplash.com/400x300/?chicken,salad",
         "description": "Lean protein with fresh veggies.",
         "nutrition": {"calories": 350, "carbs": 12, "protein": 30, "fat": 10}},
        {"name": "Quinoa Bowl", "image": "https://source.unsplash.com/400x300/?quinoa",
         "description": "Healthy quinoa with vegetables and beans.",
         "nutrition": {"calories": 400, "carbs": 60, "protein": 15, "fat": 8}},
    ],
    "Dinner": [
        {"name": "Grilled Salmon", "image": "https://source.unsplash.com/400x300/?salmon",
         "description": "Omega-3 rich salmon with veggies.",
         "nutrition": {"calories": 450, "carbs": 10, "protein": 35, "fat": 20}},
        {"name": "Vegetable Stir Fry", "image": "https://source.unsplash.com/400x300/?vegetable,stirfry",
         "description": "Mixed veggies stir fried with tofu.",
         "nutrition": {"calories": 300, "carbs": 40, "protein": 12, "fat": 8}},
    ],
    "Snacks": [
        {"name": "Greek Yogurt with Berries", "image": "https://source.unsplash.com/400x300/?yogurt,berries",
         "description": "Low-fat yogurt with fresh berries.",
         "nutrition": {"calories": 180, "carbs": 20, "protein": 12, "fat": 4}},
        {"name": "Nuts Mix", "image": "https://source.unsplash.com/400x300/?nuts",
         "description": "Healthy fats and proteins from nuts.",
         "nutrition": {"calories": 220, "carbs": 8, "protein": 6, "fat": 18}},
    ]
}

weekly_totals = {"Calories": 0, "Carbs": 0, "Protein": 0, "Fat": 0}

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="MySugar Dashboard", layout="wide")

st.title("🩸 MySugar Advanced Dashboard")

uploaded_file = st.sidebar.file_uploader("📤 Upload your blood sugar CSV", type=["csv"])

tabs = st.tabs(["📊 Dashboard", "💉 Insulin Recommendation", "🍽️ Diet Recommendation", "📈 Weekly Nutrition"])

# ----------------------------
# Dashboard Tab
# ----------------------------
with tabs[0]:
    st.header("📊 Blood Sugar & Insulin Data")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)

            # Normalize columns
            df.columns = [c.strip().lower() for c in df.columns]

            if "date" in df.columns and "time" in df.columns:
                df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
            elif "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            else:
                st.error("❌ No valid datetime column found.")
                st.stop()

            df = df.rename(columns={
                "blood sugar measurement (mg/dl)": "blood_sugar",
                "insulin injection units (pen)": "insulin"
            })

            st.dataframe(df.head())

            # Plot blood sugar
            fig = px.line(df, x="datetime", y="blood_sugar", title="📈 Blood Sugar Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)

            # Plot insulin
            if "insulin" in df.columns:
                fig2 = px.bar(df, x="datetime", y="insulin", title="💉 Insulin Taken")
                st.plotly_chart(fig2, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    else:
        st.info("📂 Please upload a CSV file to view your dashboard.")

# ----------------------------
# Insulin Recommendation Tab
# ----------------------------
with tabs[1]:
    st.header("💉 Insulin Recommendation System")

    sugar_level = st.number_input("Enter your current blood sugar level (mg/dL):", min_value=50, max_value=400, value=120)
    carbs = st.number_input("Enter carbohydrate intake (grams):", min_value=0, max_value=200, value=50)

    if st.button("🔍 Get Insulin Suggestion"):
        if sugar_level > 180:
            suggestion = "⚠️ High blood sugar detected. Consider correction dose."
        elif sugar_level < 70:
            suggestion = "⚠️ Low blood sugar! Please take glucose immediately."
        else:
            suggestion = "✅ Blood sugar normal. Take insulin as per carb intake."
        
        st.success(suggestion)
        st.info(f"💡 Suggested insulin units: {round(carbs / 15, 1)} (based on carb ratio 1:15)")

# ----------------------------
# Diet Recommendation Tab
# ----------------------------
with tabs[2]:
    st.header("🍽️ Personalized Diet Recommendation")

    categories = list(diet_plans.keys())
    selected_category = st.selectbox("Choose a meal type", categories)

    if selected_category:
        meals = diet_plans[selected_category]
        meal = random.choice(meals)

        st.subheader(f"Recommended {selected_category}: {meal['name']}")

        cols = st.columns(2)

        with cols[0]:
            st.image(meal["image"], use_container_width=True)

        with cols[1]:
            st.write(meal["description"])
            st.markdown("**Nutritional Info:**")

            cols2 = st.columns(4)
            for i, (k, v) in enumerate(meal["nutrition"].items()):
                key = k.capitalize()
                if key not in weekly_totals:
                    weekly_totals[key] = 0
                try:
                    val = float(v)
                except Exception:
                    val = 0
                cols2[i % 4].metric(key, f"{val}{'g' if key != 'Calories' else ''}")
                weekly_totals[key] += val

        st.markdown("---")
        st.markdown("### ⭐ Rate this Meal")
        rating = st.radio("How do you like this meal?", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], horizontal=True)

        st.markdown("### 💬 Feedback")
        feedback = st.text_area("Any comments or suggestions?")

# ----------------------------
# Weekly Nutrition Tracking
# ----------------------------
with tabs[3]:
    st.header("📈 Weekly Nutrition Overview")

    weekly_df = pd.DataFrame([weekly_totals])
    st.bar_chart(weekly_df.T)


import streamlit as st
import pandas as pd
import random
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------
# Export Helper: Excel
# ----------------------
def export_excel(df, doctor_name):
    filename = f"diet_history_{doctor_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    df.to_excel(filename, index=False)
    return filename

# ----------------------
# Export Helper: PDF
# ----------------------
def export_pdf(df, doctor_name):
    filename = f"diet_history_{doctor_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Diet History Report - Dr. {doctor_name}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Convert dataframe to table
    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(table)

    doc.build(elements)
    return filename

# ----------------------
# Diet History Tab (updated)
# ----------------------
with diet_tabs[-1]:
    st.markdown("### 📊 Your Meal Rating History")

    doctor_name = st.text_input("👨‍⚕️ Enter your Doctor’s Name")

    try:
        df = pd.read_csv("diet_history.csv")
        st.dataframe(df)

        avg_ratings = df.groupby("meal")["rating"].mean().sort_values(ascending=False)
        st.bar_chart(avg_ratings)

        if doctor_name.strip():
            st.markdown("### 📂 Export Options")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📥 Export to Excel"):
                    file = export_excel(df, doctor_name.strip().replace(" ", "_"))
                    st.success(f"✅ Excel file saved as {file}")

            with col2:
                if st.button("📄 Export to PDF"):
                    file = export_pdf(df, doctor_name.strip().replace(" ", "_"))
                    st.success(f"✅ PDF file saved as {file}")

        else:
            st.info("ℹ️ Please enter your Doctor’s name to enable exports.")

    except FileNotFoundError:
        st.info("No ratings saved yet. Start rating meals to build your history!")
