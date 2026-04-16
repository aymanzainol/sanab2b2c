import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. إعدادات الصفحة والتنسيق الاحترافي
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
    
    html, body, [data-testid="stHeader"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
    }

    /* --- تعديل شامل لجعل "كل" أزرار الخريطة أطول وأضخم --- */
    div[data-testid="column"] {
        display: flex;
        align-items: stretch;
    }

    div.stButton {
        width: 100%;
        margin-bottom: 20px;
    }

    .stButton > button {
        width: 100% !important;
        /* هذا هو الطول الجديد ليكون الزر "Longer" بشكل ملحوظ */
        height: 180px !important; 
        border-radius: 20px !important;
        background-color: #1f2937 !important;
        border: 2px solid #4b5563 !important;
        color: white !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    .stButton > button div p {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        line-height: 1.6 !important;
    }

    .stButton > button:hover {
        border-color: #3b82f6 !important;
        background-color: #2d3748 !important;
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }

    /* صندوق الملاحظات والنسبة داخل النافذة */
    .observer-notes-box {
        background-color: #1e1e1e; padding: 25px; border-radius: 15px;
        border-right: 6px solid #eab308; position: relative;
        margin-bottom: 25px; color: #e5e7eb !important;
    }
    
    .score-circle {
        position: absolute; left: 20px; top: 25px;
        width: 80px; height: 80px; border-radius: 50%;
        background: #111827; border: 4px solid #eab308;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 1.3rem; color: #eab308;
    }

    .staff-tag {
        display: inline-block; background-color: #374151; color: #9ca3af;
        padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 10px;
        border: 1px solid #4b5563;
    }
    
    .notes-content { margin-left: 100px; }

    .checklist-item-popup { 
        background-color: #450a0a; padding: 15px; border-radius: 8px; 
        margin-bottom: 10px; border-right: 4px solid #ef4444; color: #fecaca !important;
        text-align: right; font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال ومعالجة البيانات
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        val = str(row[col]).strip()
        if not val or val.lower() == 'nan' or val == "": continue
        current_score = None
        if "عدد" in col:
            try:
                num_val = float(val.replace('%', ''))
                current_score = 100.0 if num_val >= 1 else 0.0
            except: pass
        if current_score is None:
            if '%' in val:
                try: current_score = float(val.replace('%', ''))
                except: pass
            elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم', 'يوجد', 'متوفر', 'جاهز', 'صح', '100']): current_score = 100.0
            elif any(n in val for n in ['لا', 'غير', 'لم', 'ناقص', 'خطأ', '0']): current_score = 0.0
        if current_score is not None:
            scores.append(current_score)
            if current_score < 100: 
                missing_items.append(f"{col} ({int(current_score)}%)")
    return pd.Series([round(np.mean(scores)) if scores else 0, " | ".join(missing_items)])

SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=20)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str).str.strip()
    df['Assistant_Name'] = df.iloc[:, 1].fillna("غير مسجل")
    df['Supervisor_Name'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 2], df.iloc[:, 3])
    df['Supervisor_Name'] = df['Supervisor_Name'].fillna("غير مسجل")
    if 'طابع زمني' in df.columns:
        df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
        df = df.sort_values(by='dt_object', ascending=False) if 'dt_object' in df.columns else df
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest, checklist_cols

# 3. النافذة المنبثقة
@st.dialog("تفاصيل جاهزية الموقع 🏕️", width="large")
def show_tent_details(tent_id, full_df):
    tent_history = full_df[full_df['Unified_ID'] == tent_id].copy()
    st.write(f"## موقع: {tent_id}")
    row = tent_history.iloc[0]
    score = int(row['Overall_Score'])
    
    st.markdown(f"""
    <div class='observer-notes-box'>
        <div class='score-circle'>{score}%</div>
        <div class='notes-content'>
            <div class='staff-tag'>🤝 المعاون: {row['Assistant_Name']}</div><br>
            <div class='staff-tag'>👤 المراقب: {row['Supervisor_Name']}</div>
            <hr style='border: 0; border-top: 1px solid #374151; margin: 10px 0;'>
            <b>ملاحظات المراقب:</b><br>
            {row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) else 'لا توجد ملاحظات مكتوبة.'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    missing_list = [item.strip() for item in str(row['Missing_Details']).split('|') if item.strip()]
    if missing_list:
        st.markdown(f"### ⚠️ النواقص ({len(missing_list)} بند)")
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 4. العرض
try:
    df_full, df_latest, checklist_cols = load_data()
    page = st.sidebar.radio("تغيير العرض:", ["📊 الإحصائيات", "🏕️ خريطة المواقع"])

    if page == "🏕️ خريطة المواقع":
        st.title("🏕️ خريطة المواقع")
        df_sorted = df_latest.sort_values(by=['شركة', 'Unified_ID'])
        
        # توزيع في 4 أعمدة فقط لزيادة الطول والعرض لكل زر
        grid_cols = st.columns(4) 
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
            with grid_cols[idx % 4]:
                # كتابة النص بشكل عمودي لإجبار الزر على الطول
                label = f"{icon}\n{row['Unified_ID']}\n\nالإنجاز: {row['Overall_Score']}%"
                if st.button(label, key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row['Unified_ID'], df_full)
except Exception as e:
    st.error(f"خطأ: {e}")
