import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="MySugr Improved", page_icon="💉", layout="wide")

st.title("💉 MySugr Improved – Blood Sugar Tracker")

# File uploader
uploaded_file = st.file_uploader("📂 Upload your blood sugar CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        st.success("✅ File uploaded successfully!")
        st.write("Here’s a preview of your data:")
        st.dataframe(df.head())

        # Normalize column names (strip spaces + lowercase)
        df.columns = df.columns.str.strip().str.lower()

        # Try to auto-detect columns
        datetime_col = None
        glucose_col = None

        for col in df.columns:
            if "date" in col or "time" in col:
                datetime_col = col
            if "glucose" in col or "sugar" in col:
                glucose_col = col

        # If not detected, ask user to select
        if datetime_col is None or glucose_col is None:
            st.warning("⚠️ Couldn’t auto-detect the right columns. Please select them manually.")
            datetime_col = st.selectbox("Select Date/Time column", df.columns)
            glucose_col = st.selectbox("Select Glucose column", df.columns)

        # Convert datetime column
        df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce")
        df = df.dropna(subset=[datetime_col, glucose_col])

        if df.empty:
            st.error("❌ No valid data found after cleaning. Please check your CSV file formatting.")
        else:
            df = df.sort_values(by=datetime_col)
            df = df.rename(columns={datetime_col: "DateTime", glucose_col: "Glucose"})

            # Show summary 
            st.subheader("📊 Data Summary")
            st.write(df.describe())

            # Plot
            st.subheader("📈 Blood Sugar Trend")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["DateTime"], df["Glucose"], marker="o", linestyle="-", color="teal")
            ax.axhline(140, color="red", linestyle="--", label="High (140 mg/dL)")
            ax.axhline(70, color="orange", linestyle="--", label="Low (70 mg/dL)")
            ax.set_ylabel("Glucose (mg/dL)")
            ax.set_xlabel("Date & Time")
            ax.legend()
            st.pyplot(fig)

            # Latest reading safely
            latest = df.iloc[-1]
            st.metric(
                label="Latest Reading",
                value=f"{latest['Glucose']} mg/dL",
                delta=f"{(latest['Glucose'] - df['Glucose'].mean()):.1f} vs avg",
            )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

else:
    st.info("👆 Please upload a CSV file to continue.")
