import streamlit as st
import pandas as pd
import random
from datetime import datetime
from openai import OpenAI

# ---------------- Setup ----------------
st.set_page_config(page_title="MySugr Improved AI", layout="wide")
client = OpenAI(api_key=st.secrets["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"])  # store your key in .streamlit/secrets.toml


# ---------------- Utility ----------------
def init_user_storage():
    """Ensure global storage exists for all users."""
    if "all_users" not in st.session_state:
        st.session_state.all_users = {}

def load_user_data(username):
    """Load data for a given user into session state."""
    init_user_storage()
    if username not in st.session_state.all_users:
        st.session_state.all_users[username] = {}
    st.session_state.user_data = st.session_state.all_users[username]

def save_user_data(username):
    """Save current user data back to global store."""
    st.session_state.all_users[username] = st.session_state.user_data


def ai_chat(prompt, system_role="You are a helpful medical AI assistant specializing in diabetes management."):
    """Send query to OpenAI and return response text."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"


# ---------------- Login Page ----------------
def login():
    st.title("🔑 Login / Sign Up Page")
    username = st.text_input("Enter Username")

    if st.button("Login / Sign Up"):
        if username.strip():
            st.session_state.username = username.strip()
            load_user_data(st.session_state.username)
            st.success(f"Welcome {username}!")
            st.rerun()   # rerun after login


# ---------------- Main App ----------------
def main_app():
    st.markdown("*Made by ~Glass + AI*", unsafe_allow_html=True)
    st.title("💉 MySugr Improved AI App")
    st.write(f"👋 Welcome, **{st.session_state.username}**")

    # Tabs
    tabs = st.tabs([
        "📊 Dashboard", 
        "🥗 Diet Tracking", 
        "💉 Advanced Insulin Assistant",
        "🍎 Diet Recommendations", 
        "📂 Data Upload", 
        "📈 Reports",
        "🤖 AI Assistant"
    ])

    # ---------------- Dashboard ----------------
    with tabs[0]:
        st.header("📊 Dashboard")
        st.metric("Total Meals Tracked", len(st.session_state.user_data.get("diet_tracking", [])))
        st.metric("Total Insulin Recs", len(st.session_state.user_data.get("insulin_recommendations", [])))
        st.metric("Diet Plans Generated", len(st.session_state.user_data.get("diet_recommendations", [])))

    # ---------------- Diet Tracking ----------------
    with tabs[1]:
        st.header("🥗 Diet Tracking")
        meal = st.text_input("Meal Name")
        calories = st.number_input("Calories", min_value=0)

        if st.button("Add Meal"):
            st.session_state.user_data.setdefault("diet_tracking", []).append({
                "meal": meal,
                "calories": calories,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username)
            st.success("Meal added!")

        if st.session_state.user_data.get("diet_tracking"):
            st.subheader("Tracked Meals")
            df_meals = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.dataframe(df_meals)

    # ---------------- Advanced Insulin Assistant ----------------
    with tabs[2]:
        st.header("💉 Advanced Insulin Assistant")

        glucose = st.number_input("Current Glucose Level (mg/dL)", min_value=40, max_value=400, key="glucose_input")
        carbs = st.number_input("Carbohydrate Intake (grams)", min_value=0, key="carbs_input")
        sensitivity = st.slider("Insulin Sensitivity Factor", 10, 100, 50, key="sensitivity_input")

        if st.button("Calculate Insulin Dose", key="insulin_button"):
            recommended_dose = (glucose - 100) / sensitivity + (carbs / 10)
            recommended_dose = max(0, round(recommended_dose, 2))

            st.session_state.last_insulin_dose = recommended_dose  # ✅ persist result

            st.session_state.user_data.setdefault("insulin_recommendations", []).append({
                "glucose": glucose,
                "carbs": carbs,
                "dose": recommended_dose,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username)

        # Always show last result if available
        if "last_insulin_dose" in st.session_state:
            st.success(f"💉 Recommended Insulin Dose: **{st.session_state.last_insulin_dose} units**")

            if st.button("🤖 Explain this dose with AI"):
                explanation = ai_chat(
                    f"My glucose level is {glucose}, I ate {carbs}g carbs, "
                    f"sensitivity factor {sensitivity}, recommended dose {st.session_state.last_insulin_dose}. "
                    f"Explain in simple terms why this insulin dose is suggested."
                )
                st.info(explanation)

    # ---------------- Diet Recommendations ----------------
    with tabs[3]:
        st.header("🍎 Diet Recommendations")

        diet_choice = st.radio("Choose your diet goal:", ["Balanced", "Low-Carb", "High-Protein"])

        if st.button("Generate AI Diet Plan"):
            # Generate with OpenAI
            ai_plan_text = ai_chat(
                f"Generate a 7-day {diet_choice} diet plan for a diabetic patient. "
                f"Include breakfast, lunch, and dinner with calories."
            )

            st.text(ai_plan_text)

            st.session_state.user_data.setdefault("diet_recommendations", []).append({
                "goal": diet_choice,
                "plan": ai_plan_text,
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username)
            st.success("✅ AI Diet Plan generated!")

        # History Viewer
        if st.session_state.user_data.get("diet_recommendations"):
            st.subheader("📜 Previous Diet Plans")
            for idx, record in enumerate(reversed(st.session_state.user_data["diet_recommendations"])): 
                st.markdown(
                    f"**Plan {len(st.session_state.user_data['diet_recommendations']) - idx}** "
                    f"({record.get('goal', 'N/A')}) - _{record.get('time', 'Unknown')}_"
                )
                st.text(record.get("plan", "⚠️ No plan data."))

    # ---------------- Data Upload ----------------
    with tabs[4]:
        st.header("📂 Data Upload")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            df_upload = pd.read_csv(uploaded_file)
            st.write("✅ Uploaded Data:")
            st.dataframe(df_upload)

            st.session_state.user_data.setdefault("uploads", []).append({
                "filename": uploaded_file.name,
                "data": df_upload.to_dict(),
                "time": str(datetime.now())
            })
            save_user_data(st.session_state.username)

    # ---------------- Reports ----------------
    with tabs[5]:
        st.header("📈 Reports")

        if st.session_state.user_data.get("insulin_recommendations"):
            df_insulin = pd.DataFrame(st.session_state.user_data["insulin_recommendations"])
            st.subheader("Glucose Level Trends")
            st.line_chart(df_insulin["glucose"])

        if st.session_state.user_data.get("diet_tracking"):
            df_calories = pd.DataFrame(st.session_state.user_data["diet_tracking"])
            st.subheader("Calorie Intake")
            st.bar_chart(df_calories["calories"])

        if st.button("🤖 Summarize Report with AI"):
            report_text = ai_chat(
                f"Here is a summary of user data:\n"
                f"Insulin history: {st.session_state.user_data.get('insulin_recommendations', [])}\n"
                f"Diet tracking: {st.session_state.user_data.get('diet_tracking', [])}\n"
                f"Please provide insights and suggestions for this user."
            )
            st.info(report_text)

    # ---------------- AI Assistant ----------------
    with tabs[6]:
        st.header("🤖 AI Assistant - Ask Anything")
        query = st.text_area("Ask your health / diabetes / diet question")
        if st.button("Ask AI"):
            answer = ai_chat(query)
            st.success(answer)

    # ---------------- Logout ----------------
    if st.button("🚪 Logout"):
        st.session_state.pop("username", None)
        st.session_state.pop("user_data", None)
        st.rerun()


# ---------------- Run App ----------------
def run_app():
    if "username" not in st.session_state:
        login()
    else:
        main_app()


if __name__ == "__main__":
    run_app()
