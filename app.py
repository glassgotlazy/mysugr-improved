# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from io import BytesIO
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# =========================
# Config & Theming
# =========================
st.set_page_config(page_title="MySugr Dashboard", page_icon="💉", layout="wide")
st.markdown("""
<style>
/* Soft modern look */
:root { --card-bg: #f7fbff; --accent: #b3602d; }
.block-container { padding-top: 1.2rem; }
h1, h2, h3 { color: var(--accent); }
.metric-card{
  background: linear-gradient(135deg, #709615, #fafdff);
  border: 1px solid #e5eef8; border-radius: 18px; padding: 18px;
  box-shadow: 0 4px 14px rgba(10,30,60,0.06);
}
.diet-card{
  background: linear-gradient(135deg, #3dcc91, #fff7fb);
  border: 1px solid #fde1eb; border-radius: 18px; padding: 24px;
  box-shadow: 0 8px 18px rgba(200,0,80,0.08);
}
.big-number{ font-size: 26px; font-weight: 700; }
.subtle{ color:#141414; }
</style>
""", unsafe_allow_html=True)

# =========================
# Helpers
# =========================
def robust_detect_columns(df: pd.DataFrame):
    """
    Detect datetime and glucose columns with flexible rules.
    Supports:
      - Single timestamp column (e.g., DateTime, Timestamp)
      - Separate Date + Time columns
      - Glucose columns like: Blood Sugar Measurement (mg/dL), Blood Glucose (mg/dL), Glucose, etc.
    Returns: (dt_col, glucose_col, info_dict)
    If Date+Time separate, creates a new __datetime column.
    """
    original_cols = df.columns.tolist()
    lower_map = {c.lower().strip(): c for c in df.columns}
    lowers = list(lower_map.keys())

    # Candidate keys
    dt_single_candidates = ["datetime", "timestamp", "date time", "time stamp"]
    date_candidates = ["date"]
    time_candidates = ["time"]

    glucose_exact = [
        "blood sugar measurement (mg/dl)", "blood sugar measurement (mg/dl)", "blood glucose (mg/dl)",
        "blood glucose", "glucose (mg/dl)", "glucose value", "glucose", "bg", "measurement"
    ]

    # Detect glucose col
    glucose_col = None
    for key in glucose_exact:
        if key in lower_map:
            glucose_col = lower_map[key]
            break
    if glucose_col is None:
        # broad contains search but avoid insulin columns
        for low, orig in lower_map.items():
            if any(k in low for k in ["glucose", "sugar", "measurement"]) and "insulin" not in low:
                glucose_col = orig
                break

    # Detect datetime (single)
    dt_col = None
    for key in dt_single_candidates:
        if key in lower_map:
            dt_col = lower_map[key]
            break

    # If not single, try separate date & time
    created_dt = False
    used_date = None
    used_time = None
    if dt_col is None:
        # find date
        for key in date_candidates:
            for low, orig in lower_map.items():
                if low == key or (key in low and "updated" not in low and "timezone" not in low):
                    used_date = orig
                    break
            if used_date: break
        # find time
        for key in time_candidates:
            for low, orig in lower_map.items():
                if low == key or (key in low and "zone" not in low):
                    used_time = orig
                    break
            if used_time: break

        if used_date is not None and used_time is not None:
            df["__datetime"] = pd.to_datetime(df[used_date].astype(str) + " " + df[used_time].astype(str), errors="coerce")
            dt_col = "__datetime"
            created_dt = True

    info = {
        "original_columns": original_cols,
        "detected_datetime": dt_col,
        "detected_glucose": glucose_col,
        "used_date": used_date,
        "used_time": used_time,
        "created_datetime": created_dt
    }
    return dt_col, glucose_col, info


def insulin_needed(current_glucose, target_glucose=150.0, isf=14.13):
    if pd.isna(current_glucose) or current_glucose <= target_glucose:
        return 0.0
    return max(0.0, (float(current_glucose) - float(target_glucose)) / float(isf))


