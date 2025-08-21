# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from io import BytesIO
from datetime import datetime

# Try to import reportlab (optional). If not found, we’ll disable PDF.
try:
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# -----------------------------
# Page Config & Subtle Theming
# -----------------------------
st.set_page_config(page_title="MySugr Dashboard", page_icon="💉", layout="wide")
st.markdown("""
<style>
:root{
  --brand:#0a84ff; --ink:#0f172a; --muted:#64748b; --card:#f8fafc; --ring:#e2e8f0;
}
.block-container{padding-top:1rem;}
h1,h2,h3{color:var(--ink); letter-spacing:-0.02em;}
.small{color:var(--muted); font-size:0.9rem;}
.kpi{background:linear-gradient(180deg,#fff, #f8fbff);
     border:1px solid var(--ring); border-radius:16px; padding:14px 16px;
     box-shadow:0 6px 18px rgba(2,6,23,0.04);}
.kpi .label{color:var(--muted); font-size:0.85rem;}
.kpi .value{font-size:1.6rem; font-weight:700; color:var(--ink);}
.section{border:1px solid var(--ring); border-radius:16px; padding:16px; background:#fff;}
.badge{display:inline-block; padding:4px 10px; border-radius:999px; border:1px solid var(--ring); background:#fff; font-size:0.85rem;}
.hr{height:1px; background:var(--ring); margin:8px 0 16px;}
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { background: #fff; border:1px solid var(--ring); border-radius:12px; padding:8px 12px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utilities
# -----------------------------
def detect_columns(df: pd.DataFrame):
    """
    Robustly detect:
      - datetime column (or build from Date + Time)
      - glucose column
      - insulin columns -> build 'insulin_total'
    Returns: dt_col, sugar_col, insulin_cols(list), info(dict)
    """
    original_cols = df.columns.tolist()
    lower_map = {c.lower().strip(): c for c in df.columns}
    cols_lower = list(lower_map.keys())

    # Glucose candidates
    glucose_keys_exact = [
        "blood sugar measurement (mg/dl)", "blood glucose (mg/dl)",
        "blood glucose", "glucose (mg/dl)", "glucose value", "glucose", "bg"
    ]
    sugar_col = None
    for key in glucose_keys_exact:
        if key in lower_map:
            sugar_col = lower_map[key]
            break
    if sugar_col is None:
        for low, orig in lower_map.items():
            if any(k in low for k in ["glucose", "sugar", "measurement"]) and "insulin" not in low:
                sugar_col = orig; break

    # Datetime
    dt_col = None
    for k in ["datetime", "timestamp", "date time", "time stamp"]:
        if k in lower_map:
            dt_col = lower_map[k]; break

    used_date, used_time, built = None, None, False
    if dt_col is None:
        # find date + time
        for low, orig in lower_map.items():
            if low == "date" or (("date" in low) and "timezone" not in low):
                used_date = orig; break
        for low, orig in lower_map.items():
            if low == "time" or ("time" in low and "zone" not in low):
                used_time = orig; break
        if used_date is not None and used_time is not None:
            # build datetime
            df["__datetime"] = pd.to_datetime(
                df[used_date].astype(str) + " " + df[used_time].astype(str),
                errors="coerce")
            dt_col = "__datetime"
            built = True

    # Insulin columns (sum any relevant)
    insulin_candidates = []
    for low, orig in lower_map.items():
        if "insulin" in low and "units" in low:
            insulin_candidates.append(orig)
        elif low in ["insulin (meal)", "insulin (correction)"]:
            insulin_candidates.append(orig)
    # also consider pen/pump
    for key in [
        "insulin injection units (pen)",
        "insulin injection units (pump)",
        "basal injection units"
    ]:
        if key in lower_map and lower_map[key] not in insulin_candidates:
            insulin_candidates.append(lower_map[key])

    info = dict(
        original_columns=original_cols,
        datetime=dt_col, glucose=sugar_col,
        used_date=used_date, used_time=used_time, built_datetime=built,
        insulin_cols=insulin_candidates
    )
    return dt_col, sugar_col, insulin_candidates, info


def insulin_needed(current_glucose, target=150.0, isf=14.0):
    if pd.isna(current_glucose) or current_glucose <= target:
        return 0.0
    return max(0.0, (float(current_glucose) - float(target)) / float(isf))


def time_in_range(series, low=70, high=180):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty: return 0.0
    return 100 * np.mean((s >= low) & (s <= high))


def est_hba1c(avg_glucose):
    return (avg_glucose + 46.7) / 28.7


def trend_figure(df, dt_col, g_col):
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    x = pd.to_datetime(df[dt_col]); y = pd.to_numeric(df[g_col], errors="coerce")
    ymax = float(np.nanmax(y)) if np.isfinite(np.nanmax(y)) else 300.0
    ax.axhspan(0, 70, alpha=0.18, color="orange", label="Low < 70")
    ax.axhspan(250, max(260, ymax + 40), alpha=0.14, color="red", label="High > 250")
    ax.plot(x, y, marker="o", linewidth=1.8)
    ax.axhline(150, linestyle="--", label="Target 150")
    ax.set_title("Glucose Trend"); ax.set_ylabel("mg/dL")
    ax.grid(True, alpha=0.25); ax.legend(loc="upper left")
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig


def daily_avg_bar(daily_df):
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    x = pd.to_datetime(daily_df["Date"]); y = daily_df["Average"]
    ax.bar(x, y); ax.set_title("Daily Average Glucose"); ax.set_ylabel("mg/dL")
    ax.grid(True, axis="y", alpha=0.25); ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    fig.autofmt_xdate()
    return fig


def insulin_time_series(df, dt_col, insulin_total_col):
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    x = pd.to_datetime(df[dt_col]); y = pd.to_numeric(df[insulin_total_col], errors="coerce")
    ax.plot(x, y, marker="o", linewidth=1.8)
    ax.set_title("Insulin Over Time"); ax.set_ylabel("Units"); ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig


def insulin_daily_bar(df, dt_col, insulin_total_col):
    temp = df.copy()
    temp["__date"] = pd.to_datetime(temp[dt_col]).dt.date
    d = temp.groupby("__date")[insulin_total_col].sum().rename("Total").reset_index().rename(columns={"__date":"Date"})
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    ax.bar(pd.to_datetime(d["Date"]), d["Total"])
    ax.set_title("Daily Total Insulin"); ax.set_ylabel("Units"); ax.grid(True, axis="y", alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d")); fig.autofmt_xdate()
    return fig


def png_bytes(fig, dpi=170):
    buf = BytesIO(); fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight"); plt.close(fig); buf.seek(0)
    return buf.getvalue()


def pdf_report(payload):
    if not REPORTLAB_OK:
        return None
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("📄 MySugr Report", styles["Title"]))
    elems.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph(f"<b>Average Glucose:</b> {payload['avg_glucose']:.1f} mg/dL", styles["Normal"]))
    elems.append(Paragraph(f"<b>Latest Glucose:</b> {payload['latest_glucose']:.0f} mg/dL", styles["Normal"]))
    elems.append(Paragraph(f"<b>Time in Range (70–180):</b> {payload['tir']:.1f}%", styles["Normal"]))
    elems.append(Paragraph(f"<b>Estimated HbA1c:</b> {payload['hba1c']:.2f}%", styles["Normal"]))
    elems.append(Spacer(1, 10))

    if payload.get("insulin_section"):
        elems.append(Paragraph("💉 Insulin Recommendation", styles["Heading2"]))
        elems.append(Paragraph(payload["insulin_section"], styles["Normal"]))
        elems.append(Spacer(1, 8))

    if payload.get("trend_png"):
        elems.append(Paragraph("📈 Glucose Trend", styles["Heading2"]))
        elems.append(RLImage(BytesIO(payload["trend_png"]), width=480, height=230))
        elems.append(Spacer(1, 8))

    if payload.get("bar_png"):
        elems.append(Paragraph("📊 Daily Averages", styles["Heading2"]))
        elems.append(RLImage(BytesIO(payload["bar_png"]), width=480, height=210))
        elems.append(Spacer(1, 8))

    if payload.get("insulin_png"):
        elems.append(Paragraph("💉 Insulin Over Time", styles["Heading2"]))
        elems.append(RLImage(BytesIO(payload["insulin_png"]), width=480, height=210))
        elems.append(Spacer(1, 8))

    if not payload["daily_avg_df"].empty:
        table_data = [["Date", "Average (mg/dL)"]] + [
            [str(r["Date"]), f"{r['Average']:.1f}"] for _, r in payload["daily_avg_df"].iterrows()
        ]
        t = Table(table_data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ]))
        elems.append(t)

    doc.build(elems)
    pdf = buf.getvalue(); buf.close()
    return pdf


# -----------------------------
# Sidebar Upload
# -----------------------------
st.sidebar.header("⚙️ Settings")
uploaded = st.sidebar.file_uploader("📂 Upload mySugr CSV", type=["csv"])
st.sidebar.caption("Tip: Exports from mySugr work best. Date+Time or a single DateTime column are supported.")

if not uploaded:
    st.info("Upload your CSV to get started.")
    st.stop()

# -----------------------------
# Load & Detect
# -----------------------------
try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Couldn't read CSV: {e}")
    st.stop()

dt_col, sugar_col, insulin_cols, info = detect_columns(df)

if sugar_col is None or dt_col is None:
    st.error("❌ Could not detect the timestamp and glucose columns.")
    with st.expander("What I saw in your file"):
        st.write("Columns:", info["original_columns"])
        st.write("Detected datetime:", info["datetime"])
        st.write("Detected glucose:", info["glucose"])
        st.write("Separate Date/Time used:", info["used_date"], info["used_time"])
    st.stop()

# Parse & clean
df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
df[sugar_col] = pd.to_numeric(df[sugar_col], errors="coerce")
df = df.dropna(subset=[dt_col, sugar_col]).sort_values(dt_col)
if df.empty:
    st.error("No valid rows after parsing Date/Time and Glucose.")
    st.stop()

# Build insulin_total (optional)
if insulin_cols:
    for c in insulin_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["insulin_total"] = df[insulin_cols].sum(axis=1, skipna=True)
else:
    df["insulin_total"] = np.nan

# -----------------------------
# Header KPIs
# -----------------------------
avg_glucose = float(df[sugar_col].mean())
latest_glucose = float(df.iloc[-1][sugar_col])
tir = time_in_range(df[sugar_col], 70, 180)
hba1c = est_hba1c(avg_glucose)

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi"><div class="label">Average Glucose</div><div class="value">{avg_glucose:.1f} mg/dL</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi"><div class="label">Latest Glucose</div><div class="value">{latest_glucose:.0f} mg/dL</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi"><div class="label">Time in Range (70–180)</div><div class="value">{tir:.1f}%</div></div>', unsafe_allow_html=True)

st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Blood Sugar", "💉 Insulin", "✅ Daily Checks", "🧪 Insulin Recommendation", "📄 Report"
])

# ======== Tab 1: Blood Sugar =========
with tab1:
    st.subheader("Trends & Distribution")
    st.caption("Visualize your blood sugar over time and daily averages.")

    tr_fig = trend_figure(df, dt_col, sugar_col)
    st.pyplot(tr_fig)

    temp = df.copy()
    temp["__date"] = pd.to_datetime(temp[dt_col]).dt.date
    daily_avg_df = (
        temp.groupby("__date")[sugar_col].mean()
        .rename("Average").reset_index().rename(columns={"__date": "Date"})
    )
    st.markdown("#### Daily Averages")
    bar_fig = daily_avg_bar(daily_avg_df)
    st.pyplot(bar_fig)

    st.markdown("#### Distribution")
    fig, ax = plt.subplots(figsize=(10.5, 3.6))
    ax.hist(pd.to_numeric(df[sugar_col], errors="coerce"), bins=24)
    ax.axvline(avg_glucose, linestyle="--", label=f"Mean {avg_glucose:.1f}")
    ax.set_xlabel("mg/dL"); ax.set_ylabel("Count"); ax.legend()
    st.pyplot(fig)

# ======== Tab 2: Insulin =========
with tab2:
    st.subheader("Insulin Overview")
    if df["insulin_total"].notna().any():
        ins_line = insulin_time_series(df, dt_col, "insulin_total")
        st.pyplot(ins_line)

        st.markdown("#### Daily Totals")
        ins_bar = insulin_daily_bar(df, dt_col, "insulin_total")
        st.pyplot(ins_bar)
    else:
        st.info("No insulin columns found in the file. If available, include any of: "
                "`Insulin Injection Units (Pen)`, `Insulin Injection Units (pump)`, "
                "`Insulin (Meal)`, `Insulin (Correction)`, or `Basal Injection Units`.")

# ======== Tab 3: Daily Checks (per-row checkboxes) =========
with tab3:
    st.subheader("Daily Checks")
    st.caption("Mark whether you followed diet and insulin plan for each recent reading.")

    # Limit to last N rows for UI performance
    N = st.slider("Rows to review", min_value=5, max_value=min(100, len(df)), value=min(20, len(df)))
    recent = df.tail(N).copy().reset_index(drop=True)

    for i, r in recent.iterrows():
        dt_str = pd.to_datetime(r[dt_col]).strftime("%Y-%m-%d %H:%M")
        bs = r[sugar_col]
        with st.expander(f"🗓️ {dt_str} — {bs:.0f} mg/dL", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                diet_ok = st.checkbox("Diet followed", key=f"diet_ok_{i}")
                diet_note = st.text_input("If not, what was followed?", key=f"diet_note_{i}")
            with c2:
                insulin_ok = st.checkbox("Insulin plan followed", key=f"ins_ok_{i}")
                insulin_note = st.text_input("If not, what was followed? ", key=f"ins_note_{i}")

    st.caption("Notes are kept in the UI state. Export to CSV/DB can be added if you’d like.")

# ======== Tab 4: Insulin Recommendation =========
with tab4:
    st.subheader("Insulin Recommendation")
    st.caption("Pick a reading or use the most recent one to calculate a correction dose.")

    # Build human-readable labels + 'Most recent' shortcut
    view = df[[dt_col, sugar_col]].copy()
    view["Label"] = view.apply(
        lambda r: f"{pd.to_datetime(r[dt_col]).strftime('%Y-%m-%d %H:%M')} → {int(round(r[sugar_col]))} mg/dL",
        axis=1
    )
    most_recent_label = "⏱️ Use most recent reading"
    options = [most_recent_label] + view["Label"].tolist()

    chosen = st.selectbox("Select a reading", options=options, key="ins_sel")
    if chosen == most_recent_label:
        row = df.iloc[-1]
        sel_dt = pd.to_datetime(row[dt_col])
        current_glucose = float(row[sugar_col])
    else:
        row = view[view["Label"] == chosen].iloc[0]
        sel_dt = pd.to_datetime(row[dt_col])
        current_glucose = float(row[sugar_col])

    colA, colB, colC = st.columns(3)
    with colA:
        target = st.number_input("🎯 Target (mg/dL)", value=150, min_value=70, max_value=200, step=1, key="ins_target")
    with colB:
        isf = st.number_input("⚖️ ISF (mg/dL per unit)", value=14.0, min_value=5.0, max_value=80.0, step=0.1, format="%.1f", key="ins_isf")
    with colC:
        carb_ratio = st.number_input("🍽️ ICR (g per unit) (optional)", value=0.0, min_value=0.0, step=0.5, format="%.1f", key="ins_icr")

    st.markdown(f"**Selected:** {sel_dt.strftime('%Y-%m-%d %H:%M')}  •  **Current:** {current_glucose:.0f} mg/dL")

    correction_units = insulin_needed(current_glucose, target, isf)
    rec_lines = []
    if current_glucose < target - 20:
        rec_lines.append("⚠️ Current is below target. Avoid correction; consider fast carbs if symptomatic.")
    elif current_glucose > target + 20:
        rec_lines.append(f"⚠️ Above target. Suggested correction ≈ **{correction_units:.1f} units**.")
    else:
        rec_lines.append("✅ Near target. No correction suggested.")

    meal_carbs = st.number_input("🍚 Meal carbs (grams) (optional, for bolus calc)", value=0, min_value=0, step=5, key="meal_carbs")
    meal_units = 0.0
    if carb_ratio and carb_ratio > 0 and meal_carbs > 0:
        meal_units = meal_carbs / carb_ratio
        rec_lines.append(f"🍽️ Meal bolus estimate ≈ **{meal_units:.1f} units** (ICR {carb_ratio:.1f} g/U).")

    total_suggested = correction_units + meal_units
    if total_suggested > 0:
        rec_lines.append(f"💉 **Total suggested dose ≈ {total_suggested:.1f} units**.")
    st.info("\n\n".join(rec_lines))

    st.caption("Always follow your clinician’s guidance.")

# ======== Tab 5: Report =========
with tab5:
    st.subheader("Weekly Report")
    st.caption("Download a PDF summary with charts and key stats.")

    # Build chart bytes
    trend_png = png_bytes(trend_figure(df, dt_col, sugar_col))
    bar_png = png_bytes(daily_avg_bar(daily_avg_df))
    insulin_png = None
    if df["insulin_total"].notna().any():
        insulin_png = png_bytes(insulin_time_series(df, dt_col, "insulin_total"))

    # Insulin section text from last tab state
    ins_sec = None
    if "ins_sel" in st.session_state:
        # summarize last recommendation
        ins_sec = f"Selected reading time: {sel_dt.strftime('%Y-%m-%d %H:%M')} • Current: {current_glucose:.0f} mg/dL. " \
                  f"Target: {st.session_state['ins_target']:.0f} mg/dL • ISF: {st.session_state['ins_isf']:.1f}. " \
                  f"Suggested correction: {insulin_needed(current_glucose, st.session_state['ins_target'], st.session_state['ins_isf']):.1f} units."

    payload = dict(
        avg_glucose=avg_glucose,
        latest_glucose=latest_glucose,
        tir=tir,
        hba1c=hba1c,
        daily_avg_df=daily_avg_df,
        trend_png=trend_png,
        bar_png=bar_png,
        insulin_png=insulin_png,
        insulin_section=ins_sec
    )

    if REPORTLAB_OK:
        pdf = pdf_report(payload)
        st.download_button("📥 Download PDF", data=pdf, file_name="mysugr_report.pdf", mime="application/pdf")
    else:
        st.warning("PDF generation library (reportlab) is not installed. Add `reportlab` to requirements.txt to enable this.")
