import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ---------------- App Configuration ----------------
st.set_page_config(
    page_title="MySugr Advanced",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Backend: State Management ----------------
def initialize_session_state():
    """Ensures a flawless backend by initializing all required data structures."""
    default_states = {
        "diet_tracking": [],
        "insulin_logs": [],
        "diet_recommendations": [],
        "activity_logs": [],
        "medication_logs": [],
        "uploads": [],
        "settings": {
            "target_glucose": 100,
            "correction_factor": 50,
            "carb_ratio": 10
        }
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------------- Navigation & UI Setup ----------------
st.sidebar.title("💉 MySugr Advanced")
st.sidebar.markdown("---")
navigation = st.sidebar.radio(
    "Navigation System",
    [
        "📊 Executive Dashboard", 
        "🥗 Nutrition & Diet", 
        "💉 Insulin & Medication", 
        "🏃 Activity Tracker",
        "🍎 USDA Diet Planner", 
        "📈 Analytics & Reports",
        "⚙️ Settings & Data"
    ]
)
st.sidebar.markdown("---")
st.sidebar.info("Application operates in local mode. All data is stored in the current session.")

# ---------------- Module 1: Executive Dashboard ----------------
if navigation == "📊 Executive Dashboard":
    st.title("Executive Dashboard")
    st.markdown("Overview of your current health metrics.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate Averages safely
    bg_data = [log["glucose"] for log in st.session_state.insulin_logs if "glucose" in log]
    avg_bg = sum(bg_data) / len(bg_data) if bg_data else 0
    
    with col1:
        st.metric("Avg Glucose (mg/dL)", f"{avg_bg:.1f}", delta=None)
    with col2:
        st.metric("Meals Tracked", len(st.session_state.diet_tracking))
    with col3:
        st.metric("Insulin Administrations", len(st.session_state.insulin_logs))
    with col4:
        st.metric("Workouts Logged", len(st.session_state.activity_logs))
        
    st.markdown("---")
    st.subheader("Recent Activity Stream")
    
    if not st.session_state.insulin_logs and not st.session_state.diet_tracking:
        st.info("No data recorded yet. Begin by navigating to the other modules.")
    else:
        # Display latest 5 glucose readings
        if st.session_state.insulin_logs:
            st.write("**Latest Glucose Readings**")
            df_recent_bg = pd.DataFrame(st.session_state.insulin_logs).tail(5)[["time", "glucose", "dose"]]
            st.dataframe(df_recent_bg, use_container_width=True)

# ---------------- Module 2: Nutrition & Diet ----------------
elif navigation == "🥗 Nutrition & Diet":
    st.title("Nutrition & Diet Tracking")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Log a Meal")
        with st.form("meal_form", clear_on_submit=True):
            meal_name = st.text_input("Meal Designation")
            calories = st.number_input("Total Calories", min_value=0, step=50)
            carbs = st.number_input("Carbohydrates (g)", min_value=0.0, step=5.0)
            protein = st.number_input("Protein (g)", min_value=0.0, step=5.0)
            fat = st.number_input("Fat (g)", min_value=0.0, step=5.0)
            
            if st.form_submit_button("Submit Meal Data"):
                st.session_state.diet_tracking.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "meal": meal_name,
                    "calories": calories,
                    "carbs": carbs,
                    "protein": protein,
                    "fat": fat
                })
                st.success("Meal successfully recorded.")

    with col2:
        st.subheader("Dietary Ledger")
        if st.session_state.diet_tracking:
            df_meals = pd.DataFrame(st.session_state.diet_tracking)
            st.dataframe(df_meals, use_container_width=True)
        else:
            st.write("No meals tracked currently.")

# ---------------- Module 3: Insulin & Medication ----------------
elif navigation == "💉 Insulin & Medication":
    st.title("Clinical Insulin Assistant")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Bolus Calculator")
        st.markdown("Utilizes clinical calculation methodologies based on your personal parameters.")
        
        with st.form("insulin_form"):
            current_bg = st.number_input("Current Glucose (mg/dL)", min_value=20, max_value=600, value=120)
            meal_carbs = st.number_input("Meal Carbohydrates (g)", min_value=0, value=0)
            
            submitted = st.form_submit_button("Calculate & Log Dose")
            
            if submitted:
                target_bg = st.session_state.settings["target_glucose"]
                cf = st.session_state.settings["correction_factor"]
                cr = st.session_state.settings["carb_ratio"]
                
                correction_dose = max(0, (current_bg - target_bg) / cf)
                meal_dose = meal_carbs / cr if cr > 0 else 0
                total_dose = round(correction_dose + meal_dose, 2)
                
                st.session_state.insulin_logs.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "glucose": current_bg,
                    "carbs": meal_carbs,
                    "dose": total_dose,
                    "type": "Bolus"
                })
                
                st.success(f"Calculated Recommended Dose: **{total_dose} Units**")
                st.info(f"Correction: {correction_dose:.2f}U | Meal: {meal_dose:.2f}U")

    with col2:
        st.subheader("Medication Log")
        with st.form("med_form", clear_on_submit=True):
            med_name = st.text_input("Medication Name (e.g., Metformin, Basal Insulin)")
            dosage = st.text_input("Dosage (e.g., 500mg, 15U)")
            if st.form_submit_button("Log Medication"):
                st.session_state.medication_logs.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "medication": med_name,
                    "dosage": dosage
                })
                st.success("Medication recorded.")
                
        if st.session_state.medication_logs:
            st.dataframe(pd.DataFrame(st.session_state.medication_logs), use_container_width=True)

