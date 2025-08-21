import streamlit as st
import pandas as pd
import random
import plotly.express as px

# ----------------------------
# Sample Diet Plans Dictionary
# ----------------------------
diet_plans = {
    "Breakfast": [
        {
            "name": "Oatmeal with Berries",
            "description": "Healthy oats with fresh seasonal berries and almonds.",
            "image": "https://www.eatingwell.com/thmb/jH4_1A3R-9G5gSFDQ.jpg",
            "nutrition": {"Calories": 350, "Protein": 12, "Carbs": 55, "Fat": 8},
        },
        {
            "name": "Greek Yogurt Parfait",
            "description": "Layers of Greek yogurt, honey, and granola.",
            "image": "https://www.cookingclassy.com/wp-content/uploads/2019/04/yogurt-parfait-2.jpg",
            "nutrition": {"Calories": 280, "Protein": 15, "Carbs": 35, "Fat": 7},
        },
    ],
    "Lunch": [
        {
            "name": "Grilled Chicken Salad",
            "description": "Lean grilled chicken with leafy greens and vinaigrette.",
            "image": "https://www.simplyrecipes.com/thmb/OV3mA9.jpg",
            "nutrition": {"Calories": 420, "Protein": 30, "Carbs": 25, "Fat": 15},
        },
        {
            "name": "Veggie Wrap",
            "description": "Whole wheat tortilla with hummus and mixed veggies.",
            "image": "https://www.acouplecooks.com/wp-content/uploads/2020/04/Veggie-Wraps-010.jpg",
            "nutrition": {"Calories": 310, "Protein": 10, "Carbs": 45, "Fat": 9},
        },
    ],
    "Dinner": [
        {
            "name": "Salmon with Quinoa",
            "description": "Pan-seared salmon with lemon butter and quinoa salad.",
            "image": "https://www.wellplated.com/wp-content/uploads/2019/09/Baked-Salmon-in-Foil-Recipe.jpg",
            "nutrition": {"Calories": 500, "Protein": 35, "Carbs": 40, "Fat": 20},
        },
        {
            "name": "Stir-fried Tofu & Veggies",
            "description": "High-protein tofu stir fry with colorful vegetables.",
            "image": "https://minimalistbaker.com/wp-content/uploads/2019/06/Easy-Tofu-Stir-Fry-SQUARE.jpg",
            "nutrition": {"Calories": 380, "Protein": 20, "Carbs": 30, "Fat": 14},
        },
    ],
}

# Track weekly totals
weekly_totals = {"Calories": 0, "Protein": 0, "Carbs": 0, "Fat": 0}

# ----------------------------
# Streamlit App Layout
# ----------------------------
st.set_page_config(page_title="MySugr Improved", layout="wide")
st.title("📊 MySugr Advanced Dashboard")

tabs = st.tabs(["📂 Dashboard", "💉 Insulin Recommendation", "🍽️ Diet Recommendation"])

# ----------------------------
# Dashboard Tab
# ----------------------------
with tabs[0]:
    st.header("📂 Upload Your Data")
    uploaded_file = st.file_uploader("Upload your MySugr CSV file", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ File uploaded successfully!")
            st.dataframe(df.head())

            if "blood sugar measurement (mg/dl)" in df.columns:
                fig = px.line(
                    df,
                    x=df.index,
                    y="blood sugar measurement (mg/dl)",
                    title="Blood Sugar Trend",
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")

# ----------------------------
# Insulin Recommendation Tab
# ----------------------------
with tabs[1]:
    st.header("💉 Insulin Recommendation")
    sugar_level = st.number_input("Enter current blood sugar (mg/dL)", min_value=50, max_value=400, value=120)
    carbs = st.number_input("Enter planned carb intake (grams)", min_value=0, max_value=200, value=50)

    if st.button("Get Insulin Suggestion"):
        suggested_units = (carbs / 12) + ((sugar_level - 100) / 50)
        suggested_units = max(0, round(suggested_units, 1))
        st.success(f"💉 Suggested Insulin Dose: {suggested_units} units")

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
                cols2[i % 4].metric(k, f"{v}{'g' if k != 'Calories' else ''}")
                weekly_totals[k] += v

        st.markdown("---")
        st.markdown("### ⭐ Rate this Meal")
        st.radio(
            "How do you like this meal?",
            ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            horizontal=True,
        )

        st.markdown("### 💬 Feedback")
        st.text_area("Any comments or suggestions?")
