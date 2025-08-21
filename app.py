import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# -------------------------------
# Helper functions
# -------------------------------
def insulin_needed(current_glucose, target_glucose=150, isf=14.13):
    """Calculate insulin correction dose."""
    if current_glucose <= target_glucose:
        return 0.0
    return round((current_glucose - target_glucose) / isf, 2)


def diet_suggestions(glucose):
    """Return diet & lifestyle suggestions based on glucose level."""
    if glucose < 70:
        return "⚠️ Low sugar detected! Have a small snack (fruit juice, glucose tablet). Avoid excess insulin."
    elif 70 <= glucose <= 180:
        return "✅ Excellent! Maintain your balanced diet and regular exercise."
    elif 180 < glucose <= 250:
        return "⚠️ Elevated sugar. Prefer high-fiber foods (veggies, whole grains) and hydrate well."
    else:
        return "🚨 High sugar detected! Avoid carbs/sugary foods. Consult your doctor if persistent."


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="MySugr Improved", layout="wide")

st.title("🩸 MySugr Improved – Glucose & Insulin Tracker")

st.sidebar.header("📂 Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Example expected columns
st.sidebar.markdown(
    "Your CSV must have columns: **DateTime**, **Blood Sugar Measurement (mg/dL)**"
)

# If file is uploaded
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Normalize column names
        df.columns = df.columns.str.strip()

        # Check required columns
        if not {"DateTime", "Blood Sugar Measurement (mg/dL)"}.issubset(df.columns):
            st.error("❌ CSV must contain 'DateTime' and 'Blood Sugar Measurement (mg/dL)' columns.")
        else:
            # Convert datetime
            df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
            df = df.dropna(subset=["DateTime"])

            st.success("✅ Data loaded successfully!")

            # Show preview
            st.subheader("📊 Uploaded Data Preview")
            st.dataframe(df.head())

            # Plot glucose readings
            st.subheader("📈 Glucose Levels Over Time")
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=df, x="DateTime", y="Blood Sugar Measurement (mg/dL)", marker="o", ax=ax)
            ax.axhline(150, color="green", linestyle="--", label="Target (150)")
            ax.set_ylabel("Blood Sugar (mg/dL)")
            ax.legend()
            st.pyplot(fig)

            # Select a row
            st.subheader("📌 Pick a reading for analysis")
            selected_row = st.selectbox(
                "Select by DateTime & Value",
                options=df.itertuples(index=False),
                format_func=lambda x: f"{x.DateTime.strftime('%Y-%m-%d %H:%M')} → {x[1]} mg/dL",
            )

            if selected_row:
                glucose_val = selected_row[1]

                st.metric("📍 Selected Reading", f"{glucose_val} mg/dL")

                # Insulin suggestion
                insulin_units = insulin_needed(glucose_val)
                st.subheader("💉 Insulin Recommendation")
                st.write(f"Suggested correction dose: **{insulin_units} units**")

                # Diet suggestion
                st.subheader("🥗 Diet & Lifestyle Suggestion")
                st.info(diet_suggestions(glucose_val))

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.warning("👆 Upload your CSV file to begin.")
