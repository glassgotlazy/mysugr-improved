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
# -------------------------
# -------------------------
# Diet Recommendations Tab (Interactive + Randomizer + Nutrition Table)
# -------------------------
with tabs[3]:
    st.header("🍎 Diet Recommendations")
    st.write("Personalized diet suggestions based on your blood sugar level.")

    try:
        bs_level = st.number_input("Enter your current blood sugar (mg/dL)", min_value=50, max_value=500, step=1)
        meal_time = st.selectbox("Select Meal Time", ["Breakfast", "Lunch", "Dinner", "Snack"])

        if st.button("🍽 Get Diet Recommendation"):
            if bs_level < 70:
                st.warning("⚠️ Your blood sugar is LOW.")
                st.success("🍯 Fast-acting carbs followed by a balanced snack recommended.")

                meals = [
                    {"title": "Glucose Tablets", 
                     "img": "https://www.diabetes.org/sites/default/files/styles/paragraph_large/public/2023-06/Glucose%20Tablet.jpg",
                     "nutrition": {"Calories": 40, "Carbs": "10g", "Protein": "0g", "Fat": "0g"}},
                    
                    {"title": "Fruit Juice", 
                     "img": "https://hips.hearstapps.com/hmg-prod/images/glass-of-orange-juice-royalty-free-image-1628179032.jpg",
                     "nutrition": {"Calories": 120, "Carbs": "28g", "Protein": "2g", "Fat": "0g"}},
                    
                    {"title": "Balanced Snack (Protein + Carbs)", 
                     "img": "https://hips.hearstapps.com/hmg-prod/images/protein-snacks-1629407626.jpg",
                     "nutrition": {"Calories": 180, "Carbs": "20g", "Protein": "10g", "Fat": "6g"}}
                ]

            elif 70 <= bs_level <= 140:
                st.success("✅ Normal range.")
                st.info("🥗 Eat a balanced meal with lean protein, complex carbs, and vegetables.")

                meals = [
                    {"title": "Balanced Meal Plate", 
                     "img": "https://www.eatingwell.com/thmb/n0Uu2t91jNVF2nZXuBLDX17jJ_E=/1500x0/...",
                     "nutrition": {"Calories": 400, "Carbs": "45g", "Protein": "25g", "Fat": "15g"}},
                    
                    {"title": "Grilled Salmon with Veggies", 
                     "img": "https://www.eatingwell.com/thmb/2mKZnXZwCkhAXRjWJm7clv1OylE=/1500x0/...",
                     "nutrition": {"Calories": 350, "Carbs": "15g", "Protein": "30g", "Fat": "18g"}},
                    
                    {"title": "Chicken Salad Bowl", 
                     "img": "https://www.eatingwell.com/thmb/oFz94KfT3RkLRQqgmGBK1bnlT2I=/1500x0/...",
                     "nutrition": {"Calories": 320, "Carbs": "20g", "Protein": "28g", "Fat": "12g"}}
                ]

            elif 140 < bs_level <= 200:
                st.warning("⚠️ Slightly high sugar.")
                st.info("🍗 Focus on low-carb meals with protein and fiber.")

                meals = [
                    {"title": "Chicken & Veggie Stir-Fry", 
                     "img": "https://www.eatingwell.com/thmb/ijWcZcUby6rO-TeHCPhrwQjH4EQ=/1500x0/...",
                     "nutrition": {"Calories": 300, "Carbs": "20g", "Protein": "32g", "Fat": "10g"}},
                    
                    {"title": "Grilled Chicken & Broccoli", 
                     "img": "https://www.eatingwell.com/thmb/XG7T0YuywJH2mghOb0P7cF3n1uM=/1500x0/...",
                     "nutrition": {"Calories": 280, "Carbs": "15g", "Protein": "30g", "Fat": "8g"}},
                    
                    {"title": "Zucchini Noodles with Pesto", 
                     "img": "https://www.eatingwell.com/thmb/nQce9nZftt3VYTrMT9aB7f65h_c=/1500x0/...",
                     "nutrition": {"Calories": 260, "Carbs": "12g", "Protein": "15g", "Fat": "16g"}}
                ]

            else:
                st.error("🚨 Very high sugar!")
                st.info("🥦 Stick to very low-carb meals. Avoid sugar completely.")

                meals = [
                    {"title": "Green Salad & Lean Protein", 
                     "img": "https://www.eatingwell.com/thmb/o4LJ9Hge6B4xF65Ut9P3XWhM5lc=/1500x0/...",
                     "nutrition": {"Calories": 220, "Carbs": "10g", "Protein": "22g", "Fat": "9g"}},
                    
                    {"title": "Steamed Veggies & Tofu", 
                     "img": "https://www.eatingwell.com/thmb/VsBoqKJ2vQ7-2moohsTjqOSClCE=/1500x0/...",
                     "nutrition": {"Calories": 200, "Carbs": "12g", "Protein": "16g", "Fat": "8g"}},
                    
                    {"title": "Avocado Salad Bowl", 
                     "img": "https://www.eatingwell.com/thmb/lX2Q5IQ1VYBaN4U5N7DCVmMYrFQ=/1500x0/...",
                     "nutrition": {"Calories": 240, "Carbs": "14g", "Protein": "8g", "Fat": "18g"}}
                ]

            # 🎲 Randomizer Button
            if st.button("🎲 Surprise Me with a Meal!"):
                import random
                meal = random.choice(meals)
                st.subheader(f"✨ Random Pick: {meal['title']}")
                st.image(meal["img"], caption=meal["title"], use_container_width=True)

                # ✅ Show nutrition in table
                st.table(pd.DataFrame(meal["nutrition"], index=[0]))

            # 👉 Carousel Style
            choice = st.radio("👉 Or pick your meal:", [m["title"] for m in meals])
            meal = next(m for m in meals if m["title"] == choice)
            st.image(meal["img"], caption=meal["title"], use_container_width=True)

            # ✅ Show nutrition in table
            st.table(pd.DataFrame(meal["nutrition"], index=[0]))

    except Exception as e:
        st.error(f"❌ Error in diet recommendation: {e}")

