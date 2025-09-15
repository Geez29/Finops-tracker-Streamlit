
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# Logo and title
col1, col2 = st.columns([6, 1])
with col1:
    st.title("[1m"); st.markdown("# [1mFinOps Cost Optimization Tracker")
with col2:
    st.image("flex_logo.jpg", width=100)

# Initialize SQLite database
conn = sqlite3.connect('finops.db', check_same_thread=False)
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

# Section: Upload Excel
st.header("[1m"); st.markdown("## [1mUpload Historical Cost Optimization Data")
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

# Section: Manual Entry Form
st.header("[1m"); st.markdown("## [1mManual Entry of Cost Optimization")
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

# Section: Reporting Dashboard
st.header("[1m"); st.markdown("## [1mReporting Dashboard")
df = pd.read_sql_query("SELECT * FROM cost_optimizations", conn)

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])

    # Filters
    st.sidebar.header("Filter Data")
    date_range = st.sidebar.date_input("Date Range", [df['date'].min(), df['date'].max()])
    category_filter = st.sidebar.multiselect("Category", options=df['category'].unique(), default=df['category'].unique())
    team_filter = st.sidebar.multiselect("Team", options=df['team'].unique(), default=df['team'].unique())

    df_filtered = df[(df['date'] >= pd.to_datetime(date_range[0])) &
                     (df['date'] <= pd.to_datetime(date_range[1])) &
                     (df['category'].isin(category_filter)) &
                     (df['team'].isin(team_filter))]

    st.subheader("Total Cost Savings Over Time")
    savings_over_time = df_filtered.groupby('date')['cost_saved'].sum().reset_index()
    fig_line = px.line(savings_over_time, x='date', y='cost_saved', title='Total Savings Over Time')
    st.plotly_chart(fig_line)

    st.subheader("Savings by Category")
    savings_by_category = df_filtered.groupby('category')['cost_saved'].sum().reset_index()
    fig_bar = px.bar(savings_by_category, x='category', y='cost_saved', title='Savings by Category')
    st.plotly_chart(fig_bar)

    st.subheader("Raw Data")
    st.dataframe(df_filtered)
else:
    st.info("No data available yet. Please upload or enter cost optimization records.")
