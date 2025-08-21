import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# --- Page Config ---
st.set_page_config(page_title="MySugar Dashboard", layout="wide")

# --- Custom CSS for style ---
st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        .reportview-container .markdown-text-container {font-family: 'Arial';}
        .stMetric {background: white; border-radius: 15px; padding: 15px; box-shadow: 0px 2px 10px rgba(0,0,0,0.1);}
        .top-bar {background-color: #4CAF50; padding: 12px; border-radius: 8px; margin-bottom: 15px;}
        .top-bar h1 {color: white; font-size: 28px; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# --- Top Bar ---
st.markdown("<div class='top-bar'><h1>📊 MySugar Health Dashboard</h1></div>", unsafe_allow_html=True)

# --- File Upload ---
uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Handle datetime from "date" + "time"
    if "datetime" not in df.columns and "date" in df.columns and "time" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    elif "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # Pick main columns
    sugar_col = [c for c in df.columns if "blood sugar" in c][0]
    insulin_cols = [c for c in df.columns if "insulin" in c]

    # --- Summary Cards ---
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📉 Avg Blood Sugar", f"{df[sugar_col].mean():.1f} mg/dL")
    with c2: st.metric("💉 Total Insulin", f"{df[insulin_cols].sum().sum():.1f} units")
    with c3: st.metric("📝 Records", len(df))

    # --- Charts ---
    st.subheader("📈 Blood Sugar Trend")
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(df["datetime"], df[sugar_col], marker="o", linestyle="-", color="red", label="Blood Sugar")
    ax.set_xlabel("Date")
    ax.set_ylabel("mg/dL")
    ax.legend()
    st.pyplot(fig)

    st.subheader("💉 Insulin Trend")
    fig, ax = plt.subplots(figsize=(8,4))
    for col in insulin_cols:
        ax.plot(df["datetime"], df[col], marker="o", linestyle="--", label=col)
    ax.set_xlabel("Date")
    ax.set_ylabel("Units")
    ax.legend()
    st.pyplot(fig)

    # --- Diet & Insulin Check (fixed duplicate IDs) ---
    st.subheader("✅ Daily Checks")
    diet_followed = st.checkbox("Diet followed?", key="diet_check")
    if not diet_followed:
        diet_note = st.text_input("If not, what diet was followed?", key="diet_note")
    else:
        diet_note = None

    insulin_followed = st.checkbox("Insulin taken as prescribed?", key="insulin_check")
    if not insulin_followed:
        insulin_note = st.text_input("If not, what insulin routine was followed?", key="insulin_note")
    else:
        insulin_note = None

    # --- Export to PDF ---
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
