# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# KPI + SCORING + RANKING VERSION
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
    font-size: 34px;
    font-weight: bold;
    color: #111;
}

.small-text {
    font-size: 14px;
    color: gray;
}

.rank-1 {
    color: gold;
    font-weight: bold;
}

.rank-2 {
    color: silver;
    font-weight: bold;
}

.rank-3 {
    color: #cd7f32;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("🔥 ระบบติดตามผลงานช่าง Steam Trap")
st.markdown("### Executive KPI Dashboard")

# =========================================================
# GOOGLE SHEET
# =========================================================
sheet_id = "1xPGDL6bpA4k9_D-UkFz3ShMt-6Qzw7GY-mSF9h3i4jM"

gid = "459028693"

csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data(ttl=300)
def load_data():

    try:

        df = pd.read_csv(csv_url)

        df = df.dropna(how='all')

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
# DETECT COLUMN
# =========================================================
date_col = None
tech_col = None
score_col = None

for col in df.columns:

    text = str(col)

    if "วันที่" in text or "เวลา" in text:
        date_col = col

    if "ผู้" in text or "ช่าง" in text:
        tech_col = col

    if "คะแนน" in text:
        score_col = col

# =========================================================
# CLEAN TECHNICIAN NAME
# =========================================================
if tech_col:

    df[tech_col] = df[tech_col].astype(str).str.strip()

    df[tech_col] = df[tech_col].replace({

        "ช่าง เอ": "ช่างเอ",
        "ช่างเอ ": "ช่างเอ",
        "ช่างเอ้": "ช่างเอ",

        "ช่าง บิว": "ช่างบิว",
        "ช่างบิว ": "ช่างบิว",

        "ช่าง พู": "ช่างพู",
        "ช่างพู ": "ช่างพู",

        "ช่าง ลือ": "ช่างลือ",
        "ช่างลือ ": "ช่างลือ"

    })

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

# =========================================================
# TECH FILTER
# =========================================================
if tech_col:

    tech_list = ["ทั้งหมด"] + sorted(
        list(df[tech_col].dropna().unique())
    )

    selected_tech = st.sidebar.selectbox(
        "เลือกช่าง",
        tech_list
    )

    if selected_tech != "ทั้งหมด":

        df = df[
            df[tech_col] == selected_tech
        ]

# =========================================================
# DATE FILTER
# =========================================================
if date_col:

    try:

        df[date_col] = pd.to_datetime(
            df[date_col],
            errors='coerce',
            dayfirst=True
        )

        df = df[df[date_col].notna()]

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

    except:
        pass

# =========================================================
# KPI CALCULATION
# =========================================================
total_jobs = len(df)

if tech_col:
    total_tech = df[tech_col].nunique()
else:
    total_tech = 0

# =========================================================
# SCORING SYSTEM
# =========================================================
if tech_col:

    ranking = (
        df.groupby(tech_col)
        .size()
        .reset_index(name='Total Jobs')
    )

    # Productivity Score
    max_job = ranking["Total Jobs"].max()

    ranking["Productivity"] = (
        ranking["Total Jobs"] / max_job
    ) * 40

    # Quality Score
    ranking["Quality"] = 30

    # Attendance
    ranking["Attendance"] = 20

    # Safety
    ranking["Safety"] = 10

    # Total KPI
    ranking["KPI Score"] = (
        ranking["Productivity"] +
        ranking["Quality"] +
        ranking["Attendance"] +
        ranking["Safety"]
    ).round(2)

    # Grade
    def grade(score):

        if score >= 90:
            return "🟢 Excellent"

        elif score >= 75:
            return "🟡 Good"

        else:
            return "🔴 Improve"

    ranking["Grade"] = ranking["KPI Score"].apply(grade)

    ranking = ranking.sort_values(
        by="KPI Score",
        ascending=False
    )

    ranking.index = ranking.index + 1

# =========================================================
# KPI SUMMARY
# =========================================================
avg_score = round(
    ranking["KPI Score"].mean(),
    2
)

# =========================================================
# KPI CARDS
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
        <div class="kpi-title">Average KPI</div>
        <div class="kpi-value">{avg_score}</div>
        <div class="small-text">คะแนนเฉลี่ย</div>
    </div>
    """, unsafe_allow_html=True)

with col4:

    best_tech = ranking.iloc[0][tech_col]

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Top Performer</div>
        <div class="kpi-value">🏆</div>
        <div class="small-text">{best_tech}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# CHARTS
# =========================================================
left, right = st.columns(2)

# =========================================================
# BAR CHART
# =========================================================
with left:

    st.subheader("👷 ผลงานช่าง")

    fig_bar = px.bar(
        ranking,
        x=tech_col,
        y='Total Jobs',
        text='Total Jobs',
        color='KPI Score',
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

    fig_pie = px.pie(
        ranking,
        names=tech_col,
        values='Total Jobs',
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
# KPI SCORE CHART
# =========================================================
st.subheader("⭐ KPI Score Ranking")

fig_score = px.bar(
    ranking,
    x=tech_col,
    y='KPI Score',
    text='KPI Score',
    color='KPI Score'
)

fig_score.update_traces(
    textposition='outside'
)

fig_score.update_layout(
    height=500
)

st.plotly_chart(
    fig_score,
    width='stretch'
)

# =========================================================
# DAILY TREND
# =========================================================
if date_col and not df.empty:

    st.subheader("📈 Daily Inspection Trend")

    daily = (
        df.groupby(df[date_col].dt.date)
        .size()
        .reset_index(name='Total Jobs')
    )

    fig_line = px.line(
        daily,
        x=date_col,
        y='Total Jobs',
        markers=True
    )

    fig_line.update_layout(
        height=450
    )

    st.plotly_chart(
        fig_line,
        width='stretch'
    )

# =========================================================
# RANKING TABLE
# =========================================================
st.subheader("🏆 KPI Ranking Table")

show_table = ranking[[
    tech_col,
    "Total Jobs",
    "Productivity",
    "Quality",
    "Attendance",
    "Safety",
    "KPI Score",
    "Grade"
]]

show_table.columns = [
    "ช่าง",
    "จำนวนงาน",
    "Productivity",
    "Quality",
    "Attendance",
    "Safety",
    "KPI Score",
    "Grade"
]

st.dataframe(
    show_table,
    width='stretch',
    height=400
)

# =========================================================
# EXPORT
# =========================================================
st.subheader("⬇️ Export Data")

csv = show_table.to_csv(
    index=False
).encode('utf-8-sig')

st.download_button(
    label="📥 Download KPI CSV",
    data=csv,
    file_name='steam_trap_kpi.csv',
    mime='text/csv'
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
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
