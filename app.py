# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# KPI + SCORING + RANKING VERSION (ULTIMATE IMAGE FIX V5)
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
# TITLE & SIDEBAR
# =========================================================
st.title("🔥 ระบบติดตามผลงานช่าง Steam Trap")
st.markdown("### Executive KPI Dashboard")

st.sidebar.title("🔎 FILTER")
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Clear Cache)", type="primary"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.markdown("---")

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
# HELPER: CLEAN NAME
# =========================================================
def clean_thai_name(name):
    """ทำความสะอาดชื่อช่าง ลบช่องว่างและอักขระพิเศษ"""
    if pd.isna(name): return ""
    # เอาช่องว่างออกทั้งหมด (Space, Tab, Zero-width space)
    clean_str = re.sub(r'\s+', '', str(name)).strip()
    # แก้ไขชื่อที่พบบ่อยว่าเขียนผิด
    clean_str = clean_str.replace("ช่างเอ้", "ช่างเอ")
    return clean_str

# =========================================================
# DETECT MAIN COLUMNS
# =========================================================
date_col = "ลงวันที่ทำการตรวจสตีมแทรป" if "ลงวันที่ทำการตรวจสตีมแทรป" in df.columns else None
tech_col = "ช่าง ผู้ทำการตรวจสตีมแทรป" if "ช่าง ผู้ทำการตรวจสตีมแทรป" in df.columns else None

if not date_col or not tech_col:
    for col in df.columns:
        text = str(col).lower()
        if not date_col and ("วันที่" in text or "เวลา" in text): date_col = col
        if not tech_col and ("ผู้" in text or "ช่าง ผู้" in text): tech_col = col

# ทำความสะอาดชื่อช่างในตารางหลัก
if tech_col:
    df[tech_col] = df[tech_col].apply(clean_thai_name)

# =========================================================
# SMART IMAGE EXTRACTOR (Content-Based Scanning)
# =========================================================
tech_image_map = {}
img_col = None
map_tech_col = None

# 1. สแกนหาคอลัมน์ที่มีคำว่า http (คอลัมน์รูปภาพ)
for col in df.columns:
    if df[col].astype(str).str.contains(r'https?://', regex=True, na=False).any():
        img_col = col
        break

# 2. ถอยหลังหาคอลัมน์ชื่อช่างอ้างอิง
if img_col:
    idx = df.columns.get_loc(img_col)
    for i in range(idx - 1, -1, -1):
        col_name = df.columns[i]
        if col_name != tech_col:
            if df[col_name].astype(str).str.contains('ช่าง', na=False).any():
                map_tech_col = col_name
                break
    
    if not map_tech_col and idx > 0:
        map_tech_col = df.columns[idx - 1]

