import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# =========================
# Insulin Calculator
# =========================
def insulin_needed(current_glucose, target_glucose=150, isf=14.13):
    if current_glucose <= target_glucose:
        return 0.0
    return (current_glucose - target_glucose) / isf

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="MySugr AI Assistant", page_icon="💉", layout="wide")

st.title("💉 MySugr AI Health Assistant")
st.write("Upload your glucose data (CSV) and get **diet + insulin suggestions**, graphs, and downloadable reports.")

# Upload CSV
uploaded_file = st.file_uploader("📂 Upload your glucose CSV file", type=["csv"])

if uploaded_file:
    glucose_df = pd.read_csv(uploaded_file)

    # Standardize column names
    glucose_df.columns = [col.strip() for col in glucose_df.columns]
    if "DateTime" not in glucose_df.columns or "Blood Sugar Measurement (mg/dL)" not in glucose_df.columns:
        st.error("❌ CSV must contain 'DateTime' and 'Blood Sugar Measurement (mg/dL)' columns.")
    else:
        # Convert DateTime
        glucose_df["DateTime"] = pd.to_datetime(glucose_df["DateTime"], errors="coerce")
        glucose_df = glucose_df.dropna(subset=["DateTime"]).sort_values("DateTime")

        # Stats
        avg_glucose = glucose_df["Blood Sugar Measurement (mg/dL)"].mean()
        latest_glucose = glucose_df.iloc[-1]["Blood Sugar Measurement (mg/dL)"]

        st.metric("📊 Average Glucose", f"{avg_glucose:.2f} mg/dL")
        st.metric("🩸 Latest Glucose", f"{latest_glucose:.0f} mg/dL")

        # Graph
        st.subheader("📈 Glucose Trend")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(glucose_df["DateTime"], glucose_df["Blood Sugar Measurement (mg/dL)"], marker="o", linestyle="-")
        ax.axhline(150, color="green", linestyle="--", label="Target")
        ax.set_title("Glucose Over Time")
        ax.set_ylabel("Glucose (mg/dL)")
        ax.legend()
        st.pyplot(fig)

        # Insulin Calculator
        st.subheader("💉 Insulin Correction Calculator")
        selected_row = st.selectbox(
            "📌 Select a glucose reading:",
            options=glucose_df.itertuples(index=False),
            format_func=lambda x: f"{x.DateTime.strftime('%Y-%m-%d %H:%M')} → {x[1]} mg/dL"
        )

        current_glucose = selected_row[1]
        insulin_units = insulin_needed(current_glucose)
        st.success(f"👉 Suggested Insulin: **{insulin_units:.1f} units** (for {current_glucose} mg/dL)")

        # Diet Suggestions
        st.subheader("🥗 Personalized Diet Suggestions")
        if avg_glucose > 180:
            st.write("""
            - Avoid refined sugars & white carbs ❌  
            - Focus on **leafy greens, lentils, and whole grains** ✅  
            - Add **fiber-rich foods** (oats, beans) to slow sugar spikes 🌾  
            - Prefer **lean proteins** (fish, eggs, tofu) 🍳  
            """)
        elif avg_glucose < 90:
            st.write("""
            - Have **healthy carbs** like fruits 🍎, whole wheat bread, or brown rice 🍚  
            - Eat **small frequent meals** to prevent dips  
            - Keep a quick sugar source handy (banana, glucose tab) 🍌  
            """)
        else:
            st.write("""
            - Balanced diet: 🥗 veggies, 🍗 lean protein, 🌾 whole grains  
            - Stay hydrated 💧  
            - Avoid late-night junk food 🌙  
            """)

        # ===============================
        # 📄 PDF Export
        # ===============================
        if st.button("📥 Download PDF Report"):
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer)
            styles = getSampleStyleSheet()
            flowables = []

            # Title
            flowables.append(Paragraph("📊 Glucose & Insulin Report", styles['Title']))
            flowables.append(Spacer(1, 12))

            # Stats
            flowables.append(Paragraph(f"📊 Average Glucose: {avg_glucose:.2f} mg/dL", styles['Normal']))
            flowables.append(Paragraph(f"🩸 Latest Glucose: {latest_glucose:.0f} mg/dL", styles['Normal']))
            flowables.append(Spacer(1, 12))

            # Insulin Suggestion
            flowables.append(Paragraph("💉 Insulin Suggestion", styles['Heading2']))
            flowables.append(Paragraph(
                f"- Date/Time: {selected_row.DateTime.strftime('%Y-%m-%d %H:%M')}<br/>"
                f"- Current Glucose: {current_glucose} mg/dL<br/>"
                f"- Target: 150 mg/dL<br/>"
                f"- Suggested Dose: {insulin_units:.1f} units",
                styles['Normal']
            ))
            flowables.append(Spacer(1, 12))

            # Table of last 10 readings
            table_data = [["Date/Time", "Glucose (mg/dL)"]]
            for _, row in glucose_df.tail(10).iterrows():
                table_data.append([row['DateTime'].strftime('%Y-%m-%d %H:%M'), row['Blood Sugar Measurement (mg/dL)']])

            table = Table(table_data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            flowables.append(table)
            flowables.append(Spacer(1, 12))

            # Save graph to image & embed
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format="PNG")
            img_buffer.seek(0)
            flowables.append(RLImage(img_buffer, width=400, height=200))

            # Build PDF
            doc.build(flowables)

            # Download button
            st.download_button(
                "⬇️ Download Report",
                data=pdf_buffer.getvalue(),
                file_name="glucose_report.pdf",
                mime="application/pdf"
            )
