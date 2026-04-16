import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Configuration & Ultra-Strict CSS for Uniformity
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* General Styles */
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
    
    html, body, [data-testid="stHeader"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
    }

    /* --- THE UNIFORM GRID FIX --- */
    
    /* 1. Center the button container within the column */
    div.stButton {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
    }

    /* 2. Force every button to be identical in size and perfectly centered */
    .stButton > button {
        width: 180px !important;    /* Fixed width for all */
        height: 110px !important;   /* Fixed height for all */
        border-radius: 15px !important;
        background-color: #1f2937 !important;
        border: 2px solid #374151 !important;
        color: white !important;
        
        /* Flexbox for Internal Content Centering */
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        
        transition: all 0.2s ease-in-out !important;
        padding: 0 !important; /* Remove internal padding that causes offsets */
    }

    /* 3. Style the text inside the button for clarity */
    .stButton > button div p {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        line-height: 1.3 !important;
        width: 100% !important;
        text-align: center !important;
    }

    .stButton > button:hover {
        border-color: #3b82f6 !important;
        background-color: #2d3748 !important;
        transform: scale(1.05); /* Slight pop effect */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }

    /* Popup & Notes Styling */
    .observer-notes-box {
        background-color: #1e1e1e; padding: 18px; border-radius: 12px;
        border-right: 6px solid #eab308; color: #e5e7eb !important;
        line-height: 1.6; text-align: right;
    }
    .staff-tag {
        display: inline-block; background-color: #374151; color: #9ca3af;
        padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; margin-bottom: 8px;
        border: 1px solid #4b5563;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Processing (Same as before)
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
            if current_score < 100: missing_items.append(f"{col} (القيمة: {val})")
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
        df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest, checklist_cols

# 3. Popup Logic
@st.dialog("سجل جاهزية الموقع 🏕️")
def show_tent_details(tent_id, full_df):
    tent_history = full_df[full_df['Unified_ID'] == tent_id].copy()
    st.write(f"## موقع: {tent_id}")
    history_options = tent_history['طابع زمني'].tolist()
    selected_time = st.selectbox("🕒 اختر التقرير:", history_options)
    row = tent_history[tent_history['طابع زمني'] == selected_time].iloc[0]
    
    score = int(row['Overall_Score'])
    st.write(f"### الجاهزية: {score}%")
    st.progress(score / 100.0)

    st.markdown(f"""
    <div class='observer-notes-box'>
        <div class='staff-tag'>🤝 المعاون: {row['Assistant_Name']}</div><br>
        <div class='staff-tag'>👤 المراقب: {row['Supervisor_Name']}</div>
        <hr style='border: 0; border-top: 1px solid #374151; margin: 10px 0;'>
        {row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) else 'لا توجد ملاحظات.'}
    </div>
    """, unsafe_allow_html=True)

# 4. Main UI
try:
    df_full, df_latest, checklist_cols = load_data()

    # Tabs/Navigation
    top_m1, top_m2, top_m3 = st.columns([2, 3, 1])
    with top_m1: st.subheader("🚀 متابعة القطاعات")
    with top_m2: page = st.radio("الوضع:", ["📊 الإحصائيات", "🏕️ الخريطة"], horizontal=True, label_visibility="collapsed")
    with top_m3: 
        if st.button("🔄"): st.rerun()
    
    st.divider()

    if page == "📊 الإحصائيات":
        st.title("📊 التحليل العام")
        # Statistics logic... (as per previous version)

    elif page == "🏕️ الخريطة":
        st.title("🏕️ خريطة المواقع")
        df_sorted = df_latest.sort_values(by=['شركة', 'Unified_ID'])
        
        # --- THE GRID ---
        # Using a container to help centering
        with st.container():
            grid_cols = st.columns(6) 
            for idx, (_, row) in enumerate(df_sorted.iterrows()):
                icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
                with grid_cols[idx % 6]:
                    # The \n creates the stacked look inside our flex-centered button
                    label = f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%"
                    if st.button(label, key=f"btn_{row['Unified_ID']}"):
                        show_tent_details(row['Unified_ID'], df_full)

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
