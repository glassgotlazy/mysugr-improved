import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------
# App Config
# ---------------------------
st.set_page_config(
    page_title="MySugr AI Diabetes Assistant",
    page_icon="🩸",
    layout="wide"
)

st.title("🩸 MySugr AI Diabetes Assistant")
st.markdown("Upload your **MySugr CSV file** and get personalized insights, insulin suggestions, and diet recommendations.")

# ---------------------------
# Helper Functions
# ---------------------------
def clean_columns(df):
    col_map = {
        'Date': 'Date',
        'Time': 'Time',
        'Blood Sugar Measurement (mg/dL)': 'Glucose',
        'Blood Sugar': 'Glucose',
        'Glucose': 'Glucose'
    }
    return df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})

def insulin_needed(current_glucose, target_glucose=150, isf=14.13):
    if current_glucose <= target_glucose:
        return 0.0
    return (current_glucose - target_glucose) / isf

def diet_suggestions(glucose):
    if glucose < 70:
        return [
            "🍯 Eat fast-acting carbs (glucose tablets, juice).",
            "🍌 Follow up with fruit + protein snack.",
            "⏱️ Recheck sugar in 15 mins."
        ]
    elif 70 <= glucose <= 180:
        return [
            "🥗 Balanced diet: veggies, lean protein, whole grains.",
            "🚶‍♂️ Light walk after meals.",
            "💧 Drink water instead of sugary drinks."
        ]
    elif 180 < glucose <= 250:
        return [
            "🥦 Reduce carbs, add more protein/veggies.",
            "🚶‍♂️ Light activity recommended.",
            "❌ Avoid sweets, fried food, soda."
        ]
    else:
        return [
            "⚠️ Very high sugar! Consult doctor if persistent.",
            "🥗 Strictly avoid carbs & fried foods.",
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
        st.error("❌ CSV must contain 'Blood Sugar Measurement (mg/dL)' or 'Glucose' column.")
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
        st.write(f"➡️ Suggested correction dose: **{correction:.2f} units**")

        st.subheader("🥗 Diet & Lifestyle Suggestions")
        for s in diet_suggestions(latest_glucose):
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