# ---------------- Module 4: Activity Tracker ----------------
elif navigation == "🏃 Activity Tracker":
    st.title("Activity & Exercise Tracking")
    st.markdown("Monitor physical exertion, as it directly impacts glycemic control.")
    
    with st.form("activity_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            activity_type = st.selectbox("Activity Type", ["Walking", "Running", "Cycling", "Weightlifting", "Swimming", "Other"])
            duration = st.number_input("Duration (minutes)", min_value=1, step=5)
        with col2:
            intensity = st.select_slider("Intensity Level", options=["Low", "Moderate", "High", "Maximum"])
            notes = st.text_input("Additional Notes")
            
        if st.form_submit_button("Log Activity"):
            st.session_state.activity_logs.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "activity": activity_type,
                "duration": duration,
                "intensity": intensity,
                "notes": notes
            })
            st.success("Activity recorded successfully.")
            
    if st.session_state.activity_logs:
        st.subheader("Activity History")
        st.dataframe(pd.DataFrame(st.session_state.activity_logs), use_container_width=True)

# ---------------- Module 5: USDA Diet Planner ----------------
elif navigation == "🍎 USDA Diet Planner":
    st.title("Automated Diet Recommendations")
    st.markdown("Interface with external nutrition APIs for structured meal planning.")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            diet_choice = st.selectbox("Primary Dietary Goal", ["Balanced Glycemic", "Low-Carbohydrate", "High-Protein", "Ketogenic"])
        with col2:
            days = st.slider("Duration (Days)", 1, 14, 7)
            
        if st.button("Query USDA Database", use_container_width=True):
            with st.spinner("Establishing connection and retrieving protocols..."):
                try:
                    # Replace with actual USDA/Nutrition API endpoint in production
                    api_url = "http://localhost:8000/recommend" 
                    payload = {"goal": diet_choice, "days": days}
                    response = requests.post(api_url, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        rec_data = response.json()
                        if "plan" in rec_data:
                            df = pd.DataFrame(rec_data["plan"])
                            st.session_state.diet_recommendations.append({
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "goal": diet_choice,
                                "plan": rec_data["plan"]
                            })
                            st.success("Protocol retrieved successfully.")
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.error("Malformed payload received from API.")
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                except requests.exceptions.RequestException:
                    st.warning("⚠️ API connection failed. Simulating fallback data for demonstration purposes.")
                    # Fallback data for testing UI without a running backend
                    mock_data = [{"Day": i+1, "Meal": "Standard Diabetic Meal", "Calories": 450, "Carbs": 30} for i in range(days)]
                    df = pd.DataFrame(mock_data)
                    st.dataframe(df, use_container_width=True)

# ---------------- Module 6: Analytics & Reports ----------------
elif navigation == "📈 Analytics & Reports":
    st.title("Clinical Analytics & Reports")
    
    tab1, tab2 = st.tabs(["🩸 Glycemic Control", "🥗 Nutritional Intake"])
    
    with tab1:
        if st.session_state.insulin_logs:
            df_bg = pd.DataFrame(st.session_state.insulin_logs)
            df_bg['time'] = pd.to_datetime(df_bg['time'])
            
            st.subheader("Glucose Level Trajectory")
            
            # Advanced Plotly Chart
            fig = px.scatter(
                df_bg, x="time", y="glucose", 
                color="glucose", 
                color_continuous_scale=[(0, "blue"), (0.5, "green"), (1, "red")],
                range_color=[50, 250],
                size_max=10, 
                title="Continuous Blood Glucose Mapping"
            )
            fig.add_hline(y=st.session_state.settings["target_glucose"], line_dash="dash", line_color="green", annotation_text="Target")
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient glycemic data for analysis.")
            
    with tab2:
        if st.session_state.diet_tracking:
            df_diet = pd.DataFrame(st.session_state.diet_tracking)
            st.subheader("Macronutrient Distribution")
            
            if 'carbs' in df_diet.columns and 'protein' in df_diet.columns and 'fat' in df_diet.columns:
                totals = df_diet[['carbs', 'protein', 'fat']].sum()
                fig_pie = px.pie(
                    values=totals.values, 
                    names=totals.index, 
                    title="Aggregate Macronutrient Ratio",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.bar_chart(df_diet["calories"])
        else:
            st.info("Insufficient nutritional data for analysis.")

# ---------------- Module 7: Settings & Data ----------------
elif navigation == "⚙️ Settings & Data":
    st.title("System Configuration & Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Clinical Parameters")
        with st.form("settings_form"):
            target_bg = st.number_input("Target Glucose (mg/dL)", value=st.session_state.settings["target_glucose"])
            cf = st.number_input("Correction Factor (ISF)", value=st.session_state.settings["correction_factor"])
            cr = st.number_input("Carbohydrate Ratio (g/U)", value=st.session_state.settings["carb_ratio"])
            
            if st.form_submit_button("Update Parameters"):
                st.session_state.settings.update({
                    "target_glucose": target_bg,
                    "correction_factor": cf,
                    "carb_ratio": cr
                })
                st.success("Clinical parameters updated.")

    with col2:
        st.subheader("Data Portability")
        st.markdown("Upload historical data or export your current session data.")
        
        uploaded_file = st.file_uploader("Upload External CSV", type=["csv"])
        if uploaded_file:
            df_upload = pd.read_csv(uploaded_file)
            st.session_state.uploads.append({"filename": uploaded_file.name, "data": df_upload.to_dict()})
            st.success("Data ingested successfully.")
            st.dataframe(df_upload.head(3))
            
        st.markdown("---")
        if st.session_state.insulin_logs:
            csv_export = pd.DataFrame(st.session_state.insulin_logs).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Insulin Logs (CSV)",
                data=csv_export,
                file_name=f"insulin_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
