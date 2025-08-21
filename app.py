import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import datetime

# =========================
# Utility Functions
# =========================

def load_data(file):
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]

    # Try flexible matching
    datetime_col = None
    glucose_col = None

    for col in df.columns:
        if "date" in col and "time" in col or "datetime" in col:
            datetime_col = col
        if "glucose" in col or "blood" in col:
            glucose_col = col

    if not datetime_col or not glucose_col:
        st.error("❌ Could not detect DateTime and Glucose columns. Please check your CSV.")
        st.write("✅ Detected columns:", df.columns.tolist())
        return None

    df["datetime"] = pd.to_datetime(df[datetime_col], errors="coerce")
    df = df.dropna(subset=["datetime"])
    df = df.sort_values("datetime")
    df.rename(columns={glucose_col: "glucose"}, inplace=True)
    return df



def insulin_needed(current_glucose, target_glucose=150, isf=14.13):
    if current_glucose <= target_glucose:
        return 0.0
    return (current_glucose - target_glucose) / isf


def diet_suggestions(glucose):
    if glucose < 70:
        return {
            "Breakfast": "Oats with honey, banana smoothie, or a slice of bread with peanut butter.",
            "Lunch": "Rice with dal, small sweet potato, and a fruit juice.",
            "Dinner": "Vegetable soup with bread, or roti with paneer curry.",
            "Snacks": "Glucose biscuits, fruit yogurt, or dry fruits."
        }
    elif 70 <= glucose <= 180:
        return {
            "Breakfast": "Multigrain toast, boiled egg or poha.",
            "Lunch": "Brown rice with chicken/fish or dal & sabzi.",
            "Dinner": "2 rotis with dal & vegetables, salad.",
            "Snacks": "Nuts, apple/pear, or sprouts."
        }
    else:
        return {
            "Breakfast": "Egg whites, avocado toast, or vegetable upma.",
            "Lunch": "Grilled chicken/fish with salad, or dal with green veggies.",
            "Dinner": "2 rotis with sabzi, green salad, buttermilk.",
            "Snacks": "Cucumber, carrot sticks, roasted chickpeas."
        }


def generate_report(df, avg_glucose, latest_glucose, tir, hba1c, diet):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("📄 MySugr Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"📊 Average Glucose: {avg_glucose:.2f} mg/dL", styles["Normal"]))
    elements.append(Paragraph(f"🩸 Latest Glucose: {latest_glucose:.2f} mg/dL", styles["Normal"]))
    elements.append(Paragraph(f"📈 Time in Range: {tir:.1f}%", styles["Normal"]))
    elements.append(Paragraph(f"🧬 Estimated HbA1c: {hba1c:.2f}%", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("🍽️ Diet Suggestions:", styles["Heading2"]))
    for meal, suggestion in diet.items():
        elements.append(Paragraph(f"<b>{meal}:</b> {suggestion}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# =========================
# Streamlit App Layout
# =========================

st.set_page_config(page_title="MySugr Dashboard", layout="wide")
st.title("💉 MySugr Diabetes Dashboard")
st.markdown("Upload your glucose data and get insights, diet plans, and insulin suggestions.")

uploaded_file = st.sidebar.file_uploader("📂 Upload your MySugr CSV file", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)

    if df is not None:
        # Calculate metrics
        avg_glucose = df["glucose"].mean()
        latest_glucose = df["glucose"].iloc[-1]
        tir = (df[(df["glucose"] >= 70) & (df["glucose"] <= 180)].shape[0] / df.shape[0]) * 100
        hba1c = (avg_glucose + 46.7) / 28.7  # ADA formula

        tabs = st.tabs(["📊 Analytics", "🍽️ Diet", "💉 Insulin", "📄 Report"])

        # ================= ANALYTICS =================
        with tabs[0]:
            st.subheader("📊 Glucose Analytics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Glucose", f"{avg_glucose:.2f} mg/dL")
            col2.metric("Latest Glucose", f"{latest_glucose:.2f} mg/dL")
            col3.metric("Time in Range", f"{tir:.1f}%")

            st.line_chart(df.set_index("datetime")["glucose"], height=400)

            fig, ax = plt.subplots()
            ax.hist(df["glucose"], bins=20, color="skyblue", edgecolor="black")
            ax.axvline(avg_glucose, color="red", linestyle="--", label=f"Mean {avg_glucose:.1f}")
            ax.set_title("Glucose Distribution")
            ax.set_xlabel("Glucose (mg/dL)")
            ax.set_ylabel("Frequency")
            ax.legend()
            st.pyplot(fig)

        # ================= DIET =================
        with tabs[1]:
            st.subheader("🍽️ Personalized Diet Suggestions")
            suggestions = diet_suggestions(latest_glucose)

            for meal, suggestion in suggestions.items():
                st.markdown(f"### {meal}")
                st.markdown(f"✅ {suggestion}")

        # ================= INSULIN =================
        with tabs[2]:
            st.subheader("💉 Insulin Calculator")

            target = st.number_input("🎯 Target Glucose", 80, 180, 150)
            isf = st.number_input("⚖️ Insulin Sensitivity Factor (mg/dL per unit)", 5.0, 50.0, 14.13)
            glucose_input = st.number_input("🩸 Current Glucose", 50, 600, int(latest_glucose))

            correction_dose = insulin_needed(glucose_input, target, isf)
            st.metric("Correction Dose", f"{correction_dose:.2f} units")

        # ================= REPORT =================
        with tabs[3]:
            st.subheader("📄 Download Report")
            report = generate_report(df, avg_glucose, latest_glucose, tir, hba1c, suggestions)
            st.download_button("⬇️ Download PDF", report, "mysugr_report.pdf", "application/pdf")
