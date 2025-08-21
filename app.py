import streamlit as st
import pandas as pd
import altair as alt
import io
from datetime import datetime

# --- PDF / charts ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

# =========================
# Insulin correction logic
# =========================
def insulin_needed(current_glucose, target_glucose=150, isf=14.13):
    if current_glucose <= target_glucose:
        return 0.0
    return (current_glucose - target_glucose) / isf


# =========================
# Matplotlib chart helpers (for PDF)
# =========================
def fig_to_png_bytes(fig, dpi=160):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def build_trend_image(glucose_df):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = pd.to_datetime(glucose_df["DateTime"])
    y = glucose_df["Blood Sugar Measurement (mg/dL)"]

    # Shaded danger zones
    ax.axhspan(0, 70, alpha=0.15, color="orange", label="Low < 70")
    ax.axhspan(250, max(260, float(y.max()) + 40), alpha=0.15, color="red", label="High > 250")

    ax.plot(x, y, marker="o", linewidth=1.8)

    ax.set_title("Glucose Trend Over Time")
    ax.set_ylabel("Blood Glucose (mg/dL)")
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig_to_png_bytes(fig)

def build_daily_avg_bar_image(daily_avg_df):
    fig, ax = plt.subplots(figsize=(10, 4.0))
    x = pd.to_datetime(daily_avg_df["Date"])
    y = daily_avg_df["Blood Sugar Measurement (mg/dL)"]

    ax.bar(x, y)
    ax.set_title("Daily Average Glucose")
    ax.set_ylabel("Average (mg/dL)")
    ax.grid(True, axis="y", alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    fig.autofmt_xdate()
    return fig_to_png_bytes(fig)


# =========================
# PDF builder
# =========================
def generate_pdf(avg_glucose, latest_glucose, daily_avg_df, correction_units, target, isf, diet_text, trend_png, bar_png):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    elements = []

    # Title & metadata
    elements.append(Paragraph("📅 MySugr Weekly Report", styles["Title"]))
    elements.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Metrics
    elements.append(Paragraph(f"<b>Average Glucose:</b> {avg_glucose:.2f} mg/dL", styles["Normal"]))
    elements.append(Paragraph(f"<b>Latest Glucose:</b> {latest_glucose} mg/dL", styles["Normal"]))
    elements.append(Paragraph(f"<b>Insulin Correction:</b> {correction_units:.2f} units (Target={target}, ISF={isf})", styles["Normal"]))
    elements.append(Spacer(1, 10))

    # Diet
    elements.append(Paragraph("🥗 Diet Suggestion", styles["Heading2"]))
    elements.append(Paragraph(diet_text, styles["Normal"]))
    elements.append(Spacer(1, 16))

    # Trend chart
    elements.append(Paragraph("📈 Glucose Trend", styles["Heading2"]))
    trend_io = io.BytesIO(trend_png); trend_io.seek(0)
    elements.append(RLImage(trend_io, width=500, height=230))
    elements.append(Spacer(1, 16))

    # Daily average bar
    elements.append(Paragraph("📊 Daily Average Glucose", styles["Heading2"]))
    bar_io = io.BytesIO(bar_png); bar_io.seek(0)
    elements.append(RLImage(bar_io, width=500, height=220))
    elements.append(Spacer(1, 12))

    # Daily table
    table_data = [["Date", "Average Glucose (mg/dL)"]] + [
        [str(r["Date"]), f"{r['Blood Sugar Measurement (mg/dL)']:.2f}"]
        for _, r in daily_avg_df.iterrows()
    ]
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.teal),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.beige]),
    ]))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="MySugr Health Coach", page_icon="💉", layout="wide")

# Styles
st.markdown("""
<style>
    body { background-color: #f5f7fa; }
    .metric-card {
        background: linear-gradient(135deg, #f0f9ff, #cbebff);
        padding: 20px; border-radius: 16px; text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .diet-card {
        background: linear-gradient(135deg, #fff0f5, #ffe6f0);
        padding: 30px; border-radius: 18px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 20px 0;
    }
    .diet-card h2 { font-size: 28px; color: #b30047; margin-bottom: 15px; }
    .diet-card p  { font-size: 20px; font-weight: 500; line-height: 1.6; }
    h1 { color: #0066cc; text-align: center; font-weight: 700; }
    h2 { color: #004d99; margin-top: 25px; }
</style>
""", unsafe_allow_html=True)