# 3. จับคู่ข้อมูลชื่อกับรูปภาพแบบสุดโหด (Bulletproof Mapping)
if img_col and map_tech_col:
    for _, row in df.iterrows():
        raw_name = str(row[map_tech_col])
        raw_url = str(row[img_col])
        
        if raw_name.lower() in ['nan', 'none', '']: continue
        if raw_url.lower() in ['nan', 'none', '']: continue
        
        # คลีนชื่อให้เหลือแค่ข้อความติดกัน (เช่น 'ช่างสอ')
        clean_name = clean_thai_name(raw_name)
        
        # ตัด tag ขยะ BBCode ทิ้งก่อน
        clean_url_str = re.sub(r'\[/?url.*?\]', '', raw_url, flags=re.IGNORECASE)
        clean_url_str = re.sub(r'\[/?img.*?\]', '', clean_url_str, flags=re.IGNORECASE)
        
        # ดึงเฉพาะลิงก์ที่ซ่อนอยู่ออกมา
        final_url = None
        urls = re.findall(r'(https?://[^\s<>\[\]]+)', clean_url_str)
        
        if urls:
            # คัดกรองเอาเฉพาะลิงก์ที่เป็นรูปภาพ
            for u in urls:
                if any(ext in u.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                    final_url = u
                    break
            # ถ้าหาลิงก์นามสกุลภาพไม่เจอ ให้เอาลิงก์แรกที่เจอมาใช้เผื่อไว้ก่อน
            if not final_url:
                final_url = urls[0]
            
        if final_url and clean_name:
            tech_image_map[clean_name] = final_url

# =========================================================
# FILTER LOGIC
# =========================================================
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
    ranking = ranking.sort_values(by=["Total Jobs", "KPI Score"], ascending=[False, False]).reset_index(drop=True)
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
    cols = st.columns(4)
    
    medals = ["🥇", "🥈", "🥉", "🏅"]
    rank_classes = ["rank-1", "rank-2", "rank-3", "rank-4"]
    img_classes = ["img-rank-1", "img-rank-2", "img-rank-3", "img-rank-4"]

    for i in range(top_n):
        with cols[i]:
            tech_name = ranking.iloc[i][tech_col]
            score = ranking.iloc[i]["KPI Score"]
            jobs_done = ranking.iloc[i]["Total Jobs"]
            
            # ดึงรูปลิงก์จากพจนานุกรมที่เราจับคู่ไว้
            img_url = tech_image_map.get(tech_name)
            
            # ถ้าระบบหาไม่เจอ ให้ใช้รูปหมวกเหลืองสำรอง
            if not img_url:
                img_url = "https://cdn-icons-png.flaticon.com/512/4140/4140048.png"
            
            # สร้างการ์ดแสดงผล (มีการใส่ referrerpolicy="no-referrer" เพื่อกันการโดนบล็อก)
            st.markdown(f"""
            <div class="performer-card">
                <div class="profile-img-container">
                    <img src="{img_url}" class="profile-img {img_classes[i]}" alt="Profile Image" referrerpolicy="no-referrer" />
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
# RANKING TABLE & EXPORT
# =========================================================
st.subheader("🏆 KPI Ranking Table")

if not ranking.empty:
    show_table = ranking[[tech_col, "Total Jobs", "Productivity", "Quality", "Attendance", "Safety", "KPI Score", "Grade"]].copy()
    show_table.columns = ["ช่าง", "จำนวนงาน", "Productivity", "Quality", "Attendance", "Safety", "KPI Score", "Grade"]
    st.dataframe(show_table, use_container_width=True, height=400)

    st.subheader("⬇️ Export Data")
    csv = show_table.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Download KPI CSV", data=csv, file_name='steam_trap_kpi.csv', mime='text/csv')

# =========================================================
# RAW DATA (DEBUGGER)
# =========================================================
with st.expander("🛠️ ตรวจสอบสถานะการเชื่อมต่อรูปภาพ (คลิกเพื่อดูรายละเอียด)"):
    st.markdown("**1. สถานะการดึงรูปลิงก์จาก Sheet:**")
    if tech_image_map:
        for t_name, link in tech_image_map.items():
            st.success(f"✅ พบรูปของ **{t_name}** -> [คลิกเพื่อดูรูปลิงก์]({link})")
            if not any(ext in link.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                st.warning(f"⚠️ คำเตือน: ลิงก์ของ {t_name} ไม่ได้ลงท้ายด้วย .png หรือ .jpg อาจจะทำให้รูปภาพไม่แสดงผล")
    else:
        st.error("❌ หาลิงก์รูปไม่เจอเลย กรุณาตรวจสอบตาราง Sheet")
    
    st.markdown("---")
    st.markdown("**2. ข้อมูลคอลัมน์ที่ระบบ AI ตรวจพบ (Raw Table):**")
    if img_col and map_tech_col:
        st.info(f"🔍 ตรวจพบ Column อ้างอิงชื่อช่าง: **'{map_tech_col}'** | Column รูป: **'{img_col}'**")
        raw_show = df[[map_tech_col, img_col]].copy()
        raw_show = raw_show.dropna(subset=[img_col])
        st.dataframe(raw_show, use_container_width=True)
    else:
        st.error("❌ สแกนไม่พบคอลัมน์ที่มีเนื้อหาเป็นลิงก์ http")
    
    st.markdown("---")
    st.markdown("**3. ข้อมูลดิบทั้งหมดใน Sheet:**")
    st.dataframe(df, use_container_width=True, height=300)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
