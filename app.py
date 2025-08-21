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
      # ==============================
# 📊 Insulin Recommendation Tab
# ==============================
with tabs[3]:
    st.markdown("### 💉 Insulin Recommendations")
    st.write("Get AI-assisted insights for your insulin dosage.")

    # Sidebar-like input panel
    st.markdown("#### 🔧 Customize your input")
    col1, col2 = st.columns(2)

    with col1:
        current_sugar = st.number_input(
            "🩸 Current Blood Sugar (mg/dL)", min_value=50, max_value=400, value=120
        )
        target_sugar = st.number_input(
            "🎯 Target Blood Sugar (mg/dL)", min_value=70, max_value=150, value=100
        )

    with col2:
        carbs = st.slider(
            "🍽️ Estimated Carbs (grams)", min_value=0, max_value=200, value=50, step=5
        )
        insulin_sensitivity = st.slider(
            "⚡ Insulin Sensitivity Factor (mg/dL drop per unit)",
            min_value=10, max_value=100, value=50, step=5
        )
        carb_ratio = st.slider(
            "🥖 Insulin-to-Carb Ratio (g/unit)",
            min_value=5, max_value=30, value=15, step=1
        )

    # === Calculation ===
    correction_dose = max((current_sugar - target_sugar) / insulin_sensitivity, 0)
    meal_dose = carbs / carb_ratio
    total_dose = round(correction_dose + meal_dose, 1)

    # === Fancy gauge meter ===
    import plotly.graph_objects as go

    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=total_dose,
            delta={'reference': 5, "increasing": {"color": "red"}, "decreasing": {"color": "green"}},
            title={'text': "💉 Suggested Insulin Units"},
            gauge={
                'axis': {'range': [0, 20]},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgreen"},
                    {'range': [5, 10], 'color': "yellow"},
                    {'range': [10, 20], 'color': "red"}
                ],
                'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.8, 'value': total_dose}
            }
        )
    )

    st.plotly_chart(gauge, use_container_width=True)

    # === Recommendation Cards ===
    st.markdown("#### 🧾 Recommendation")
    if total_dose == 0:
        st.success("✅ No insulin needed. You're within target range!")
    elif total_dose <= 5:
        st.info(f"👉 Suggested Dose: **{total_dose} units** (small correction).")
    elif total_dose <= 10:
        st.warning(f"⚠️ Suggested Dose: **{total_dose} units** (moderate dose). Monitor closely.")
    else:
        st.error(f"🚨 Suggested Dose: **{total_dose} units** (high dose). Please double-check with your doctor!")

    # === Historical insulin vs sugar trends ===
    if not df.empty:
        st.markdown("#### 📈 Insulin & Sugar Trends")
        insulin_trend = df[['datetime', 'blood sugar measurement (mg/dl)', 'insulin']]
        insulin_trend = insulin_trend.dropna()

        fig = px.line(
            insulin_trend,
            x="datetime",
            y=["blood sugar measurement (mg/dl)", "insulin"],
            labels={"value": "Level", "variable": "Measurement"},
            title="📊 Blood Sugar vs Insulin Trend",
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
