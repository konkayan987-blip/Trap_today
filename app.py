# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# VERSION : EXECUTIVE EDITION
# DEVELOPED WITH STREAMLIT
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

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

.block-container {
    padding-top: 1rem;
}

.kpi-card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0px 2px 15px rgba(0,0,0,0.08);
    border-left: 8px solid #ff4b4b;
}

.kpi-title {
    font-size: 16px;
    color: gray;
}

.kpi-value {
    font-size: 38px;
    font-weight: bold;
    color: #0E1117;
}

.small-text {
    font-size: 14px;
    color: gray;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("🔥 ระบบติดตามผลงานช่าง Steam Trap")
st.markdown("### Executive Dashboard")

# =========================================================
# GOOGLE SHEET
# =========================================================
sheet_id = "1xPGDL6bpA4k9_D-UkFz3ShMt-6Qzw7GY-mSF9h3i4jM"

csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data(ttl=300)
def load_data():

    df = pd.read_csv(csv_url)

    # ลบแถวว่าง
    df = df.dropna(how='all')

    # clean column
    df.columns = [str(col).strip() for col in df.columns]

    return df

df = load_data()

# =========================================================
# DETECT COLUMN
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
# DATE CLEAN
# =========================================================
if date_col:

    df[date_col] = pd.to_datetime(
        df[date_col],
        errors='coerce'
    )

    df = df.dropna(subset=[date_col])

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

# -------------------------
# TECH FILTER
# -------------------------
if tech_col:

    tech_list = ["ทั้งหมด"] + list(
        sorted(df[tech_col].dropna().unique())
    )

    selected_tech = st.sidebar.selectbox(
        "เลือกช่าง",
        tech_list
    )

    if selected_tech != "ทั้งหมด":

        df = df[df[tech_col] == selected_tech]

# -------------------------
# DATE FILTER
# -------------------------
if date_col:

    min_date = df[date_col].min().date()
    max_date = df[date_col].max().date()

    date_range = st.sidebar.date_input(
        "เลือกช่วงวันที่",
        value=(min_date, max_date)
    )

    if len(date_range) == 2:

        start_date, end_date = date_range

        df = df[
            (df[date_col].dt.date >= start_date) &
            (df[date_col].dt.date <= end_date)
        ]

# =========================================================
# KPI CALCULATION
# =========================================================
total_jobs = len(df)

# technician
if tech_col:
    total_tech = df[tech_col].nunique()
else:
    total_tech = 0

# score
avg_score = 0

if score_col:

    try:
        df[score_col] = pd.to_numeric(
            df[score_col],
            errors='coerce'
        )

        avg_score = round(
            df[score_col].mean(),
            2
        )

    except:
        avg_score = 0

# completion
completion_rate = 100

# status
if avg_score >= 90:
    status = "🟢 Excellent"

elif avg_score >= 75:
    status = "🟡 Good"

else:
    status = "🔴 Need Improve"

# =========================================================
# KPI DISPLAY
# =========================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Inspection</div>
        <div class="kpi-value">{total_jobs}</div>
        <div class="small-text">จำนวนงานตรวจทั้งหมด</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Technician</div>
        <div class="kpi-value">{total_tech}</div>
        <div class="small-text">จำนวนช่าง</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Average Score</div>
        <div class="kpi-value">{avg_score}</div>
        <div class="small-text">คะแนนเฉลี่ย</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Performance</div>
        <div class="kpi-value">{status}</div>
        <div class="small-text">สถานะรวม</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# CHART SECTION
# =========================================================
left, right = st.columns(2)

# =========================================================
# TECHNICIAN PERFORMANCE
# =========================================================
with left:

    st.subheader("👷 ผลงานช่าง")

    if tech_col:

        tech_summary = (
            df.groupby(tech_col)
            .size()
            .reset_index(name='Total Jobs')
            .sort_values(
                by='Total Jobs',
                ascending=False
            )
        )

        fig_bar = px.bar(
            tech_summary,
            x=tech_col,
            y='Total Jobs',
            text='Total Jobs',
            title='จำนวนงานตรวจของช่าง'
        )

        fig_bar.update_traces(
            textposition='outside'
        )

        fig_bar.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_bar,
            use_container_width=True
        )

# =========================================================
# PIE CHART
# =========================================================
with right:

    st.subheader("📊 สัดส่วนงานของช่าง")

    if tech_col:

        pie_data = (
            df.groupby(tech_col)
            .size()
            .reset_index(name='Total')
        )

        fig_pie = px.pie(
            pie_data,
            names=tech_col,
            values='Total',
            hole=0.45
        )

        fig_pie.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True
        )

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

    fig_line.update_layout(
        height=450
    )

    st.plotly_chart(
        fig_line,
        use_container_width=True
    )

# =========================================================
# SCORE ANALYSIS
# =========================================================
if score_col:

    st.subheader("⭐ Score Analysis")

    try:

        fig_hist = px.histogram(
            df,
            x=score_col,
            nbins=20,
            title='Distribution of Score'
        )

        fig_hist.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_hist,
            use_container_width=True
        )

    except:
        st.warning("ไม่สามารถวิเคราะห์คะแนนได้")

# =========================================================
# RANKING TABLE
# =========================================================
st.subheader("🏆 Technician Ranking")

if tech_col:

    ranking = (
        df.groupby(tech_col)
        .size()
        .reset_index(name='Total Jobs')
        .sort_values(
            by='Total Jobs',
            ascending=False
        )
    )

    ranking.index = ranking.index + 1

    ranking.columns = [
        "ช่าง",
        "จำนวนงาน"
    ]

    st.dataframe(
        ranking,
        use_container_width=True,
        height=300
    )

# =========================================================
# RAW DATA
# =========================================================
with st.expander("📄 ดูข้อมูลทั้งหมด"):

    st.dataframe(
        df,
        use_container_width=True,
        height=500
    )

# =========================================================
# EXPORT CSV
# =========================================================
st.subheader("⬇️ Export Data")

csv = df.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name='steam_trap_dashboard.csv',
    mime='text/csv'
)

# =========================================================
# AUTO REFRESH INFO
# =========================================================
st.caption("🔄 Auto Refresh ทุก 5 นาที")

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown(
    "### Developed for Maintenance Team 🚀"
)
