import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. إعدادات الصفحة والتنسيق
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
    }
    .date-badge { background-color: #451a03; color: #fbbf24; padding: 4px 10px; border-radius: 6px; font-size: 13px; }
    [data-testid="stSidebar"] { display: none; }
    .checklist-item-popup { 
        background-color: #450a0a; padding: 12px; border-radius: 8px; 
        margin-bottom: 6px; border-right: 4px solid #ef4444; color: #fecaca !important;
    }
    /* تنسيق صندوق الاختيار (Dropdown) ليناسب الوضع الداكن */
    div[data-baseweb="select"] > div {
        background-color: #1f2937 !important;
        color: white !important;
        border-color: #374151 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. دوال تحليل البيانات
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
    
    # تحديد الهوية الموحدة
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str).str.strip()
    
    # تحويل الوقت والترتيب
    if 'طابع زمني' in df.columns:
        df['طابع زمني'] = pd.to_datetime(df['طابع زمني'], dayfirst=True, errors='coerce')
        df = df.sort_values(by='طابع زمني', ascending=False) # الأحدث أولاً
    
    # حساب النتائج لكل السجلات (بما فيها القديمة)
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    
    # نسخة لأحدث البيانات فقط للعرض الرئيسي
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    
    return df, df_latest, checklist_cols

# 3. النافذة المنبثقة مع سجل التاريخ
@st.dialog("سجل جاهزية الموقع 🏕️")
def show_tent_details(tent_id, full_df):
    # تصفية البيانات لهذا الموقع فقط
    tent_history = full_df[full_df['Unified_ID'] == tent_id].copy()
    
    st.write(f"## موقع: {tent_id}")
    st.write(f"**الشركة:** {tent_history['شركة'].iloc[0]}")
    
    # --- قائمة اختيار التاريخ ---
    st.markdown("### 🕒 تاريخ التقييم")
    dates = tent_history['طابع زمني'].dt.strftime('%Y-%m-%d %H:%M').tolist()
    selected_date_str = st.selectbox("اختر تاريخاً لعرض حالة التقدم في ذلك الوقت:", dates)
    
    # جلب السجل المختار
    selected_row = tent_history[tent_history['طابع زمني'].dt.strftime('%Y-%m-%d %H:%M') == selected_date_str].iloc[0]
    
    # --- عرض البيانات بناءً على التاريخ المختار ---
    score = int(selected_row['Overall_Score'])
    st.write(f"### نسبة الجاهزية بتاريخ {selected_date_str}: {score}%")
    st.progress(score / 100.0)

    st.markdown("### 📝 ملاحظات المراقب")
    notes = selected_row['ملاحظات المراقب'] if pd.notna(selected_row['ملاحظات المراقب']) and str(selected_row['ملاحظات المراقب']).strip() != "" else "لا توجد ملاحظات."
    st.markdown(f"<div class='observer-notes-box'>{notes}</div>", unsafe_allow_html=True)

    missing_list = [item.strip() for item in str(selected_row['Missing_Details']).split('|') if item.strip()]
    st.markdown(f"### ⚠️ الأنشطة المتبقية ({len(missing_list)})")
    if not missing_list:
        st.success("🎉 الموقع كان مكتملاً في هذا التاريخ")
    else:
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 4. واجهة التطبيق الرئيسية
try:
    df_full, df_latest, checklist_cols = load_data()

    top_menu_1, top_menu_2, top_menu_3 = st.columns([2, 3, 1])
    with top_menu_1: st.subheader("🚀 لوحة التحكم")
    with top_menu_2: page = st.radio("العرض:", ["📊 الإحصائيات", "🏕️ الخريطة"], horizontal=True, label_visibility="collapsed")
    with top_menu_3:
        if st.button("🔄 تحديث"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()

    if page == "📊 الإحصائيات":
        st.title("📊 التحليل البياني (آخر تحديث)")
        for company, color in [("سنا", "#b91c1c"), ("ركين", "#8b5e3c")]:
            sub_df = df_latest[df_latest['شركة'].str.contains(company, na=False)]
            st.subheader(f"{'🔴' if company=='سنا' else '🟤'} شركة {company}")
            c1, c2 = st.columns([1, 4])
            avg = round(sub_df['Overall_Score'].mean()) if not sub_df.empty else 0
            c1.metric("متوسط الإنجاز الحالي", f"{avg}%")
            if not sub_df.empty:
                fig = px.bar(sub_df, x='Unified_ID', y='Overall_Score', color_discrete_sequence=[color], text='Overall_Score')
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", yaxis=dict(range=[0, 110]))
                c2.plotly_chart(fig, use_container_width=True)

    elif page == "🏕️ الخريطة":
        st.title("🏕️ توزيع المواقع الميدانية")
        df_sorted = df_latest.sort_values(by=['شركة', 'Unified_ID'])
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
            with grid_cols[idx % 6]:
                label = f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%"
                if st.button(label, key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row['Unified_ID'], df_full)

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
