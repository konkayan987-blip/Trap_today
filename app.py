# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# SAFE VERSION - GOOGLE SHEET READY
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
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
    font-size: 36px;
    font-weight: bold;
    color: #111;
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

csv_url = csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=459028693

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data(ttl=300)
def load_data():

    try:

        df = pd.read_csv(csv_url)

        # ลบแถวว่าง
        df = df.dropna(how='all')

        # clean columns
        df.columns = [str(col).strip() for col in df.columns]

        return df

    except Exception as e:

        st.error(f"โหลดข้อมูลไม่ได้ : {e}")
        return pd.DataFrame()

df = load_data()

# =========================================================
# CHECK DATA
# =========================================================
if df.empty:

    st.warning("⚠️ ไม่มีข้อมูล")
    st.stop()

# =========================================================
# DETECT COLUMNS
# =========================================================
date_col = None
tech_col = None
score_col = None

for col in df.columns:

    col_text = str(col)

    if "วันที่" in col_text or "เวลา" in col_text:
        date_col = col

    if "ผู้" in col_text or "ช่าง" in col_text:
        tech_col = col

    if "คะแนน" in col_text:
        score_col = col

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

# =========================================================
# TECH FILTER
# =========================================================
if tech_col:

    tech_list = ["ทั้งหมด"] + sorted(
        list(df[tech_col].dropna().astype(str).unique())
    )

    selected_tech = st.sidebar.selectbox(
        "เลือกช่าง",
        tech_list
    )

    if selected_tech != "ทั้งหมด":

        df = df[
            df[tech_col].astype(str) == selected_tech
        ]

# =========================================================
# DATE FILTER SAFE VERSION
# =========================================================
if date_col:

    try:

        # แปลงวันที่
        df[date_col] = pd.to_datetime(
            df[date_col],
            errors='coerce',
            dayfirst=True
        )

        # ลบวันที่เสีย
        df = df[df[date_col].notna()]

        # ถ้ามีข้อมูลวันที่
        if not df.empty:

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

        else:

            st.warning("⚠️ ไม่พบข้อมูลวันที่ที่ถูกต้อง")

    except Exception as e:

        st.error(f"Date Error : {e}")

# =========================================================
# KPI
# =========================================================
total_jobs = len(df)

# technician
if tech_col:
    total_tech = df[tech_col].nunique()
else:
    total_tech = 0

# average score
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

# performance
if avg_score >= 90:
    performance = "🟢 Excellent"

elif avg_score >= 75:
    performance = "🟡 Good"

else:
    performance = "🔴 Need Improve"

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
        <div class="kpi-value">{performance}</div>
        <div class="small-text">สถานะรวม</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# CHART SECTION
# =========================================================
left, right = st.columns(2)

# =========================================================
# TECH PERFORMANCE
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
            width='stretch'
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
            width='stretch'
        )

# =========================================================
# DAILY TREND
# =========================================================
st.subheader("📈 Daily Inspection Trend")

if date_col and not df.empty:

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
        width='stretch'
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
            width='stretch'
        )

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
        width='stretch',
        height=350
    )

# =========================================================
# RAW DATA
# =========================================================
with st.expander("📄 ดูข้อมูลทั้งหมด"):

    st.dataframe(
        df,
        width='stretch',
        height=500
    )

# =========================================================
# EXPORT CSV
# =========================================================
st.subheader("⬇️ Export Data")

csv = df.to_csv(
    index=False
).encode('utf-8-sig')

st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name='steam_trap_dashboard.csv',
    mime='text/csv'
)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
