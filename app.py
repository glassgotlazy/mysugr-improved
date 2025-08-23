import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime
import os

# ---------------------------------
# Page Config (must be first Streamlit call)
# ---------------------------------
st.set_page_config(
    page_title="MySugar Advanced",
    page_icon="💉",
    layout="wide",
)

# ---------------------------------
# User Authentication Utils
# ---------------------------------
USER_FILE = "users.csv"

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False  # User already exists
    users = pd.concat(
        [users, pd.DataFrame([[username, password]], columns=["username", "password"])],
        ignore_index=True,
    )
    users.to_csv(USER_FILE, index=False)
    return True

def check_login(username, password):
    users = load_users()
    match = users[(users["username"] == username) & (users["password"] == password)]
    return not match.empty

# ---------------------------------
# Session State
# ---------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# ---------------------------------
# Login / Signup Pages
# ---------------------------------
if not st.session_state.logged_in:
    st.title("🔐 Welcome to MySugr Improved")

    auth_choice = st.radio("Select Action", ["Login", "Sign Up"], horizontal=True)

    if auth_choice == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    else:  # Signup
        st.subheader("Create a new account")
        new_username = st.text_input("Choose a username")
        new_password = st.text_input("Choose a password", type="password")
        if st.button("Sign Up"):
            if save_user(new_username, new_password):
                st.success("🎉 Account created! Please log in.")
            else:
                st.error("⚠ Username already exists. Try a different one.")

    st.stop()  # Prevents the rest of the app from running until logged in

