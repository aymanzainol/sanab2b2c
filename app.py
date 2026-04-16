import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Configuration & Styling
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
    html, body, [data-testid="stHeader"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #ffffff !important;
    }
    .stButton>button { 
        border-radius: 12px; width: 100%; height: 80px; font-weight: bold; 
        background-color: #1f2937; border: 1px solid #374151; transition: all 0.3s; color: white !important;
    }
    .stButton>button:hover { border-color: #3b82f6; background-color: #374151; }
    .observer-notes-box {
        background-color: #1e1e1e; padding: 18px; border-radius: 12px;
        border-right: 6px solid #eab308; margin-bottom: 20px; color: #e5e7eb !important;
        line-height: 1.6;
    }
    .staff-tag {
        display: inline-block; background-color: #374151; color: #9ca3af;
        padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; margin-bottom: 8px;
    }
    .checklist-item-popup { 
        background-color: #450a0a; padding: 12px; border-radius: 8px; 
        margin-bottom: 6px; border-right: 4px solid #ef4444; color: #fecaca !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Advanced Data Analysis Function
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        val = str(row[col]).strip()
        if not val or val.lower() == 'nan' or val == "": continue
        
        current_score = None
        # Logic for "Count" (عدد) columns
        if "عدد" in col:
            try:
                num_val = float(val.replace('%', ''))
                current_score = 100.0 if num_val >= 1 else 0.0
            except: pass
            
        if current_score is None:
            if '%' in val:
                try: current_score = float(val.replace('%', ''))
                except: pass
            elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم', 'يوجد', 'متوفر', 'جاهز', 'صح', '100']): 
                current_score = 100.0
            elif any(n in val for n in ['لا', 'غير', 'لم', 'ناقص', 'خطأ', '0']): 
                current_score = 0.0
        
        if current_score is not None:
            scores.append(current_score)
            if current_score < 100: missing_items.append(f"{col} (القيمة: {val})")
            
    return pd.Series([round(np.mean(scores)) if scores else 0, " | ".join(missing_items)])

SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=20)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    
    # Unified ID Logic
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str).str.strip()
    
    # --- NEW: Extract Assistant & Supervisor based on Company ---
    # Assistant (المعاون) is usually Column B (Index 1)
    df['Assistant_Name'] = df.iloc[:, 1].fillna("غير مسجل")
    # Supervisor (المراقب): Rakeen uses Index 2 (Column C), Sana uses Index 3 (Column D)
    df['Supervisor_Name'] = np.where(
        df['شركة'].str.contains('ركين', na=False), 
        df.iloc[:, 2], 
        df.iloc[:, 3]
    )
    df['Supervisor_Name'] = df['Supervisor_Name'].fillna("غير مسجل")

    # Arabic Timestamp Handling
    if 'طابع زمني' in df.columns:
        df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
        df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)
    
    # Analysis
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest, checklist_cols

# 3. Enhanced Pop-up with History and Staff Details
@st.dialog("سجل جاهزية الموقع والتفاصيل الميدانية 🏕️")
def show_tent_details(tent_id, full_df):
    tent_history = full_df[full_df['Unified_ID'] == tent_id].copy()
    
    if tent_history.empty:
        st.error("بيانات غير متوفرة")
        return

    st.write(f"## موقع: {tent_id}")
    st.write(f"**الشركة:** {tent_history['شركة'].iloc[0]}")
    
    # Date History Selector
    history_options = tent_history['طابع زمني'].tolist()
    selected_time = st.selectbox("📅 اختر تاريخ التقرير لعرض الحالة:", history_options)
    
    # Get details for selected timestamp
    row = tent_history[tent_history['طابع زمني'] == selected_time].iloc[0]
    
    score = int(row['Overall_Score'])
    st.write(f"### نسبة الجاهزية: {score}%")
    st.progress(score / 100.0)

    # --- Display Staff & Notes ---
    st.markdown("### 📝 تفاصيل المراقب والملاحظات")
    notes = row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) and str(row['ملاحظات المراقب']).strip() != "" else "لا توجد ملاحظات نصية."
    
    # Combine Staff into the Notes Box
    st.markdown(f"""
    <div class='observer-notes-box'>
        <div class='staff-tag'>👤 المراقب: {row['Supervisor_Name']}</div><br>
        <div class='staff-tag'>🤝 المعاون: {row['Assistant_Name']}</div>
        <hr style='border: 0; border-top: 1px solid #374151; margin: 10px 0;'>
        <b>الملاحظات:</b><br>{notes}
    </div>
    """, unsafe_allow_html=True)

    # Missing Activities
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('|') if item.strip()]
    st.markdown(f"### ⚠️ الأنشطة المتبقية")
    if not missing_list:
        st.success("🎉 هذا الموقع مكتمل بنسبة 100% في هذا الوقت")
    else:
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 4. Main UI
try:
    df_full, df_latest, checklist_cols = load_data()

    top_m1, top_m2, top_m3 = st.columns([2, 3, 1])
    with top_m1: st.subheader("🚀 لوحة التحكم")
    with top_m2: page = st.radio("العرض:", ["📊 الإحصائيات", "🏕️ الخريطة"], horizontal=True, label_visibility="collapsed")
    with top_m3:
        if st.button("🔄 تحديث"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()

    if page == "📊 الإحصائيات":
        st.title("📊 التحليل البياني العام")
        for company, color in [("سنا", "#b91c1c"), ("ركين", "#8b5e3c")]:
            sub_df = df_latest[df_latest['شركة'].str.contains(company, na=False)]
            st.subheader(f"{'🔴' if company=='سنا' else '🟤'} شركة {company}")
            if not sub_df.empty:
                c1, c2 = st.columns([1, 4])
                avg = round(sub_df['Overall_Score'].mean())
                c1.metric("متوسط الإنجاز", f"{avg}%")
                fig = px.bar(sub_df, x='Unified_ID', y='Overall_Score', color_discrete_sequence=[color], text='Overall_Score')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                c2.plotly_chart(fig, use_container_width=True)

    elif page == "🏕️ الخريطة":
        st.title("🏕️ خريطة المواقع")
        df_sorted = df_latest.sort_values(by=['شركة', 'Unified_ID'])
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
            with grid_cols[idx % 6]:
                if st.button(f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%", key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row['Unified_ID'], df_full)

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
