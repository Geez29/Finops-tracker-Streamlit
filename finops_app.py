
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import tempfile

# Use a temporary file for SQLite database
temp_db = tempfile.NamedTemporaryFile(delete=False)
conn = sqlite3.connect(temp_db.name, check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS cost_optimizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    cost_saved REAL,
    team TEXT,
    category TEXT
)
""")
conn.commit()

# Logo and title
st.image("flex_logo.jpg", width=120)
st.title("FinOps Cost Optimization Tracker")

# Upload Excel
st.header("Upload Historical Cost Optimization Data")
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    try:
        df_upload = pd.read_excel(uploaded_file, engine='openpyxl')
        required_columns = {"date", "description", "cost_saved", "team", "category"}
        if required_columns.issubset(df_upload.columns):
            df_upload.to_sql('cost_optimizations', conn, if_exists='append', index=False)
            st.success("Excel data uploaded and saved successfully!")
        else:
            st.error(f"Excel must contain columns: {required_columns}")
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")

# Manual Entry
st.header("Manual Entry of Cost Optimization")
with st.form("manual_entry_form"):
    date = st.date_input("Date", value=datetime.today())
    description = st.text_input("Optimization Description")
    cost_saved = st.number_input("Cost Saved ($)", min_value=0.0)
    team = st.text_input("Team/Owner")
    category = st.text_input("Category")
    submitted = st.form_submit_button("Add Entry")
    if submitted:
        cursor.execute("""
        INSERT INTO cost_optimizations (date, description, cost_saved, team, category)
        VALUES (?, ?, ?, ?, ?)
        """, (date.strftime("%Y-%m-%d"), description, cost_saved, team, category))
        conn.commit()
        st.success("Entry added successfully!")

# Reporting Dashboard
st.header("Reporting Dashboard")
df = pd.read_sql_query("SELECT * FROM cost_optimizations", conn)

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['date_str'] = df['date'].dt.strftime('%m/%d/%Y')

    # Fiscal Year Mapping
    def get_fy(date):
        if datetime(2024, 4, 1) <= date <= datetime(2025, 3, 31):
            return 'FY25'
        elif datetime(2025, 4, 1) <= date <= datetime(2026, 3, 31):
            return 'FY26'
        elif datetime(2026, 4, 1) <= date <= datetime(2027, 3, 31):
            return 'FY27'
        elif datetime(2023, 4, 1) <= date <= datetime(2024, 3, 31):
            return 'FY24'
        return 'Other'

    def get_quarter(date):
        if date.month in [4, 5, 6]:
            return 'Q1'
        elif date.month in [7, 8, 9]:
            return 'Q2'
        elif date.month in [10, 11, 12]:
            return 'Q3'
        else:
            return 'Q4'

    df['Fiscal Year'] = df['date'].apply(get_fy)
    df['Quarter'] = df['date'].apply(get_quarter)

    # Sidebar Filters
    st.sidebar.header("Filter Data")
    fy_filter = st.sidebar.multiselect("Fiscal Year", options=df['Fiscal Year'].unique(), default=df['Fiscal Year'].unique())
    quarter_filter = st.sidebar.multiselect("Quarter", options=['Q1', 'Q2', 'Q3', 'Q4'], default=['Q1', 'Q2', 'Q3', 'Q4'])
    category_filter = st.sidebar.multiselect("Category", options=df['category'].unique(), default=df['category'].unique())
    team_filter = st.sidebar.multiselect("Team", options=df['team'].unique(), default=df['team'].unique())

    df_filtered = df[(df['Fiscal Year'].isin(fy_filter)) &
                     (df['Quarter'].isin(quarter_filter)) &
                     (df['category'].isin(category_filter)) &
                     (df['team'].isin(team_filter))]

    # Charts
    st.subheader("Total Cost Savings Over Time")
    savings_over_time = df_filtered.groupby('date_str')['cost_saved'].sum().reset_index()
    fig_line = px.line(savings_over_time, x='date_str', y='cost_saved', title='Total Savings Over Time',
                       color_discrete_sequence=['#00338D'])
    st.plotly_chart(fig_line)

    st.subheader("Savings by Category")
    savings_by_category = df_filtered.groupby('category')['cost_saved'].sum().reset_index()
    fig_bar = px.bar(savings_by_category, x='category', y='cost_saved', title='Savings by Category',
                     color_discrete_sequence=['#00338D'])
    st.plotly_chart(fig_bar)

    st.subheader("Raw Data")
    st.dataframe(df_filtered)

    # Download Button
    st.download_button("Download Filtered Data as Excel", data=df_filtered.to_excel(index=False, engine='openpyxl'),
                       file_name="filtered_cost_optimizations.xlsx")
else:
    st.info("No data available yet. Please upload or enter cost optimization records.")