def diet_suggestions(glucose):
    if glucose < 70:
        return {
            "Status": "⚠️ Low glucose",
            "Breakfast": "Banana or juice now; then toast with peanut butter.",
            "Lunch": "Balanced carbs + protein (dal & rice) and recheck.",
            "Dinner": "Veg soup with bread; avoid excess insulin before bed.",
            "Snacks": "Glucose tabs/juice; then nuts/yogurt."
        }
    elif glucose <= 180:
        return {
            "Status": "✅ In range",
            "Breakfast": "Poha/multigrain toast + omelette or sprouts.",
            "Lunch": "Brown rice + dal & sabzi or grilled chicken/fish.",
            "Dinner": "2 rotis + dal & veggies; salad & buttermilk.",
            "Snacks": "Apple/pear, roasted chana, sprouts, nuts."
        }
    else:
        return {
            "Status": "⚠️ High glucose",
            "Breakfast": "Egg whites, avocado toast or veggie upma (low GI).",
            "Lunch": "Grilled paneer/chicken + big salad; avoid white rice.",
            "Dinner": "2 small rotis + non-starchy veg; walk 10–20 min.",
            "Snacks": "Cucumber/carrot sticks, roasted chana; avoid sweets."
        }


def time_in_range(series, low=70, high=180):
    s = pd.to_numeric(series, errors="coerce")
    s = s.dropna()
    if s.empty:
        return 0.0
    return 100.0 * np.mean((s >= low) & (s <= high))


def est_hba1c(avg_glucose):
    # ADA eAG to HbA1c conversion
    return (avg_glucose + 46.7) / 28.7


def build_trend_figure(df, dt_col, g_col):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = pd.to_datetime(df[dt_col])
    y = pd.to_numeric(df[g_col], errors="coerce")

    # Danger zones
    ymax = float(np.nanmax(y)) if np.isfinite(np.nanmax(y)) else 300.0
    ax.axhspan(0, 70, alpha=0.18, color="orange", label="Low < 70")
    ax.axhspan(250, max(260, ymax + 40), alpha=0.14, color="red", label="High > 250")

    ax.plot(x, y, marker="o", linewidth=1.9)
    ax.axhline(150, linestyle="--", label="Target 150")

    ax.set_title("Glucose Trend Over Time")
    ax.set_ylabel("mg/dL")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig


