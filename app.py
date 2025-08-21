# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# =========================
# UI CONFIG & STYLES
# =========================
st.set_page_config(page_title="MySugr Health Coach", page_icon="💉", layout="wide")
st.markdown("""
<style>
    body { background-color: #f5f7fa; }
    .metric-card {
        background: linear-gradient(135deg, #6e2e42, #cbebff);
        padding: 20px; border-radius: 16px; text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .diet-card {
        background: linear-gradient(135deg, #1e942f, #ffe6f0);
        padding: 28px; border-radius: 18px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 20px 0;
    }
    .diet-card h2 { font-size: 28px; color: #b3602d; margin-bottom: 12px; }
    .diet-card p  { font-size: 20px; font-weight: 500; line-height: 1.55; }
    h1 { color: #0066cc; text-align: center; font-weight: 700; }
    h2 { color: #004d99; margin-top: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("💉 MySugr Health Coach")
st.caption("Upload your mySugr CSV to see trends, get diet guidance, insulin correction suggestions, and download a PDF. "
           "This tool does not replace medical advice. Always follow your clinician’s guidance.")

# =========================
# HELPER FUNCTIONS
# =========================
def insulin_needed(current_glucose: float, target_glucose: float = 150.0, isf: float = 14.13) -> float:
    """Calculate correction insulin units using ISF."""
    if pd.isna(current_glucose):
        return 0.0
    if current_glucose <= target_glucose:
        return 0.0
    return max(0.0, (float(current_glucose) - float(target_glucose)) / float(isf))

def detect_columns(df: pd.DataFrame):
    """Auto-detect datetime and glucose columns (handles typical mySugr headers)."""
    cols = [c.strip() for c in df.columns]
    lower = [c.lower().strip() for c in cols]
    col_map = dict(zip(lower, cols))

    # Candidates for glucose
    glucose_candidates_exact = [
        "blood sugar measurement (mg/dl)",
        "blood glucose (mg/dl)",
        "blood glucose",
        "glucose",
        "glucose (mg/dl)",
        "bg",
        "measurement",
        "glucose value",
    ]
    glucose_col = None
    for key in glucose_candidates_exact:
        if key in col_map:
            glucose_col = col_map[key]
            break
    if glucose_col is None:
        # substring search
        for i, lc in enumerate(lower):
            if ("glucose" in lc or "sugar" in lc or "measurement" in lc) and "insulin" not in lc:
                glucose_col = cols[i]
                break

    # Datetime can be a single column or Date + Time
    dt_col = None
    date_col = None
    time_col = None

    # direct timestamp-like column
    dt_candidates = ["datetime", "timestamp", "date time", "time stamp"]
    for key in dt_candidates:
        if key in col_map:
            dt_col = col_map[key]
            break

    if dt_col is None:
        # look for "date" and "time" columns separately
        for i, lc in enumerate(lower):
            if lc == "date" or ("date" in lc and "updated" not in lc):
                date_col = cols[i]
        for i, lc in enumerate(lower):
            if lc == "time" or ("time" in lc and "zone" not in lc):
                time_col = cols[i]

    return dt_col, date_col, time_col, glucose_col

def build_trend_figure(df: pd.DataFrame, dt_col: str, g_col: str):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = pd.to_datetime(df[dt_col])
    y = pd.to_numeric(df[g_col], errors="coerce")

    # Shaded danger zones
    ymax = float(np.nanmax(y)) if np.isfinite(np.nanmax(y)) else 300.0
    ax.axhspan(0, 70, alpha=0.18, color="orange", label="Low < 70")
    ax.axhspan(250, max(260, ymax + 40), alpha=0.18, color="red", label="High > 250")

    ax.plot(x, y, marker="o", linewidth=1.8)
    ax.axhline(150, color="green", linestyle="--", label="Target 150")

    ax.set_title("Glucose Trend Over Time")
    ax.set_ylabel("Blood Glucose (mg/dL)")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig

def build_daily_avg_bar_figure(daily_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4.0))
    x = pd.to_datetime(daily_df["Date"])
    y = daily_df["Average"]

    ax.bar(x, y)
    ax.set_title("Daily Average Glucose")
    ax.set_ylabel("Average (mg/dL)")
    ax.grid(True, axis="y", alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    fig.autofmt_xdate()
    return fig

def fig_to_png_bytes(fig, dpi=160):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def generate_pdf(avg_glucose, latest_glucose, selected_dt, current_glucose, insulin_units,
                 daily_avg_df, trend_png, bar_png, diet_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("📅 MySugr Weekly Report", styles["Title"]))
    elems.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    elems.append(Spacer(1, 10))

    # Metrics
    elems.append(Paragraph(f"<b>Average Glucose:</b> {avg_glucose:.2f} mg/dL", styles["Normal"]))
    elems.append(Paragraph(f"<b>Latest Glucose:</b> {latest_glucose:.0f} mg/dL", styles["Normal"]))
    if selected_dt is not None:
        elems.append(Paragraph("<b>Insulin Suggestion</b>", styles["Heading2"]))
        elems.append(Paragraph(
            f"Date/Time: {selected_dt}<br/>"
            f"Current Glucose: {current_glucose:.0f} mg/dL<br/>"
            f"Target: 150 mg/dL<br/>"
            f"Suggested Correction: {insulin_units:.1f} units",
            styles["Normal"]
        ))
    elems.append(Spacer(1, 8))

    # Diet
    elems.append(Paragraph("🥗 Diet Suggestion", styles["Heading2"]))
    elems.append(Paragraph(diet_text, styles["Normal"]))
    elems.append(Spacer(1, 10))

    # Trend chart
    if trend_png:
        trend_io = BytesIO(trend_png); trend_io.seek(0)
        elems.append(Paragraph("📈 Glucose Trend", styles["Heading2"]))
        elems.append(RLImage(trend_io, width=480, height=230))
        elems.append(Spacer(1, 10))

    # Daily average bar
    if bar_png:
        bar_io = BytesIO(bar_png); bar_io.seek(0)
        elems.append(Paragraph("📊 Daily Average Glucose", styles["Heading2"]))
        elems.append(RLImage(bar_io, width=480, height=220))
        elems.append(Spacer(1, 10))

    # Daily table
    if not daily_avg_df.empty:
        table_data = [["Date", "Average Glucose (mg/dL)"]] + [
            [str(r["Date"]), f"{r['Average']:.2f}"] for _, r in daily_avg_df.iterrows()
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
        elems.append(table)

    doc.build(elems)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# =========================
# FILE UPLOAD
# =========================
uploaded = st.file_uploader("📂 Upload your mySugr CSV (any common header names are okay)", type=["csv"])

if uploaded:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

    # Detect columns
    dt_col, date_col, time_col, glucose_col = detect_columns(df)

    if glucose_col is None or (dt_col is None and (date_col is None or time_col is None)):
        st.error("❌ Could not detect required columns.\n\n"
                 "- Provide either a combined timestamp column (e.g., 'DateTime'/'Timestamp')\n"
                 "- Or separate 'Date' and 'Time' columns\n"
                 "- And a glucose column (e.g., 'Blood Sugar Measurement (mg/dL)' / 'Glucose').")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    # Build DateTime column
    if dt_col is None:
        df["__DateTime"] = pd.to_datetime(df[date_col].astype(str) + " " + df[time_col].astype(str), errors="coerce")
        dt_col = "__DateTime"
    else:
        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")

    # Clean & sort
    df[glucose_col] = pd.to_numeric(df[glucose_col], errors="coerce")
    df = df.dropna(subset=[dt_col, glucose_col]).sort_values(dt_col)
    if df.empty:
        st.warning("No valid rows after parsing Date/Time and glucose values.")
        st.stop()

    # =========================
    # METRICS
    # =========================
    avg_glucose = float(df[glucose_col].mean())
    latest_glucose = float(df.iloc[-1][glucose_col])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Average Glucose</h3>
                <p style="font-size:24px; font-weight:600;">{avg_glucose:.2f} mg/dL</p>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <h3>🩸 Latest Glucose</h3>
                <p style="font-size:24px; font-weight:600;">{latest_glucose:.0f} mg/dL</p>
            </div>
        """, unsafe_allow_html=True)

    # =========================
    # DIET CARD (big)
    # =========================
    st.markdown("## 🥗 Suggested Diet")
    if latest_glucose > 250:
        diet_text = ("Avoid refined carbs/sugary foods and sweetened drinks. "
                     "Choose lean protein (chicken/fish/eggs), green veggies, and water. "
                     "Consider a gentle 10–20 min walk after meals.")
        st.markdown("""
            <div class="diet-card">
                <h2>⚠️ High Glucose Detected</h2>
                <p>❌ Skip refined carbs & sugary drinks.<br>
                ✅ Lean protein + veggies + water.<br>
                🚶 Light walk after meals.</p>
            </div>
        """, unsafe_allow_html=True)
    elif latest_glucose < 70:
        diet_text = ("Take fast-acting carbs now (juice, glucose tablets, or fruit). "
                     "Then follow with a protein snack (e.g., peanut butter toast). "
                     "Recheck in 15 minutes and avoid being alone.")
        st.markdown("""
            <div class="diet-card">
                <h2>⚠️ Low Glucose Detected</h2>
                <p>🥤 Fast carbs now (juice/tablets/fruit).<br>
                🍞 Then a protein snack.<br>
                ⏱️ Recheck in 15 minutes.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        diet_text = ("Balanced meals: whole grains + lean protein + vegetables + healthy fats. "
                     "Hydrate well and keep regular meal timing.")
        st.markdown("""
            <div class="diet-card">
                <h2>✅ Glucose in Target Range</h2>
                <p>🍛 Balanced carbs + protein + veggies.<br>
                🥑 Include healthy fats.<br>
                💧 Hydrate & keep regular meal times.</p>
            </div>
        """, unsafe_allow_html=True)

    # =========================
    # TREND CHART
    # =========================
    st.markdown("## 📈 Glucose Trend Over Time")
    trend_fig = build_trend_figure(df, dt_col, glucose_col)
    st.pyplot(trend_fig)

    # =========================
    # WEEKLY REPORT (daily averages)
    # =========================
    st.markdown("## 📅 Weekly Glucose Report")
    df["__Date"] = pd.to_datetime(df[dt_col]).dt.date
    daily_avg = (
        df.groupby("__Date")[glucose_col]
        .mean()
        .rename("Average")
        .reset_index()
        .rename(columns={"__Date": "Date"})
    )
    bar_fig = build_daily_avg_bar_figure(daily_avg)
    st.pyplot(bar_fig)

    # =========================
    # INSULIN CORRECTION ADVISOR (safe select)
    # =========================
    st.markdown("## 💉 Insulin Correction Advisor")

    # Create a human-readable label for dropdown
    view_df = df[[dt_col, glucose_col]].copy()
    view_df["Label"] = view_df.apply(
        lambda r: f"{pd.to_datetime(r[dt_col]).strftime('%Y-%m-%d %H:%M')} → {int(round(r[glucose_col]))} mg/dL", axis=1
    )

    chosen_label = st.selectbox("📌 Select a reading:", options=view_df["Label"].tolist())
    chosen_row = view_df[view_df["Label"] == chosen_label].iloc[0]
    selected_dt_str = pd.to_datetime(chosen_row[dt_col]).strftime("%Y-%m-%d %H:%M")
    current_glucose = float(df.loc[df[dt_col] == pd.to_datetime(chosen_row[dt_col]), glucose_col].iloc[-1])

    # Editable target & ISF
    cc1, cc2 = st.columns(2)
    with cc1:
        target_glucose = st.number_input("🎯 Target Glucose (mg/dL)", value=150, step=5)
    with cc2:
        isf = st.number_input("⚖️ Insulin Sensitivity Factor (mg/dL per unit)", value=14.13, step=0.01, format="%.2f")

    correction_units = insulin_needed(current_glucose, target_glucose, isf)

    st.success(
        f"**Date/Time:** {selected_dt_str}  \n"
        f"**Current:** {current_glucose:.0f} mg/dL  \n"
        f"**Target:** {target_glucose:.0f} mg/dL  \n"
        f"**Suggested Correction:** {correction_units:.1f} units"
    )

    # =========================
    # PDF EXPORT (with charts)
    # =========================
    st.markdown("## 📄 Download PDF Report")
    trend_png = fig_to_png_bytes(build_trend_figure(df, dt_col, glucose_col))
    bar_png = fig_to_png_bytes(build_daily_avg_bar_figure(daily_avg))

    pdf_bytes = generate_pdf(
        avg_glucose=avg_glucose,
        latest_glucose=latest_glucose,
        selected_dt=selected_dt_str,
        current_glucose=current_glucose,
        insulin_units=correction_units,
        daily_avg_df=daily_avg,
        trend_png=trend_png,
        bar_png=bar_png,
        diet_text=diet_text
    )

    st.download_button(
        label="📥 Download Weekly Report (PDF)",
        data=pdf_bytes,
        file_name="mysugr_weekly_report.pdf",
        mime="application/pdf"
    )
