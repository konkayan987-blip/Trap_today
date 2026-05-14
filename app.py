# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# KPI + SCORING + RANKING VERSION
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re  # เพิ่ม regex สำหรับจัดการลิงก์ Google Drive
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
    border: 3px solid #ff4b4b;
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
image_col = "รูปภาพ" if "รูปภาพ" in df.columns else None

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
    df[tech_col] = df[tech_col].astype(str).str.strip()
    df[tech_col] = df[tech_col].replace({
        "ช่าง เอ": "ช่างเอ", "ช่างเอ ": "ช่างเอ", "ช่างเอ้": "ช่างเอ",
        "ช่าง บิว": "ช่างบิว", "ช่างบิว ": "ช่างบิว",
        "ช่าง พู": "ช่างพู", "ช่างพู ": "ช่างพู",
        "ช่าง ลือ": "ช่างลือ", "ช่างลือ ": "ช่างลือ",
        "ช่าง อ๊อฟ": "ช่างอ๊อฟ", "ช่างอ๊อฟ ": "ช่างอ๊อฟ",
        "ช่าง สอ": "ช่างสอ", "ช่างสอ ": "ช่างสอ"
    })

# 2. สร้าง Dictionary จับคู่ "ชื่อช่าง" กับ "ลิงก์รูปภาพ Google Drive"
tech_image_map = {}
if 'ช่าง' in df.columns and 'รูปภาพ' in df.columns:
    ref_df = df[['ช่าง', 'รูปภาพ']].dropna()
    for _, row in ref_df.iterrows():
        ref_name = str(row['ช่าง']).strip().replace(" ", "") # ลบช่องว่างให้ตรงกัน
        if ref_name.startswith("ช่าง") and len(ref_name) > 4:
            # แปลง "ช่างอ๊อฟ" (ไม่มีวรรค) เผื่อไว้เทียบ
            pass
        else:
             # ใส่ตรรกะทำความสะอาดแบบเดียวกัน
             ref_name = str(row['ช่าง']).strip()
             ref_name = ref_name.replace("ช่าง ", "ช่าง")

        raw_url = str(row['รูปภาพ']).strip()
        
        # แปลงลิงก์ Google Drive ให้เป็น Direct Image Link
        img_id_match = re.search(r'id=([a-zA-Z0-9_-]+)|d/([a-zA-Z0-9_-]+)', raw_url)
        if img_id_match:
            img_id = img_id_match.group(1) if img_id_match.group(1) else img_id_match.group(2)
            tech_image_map[ref_name] = f"https://drive.google.com/uc?id={img_id}"
        else:
            tech_image_map[ref_name] = raw_url

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

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
total_tech = df[tech_col].nunique() if tech_col else 0

# =========================================================
# SCORING SYSTEM
# =========================================================
ranking = pd.DataFrame()
if tech_col and not df.empty:
    # นับจำนวนแถว (จำนวนงานตรวจ)
    ranking = df.groupby(tech_col).size().reset_index(name='Total Jobs')
    
    # Productivity Score
    max_job = ranking["Total Jobs"].max()
    if max_job > 0:
        ranking["Productivity"] = (ranking["Total Jobs"] / max_job) * 40
    else:
        ranking["Productivity"] = 0

    # Quality, Attendance, Safety
    ranking["Quality"] = 30
    ranking["Attendance"] = 20
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
        if score >= 90: return "🟢 Excellent"
        elif score >= 75: return "🟡 Good"
        else: return "🔴 Improve"

    ranking["Grade"] = ranking["KPI Score"].apply(grade)
    
    # สำคัญ: จัดอันดับโดยเน้นที่ Total Jobs (จำนวนงานตรวจ) เป็นหลัก หากเท่ากันค่อยดู KPI
    ranking = ranking.sort_values(by=["Total Jobs", "KPI Score"], ascending=[False, False])
    ranking.index = range(1, len(ranking) + 1)

# =========================================================
# KPI SUMMARY
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
# TOP PERFORMER PROFILES (TOP 3)
# =========================================================
st.subheader("🏆 Top Performers (จัดอันดับตามจำนวนงานที่ตรวจ)")

if not ranking.empty:
    top_n = min(3, len(ranking)) # แสดงผลสูงสุด 3 อันดับแรก
    cols = st.columns(top_n)
    
    medals = ["🥇 อันดับ 1", "🥈 อันดับ 2", "🥉 อันดับ 3"]
    
    for i in range(top_n):
        with cols[i]:
            tech_name = ranking.iloc[i][tech_col]
            top_score = ranking.iloc[i]["KPI Score"]
            jobs_done = ranking.iloc[i]["Total Jobs"]
            
            # ดึงรูปภาพจาก Dictionary ที่เราสร้างไว้ตอนต้น
            img_url = tech_image_map.get(tech_name, "https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
            
            st.markdown(f"""
            <div style="text-align: center; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div class="profile-img-container">
                    <img src="{img_url}" class="profile-img" onerror="this.src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png'">
                </div>
                <h3 style="margin-bottom: 5px; color: #000000;">{medals[i]}</h3>
                <h4 style="margin-top: 0; color: #333333;">👷 {tech_name}</h4>
                <p style="margin: 5px 0; color: #222222;">⭐ KPI Score: <b style="color: #ff4b4b;">{top_score}</b></p>
                <p style="margin: 5px 0; color: #222222;">🔧 ตรวจแล้ว: <b style="color: #000000;">{jobs_done}</b> รายการ</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("ยังไม่มีข้อมูลผลงานสำหรับจัดอันดับ")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# CHARTS
# =========================================================
if not ranking.empty:
    left, right = st.columns(2)

    # BAR CHART
    with left:
        st.subheader("👷 จำนวนงานตรวจของช่าง")
        fig_bar = px.bar(
            ranking, x=tech_col, y='Total Jobs',
            text='Total Jobs', color='KPI Score',
            color_continuous_scale="Reds"
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(height=450)
        st.plotly_chart(fig_bar, use_container_width=True)

    # PIE CHART
    with right:
        st.subheader("📊 สัดส่วนงานของช่าง")
        fig_pie = px.pie(
            ranking, names=tech_col, values='Total Jobs',
            hole=0.45, color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_pie.update_layout(height=450)
        st.plotly_chart(fig_pie, use_container_width=True)

    # KPI SCORE CHART
    st.subheader("⭐ KPI Score Ranking")
    fig_score = px.bar(
        ranking, x=tech_col, y='KPI Score',
        text='KPI Score', color='KPI Score',
        color_continuous_scale="Viridis"
    )
    fig_score.update_traces(textposition='outside')
    fig_score.update_layout(height=500)
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
if not ranking.empty:
    st.subheader("🏆 KPI Ranking Table")
    
    show_table = ranking[[
        tech_col, "Total Jobs", "Productivity", 
        "Quality", "Attendance", "Safety", "KPI Score", "Grade"
    ]].copy()
    
    show_table.columns = [
        "ช่าง", "จำนวนงาน", "Productivity", 
        "Quality", "Attendance", "Safety", "KPI Score", "Grade"
    ]
    
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
with st.expander("📄 ดูข้อมูล Raw Data ทั้งหมด"):
    st.dataframe(df, use_container_width=True, height=500)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