# ---------------------------------
# If logged in → Continue App
# ---------------------------------
st.sidebar.success(f"👤 Logged in as {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

st.title("🩸 MySugar - Diabetes Tracking Dashboard")

# ---------------------------------
# Tabs (single, unified)
# ---------------------------------
tabs = st.tabs([
    "📊 Dashboard",
    "🥗 Diet Tracking",
    "💉 Insulin Recommendations",
    "🍎 Diet Recommendations",
])

# ---------------------------------
# 📊 Dashboard Tab
# ---------------------------------
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
                df["datetime"] = pd.to_datetime(
                    df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce"
                )
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
                fig = px.line(
                    df.sort_values("datetime"),
                    x="datetime",
                    y="blood sugar measurement (mg/dl)",
                    title="Blood Sugar Over Time",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Line chart for any insulin-related columns
            insulin_cols = [col for col in df.columns if "insulin" in col]
            if insulin_cols:
                for col in insulin_cols:
                    fig = px.line(
                        df.sort_values("datetime"),
                        x="datetime",
                        y=col,
                        title=f"{col.title()} Over Time",
                    )
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    else:
        st.info("Upload a CSV file to see your dashboard.")

# ---------------------------------
# 🥗 Diet Tracking Tab
# ---------------------------------
with tabs[1]:
    st.header("🥗 Diet Tracking")

    st.write("Keep track of whether you followed your diet plan today.")

    col1, col2 = st.columns([1, 2])

    with col1:
        diet_followed = st.checkbox("✅ Did you follow your diet today?")

    with col2:
        if not diet_followed:
            st.text_input("❌ If not, what did you eat instead?")

# ---------------------------------
# 💉 Insulin Recommendation Tab
# ---------------------------------
with tabs[2]:
    st.header("💉 Insulin Assistant")

    st.markdown(
        "This tool helps you calculate your *meal-time insulin dose* based on your carbs and blood sugar levels."
    )

    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        carbs = st.number_input("🍞 Carbs in your meal (grams)", min_value=0, max_value=200, value=50)
        carb_ratio = st.number_input("⚖ Insulin-to-Carb Ratio (g/unit)", min_value=1, max_value=30, value=10)
    with col2:
        glucose = st.number_input("🩸 Current Blood Sugar (mg/dL)", min_value=50, max_value=400, value=150)
        correction_factor = st.number_input(
            "🔧 Correction Factor (mg/dL per unit)", min_value=10, max_value=100, value=50
        )

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
    st.progress(min(int((total_dose / 20) * 100), 100))  # progress bar out of 20 units
    st.bar_chart(
        pd.DataFrame(
            {"Insulin Units": [carb_insulin, correction_insulin]},
            index=["Carb Coverage", "Correction"],
        )
    )

    # Notes
    st.markdown("💡 *Note:* This is a helper tool, not medical advice. Always confirm with your doctor before making insulin adjustments.")

# ---------------------------------
# 🍎 Diet Recommendations Tab
# ---------------------------------
with tabs[3]:
    st.header("🍎 Diet Recommendations")

    # Days of the week & categories
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    categories = ["Breakfast", "Lunch", "Dinner", "Snack"]

    # Meals categorized with nutrition + real images
    meals = {
        "Breakfast": [
            {"name": "Oatmeal with Fruits",
             "img": "https://www.pcrm.org/sites/default/files/Oatmeal%20and%20Berries.jpg",
             "nutrition": {"Calories": 250, "Protein": 8, "Carbs": 45, "Fat": 5}},
            {"name": "Avocado Toast",
             "img": "https://www.spendwithpennies.com/wp-content/uploads/2022/09/Avocado-Toast-SpendWithPennies-1.jpg",
             "nutrition": {"Calories": 300, "Protein": 10, "Carbs": 30, "Fat": 12}},
            {"name": "Smoothie Bowl",
             "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9Fr7Ab7WaznNaTenCirjohOtnd0P7JOcO1Q&s",
             "nutrition": {"Calories": 280, "Protein": 9, "Carbs": 40, "Fat": 7}},
            {"name": "Idli with Sambar",
             "img": "https://maayeka.com/wp-content/uploads/2013/10/soft-idli-recipe.jpg",
             "nutrition": {"Calories": 320, "Protein": 11, "Carbs": 55, "Fat": 6}},
            {"name": "Vegetable Upma",
             "img": "https://beextravegant.com/wp-content/uploads/2022/05/Untitled.png",
             "nutrition": {"Calories": 280, "Protein": 8, "Carbs": 48, "Fat": 7}},
        ],
        "Lunch": [
            {"name": "Grilled Chicken Salad",
             "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6a3xakcHAEaQRTfoC2aOAJL7j3rZXR397NA&s",
             "nutrition": {"Calories": 400, "Protein": 35, "Carbs": 20, "Fat": 15}},
            {"name": "Quinoa Bowl",
             "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVge3iLT0xXk-PF3uA7XBtbsD6j3P8pISHYA&s",
             "nutrition": {"Calories": 420, "Protein": 18, "Carbs": 55, "Fat": 12}},
            {"name": "Paneer Butter Masala with Roti",
             "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS-Ac_83R91yFAml5yt8twiimb_LSUNkbaEfw&s",
             "nutrition": {"Calories": 520, "Protein": 20, "Carbs": 45, "Fat": 28}},
            {"name": "Dal Tadka with Rice",
             "img": "https://i0.wp.com/upbeetanisha.com/wp-content/uploads/2024/01/IMG_9643.jpg?resize=768%2C1024&ssl=1",
             "nutrition": {"Calories": 450, "Protein": 16, "Carbs": 60, "Fat": 14}},
        ],
        "Dinner": [
            {"name": "Baked Salmon with Veggies",
             "img": "https://hungryfoodie.com/wp-content/uploads/2023/09/Sheet-Pan-Salmon-and-Vegetables-21.jpg",
             "nutrition": {"Calories": 500, "Protein": 40, "Carbs": 25, "Fat": 22}},
            {"name": "Veggie Stir Fry",
             "img": "https://hips.hearstapps.com/hmg-prod/images/veggie-stir-fry-1597687367.jpg?crop=0.793xw:0.793xh;0.0619xw,0.0928xh&resize=1200:*",
             "nutrition": {"Calories": 350, "Protein": 12, "Carbs": 50, "Fat": 10}},
            {"name": "Rajma Chawal",
             "img": "https://images.squarespace-cdn.com/content/v1/5ea3b22556f3d073f3d9cae4/e37ea0ac-2f37-4df2-8e1e-3678f2f80fee/IMG_0856.jpg",
             "nutrition": {"Calories": 480, "Protein": 18, "Carbs": 70, "Fat": 12}},
            {"name": "Grilled Paneer with Veggies",
             "img": "https://madscookhouse.com/wp-content/uploads/2021/07/Peri-Peri-Paneer-Steaks.jpg",
             "nutrition": {"Calories": 430, "Protein": 25, "Carbs": 22, "Fat": 24}},
        ],
        "Snack": [
            {"name": "Greek Yogurt with Honey",
             "img": "https://realgreekrecipes.com/wp-content/uploads/2018/02/Greek-Yogurt-With-Honey-And-Walnuts-Recipe.jpg",
             "nutrition": {"Calories": 180, "Protein": 12, "Carbs": 20, "Fat": 4}},
            {"name": "Mixed Nuts",
             "img": "https://m.media-amazon.com/images/I/71oR9w5AjbL.UF1000,1000_QL80.jpg",
             "nutrition": {"Calories": 200, "Protein": 6, "Carbs": 8, "Fat": 18}},
            {"name": "Fruit Salad",
             "img": "https://www.modernhoney.com/wp-content/uploads/2023/05/Fruit-Salad-10.jpg",
             "nutrition": {"Calories": 150, "Protein": 2, "Carbs": 35, "Fat": 1}},
            {"name": "Roasted Chickpeas",
             "img": "https://www.allrecipes.com/thmb/WdQzwYsrWX0-6zRprlfn7OitWN8=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/81548-roasted-chickpeas-ddmfs-0442-1x2-hero-295c03efec90435a8588848f7e50f0bf.jpg",
             "nutrition": {"Calories": 170, "Protein": 9, "Carbs": 30, "Fat": 4}},
        ],
    }

    # --- SAFE INIT / HEAL weekly_meals ---
    def _pick(day_index: int):
        category = categories[day_index % len(categories)]
        return random.choice(meals[category])

    if "weekly_meals" not in st.session_state or not isinstance(st.session_state.weekly_meals, dict):
        st.session_state.weekly_meals = {d: _pick(i) for i, d in enumerate(days)}
    else:
        for i, d in enumerate(days):
            entry = st.session_state.weekly_meals.get(d)
            if not isinstance(entry, dict) or "name" not in entry or "nutrition" not in entry or "img" not in entry:
                st.session_state.weekly_meals[d] = _pick(i)

    # Track weekly totals
    weekly_totals = {"Calories": 0, "Protein": 0, "Carbs": 0, "Fat": 0}

    # Show each day
    for i, day in enumerate(days):
        meal = st.session_state.weekly_meals[day]

        st.markdown(f"### {day}")
        cols = st.columns([2, 1, 2])

        with cols[0]:
            st.subheader(meal["name"])
            st.write("📊 Nutrition:")
            st.write(meal["nutrition"])

        with cols[1]:
            st.image(meal["img"], caption=meal["name"], width=150)

        with cols[2]:
            st.slider(f"⭐ Rate {meal['name']}", 1, 5, 3, key=f"rating_{day}")
            st.text_area(f"📝 Notes for {meal['name']}", key=f"note_{day}")

        # Add to totals
        for k, v in meal["nutrition"].items():
            weekly_totals[k] += v

        # Replace option
        if st.button(f"🔄 Change {day}", key=f"change_{day}"):
            st.session_state.weekly_meals[day] = _pick(i)
            st.rerun()

        st.markdown("---")

    # 📅 Weekly Summary
    st.subheader("📅 Weekly Nutrition Summary")
    summary_cols = st.columns(4)
    for i, (k, v) in enumerate(weekly_totals.items()):
        summary_cols[i].metric(k, f"{v}{'g' if k != 'Calories' else ''}")
