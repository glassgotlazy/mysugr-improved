import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

# -------------------
# PAGE CONFIG
# -------------------
st.set_page_config(page_title="MySugar Advanced", page_icon="💉", layout="wide")

# -------------------
# HEADER
# -------------------
st.markdown(
    """
    <style>
        .main-title {
            font-size: 36px;
            color: #2E86C1;
            text-align: center;
            font-weight: bold;
        }
        .subtitle {
            text-align: center;
            color: #117A65;
            font-size: 18px;
        }
    </style>
    <div class="main-title">💉 MySugar Advanced</div>
    <div class="subtitle">Track Blood Sugar • Manage Insulin • Stay Healthy</div>
    <br>
    """,
    unsafe_allow_html=True
)

# -------------------
# FILE UPLOAD
# -------------------
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV Data", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Clean column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Handle missing datetime
        if "datetime" not in df.columns:
            if "date" in df.columns and "time" in df.columns:
                df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
            else:
                st.error("❌ No valid 'datetime' found.")
                st.stop()

        # Ensure main columns exist
        if "blood_sugar_measurement_(mg/dl)" not in df.columns:
            st.error("❌ Missing 'blood sugar measurement (mg/dl)' column.")
            st.stop()

        if "insulin" not in df.columns:
            # Try to merge different insulin-related cols
            insulin_cols = [c for c in df.columns if "insulin" in c]
            if insulin_cols:
                df["insulin"] = df[insulin_cols].sum(axis=1, numeric_only=True)
            else:
                df["insulin"] = 0

        # Sort values
        df = df.sort_values("datetime")

        # -------------------
        # NAVIGATION TABS
        # -------------------
        tabs = st.tabs(["📊 Dashboard", "💉 Insulin Insights", "🍽 Diet Tracking", "📄 Reports"])

        # -------------------
        # TAB 1: DASHBOARD
        # -------------------
        with tabs[0]:
            st.subheader("📊 Blood Sugar Overview")

            st.line_chart(df.set_index("datetime")["blood_sugar_measurement_(mg/dl)"])

            avg = df["blood_sugar_measurement_(mg/dl)"].mean()
            st.metric("Average Blood Sugar", f"{avg:.1f} mg/dL")

        # -------------------
        # TAB 2: INSULIN
        # -------------------
        with tabs[1]:
            st.subheader("💉 Insulin Tracking")

            st.line_chart(df.set_index("datetime")["insulin"])

            total_insulin = df["insulin"].sum()
            st.metric("Total Insulin Taken", f"{total_insulin:.1f} units")

            # Recommended adjustment
            avg_sugar = df["blood_sugar_measurement_(mg/dl)"].mean()
            if avg_sugar > 180:
                st.warning("⚠️ High average sugar detected. Consider reviewing insulin dosage with your doctor.")
            elif avg_sugar < 70:
                st.warning("⚠️ Low average sugar detected. Risk of hypoglycemia!")
            else:
                st.success("✅ Your blood sugar levels are within a good range!")

        # -------------------
        # TAB 3: DIET
        # -------------------
        with tabs[2]:
            st.subheader("🍽 Diet Tracking")

            followed_diet = st.checkbox("Did you follow your planned diet?")
            if not followed_diet:
                alt_diet = st.text_input("If not, what did you eat instead?")
                if alt_diet:
                    st.info(f"🍕 You reported eating: {alt_diet}")

        # -------------------
        # TAB 4: REPORT
        # -------------------
        with tabs[3]:
            st.subheader("📄 Generate Health Report")

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("MySugar Health Report", styles["Title"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Average Blood Sugar: {avg:.1f} mg/dL", styles["Normal"]))
            elements.append(Paragraph(f"Total Insulin: {total_insulin:.1f} units", styles["Normal"]))

            doc.build(elements)

            st.download_button(
                label="⬇️ Download PDF Report",
                data=buffer.getvalue(),
                file_name="health_report.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

else:
    st.info("📂 Please upload your CSV file to continue.")
