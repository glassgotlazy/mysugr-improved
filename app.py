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

# -------------------------
# Helper function for nutrition badges
def show_nutrition_badges(nutrition: dict):
    badge_styles = {
        "Calories": "background-color:#FFDD57;color:#000;padding:6px 12px;border-radius:12px;margin:3px;display:inline-block;font-weight:bold;",
        "Carbs": "background-color:#4DB6FF;color:white;padding:6px 12px;border-radius:12px;margin:3px;display:inline-block;font-weight:bold;",
        "Protein": "background-color:#57E47B;color:white;padding:6px 12px;border-radius:12px;margin:3px;display:inline-block;font-weight:bold;",
        "Fat": "background-color:#FF6B6B;color:white;padding:6px 12px;border-radius:12px;margin:3px;display:inline-block;font-weight:bold;",
    }

    badges = " ".join(
        [f"<span style='{badge_styles[nutr]}'>{nutr}: {val}</span>" for nutr, val in nutrition.items()]
    )
    st.markdown(badges, unsafe_allow_html=True)


# Inside your recommendation display
if st.button("🎲 Surprise Me with a Meal!"):
    import random
    meal = random.choice(meals)
    st.subheader(f"✨ Random Pick: {meal['title']}")
    st.image(meal["img"], caption=meal["title"], use_container_width=True)

    # ✅ Show nutrition as badges
    show_nutrition_badges(meal["nutrition"])

# 👉 Carousel Style
choice = st.radio("👉 Or pick your meal:", [m["title"] for m in meals])
meal = next(m for m in meals if m["title"] == choice)
st.image(meal["img"], caption=meal["title"], use_container_width=True)

# ✅ Show nutrition as badges
show_nutrition_badges(meal["nutrition"])


