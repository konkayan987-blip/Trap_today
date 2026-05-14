# =========================================================
# STEAM TRAP MAINTENANCE DASHBOARD
# KPI + SCORING + RANKING VERSION
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re  # เพิ่ม regex สำหรับจัดการลิงก์ Google Drive
import urllib.request # เพิ่มไลบรารีเพื่อโหลดรูปจาก Google Drive หลังบ้าน
import base64         # เพิ่มไลบรารีแปลงภาพหลบการบล็อก
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
# 1. ทำความสะอาดชื่อช่างในคอลัมน์หลัก (ตัดช่องว่างออกทั้งหมด ป้องกันการจับคู่ผิดพลาด)
if tech_col:
    df[tech_col] = df[tech_col].astype(str).str.replace(r'\s+', '', regex=True)
    df[tech_col] = df[tech_col].replace({"ช่างเอ้": "ช่างเอ"})

# 2. สร้าง Dictionary จับคู่ "ชื่อช่าง" กับ "ลิงก์รูปภาพโดยตรง"
tech_image_map = {}
if 'ช่าง' in df.columns and 'รูปภาพ' in df.columns:
    ref_df = df[['ช่าง', 'รูปภาพ']].dropna()
    for _, row in ref_df.iterrows():
        # ทำความสะอาดชื่อให้ไร้ช่องว่างเหมือนตารางหลัก
        ref_name = str(row['ช่าง']).replace(" ", "")
        ref_name = ref_name.replace("ช่างเอ้", "ช่างเอ")

        raw_url = str(row['รูปภาพ']).strip()
        
        # ป้องกันขั้นสุด: ลบแท็กขยะที่อาจจะติดมาจากการคัดลอกใน Postimages
        raw_url = raw_url.replace("[/img][/url]", "").replace("[img]", "").replace("[url=", "").strip()
        
        # เก็บ URL ตรงๆ ไว้
        if raw_url.startswith('http'):
            tech_image_map[ref_name] = raw_url
        else:
            tech_image_map[ref_name] = None

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔎 FILTER")

# เพิ่มปุ่มเคลียร์แคช เพื่อให้ดึงข้อมูลใหม่จาก Sheet ทันที
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
with st.expander("📄 ดูข้อมูล Raw Data ทั้งหมด (คลิกเพื่อตรวจสอบการเชื่อมลิงก์)"):
    st.write("**สถานะการจับคู่รูปภาพของช่าง:**")
    st.json(tech_image_map) # พิมพ์ค่าที่จับคู่ได้ให้ดูเลย จะได้รู้ว่าลิงก์ถูกดึงมาไหม
    st.write("---")
    st.write("**ข้อมูลหลักในตาราง:**")
    st.dataframe(df, use_container_width=True, height=500)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🔄 Auto Refresh ทุก 5 นาที")
st.markdown("### Developed for Maintenance Team 🚀")
