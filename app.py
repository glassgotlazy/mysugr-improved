import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ---------------------------
# App Config
# ---------------------------
st.set_page_config(
    page_title="MySugr AI Diabetes Assistant",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🩸 MySugr AI Diabetes Assistant")
st.markdown("Upload your **MySugr CSV file** and get personalized insights, insulin suggestions, and diet recommendations.")

# ---------------------------
# Helper Functions
# ---------------------------
def clean_columns(df):
    """Rename columns to standard names if needed"""
    col_map = {
        'Date': 'Date',
        'Time': 'Time',
        'Blood Sugar Measurement (mg/dL)': 'Glucose',
        'Blood Sugar': 'Glucose',
        'Glucose': 'Glucose'
    }
    df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})
    return df

def insulin_needed(current_glucose, target_glucose=150, isf=14.13):
    """Correction dose calculator"""
    if current_glucose <= target_glucose:
        return 0.0
    return (current_glucose - target_glucose) / isf

def diet_suggestions(glucose):
    """Rule-based diet suggestions"""
    if glucose < 70:
        return [
            "🍯 Eat fast-acting carbs (like glucose tablets, juice).",
            "🍌 Follow up with a balanced snack (fruit + protein).",
            "⏱️ Recheck sugar in 15 mins."
        ]
    elif 70 <= glucose <= 180:
        return [
            "🥗 Continue with a balanced diet (veggies, lean protein, whole grains).",
            "🚶‍♂️ Light walk after meals helps maintain stability.",
            "💧 Stay hydrated (water > sugary drinks)."
        ]
    elif 180 < glucose <= 250:
        return [
            "🥦 Reduce carb-heavy meals, add more veggies & protein.",
            "🚶‍♂️ Try light activity (walk, stretching).",
            "❌ Avoid sweets, fried food, soft drinks."
        ]
    else:  # Very high
        return [
            "⚠️ Blood sugar is very high! Consult doctor if persistent.",
            "🥗 Strictly avoid high-carb and fried foods.",
            "💧 Drink water, stay hydrated.",
            "🧘‍♂️ Rest and monitor closely."
        ]

# ---------------------------
# File Upload
# ---------------------------
uploaded_file = st.file_uploader("📂 Upload your MySugr CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = clean_columns(df)

    if "Glucose" not in df.columns:
        st.error("❌ CSV must contain a 'Blood Sugar Measurement (mg/dL)' column.")
    else:
        if "Date" in df.columns and "Time" in df.columns:
            df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")
        elif "Date" in df.columns:
            df["DateTime"] = pd.to_datetime(df["Date"], errors="coerce")
        else:
            df["DateTime"] = pd.to_datetime("now")

        glucose_df = df[["DateTime", "Glucose"]].dropna()

        avg_glucose = glucose_df["Glucose"].mean()
        latest_glucose = glucose_df["Glucose"].iloc[-1]

        st.metric("📊 Average Glucose", f"{avg_glucose:.2f} mg/dL")
        st.metric("🩸 Latest Glucose", f"{latest_glucose} mg/dL")

        st.subheader("💉 Insulin Correction Suggestion")
        correction = insulin_needed(latest_glucose)
        st.write(f"➡️ Suggested correction dose: **{correction:.2f} units** (based on ISF=14.13)")

        st.subheader("🥗 Diet & Lifestyle Suggestions")
        suggestions = diet_suggestions(latest_glucose)
        for s in suggestions:
            st.markdown(f"- {s}")

        st.subheader("📈 Glucose Trend Over Time")
        fig, ax = plt.subplots(figsize=(10,5))
        sns.lineplot(data=glucose_df, x="DateTime", y="Glucose", marker="o", ax=ax)
        ax.axhline(150, color="green", linestyle="--", label="Target (150)")
        ax.axhline(180, color="orange", linestyle="--", label="Upper Normal (180)")
        ax.axhline(250, color="red", linestyle="--", label="High (250)")
        ax.set_title("Glucose Levels Over Time")
        ax.set_ylabel("Glucose (mg/dL)")
        ax.set_xlabel("Date/Time")
        ax.legend()
        st.pyplot(fig)

else:
    st.info("📂 Please upload your MySugr CSV file to continue.")
