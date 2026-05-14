# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# KPI + SCORING + RANKING VERSION (ULTIMATE IMAGE FIX)
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re

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
.main { background-color: #f5f7fa; }
.block-container { padding-top: 1rem; }
.kpi-card {
    background: white; padding: 20px; border-radius: 18px;
    text-align: center; box-shadow: 0px 2px 15px rgba(0,0,0,0.08);
    border-left: 8px solid #ff4b4b; margin-bottom: 20px;
}
.kpi-title { font-size: 16px; color: gray; }
.kpi-value { font-size: 34px; font-weight: bold; color: #111; }
.small-text { font-size: 14px; color: gray; }

.profile-img-container { display: flex; justify-content: center; margin-bottom: 15px; position: relative; }
.profile-img {
    border-radius: 50%; width: 140px; height: 140px;
    object-fit: cover; box-shadow: 0px 5px 15px rgba(0,0,0,0.15);
    background-color: #f0f2f6;
}
.img-rank-1 { border: 6px solid gold; }
.img-rank-2 { border: 6px solid silver; }
.img-rank-3 { border: 6px solid #cd7f32; }
.img-rank-4 { border: 6px solid #4a90e2; }

.rank-1 { color: gold; font-weight: bold; text-shadow: 1px 1px 2px #000; font-size: 24px;}
.rank-2 { color: silver; font-weight: bold; text-shadow: 1px 1px 2px #000; font-size: 22px;}
.rank-3 { color: #cd7f32; font-weight: bold; text-shadow: 1px 1px 2px #000; font-size: 20px;}
.rank-4 { color: #4a90e2; font-weight: bold; text-shadow: 1px 1px 2px #000; font-size: 18px;}

.performer-card {
    background: white; padding: 25px 20px; border-radius: 20px;
    text-align: center; box-shadow: 0px 6px 20px rgba(0,0,0,0.08);
    color: #000000; transition: transform 0.2s;
    height: 100%;
}
.performer-card:hover { transform: translateY(-5px); }
.tech-name-text { color: #222; font-weight: 800; font-size: 22px; margin-top: 10px;}
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

if df.empty:
    st.warning("⚠️ ไม่มีข้อมูล หรือไม่สามารถเชื่อมต่อ Google Sheet ได้")
    st.stop()

# =========================================================
# DETECT COLUMN
# =========================================================
date_col = "ลงวันที่ทำการตรวจสตีมแทรป" if "ลงวันที่ทำการตรวจสตีมแทรป" in df.columns else None
tech_col = "ช่าง ผู้ทำการตรวจสตีมแทรป" if "ช่าง ผู้ทำการตรวจสตีมแทรป" in df.columns else None

if not date_col or not tech_col:
    for col in df.columns:
        text = str(col).lower()
        if not date_col and ("วันที่" in text or "เวลา" in text): date_col = col
        if not tech_col and ("ผู้" in text or "ช่าง ผู้" in text): tech_col = col

# ทำความสะอาดชื่อช่างคอลัมน์หลัก (ลบช่องว่างทั้งหมด)
if tech_col:
    df[tech_col] = df[tech_col].astype(str).str.replace(r'\s+', '', regex=True)
    df[tech_col] = df[tech_col].replace({"ช่างเอ้": "ช่างเอ"})

# =========================================================
# SMART IMAGE EXTRACTOR (ป้องกันลิงก์เสีย 100%)
# =========================================================
def extract_clean_image_url(raw_text):
    text = str(raw_text).strip()
    if not text or text.lower() == 'nan': return None
    
    # สแกนหาลิงก์ที่ลงท้ายด้วยนามสกุลรูปภาพโดยตรง (มองข้ามวงเล็บหรือ tag ขยะ)
    match = re.search(r'(https?://[^\s"\'<>\[\]]+\.(?:png|jpg|jpeg|webp))', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # ถ้าไม่มีนามสกุล ลองดึงจาก tag [img]...[/img] 
    match_bb = re.search(r'\[img\](.*?)\[/img\]', text, re.IGNORECASE)
    if match_bb:
        return match_bb.group(1).strip()
        
    # เผื่อกรณีใส่ลิงก์มาดื้อๆ
    if text.startswith('http') and '[' not in text:
        return text
        
    return None

tech_image_map = {}

# ค้นหาคอลัมน์รูปภาพและคอลัมน์ชื่อช่างอ้างอิง
img_col = None
map_tech_col = None

for col in df.columns:
    if "รูป" in col or "ภาพ" in col:
        img_col = col

if img_col:
    # หาคอลัมน์ "ช่าง" ที่อยู่ใกล้กับคอลัมน์ "รูปภาพ"
    if 'ช่าง' in df.columns and img_col != 'ช่าง':
        map_tech_col = 'ช่าง'
    else:
        # ถ้าหาชื่อคอลัมน์ไม่เจอ ให้เอาคอลัมน์ทางซ้ายมือของคอลัมน์รูปภาพ
        idx = df.columns.get_loc(img_col)
        map_tech_col = df.columns[idx-1]

if img_col and map_tech_col:
    temp_df = df[[map_tech_col, img_col]].dropna()
    for _, row in temp_df.iterrows():
        raw_name = str(row[map_tech_col]).replace(" ", "").replace("ช่างเอ้", "ช่างเอ")
        raw_url = str(row[img_col])
        clean_url = extract_clean_image_url(raw_url)
        
        if clean_url and "ช่าง" in raw_name:
            tech_image_map[raw_name] = clean_url

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Clear Cache)", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

if tech_col:
    tech_list = ["ทั้งหมด"] + sorted(list(df[tech_col].dropna().unique()))
    selected_tech = st.sidebar.selectbox("เลือกช่าง", tech_list)
    if selected_tech != "ทั้งหมด":
        df = df[df[tech_col] == selected_tech]

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
ranking = pd.DataFrame()

if tech_col and total_jobs > 0:
    ranking = df.groupby(tech_col).size().reset_index(name='Total Jobs')
    max_job = ranking["Total Jobs"].max()
    ranking["Productivity"] = (ranking["Total Jobs"] / max_job) * 40 if max_job > 0 else 0
    ranking["Quality"] = 30
    ranking["Attendance"] = 20
    ranking["Safety"] = 10
    ranking["KPI Score"] = (ranking["Productivity"] + ranking["Quality"] + ranking["Attendance"] + ranking["Safety"]).round(2)

    def grade(score):
        if score >= 90: return "🟢 Excellent"
        elif score >= 75: return "🟡 Good"
        else: return "🔴 Improve"

    ranking["Grade"] = ranking["KPI Score"].apply(grade)
    # บังคับให้เรียงตามจำนวนงานเป็นหลัก
    ranking = ranking.sort_values(by=["Total Jobs", "KPI Score"], ascending=[False, False])
    ranking = ranking.reset_index(drop=True)
    ranking.index = ranking.index + 1

# =========================================================
# KPI CARDS SUMMARY
# =========================================================
avg_score = round(ranking["KPI Score"].mean(), 2) if not ranking.empty else 0
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Inspection</div><div class="kpi-value">{total_jobs}</div><div class="small-text">จำนวนงานตรวจทั้งหมด</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Technician</div><div class="kpi-value">{total_tech}</div><div class="small-text">จำนวนช่าง</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Average KPI</div><div class="kpi-value">{avg_score}</div><div class="small-text">คะแนนเฉลี่ย</div></div>', unsafe_allow_html=True)
with col4:
    best_tech = ranking.iloc[0][tech_col] if not ranking.empty else "-"
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Top Performer</div><div class="kpi-value">🏆</div><div class="small-text">{best_tech}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# TOP PERFORMER PROFILES (TOP 4)
# =========================================================
st.subheader("🏆 Top Performers (จัดอันดับตามจำนวนงานที่ตรวจ)")

if not ranking.empty:
    top_n = min(4, len(ranking))
    cols = st.columns(4) # แบ่ง 4 คอลัมน์คงที่
    
    medals = ["🥇", "🥈", "🥉", "🏅"]
    rank_classes = ["rank-1", "rank-2", "rank-3", "rank-4"]
    img_classes = ["img-rank-1", "img-rank-2", "img-rank-3", "img-rank-4"]

    for i in range(top_n):
        with cols[i]:
            tech_name = ranking.iloc[i][tech_col]
            score = ranking.iloc[i]["KPI Score"]
            jobs_done = ranking.iloc[i]["Total Jobs"]
            
            # ดึงรูปลิงก์ตรงที่ถูกทำความสะอาดแล้ว
            img_url = tech_image_map.get(tech_name)
            
            if not img_url:
                img_url = "https://cdn-icons-png.flaticon.com/512/4140/4140048.png"
            
            st.markdown(f"""
            <div class="performer-card">
                <div class="profile-img-container">
                    <img src="{img_url}" class="profile-img {img_classes[i]}" alt="Profile Image" />
                </div>
                <div class="{rank_classes[i]}">{medals[i]} อันดับ {i+1}</div>
                <div class="tech-name-text">👷 {tech_name}</div>
                <hr style="margin: 10px 0; border-color: #eee;">
                <div style="color:#d4af37; font-weight:bold; font-size: 16px;">⭐ KPI: {score}</div>
                <div style="color:#777; font-size:13px; margin-top:5px;">🔧 ตรวจแล้ว: {jobs_done} รายการ</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br><hr>", unsafe_allow_html=True)

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

    # EXPORT
    st.subheader("⬇️ Export Data")
    csv = show_table.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Download KPI CSV", data=csv, file_name='steam_trap_kpi.csv', mime='text/csv')

# =========================================================
# RAW DATA (DEBUGGER)
# =========================================================
with st.expander("🛠️ ตรวจสอบสถานะการเชื่อมต่อรูปภาพ (คลิกเพื่อดูรายละเอียด)"):
    st.markdown("**1. สถานะการดึงรูปลิงก์จาก Postimages:**")
    if tech_image_map:
        for t_name, link in tech_image_map.items():
            st.success(f"✅ พบรูปของ **{t_name}** -> {link}")
    else:
        st.error("❌ หาลิงก์รูปไม่เจอเลย กรุณาตรวจสอบตาราง Sheet")
    
    st.markdown("---")
    st.markdown("**2. ข้อมูลตารางอ้างอิง (Raw Table):**")
    if img_col and map_tech_col:
        st.dataframe(df[[map_tech_col, img_col]].dropna(), use_container_width=True)
    
    st.markdown("---")
    st.markdown("**3. ข้อมูลดิบทั้งหมด:**")
    st.dataframe(df, use_container_width=True, height=300)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
