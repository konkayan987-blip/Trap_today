# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# Developed for Factory Maintenance Team
# Streamlit + Google Sheet
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Steam Trap Dashboard",
    page_icon="🔥",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

.kpi-card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}

.big-font {
    font-size: 32px;
    font-weight: bold;
    color: #0E1117;
}

.small-font {
    font-size: 16px;
    color: gray;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("🔥 Steam Trap Maintenance Dashboard")
st.markdown("### ระบบติดตามผลงานช่าง Steam Trap")

# =========================================================
# GOOGLE SHEET CSV URL
# =========================================================

sheet_id = "1xPGDL6bpA4k9_D-UkFz3ShMt-6Qzw7GY-mSF9h3i4jM"

csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(csv_url)

    # เปลี่ยนชื่อคอลัมน์ภาษาไทยให้อ่านง่าย
    df.columns = [str(col).strip() for col in df.columns]

    return df

df = load_data()

# =========================================================
# SHOW RAW DATA
# =========================================================
with st.expander("📄 ดูข้อมูลทั้งหมด"):
    st.dataframe(df, use_container_width=True)

# =========================================================
# DETECT COLUMNS
# =========================================================

date_col = None
tech_col = None
score_col = None

for col in df.columns:

    if "วันที่" in col or "เวลา" in col:
        date_col = col

    if "ผู้" in col or "ช่าง" in col:
        tech_col = col

    if "คะแนน" in col:
        score_col = col

# =========================================================
# DATE CONVERT
# =========================================================
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("🔎 Filter")

# ช่าง
if tech_col:
    tech_list = ["ทั้งหมด"] + list(df[tech_col].dropna().unique())

    selected_tech = st.sidebar.selectbox(
        "เลือกช่าง",
        tech_list
    )

    if selected_tech != "ทั้งหมด":
        df = df[df[tech_col] == selected_tech]

# วันที่
if date_col:

    min_date = df[date_col].min()
    max_date = df[date_col].max()

    date_range = st.sidebar.date_input(
        "เลือกช่วงวันที่",
        [min_date, max_date]
    )

    if len(date_range) == 2:
        start_date, end_date = date_range

        df = df[
            (df[date_col].dt.date >= start_date) &
            (df[date_col].dt.date <= end_date)
        ]

# =========================================================
# KPI
# =========================================================

total_jobs = len(df)

total_tech = 0
if tech_col:
    total_tech = df[tech_col].nunique()

avg_score = 0
if score_col:
    try:
        avg_score = round(pd.to_numeric(df[score_col], errors='coerce').mean(), 2)
    except:
        avg_score = 0

completion_rate = 100

# =========================================================
# KPI DISPLAY
# =========================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="small-font">Total Inspection</div>
        <div class="big-font">{total_jobs}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="small-font">Technician</div>
        <div class="big-font">{total_tech}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="small-font">Average Score</div>
        <div class="big-font">{avg_score}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="small-font">Completion</div>
        <div class="big-font">{completion_rate}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# TECHNICIAN PERFORMANCE
# =========================================================
st.subheader("👷 Technician Performance")

if tech_col:

    tech_summary = (
        df.groupby(tech_col)
        .size()
        .reset_index(name='Total Jobs')
        .sort_values(by='Total Jobs', ascending=False)
    )

    fig_bar = px.bar(
        tech_summary,
        x=tech_col,
        y='Total Jobs',
        text='Total Jobs',
        title='จำนวนงานตรวจของช่าง'
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# DAILY TREND
# =========================================================
st.subheader("📈 Daily Inspection Trend")

if date_col:

    daily = (
        df.groupby(df[date_col].dt.date)
        .size()
        .reset_index(name='Total Jobs')
    )

    fig_line = px.line(
        daily,
        x=date_col,
        y='Total Jobs',
        markers=True,
        title='แนวโน้มการตรวจรายวัน'
    )

    st.plotly_chart(fig_line, use_container_width=True)

# =========================================================
# SCORE ANALYSIS
# =========================================================
if score_col:

    st.subheader("⭐ Score Analysis")

    try:

        df[score_col] = pd.to_numeric(df[score_col], errors='coerce')

        fig_hist = px.histogram(
            df,
            x=score_col,
            nbins=20,
            title='Distribution of Score'
        )

        st.plotly_chart(fig_hist, use_container_width=True)

    except:
        st.warning("ไม่สามารถวิเคราะห์คะแนนได้")

# =========================================================
# RANKING
# =========================================================
st.subheader("🏆 Technician Ranking")

if tech_col:

    ranking = (
        df.groupby(tech_col)
        .size()
        .reset_index(name='Total Jobs')
        .sort_values(by='Total Jobs', ascending=False)
    )

    ranking.index = ranking.index + 1

    st.dataframe(
        ranking,
        use_container_width=True
    )

# =========================================================
# DATA TABLE
# =========================================================
st.subheader("📋 Inspection Data")

st.dataframe(
    df,
    use_container_width=True,
    height=500
)

# =========================================================
# AUTO REFRESH
# =========================================================
st.caption("🔄 Auto Refresh ทุก 5 นาที")

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown("### Developed for Maintenance Team 🚀")
