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
               # -------------------
        # INSULIN TAB
        # -------------------
        with tabs[1]:
            st.subheader("💉 Insulin Tracking")

            # Line chart of insulin usage
            st.line_chart(df.set_index("datetime")["insulin"], height=300)

            total_insulin = df["insulin"].sum()
            st.metric("Total Insulin Taken", f"{total_insulin:.1f} units")

            st.markdown("### 🧠 Smart Insulin Recommendations")

            latest_value = df["blood_sugar_measurement_(mg/dl)"].iloc[-1]
            st.write(f"📌 Latest Blood Sugar: **{latest_value} mg/dL**")

            # -------------------
            # Recommendation + Gauge
            # -------------------
            import plotly.graph_objects as go

            if latest_value < 70:
                suggestion = "⚠️ Low! Eat carbs, **no insulin now**."
                color = "red"
                value = 20
            elif 70 <= latest_value <= 140:
                suggestion = "✅ Normal range. Maintain your current insulin dose."
                color = "green"
                value = 50
            elif 140 < latest_value <= 200:
                suggestion = "⚠️ High. Suggested correction: **2–4 units insulin**."
                color = "orange"
                value = 75
            else:
                suggestion = "🔥 Very high! Suggested correction: **5–8 units insulin**."
                color = "red"
                value = 95

            # Show recommendation card
            st.markdown(
                f"""
                <div style="padding:15px; border-radius:12px; background-color:{color}; color:white; font-size:18px;">
                    {suggestion}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Gauge chart
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    title={"text": "Insulin Suggestion Level"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": color},
                        "steps": [
                            {"range": [0, 50], "color": "lightgreen"},
                            {"range": [50, 80], "color": "yellow"},
                            {"range": [80, 100], "color": "red"},
                        ],
                    },
                )
            )
            st.plotly_chart(fig, use_container_width=True)


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
