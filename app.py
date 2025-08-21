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
# HEADER WITH EXTRA SPACING
# -------------------
st.markdown(
    """
    <style>
        .main-title {
            font-size: 36px;
            color: #2E86C1;
            text-align: center;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        .subtitle {
            text-align: center;
            color: #117A65;
            font-size: 18px;
            margin-bottom: 40px;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
    <div class="main-title">💉 MySugar Advanced</div>
    <div class="subtitle">Track Blood Sugar • Manage Insulin • Stay Healthy</div>
    """,
    unsafe_allow_html=True
)

# -------------------
# PROCESS FILE FUNCTION
# -------------------
def process_file(file):
    try:
        df = pd.read_csv(file)

        # Clean column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Handle datetime
        if "datetime" not in df.columns:
            if "date" in df.columns and "time" in df.columns:
                df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
            else:
                st.error("❌ No valid 'datetime' found.")
                return

        # Ensure sugar column exists
        if "blood_sugar_measurement_(mg/dl)" not in df.columns:
            st.error("❌ Missing 'blood sugar measurement (mg/dl)' column.")
            return

        # Handle insulin column
        if "insulin" not in df.columns:
            insulin_cols = [c for c in df.columns if "insulin" in c]
            if insulin_cols:
                df["insulin"] = df[insulin_cols].sum(axis=1, numeric_only=True)
            else:
                df["insulin"] = 0

        df = df.sort_values("datetime")

        # -------------------
        # NAVIGATION TABS
        # -------------------
        tabs = st.tabs(["📊 Dashboard", "💉 Insulin Insights", "🍽 Diet Tracking", "📄 Reports"])

        # Dashboard
        with tabs[0]:
            st.subheader("📊 Blood Sugar Overview")
            st.line_chart(df.set_index("datetime")["blood_sugar_measurement_(mg/dl)"])
            avg = df["blood_sugar_measurement_(mg/dl)"].mean()
            st.metric("Average Blood Sugar", f"{avg:.1f} mg/dL")

        # =====================
        # INSULIN TAB
        # =====================
        with tabs[1]:
            st.subheader("💉 Insulin Insights")

            # Plot insulin usage
            st.markdown("#### 📊 Insulin Over Time")
            st.line_chart(df.set_index("datetime")["insulin"])

            # Daily average insulin
            daily_insulin = df.groupby(df["datetime"].dt.date)["insulin"].sum()
            st.bar_chart(daily_insulin)

            # Latest reading
            latest_value = df["blood_sugar_measurement_(mg/dl)"].iloc[-1]
            st.markdown(f"### 📌 Latest Blood Sugar: **{latest_value} mg/dL**")

            # -----------------
            # INSULIN RECOMMENDATION GAUGE
            # -----------------
            st.markdown("#### 🎯 Insulin Recommendation Gauge")

            if latest_value < 70:
                suggestion = "⚠️ LOW! Eat carbs immediately, no insulin now."
                gauge_level = 0
                color = "🔵"
            elif 70 <= latest_value <= 140:
                suggestion = "✅ Normal range. Maintain current insulin dose."
                gauge_level = 40
                color = "🟢"
            elif 140 < latest_value <= 200:
                suggestion = "⚠️ High. Suggested correction: **2–4 units insulin**."
                gauge_level = 70
                color = "🟡"
            else:
                suggestion = "🔥 Very high! Suggested correction: **5–8 units insulin**."
                gauge_level = 100
                color = "🔴"

            # Styled progress bar
            st.progress(gauge_level / 100)

            # Show recommendation
            st.markdown(f"### {color} Recommendation")
            st.info(suggestion)

            # -----------------
            # SUMMARY TABLE
            # -----------------
            st.markdown("#### 📅 Daily Insulin Summary")
            insulin_summary = pd.DataFrame({
                "Date": daily_insulin.index,
                "Total Insulin (units)": daily_insulin.values
            })
            st.dataframe(insulin_summary, use_container_width=True)

         



        # Diet
        with tabs[2]:
            st.subheader("🍽 Diet Tracking")
            followed_diet = st.checkbox("Did you follow your planned diet?")
            if not followed_diet:
                alt_diet = st.text_input("If not, what did you eat instead?")
                if alt_diet:
                    st.info(f"🍕 You reported eating: {alt_diet}")

        # Report
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


# -------------------
# FILE UPLOAD
# -------------------
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV Data", type="csv")
if uploaded_file:
    process_file(uploaded_file)
else:
    st.info("📂 Please upload your CSV file to continue.")