st.title("💉 MySugr Health & Insulin Coach")
uploaded_file = st.file_uploader("📂 Upload your **mysugr.csv** file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    required = {"Blood Sugar Measurement (mg/dL)", "Date", "Time"}
    if required.issubset(df.columns):
        df["DateTime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors="coerce")
        glucose_df = df[["DateTime", "Blood Sugar Measurement (mg/dL)"]].dropna()

        if not glucose_df.empty:
            avg_glucose = glucose_df["Blood Sugar Measurement (mg/dL)"].mean()
            latest_row = glucose_df.iloc[-1]
            latest_glucose = latest_row["Blood Sugar Measurement (mg/dL)"]

            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>📊 Average Glucose</h3>
                        <p style="font-size:24px; font-weight:600;">{avg_glucose:.2f} mg/dL</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>🩸 Latest Glucose</h3>
                        <p style="font-size:24px; font-weight:600;">{latest_glucose} mg/dL</p>
                    </div>
                """, unsafe_allow_html=True)

            # Diet card (big)
            st.markdown("## 🥗 Suggested Diet")
            if latest_glucose > 250:
                diet_text = ("Avoid carbs, sugar, fried foods, and sweetened drinks. "
                             "Eat lean protein (chicken, fish, eggs), green veggies, and drink water. "
                             "Add a light walk after meals.")
                st.markdown(f"""
                    <div class="diet-card">
                        <h2>⚠️ High Glucose Detected</h2>
                        <p>❌ Avoid carbs/sugar/fried foods.<br>
                        ✅ Lean protein, veggies, water.<br>
                        🚶 Light walk after meals.</p>
                    </div>
                """, unsafe_allow_html=True)
            elif latest_glucose < 70:
                diet_text = ("Take juice, glucose tablets, or fruit immediately. "
                             "Follow with a protein-containing snack. Monitor closely and recheck in 15 minutes.")
                st.markdown(f"""
                    <div class="diet-card">
                        <h2>⚠️ Low Glucose Detected</h2>
                        <p>🥤 Fast carbs now (juice/tablets/fruit).<br>
                        🍞 Then a protein snack.<br>
                        ⏱️ Recheck in 15 minutes.</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                diet_text = ("Balanced meals with whole grains, lean protein, vegetables, and healthy fats. "
                             "Stay hydrated and keep regular meal timings.")
                st.markdown(f"""
                    <div class="diet-card">
                        <h2>✅ Glucose in Target Range</h2>
                        <p>🍛 Balanced carbs + protein + veggies.<br>
                        🥑 Include healthy fats.<br>
                        💧 Hydrate & keep regular meal times.</p>
                    </div>
                """, unsafe_allow_html=True)

            # Trend chart (Altair for UI)
            st.markdown("## 📈 Glucose Trend Over Time")
            base = alt.Chart(glucose_df).encode(x="DateTime:T")
            line = base.mark_line(point=True, color="blue").encode(
                y="Blood Sugar Measurement (mg/dL):Q"
            )
            high_zone = base.mark_area(opacity=0.2, color="red").encode(
                y=alt.Y("y:Q", scale=alt.Scale(domain=[250, float(glucose_df['Blood Sugar Measurement (mg/dL)'].max()) + 50])),
                y2=alt.value(250)
            )
            low_zone = base.mark_area(opacity=0.2, color="orange").encode(
                y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 70])),
                y2=alt.value(70)
            )
            st.altair_chart((low_zone + high_zone + line).properties(height=400), use_container_width=True)

            # Weekly report (daily averages)
            st.markdown("## 📅 Weekly Glucose Report")
            glucose_df["Date"] = glucose_df["DateTime"].dt.date
            daily_avg = glucose_df.groupby("Date")["Blood Sugar Measurement (mg/dL)"].mean().reset_index()

            bar_chart = alt.Chart(daily_avg).mark_bar(color="teal").encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("Blood Sugar Measurement (mg/dL):Q", title="Average Glucose"),
                tooltip=["Date", "Blood Sugar Measurement (mg/dL)"]
            ).properties(height=320)
            st.altair_chart(bar_chart, use_container_width=True)

            # Insulin calculator with timestamp selection
            st.markdown("## 💉 Insulin Correction Calculator")
            selected_row = st.selectbox(
                "📌 Select a glucose reading with timestamp:",
                options=glucose_df.itertuples(index=False),
                format_func=lambda x: f"{x.DateTime.strftime('%Y-%m-%d %H:%M')} → {x._2} mg/dL"
            )
            target = st.number_input("🎯 Target Glucose (mg/dL)", value=150, step=5)
            isf = st.number_input("⚖️ Insulin Sensitivity Factor (mg/dL per unit)", value=14.13, step=0.1)
            correction_units = insulin_needed(selected_row._2, target, isf)

            st.markdown(f"""
                <div class="metric-card">
                    <h3>💉 Suggested Correction Dose</h3>
                    <p style="font-size:24px; font-weight:600;">{correction_units:.2f} units</p>
                </div>
            """, unsafe_allow_html=True)

            # --------- Build chart PNGs for PDF ----------
            trend_png = build_trend_image(glucose_df)
            bar_png = build_daily_avg_bar_image(daily_avg)

            # --------- Generate & download PDF ----------
            pdf_data = generate_pdf(
                avg_glucose=avg_glucose,
                latest_glucose=latest_glucose,
                daily_avg_df=daily_avg,
                correction_units=correction_units,
                target=target,
                isf=isf,
                diet_text=diet_text,
                trend_png=trend_png,
                bar_png=bar_png
            )

            st.download_button(
                label="📥 Download Weekly Report (PDF)",
                data=pdf_data,
                file_name="mysugr_weekly_report.pdf",
                mime="application/pdf"
            )

        else:
            st.warning("No glucose rows found after parsing Date/Time.")
    else:
        st.error("❌ CSV must contain 'Date', 'Time', and 'Blood Sugar Measurement (mg/dL)' columns")

# Friendly note
st.caption("This tool does not replace medical advice. Always follow your clinician’s guidance.")
