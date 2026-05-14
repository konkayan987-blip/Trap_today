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
    margin-bottom: 20px;
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
.profile-img-container {
    display: flex;
    justify-content: center;
    margin-bottom: 10px;
}
.profile-img {
    border-radius: 50%;
    width: 120px;
    height: 120px;
    object-fit: cover;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
}
.img-rank-1 { border: 4px solid gold; }
.img-rank-2 { border: 4px solid silver; }
.img-rank-3 { border: 4px solid #cd7f32; }
.img-rank-4 { border: 4px solid #4a90e2; }

.rank-1 { color: gold; font-weight: bold; text-shadow: 1px 1px 2px #000; }
.rank-2 { color: silver; font-weight: bold; text-shadow: 1px 1px 2px #000; }
.rank-3 { color: #cd7f32; font-weight: bold; text-shadow: 1px 1px 2px #000;}
.rank-4 { color: #4a90e2; font-weight: bold; text-shadow: 1px 1px 2px #000;}

/* บังคับสีตัวหนังสือในการ์ดจัดอันดับให้เข้มขึ้นสำหรับ Dark Mode */
.performer-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    color: #333;
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
    st.warning("⚠️ ไม่มีข้อมูล หรือไม่สามารถเชื่อมต่อ Google Sheet ได้")
    st.stop()

# =========================================================
# DETECT COLUMN
# =========================================================
date_col = "ลงวันที่ทำการตรวจสตีมแทรป" if "ลงวันที่ทำการตรวจสตีมแทรป" in df.columns else None
tech_col = "ช่าง ผู้ทำการตรวจสตีมแทรป" if "ช่าง ผู้ทำการตรวจสตีมแทรป" in df.columns else None
score_col = None

# ค้นหาคอลัมน์สำรองกรณีชื่อคอลัมน์เปลี่ยน
if not date_col or not tech_col:
    for col in df.columns:
        text = str(col).lower()
        if not date_col and ("วันที่" in text or "เวลา" in text):
            date_col = col
        if not tech_col and ("ผู้" in text or "ช่าง ผู้" in text or "ช่าง" in text):
            # หลีกเลี่ยงคอลัมน์ "ช่าง" เดี่ยวๆ ที่เป็นแค่ตารางอ้างอิง
            if col != "ช่าง": 
                tech_col = col

# =========================================================
# CLEAN TECHNICIAN NAME & CREATE IMAGE MAP
# =========================================================
# 1. ทำความสะอาดชื่อช่างในคอลัมน์หลัก
if tech_col:
    # ลบช่องว่างทั้งหมดเพื่อป้องกันการจับคู่ผิด
    df[tech_col] = df[tech_col].astype(str).str.replace(r'\s+', '', regex=True)
    df[tech_col] = df[tech_col].replace({"ช่างเอ้": "ช่างเอ"})

# 2. สร้าง Dictionary จับคู่รูปภาพจากคอลัมน์ขวาสุด (รองรับ Postimages)
tech_image_map = {}
if 'ช่าง' in df.columns and 'รูปภาพ' in df.columns:
    ref_df = df[['ช่าง', 'รูปภาพ']].dropna()
    for _, row in ref_df.iterrows():
        # ทำความสะอาดชื่อให้อยู่ในรูปแบบเดียวกัน (ไม่มีช่องว่าง)
        ref_name = str(row['ช่าง']).replace(" ", "")
        ref_name = ref_name.replace("ช่างเอ้", "ช่างเอ")

        raw_url = str(row['รูปภาพ']).strip()
        
        # ลบ BBCode ที่อาจจะติดมาด้วย
        raw_url = raw_url.replace("[/img][/url]", "").replace("[img]", "").replace("[url=", "").strip()
        
        if raw_url.startswith('http'):
            tech_image_map[ref_name] = raw_url
        else:
            tech_image_map[ref_name] = None

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Clear Cache)"):
    st.cache_data.clear()
    st.rerun()

# =========================================================
# TECH FILTER
# =========================================================
if tech_col:
    tech_list = ["ทั้งหมด"] + sorted(list(df[tech_col].dropna().unique()))
    selected_tech = st.sidebar.selectbox("เลือกช่าง", tech_list)

    if selected_tech != "ทั้งหมด":
        df = df[df[tech_col] == selected_tech]

# =========================================================
# DATE FILTER
# =========================================================
if date_col:
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
        df = df[df[date_col].notna()]
        if not df.empty:
            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()
            date_range = st.sidebar.date_input("เลือกช่วงวันที่", value=(min_date, max_date))
            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]
    except:
        pass

# =========================================================
# KPI CALCULATION
# =========================================================
total_jobs = len(df)
total_tech = df[tech_col].nunique() if tech_col else 0

# =========================================================
# SCORING SYSTEM
# =========================================================
ranking = pd.DataFrame()

if tech_col and total_jobs > 0:
    ranking = df.groupby(tech_col).size().reset_index(name='Total Jobs')

    # Productivity Score
    max_job = ranking["Total Jobs"].max()
    ranking["Productivity"] = (ranking["Total Jobs"] / max_job) * 40 if max_job > 0 else 0

    # Quality, Attendance, Safety Scores
    ranking["Quality"] = 30
    ranking["Attendance"] = 20
    ranking["Safety"] = 10

    # Total KPI
    ranking["KPI Score"] = (ranking["Productivity"] + ranking["Quality"] + ranking["Attendance"] + ranking["Safety"]).round(2)

    def grade(score):
        if score >= 90: return "🟢 Excellent"
        elif score >= 75: return "🟡 Good"
        else: return "🔴 Improve"

    ranking["Grade"] = ranking["KPI Score"].apply(grade)

    # จัดอันดับตามจำนวนงานที่ทำได้ก่อน แล้วค่อยตามด้วย KPI
    ranking = ranking.sort_values(by=["Total Jobs", "KPI Score"], ascending=[False, False])
    ranking = ranking.reset_index(drop=True)
    ranking.index = ranking.index + 1

# =========================================================
# KPI CARDS SUMMARY
# =========================================================
avg_score = round(ranking["KPI Score"].mean(), 2) if not ranking.empty else 0

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
    best_tech = ranking.iloc[0][tech_col] if not ranking.empty else "-"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Top Performer</div>
        <div class="kpi-value">🏆</div>
        <div class="small-text">{best_tech}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# TOP PERFORMER PROFILES (TOP 4)
# =========================================================
st.subheader("🏆 Top Performers (จัดอันดับตามจำนวนงานที่ตรวจ)")

if not ranking.empty:
    top_n = min(4, len(ranking))
    cols = st.columns(top_n)
    
    medals = ["🥇", "🥈", "🥉", "🏅"]
    rank_classes = ["rank-1", "rank-2", "rank-3", "rank-4"]
    img_classes = ["img-rank-1", "img-rank-2", "img-rank-3", "img-rank-4"]

    for i in range(top_n):
        with cols[i]:
            tech_name = ranking.iloc[i][tech_col]
            score = ranking.iloc[i]["KPI Score"]
            jobs_done = ranking.iloc[i]["Total Jobs"]
            
            img_url = tech_image_map.get(tech_name)
            
            if not img_url:
                img_url = "https://cdn-icons-png.flaticon.com/512/4140/4140048.png"
            
            st.markdown(f"""
            <div class="performer-card">
                <div class="profile-img-container">
                    <img src="{img_url}" class="profile-img {img_classes[i]}" />
                </div>
                <h3 class="{rank_classes[i]}">{medals[i]} อันดับ {i+1}</h3>
                <h4 style="color:#222;">👷 {tech_name}</h4>
                <p style="color:#d4af37; font-weight:bold;">⭐ KPI Score: {score}</p>
                <p style="color:#777; font-size:12px;">🔧 ตรวจแล้ว: {jobs_done} รายการ</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# CHARTS
# =========================================================
left, right = st.columns(2)

with left:
    st.subheader("👷 จำนวนงานตรวจของช่าง")
    if not ranking.empty:
        fig_bar = px.bar(ranking, x=tech_col, y='Total Jobs', text='Total Jobs', color='KPI Score')
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(height=450)
        st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.subheader("📊 สัดส่วนงานของช่าง")
    if not ranking.empty:
        fig_pie = px.pie(ranking, names=tech_col, values='Total Jobs', hole=0.45)
        fig_pie.update_layout(height=450)
        st.plotly_chart(fig_pie, use_container_width=True)

# =========================================================
# KPI SCORE CHART
# =========================================================
st.subheader("⭐ KPI Score Ranking")
if not ranking.empty:
    fig_score = px.bar(ranking, x=tech_col, y='KPI Score', text='KPI Score', color='KPI Score')
    fig_score.update_traces(textposition='outside')
    fig_score.update_layout(height=450)
    st.plotly_chart(fig_score, use_container_width=True)

# =========================================================
# DAILY TREND
# =========================================================
if date_col and not df.empty:
    st.subheader("📈 Daily Inspection Trend")
    daily = df.groupby(df[date_col].dt.date).size().reset_index(name='Total Jobs')
    fig_line = px.line(daily, x=date_col, y='Total Jobs', markers=True)
    fig_line.update_layout(height=450)
    st.plotly_chart(fig_line, use_container_width=True)

# =========================================================
# RANKING TABLE
# =========================================================
st.subheader("🏆 KPI Ranking Table")

if not ranking.empty:
    show_table = ranking[[tech_col, "Total Jobs", "Productivity", "Quality", "Attendance", "Safety", "KPI Score", "Grade"]].copy()
    show_table.columns = ["ช่าง", "จำนวนงาน", "Productivity", "Quality", "Attendance", "Safety", "KPI Score", "Grade"]
    st.dataframe(show_table, use_container_width=True, height=400)

    # =========================================================
    # EXPORT
    # =========================================================
    st.subheader("⬇️ Export Data")
    csv = show_table.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Download KPI CSV",
        data=csv,
        file_name='steam_trap_kpi.csv',
        mime='text/csv'
    )

# =========================================================
# RAW DATA
# =========================================================
with st.expander("📄 ดูข้อมูล Raw Data ทั้งหมด (ใช้ตรวจสอบปัญหาการลิงก์รูปภาพ)"):
    st.write("**สถานะการจับคู่รูปภาพของช่าง:**")
    st.json(tech_image_map) 
    st.write("---")
    st.write("**ข้อมูลหลักในตาราง:**")
    st.dataframe(df, use_container_width=True, height=500)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
