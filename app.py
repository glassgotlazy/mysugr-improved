import streamlit as st
import pandas as pd
import datetime

# ---------------- Session & Auth ---------------- #
if "users" not in st.session_state:
    st.session_state["users"] = {}  # username -> password
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None


def login(username, password):
    if username in st.session_state["users"] and st.session_state["users"][username] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        return True
    return False


def signup(username, password):
    if username not in st.session_state["users"]:
        st.session_state["users"][username] = password
        return True
    return False


def get_user_key(suffix):
    return f"{st.session_state['username']}_{suffix}"


# ---------------- Login / Signup ---------------- #
if not st.session_state["logged_in"]:
    st.title("🔐 Login / Signup")

    auth_choice = st.radio("Choose action:", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_choice == "Login":
        if st.button("Login"):
            if login(username, password):
                st.success("Logged in ✅")
                st.rerun()
            else:
                st.error("Invalid credentials ❌")
    else:
        if st.button("Signup"):
            if signup(username, password):
                st.success("Account created 🎉 Please login.")
            else:
                st.error("Username already exists ❌")
    st.stop()

# ---------------- Sidebar ---------------- #
st.sidebar.title(f"👋 Welcome, {st.session_state['username']}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.rerun()

# ---------------- Tabs ---------------- #
tab0, tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💉 Insulin", "🥗 Diet", "📈 Weekly Summary"])

# ===================================================== #
# 📊 DASHBOARD
# ===================================================== #
    st.header("📊 Dashboard")

    # Upload glucose log
    uploaded_glucose = st.file_uploader("📤 Upload Glucose Log (CSV)", type=["csv"], key="upload_glucose")
    if uploaded_glucose is not None:
        glucose_df = pd.read_csv(uploaded_glucose)

        # Ensure proper datetime handling
        if "timestamp" in glucose_df.columns:
            glucose_df["timestamp"] = pd.to_datetime(glucose_df["timestamp"])
            glucose_df = glucose_df.sort_values("timestamp")

            # Filter last 24 hours
            last_24h = glucose_df[glucose_df["timestamp"] >= (pd.Timestamp.now() - pd.Timedelta(hours=24))]

            if not last_24h.empty:
                st.subheader("📈 Last 24 Hours Glucose Trend")

                # Metrics
                st.metric("Avg Glucose (mg/dL)", f"{last_24h['glucose'].mean():.1f}")
                st.metric("Min Glucose (mg/dL)", f"{last_24h['glucose'].min():.1f}")
                st.metric("Max Glucose (mg/dL)", f"{last_24h['glucose'].max():.1f}")
                st.metric("Std Dev (mg/dL)", f"{last_24h['glucose'].std():.1f}")

                # Line chart
                st.line_chart(last_24h.set_index("timestamp")["glucose"])
            else:
                st.warning("⚠️ No data in last 24 hours found in file.")
        else:
            st.error("Uploaded file must contain a 'timestamp' column and 'glucose' column.")



    insulin_key = get_user_key("insulin_history")
    diet_key = get_user_key("diet_history")

    if insulin_key not in st.session_state:
        st.session_state[insulin_key] = pd.DataFrame(columns=["carbs", "bg", "dose", "timestamp"])
    if diet_key not in st.session_state:
        st.session_state[diet_key] = pd.DataFrame(columns=["meal", "rating", "notes", "timestamp"])

    insulin_df = st.session_state[insulin_key]
    diet_df = st.session_state[diet_key]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("💉 Total Insulin Records", len(insulin_df))
    with col2:
        st.metric("🥗 Meals Logged", len(diet_df))

    if not insulin_df.empty:
        st.subheader("📉 Blood Glucose & Dose History")
        st.line_chart(insulin_df.set_index("timestamp")[["bg", "dose"]])

    if not diet_df.empty:
        st.subheader("⭐ Meal Ratings Trend")
        st.line_chart(diet_df.set_index("timestamp")[["rating"]])

# ===================================================== #
# 💉 INSULIN TAB
# ===================================================== #
with tab1:
    st.header("💉 Insulin Dose Calculator")

    carbs = st.number_input("Carbohydrates (grams)", min_value=0, step=1)
    current_bg = st.number_input("Current Blood Glucose (mg/dL)", min_value=0, step=1)
    target_bg = st.number_input("Target Blood Glucose (mg/dL)", min_value=80, value=110, step=1)
    carb_ratio = st.number_input("Insulin-to-Carb Ratio (g/unit)", min_value=1, value=15, step=1)
    correction_factor = st.number_input("Correction Factor (mg/dL/unit)", min_value=10, value=50, step=1)

    if st.button("Calculate Insulin Dose"):
        carb_insulin = carbs / carb_ratio if carb_ratio > 0 else 0
        correction_insulin = (current_bg - target_bg) / correction_factor if current_bg > target_bg else 0
        total_dose = carb_insulin + correction_insulin

        st.subheader("📊 Dose Recommendation")
        st.metric("Carb Coverage", f"{carb_insulin:.1f} units")
        st.metric("Correction Dose", f"{correction_insulin:.1f} units")
        st.metric("✅ Total Recommended Dose", f"{total_dose:.1f} units")

        insulin_key = get_user_key("insulin_history")
        new_entry = {
            "carbs": carbs,
            "bg": current_bg,
            "dose": total_dose,
            "timestamp": datetime.datetime.now(),
        }
        st.session_state[insulin_key] = pd.concat(
            [st.session_state[insulin_key], pd.DataFrame([new_entry])],
            ignore_index=True
        )

# ===================================================== #
# 🥗 DIET TAB
# ===================================================== #
with tab2:
    st.header("🥗 Diet Planner")

    diet_plans = {
        "Breakfast": [
            ("Oatmeal with fruits", "https://i.imgur.com/1O4iN5c.jpg"),
            ("Vegetable omelette", "https://i.imgur.com/Ht6p8Qq.jpg"),
            ("Greek yogurt with honey", "https://i.imgur.com/TSJ0A9Z.jpg"),
        ],
        "Lunch": [
            ("Grilled chicken with salad", "https://i.imgur.com/jh5N8x7.jpg"),
            ("Brown rice with dal & veggies", "https://i.imgur.com/UKxjxnT.jpg"),
            ("Paneer wrap", "https://i.imgur.com/9LZxO7Q.jpg"),
        ],
        "Dinner": [
            ("Baked salmon with veggies", "https://i.imgur.com/G2X8Z6H.jpg"),
            ("Whole wheat roti with sabzi", "https://i.imgur.com/kN4F0uQ.jpg"),
            ("Soup with whole grain bread", "https://i.imgur.com/ct7V9kW.jpg"),
        ],
    }

    history_key = get_user_key("diet_history")
    if history_key not in st.session_state:
        st.session_state[history_key] = pd.DataFrame(columns=["meal", "rating", "notes", "timestamp"])

    for category, meals in diet_plans.items():
        st.subheader(category)
        cols = st.columns(len(meals))
        for idx, (meal, img) in enumerate(meals):
            with cols[idx]:
                st.image(img, caption=meal, use_container_width=True)
                rating = st.slider(f"Rate {meal}", 1, 5, 3, key=f"{category}_{meal}_rating")
                notes = st.text_input(f"Notes for {meal}", key=f"{category}_{meal}_notes")
                if st.button(f"Save {meal}", key=f"{category}_{meal}_save"):
                    new_entry = {
                        "meal": meal,
                        "rating": rating,
                        "notes": notes,
                        "timestamp": datetime.datetime.now()
                    }
                    st.session_state[history_key] = pd.concat(
                        [st.session_state[history_key], pd.DataFrame([new_entry])],
                        ignore_index=True
                    )
                    st.success(f"Saved {meal} ✅")

    st.subheader("📜 Diet History")
    df = st.session_state[history_key]
    st.dataframe(df)

    if not df.empty:
        csv_file = f"diet_history_{st.session_state['username']}.csv"
        df.to_csv(csv_file, index=False)
        with open(csv_file, "rb") as f:
            st.download_button("📥 Download Diet History (CSV)", f, file_name=csv_file)

# ===================================================== #
# 📈 WEEKLY SUMMARY TAB
# ===================================================== #
with tab3:
    st.header("📈 Weekly Summary")

    history_key = get_user_key("diet_history")
    if history_key in st.session_state and not st.session_state[history_key].empty:
        df = st.session_state[history_key]
        df["day"] = pd.to_datetime(df["timestamp"]).dt.day_name()

        weekly_totals = df.groupby("day")["rating"].mean()
        st.bar_chart(weekly_totals)
    else:
        st.info("No history found for this week.")
