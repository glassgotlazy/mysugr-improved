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
# ⚙️ Page Config
# ----------------------------
st.set_page_config(page_title="MySugr Improved", layout="wide")

# ----------------------------
# 📊 Sidebar: File Upload
# ----------------------------
st.sidebar.title("📂 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

# ----------------------------
# 🥗 Diet Plan Data
# ----------------------------
diet_plans = {
    "Breakfast": [
        {"name": "Oats with Fruits", "image": "https://i.imgur.com/8Kh7T4t.jpg",
         "description": "Fiber-rich oats with fresh fruits for stable sugar.",
         "nutrition": {"calories": 350, "carbs": 50, "protein": 10, "fat": 5}},
        {"name": "Vegetable Omelette", "image": "https://i.imgur.com/x5Z4o5Z.jpg",
         "description": "Egg omelette with spinach, onions, and tomatoes.",
         "nutrition": {"calories": 280, "carbs": 5, "protein": 18, "fat": 12}},
    ],
    "Lunch": [
        {"name": "Grilled Chicken Salad", "image": "https://i.imgur.com/n3f4uO3.jpg",
         "description": "High-protein chicken with green veggies.",
         "nutrition": {"calories": 400, "carbs": 15, "protein": 35, "fat": 10}},
        {"name": "Quinoa with Vegetables", "image": "https://i.imgur.com/4RkGZLQ.jpg",
         "description": "Nutritious quinoa with sauteed vegetables.",
         "nutrition": {"calories": 420, "carbs": 55, "protein": 15, "fat": 8}},
    ],
    "Dinner": [
        {"name": "Baked Salmon with Veggies", "image": "https://i.imgur.com/IwlL9Yf.jpg",
         "description": "Omega-3 rich salmon with steamed vegetables.",
         "nutrition": {"calories": 500, "carbs": 10, "protein": 40, "fat": 20}},
        {"name": "Tofu Stir Fry", "image": "https://i.imgur.com/BqZQ0oP.jpg",
         "description": "Plant protein tofu with colorful bell peppers.",
         "nutrition": {"calories": 350, "carbs": 20, "protein": 22, "fat": 12}},
    ]
}

weekly_totals = {}

# ----------------------------
# 🧾 Tabs Layout
# ----------------------------
tabs = st.tabs(["📊 Dashboard", "📈 Graphs", "🥗 Diet", "💉 Insulin Recommendation"])

# ----------------------------
# 📊 Dashboard Tab
# ----------------------------
with tabs[0]:
    st.header("📊 Dashboard Overview")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)

            # Ensure lowercase column names
            df.columns = [c.strip().lower() for c in df.columns]

            st.success("✅ File uploaded successfully!")
            st.write("### Preview of Data")
            st.dataframe(df.head())

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    else:
        st.info("Please upload a CSV file to view your data.")

# ----------------------------
# 📈 Graphs Tab
# ----------------------------
with tabs[1]:
    st.header("📈 Blood Sugar & Insulin Graphs")

    if uploaded_file:
        try:
            if "datetime" in df.columns and "blood sugar measurement (mg/dl)" in df.columns:
                fig = px.line(df, x="datetime", y="blood sugar measurement (mg/dl)",
                              title="Blood Sugar Over Time")
                st.plotly_chart(fig, use_container_width=True)

            if "datetime" in df.columns and "insulin" in df.columns:
                fig2 = px.line(df, x="datetime", y="insulin",
                               title="Insulin Usage Over Time")
                st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Error creating graphs: {e}")
    else:
        st.info("Upload a file to generate graphs.")

# ----------------------------
# 🥗 Diet Tab (Improved)
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

                cols2[i % 4].metric(
                    key, f"{val}{'g' if key != 'Calories' else ''}"
                )
                weekly_totals[key] += val

        st.markdown("---")
        st.markdown("### ⭐ Rate this Meal")
        rating = st.radio(
            "How do you like this meal?",
            ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            horizontal=True
        )

        st.markdown("### 💬 Feedback")
        feedback = st.text_area("Any comments or suggestions?")

# ----------------------------
# 💉 Insulin Recommendation Tab
# ----------------------------
with tabs[3]:
    st.header("💉 Insulin Recommendation System")

    current_sugar = st.number_input("Enter current blood sugar level (mg/dL):", min_value=50, max_value=400, value=120)
    carbs = st.number_input("Enter carbs intake (grams):", min_value=0, max_value=200, value=0)
    sensitivity = st.slider("Insulin Sensitivity Factor (mg/dL per unit)", 20, 100, 50)
    carb_ratio = st.slider("Carb Ratio (grams/unit)", 5, 30, 15)

    if st.button("Calculate Recommendation"):
        correction_dose = max((current_sugar - 120) / sensitivity, 0)
        carb_dose = carbs / carb_ratio
        total_dose = round(correction_dose + carb_dose, 1)

        st.success(f"💉 Recommended Insulin Dose: **{total_dose} units**")

        st.info(f"- Correction Dose: {correction_dose:.1f} units")
        st.info(f"- Carb Coverage Dose: {carb_dose:.1f} units")

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