def build_daily_avg_bar_figure(daily_df):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = pd.to_datetime(daily_df["Date"])
    y = daily_df["Average"]
    ax.bar(x, y)
    ax.set_title("Daily Average Glucose")
    ax.set_ylabel("mg/dL")
    ax.grid(True, axis="y", alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    fig.autofmt_xdate()
    return fig


def fig_png(fig, dpi=170):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def pdf_report(avg_glucose, latest_glucose, tir, hba1c, selected_dt, current_glucose,
               correction_units, daily_avg_df, trend_png, bar_png, diet_text):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("📄 MySugr Report", styles["Title"]))
    elems.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph(f"<b>Average Glucose:</b> {avg_glucose:.2f} mg/dL", styles["Normal"]))
    elems.append(Paragraph(f"<b>Latest Glucose:</b> {latest_glucose:.0f} mg/dL", styles["Normal"]))
    elems.append(Paragraph(f"<b>Time in Range (70–180):</b> {tir:.1f}%", styles["Normal"]))
    elems.append(Paragraph(f"<b>Estimated HbA1c:</b> {hba1c:.2f}%", styles["Normal"]))
    elems.append(Spacer(1, 10))

    if selected_dt:
        elems.append(Paragraph("💉 Insulin Correction", styles["Heading2"]))
        elems.append(Paragraph(
            f"Date/Time: {selected_dt}<br/>"
            f"Current: {current_glucose:.0f} mg/dL<br/>"
            f"Target: 150 mg/dL<br/>"
            f"Suggested: {correction_units:.1f} units",
            styles["Normal"]
        ))
        elems.append(Spacer(1, 8))

    elems.append(Paragraph("🍽️ Diet Suggestions", styles["Heading2"]))
    elems.append(Paragraph(diet_text, styles["Normal"]))
    elems.append(Spacer(1, 8))

    if trend_png:
        elems.append(Paragraph("📈 Glucose Trend", styles["Heading2"]))
        elems.append(RLImage(BytesIO(trend_png), width=480, height=230))
        elems.append(Spacer(1, 8))
    if bar_png:
        elems.append(Paragraph("📊 Daily Averages", styles["Heading2"]))
        elems.append(RLImage(BytesIO(bar_png), width=480, height=210))
        elems.append(Spacer(1, 8))

    if not daily_avg_df.empty:
        table_data = [["Date", "Average (mg/dL)"]] + [
            [str(r["Date"]), f"{r['Average']:.1f}"] for _, r in daily_avg_df.iterrows()
        ]
        t = Table(table_data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        elems.append(t)

    doc.build(elems)
    pdf = buf.getvalue()
    buf.close()
    return pdf

# =========================
# Sidebar Upload
# =========================
st.sidebar.header("⚙️ Settings")
uploaded = st.sidebar.file_uploader("📂 Upload mySugr CSV", type=["csv"])
st.sidebar.caption("Tip: You can export CSV from mySugr. This app auto-detects headers.")

if not uploaded:
    st.info("Upload your CSV to get started.")
    st.stop()

# =========================
# Load & Detect Columns
# =========================
try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Couldn't read CSV: {e}")
    st.stop()

dt_col, g_col, info = robust_detect_columns(df)

if g_col is None or dt_col is None:
    st.error("❌ Could not detect the timestamp and glucose columns automatically.")
    with st.expander("What I saw in your file"):
        st.write("Columns:", info["original_columns"])
        st.write("Detected datetime:", info["detected_datetime"])
        st.write("Detected glucose:", info["detected_glucose"])
        st.write("Separate Date/Time used:", info["used_date"], info["used_time"])
    st.stop()

# Parse datetime & glucose
df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
df[g_col] = pd.to_numeric(df[g_col], errors="coerce")
df = df.dropna(subset=[dt_col, g_col]).sort_values(dt_col)
if df.empty:
    st.error("No valid rows after parsing Date/Time and Glucose.")
    st.stop()

# Show detection summary
with st.expander("🔎 Detected Columns (auto)"):
    st.write(f"**Timestamp column:** `{dt_col}`" + (f" (built from `{info['used_date']}` + `{info['used_time']}`)" if info["created_datetime"] else ""))
    st.write(f"**Glucose column:** `{g_col}`")

# =========================
# Metrics
# =========================
avg_glucose = float(df[g_col].mean())
latest_glucose = float(df.iloc[-1][g_col])
tir = time_in_range(df[g_col], 70, 180)
hba1c = est_hba1c(avg_glucose)

mc1, mc2, mc3 = st.columns(3)
with mc1:
    st.markdown(f'<div class="metric-card"><div class="subtle">Average Glucose</div><div class="big-number">{avg_glucose:.1f} mg/dL</div></div>', unsafe_allow_html=True)
with mc2:
    st.markdown(f'<div class="metric-card"><div class="subtle">Latest Glucose</div><div class="big-number">{latest_glucose:.0f} mg/dL</div></div>', unsafe_allow_html=True)
with mc3:
    st.markdown(f'<div class="metric-card"><div class="subtle">Time in Range (70–180)</div><div class="big-number">{tir:.1f}%</div></div>', unsafe_allow_html=True)

# =========================
# Tabs
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "🍽️ Diet", "💉 Insulin", "📄 Report"])

