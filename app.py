import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# --- Page Config ---
st.set_page_config(page_title="MySugar Dashboard", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        .stMetric {background: white; border-radius: 15px; padding: 15px; 
                   box-shadow: 0px 2px 10px rgba(0,0,0,0.1);}
        .top-bar {background-color: #4CAF50; padding: 14px; border-radius: 10px; margin-bottom: 15px;}
        .top-bar h1 {color: white; font-size: 28px; text-align: center; margin: 0;}
        .stTabs [role="tablist"] {justify-content: center;}
    </style>
""", unsafe_allow_html=True)

# --- Top Bar ---
st.markdown("<div class='top-bar'><h1>📊 MySugar Health Dashboard</h1></div>", unsafe_allow_html=True)

# --- File Upload ---
uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize columns
    df.columns = [c.strip().lower() for c in df.columns]

    # Fix datetime column
    if "datetime" not in df.columns and "date" in df.columns and "time" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    elif "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # Find relevant columns
    sugar_col = [c for c in df.columns if "blood sugar" in c][0]
    insulin_cols = [c for c in df.columns if "insulin" in c]

    # --- Summary Metrics ---
    st.subheader("📌 Quick Summary")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📉 Avg Blood Sugar", f"{df[sugar_col].mean():.1f} mg/dL")
    with c2: st.metric("💉 Total Insulin", f"{df[insulin_cols].sum().sum():.1f} units")
    with c3: st.metric("📝 Records", len(df))

    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Blood Sugar", "💉 Insulin", "✅ Daily Checks", "📄 Report"])

    # --- Tab 1: Blood Sugar ---
    with tab1:
        st.subheader("📈 Blood Sugar Trend")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(df["datetime"], df[sugar_col], marker="o", linestyle="-", color="red", label="Blood Sugar")
        ax.set_xlabel("Date")
        ax.set_ylabel("mg/dL")
        ax.legend()
        st.pyplot(fig)

    # --- Tab 2: Insulin ---
    with tab2:
        st.subheader("💉 Insulin Trend")
        fig, ax = plt.subplots(figsize=(8,4))
        for col in insulin_cols:
            ax.plot(df["datetime"], df[col], marker="o", linestyle="--", label=col)
        ax.set_xlabel("Date")
        ax.set_ylabel("Units")
        ax.legend()
        st.pyplot(fig)

    # --- Tab 3: Daily Checks ---
    with tab3:
        st.subheader("✅ Daily Checks")

        diet_followed = st.checkbox("Diet followed?", key="diet_check")
        diet_note = st.text_input("If not, what diet was followed?", key="diet_note") if not diet_followed else None

        insulin_followed = st.checkbox("Insulin taken as prescribed?", key="insulin_check")
        insulin_note = st.text_input("If not, what insulin routine was followed?", key="insulin_note") if not insulin_followed else None

    # --- Tab 4: Report ---
    with tab4:
        st.subheader("📄 Export Report")
        if st.button("Generate PDF Report"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()
            content = []

            content.append(Paragraph("MySugar Report", styles['Title']))
            content.append(Spacer(1, 12))
            content.append(Paragraph(f"Average Blood Sugar: {df[sugar_col].mean():.1f} mg/dL", styles['Normal']))
            content.append(Paragraph(f"Total Insulin: {df[insulin_cols].sum().sum():.1f} units", styles['Normal']))
            content.append(Spacer(1, 12))

            if not diet_followed:
                content.append(Paragraph(f"❌ Diet not followed: {diet_note}", styles['Normal']))
            else:
                content.append(Paragraph("✅ Diet followed", styles['Normal']))

            if not insulin_followed:
                content.append(Paragraph(f"❌ Insulin not followed: {insulin_note}", styles['Normal']))
            else:
                content.append(Paragraph("✅ Insulin followed", styles['Normal']))

            doc.build(content)
            buffer.seek(0)
            st.download_button("⬇️ Download Report", buffer, "mysugar_report.pdf", "application/pdf")

else:
    st.info("👆 Please upload a CSV file to get started.")