# -------- Analytics --------
with tab1:
    st.subheader("Trend & Distribution")

    # Trend chart
    trend_fig = build_trend_figure(df, dt_col, g_col)
    st.pyplot(trend_fig)

    # Daily averages
    st.markdown("### Daily Averages")
    ddf = df.copy()
    ddf["__Date"] = pd.to_datetime(ddf[dt_col]).dt.date
    daily_avg = ddf.groupby("__Date")[g_col].mean().rename("Average").reset_index().rename(columns={"__Date": "Date"})
    bar_fig = build_daily_avg_bar_figure(daily_avg)
    st.pyplot(bar_fig)

    # Histogram
    st.markdown("### Glucose Distribution")
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.hist(pd.to_numeric(df[g_col], errors="coerce"), bins=24)
    ax.axvline(avg_glucose, linestyle="--", label=f"Mean {avg_glucose:.1f}")
    ax.set_xlabel("mg/dL"); ax.set_ylabel("Count"); ax.legend()
    st.pyplot(fig)

# -------- Diet --------
with tab2:
    st.subheader("Personalized Diet Suggestions")
    d = diet_suggestions(latest_glucose)
    status = d.pop("Status", "Diet")
    st.markdown(f'<div class="diet-card"><div class="big-number">{status}</div>'
                f'<div class="subtle">Tailored for your most recent reading</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Breakfast**")
        st.write(d["Breakfast"])
        st.markdown("**Lunch**")
        st.write(d["Lunch"])
    with c2:
        st.markdown("**Dinner**")
        st.write(d["Dinner"])
        st.markdown("**Snacks**")
        st.write(d["Snacks"])

# -------- Insulin --------
with tab3:
    st.subheader("Insulin Correction Advisor")

    # Safe human-readable select
    view = df[[dt_col, g_col]].copy()
    view["Label"] = view.apply(lambda r: f"{pd.to_datetime(r[dt_col]).strftime('%Y-%m-%d %H:%M')} → {int(round(r[g_col]))} mg/dL", axis=1)
    chosen = st.selectbox("Select a reading", options=view["Label"].tolist())
    row = view[view["Label"] == chosen].iloc[0]
    selected_dt = pd.to_datetime(row[dt_col])
    selected_dt_str = selected_dt.strftime("%Y-%m-%d %H:%M")
    current_glucose = float(row[g_col])

    colA, colB = st.columns(2)
    with colA:
        target_glucose = st.number_input("🎯 Target (mg/dL)", value=150, min_value=70, max_value=200, step=5)
    with colB:
        isf = st.number_input("⚖️ ISF (mg/dL per unit)", value=14.13, min_value=5.0, max_value=80.0, step=0.01, format="%.2f")

    correction_units = insulin_needed(current_glucose, target_glucose, isf)
    st.success(f"**{selected_dt_str}**  \nCurrent: **{current_glucose:.0f} mg/dL** → Suggested correction: **{correction_units:.1f} units**")

# -------- Report --------
with tab4:
    st.subheader("Download PDF Report")
    # Build images for PDF
    trend_png = fig_png(build_trend_figure(df, dt_col, g_col))
    bar_png = fig_png(build_daily_avg_bar_figure(daily_avg))
    # Diet text
    diet_block = diet_suggestions(latest_glucose)
    diet_text = "; ".join([f"{k}: {v}" for k, v in diet_block.items() if k != "Status"])

    pdf_bytes = pdf_report(
        avg_glucose=avg_glucose,
        latest_glucose=latest_glucose,
        tir=tir,
        hba1c=hba1c,
        selected_dt=selected_dt_str if 'selected_dt_str' in locals() else None,
        current_glucose=current_glucose if 'current_glucose' in locals() else np.nan,
        correction_units=correction_units if 'correction_units' in locals() else 0.0,
        daily_avg_df=daily_avg,
        trend_png=trend_png,
        bar_png=bar_png,
        diet_text=diet_text
    )

    st.download_button(
        "📥 Download Weekly Report (PDF)",
        data=pdf_bytes,
        file_name="mysugr_weekly_report.pdf",
        mime="application/pdf"
    )
