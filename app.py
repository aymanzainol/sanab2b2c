import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) - الوضع الداكن وإلغاء الأبيض
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* تغيير خلفية التطبيق بالكامل وتغيير لون النص */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }

    /* ضبط الاتجاه للعربية */
    .main .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
    
    html, body, [data-testid="stHeader"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #ffffff !important;
    }

    /* تنسيق أزرار المواقع في الخريطة */
    .stButton>button { 
        border-radius: 12px; 
        width: 100%; 
        height: 80px; 
        font-weight: bold; 
        background-color: #1f2937;
        border: 1px solid #374151;
        transition: all 0.3s;
        color: white !important;
    }
    .stButton>button:hover {
        border-color: #3b82f6;
        background-color: #374151;
    }
    
    /* صندوق ملاحظات المراقب */
    .observer-notes-box {
        background-color: #1e1e1e;
        padding: 18px;
        border-radius: 12px;
        border-right: 6px solid #eab308;
        margin-bottom: 20px;
        color: #e5e7eb !important;
    }
    
    .date-badge {
        background-color: #451a03;
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
    }

    /* إخفاء شريط التنقل الجانبي تماماً */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* تنسيق الأنشطة المتبقية */
    .checklist-item-popup { 
        background-color: #450a0a; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 6px; 
        border-right: 4px solid #ef4444; 
        color: #fecaca !important;
    }
    
    /* تعديل ألوان الـ Metrics */
    [data-testid="stMetricValue"] {
        color: #3b82f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. دوال تحليل البيانات
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        val = str(row[col]).strip()
        current_score = None
        if '%' in val:
            try: current_score = float(val.replace('%', ''))
            except: pass
        elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم']): current_score = 100.0
        elif any(n in val for n in ['لا', 'غير مطابق', 'لم يتم']): current_score = 0.0
        
        if current_score is not None:
            scores.append(current_score)
            if current_score < 100: missing_items.append(col)
            
    avg_score = np.mean(scores) if scores else 0
    return pd.Series([round(avg_score), "، ".join(missing_items)])

SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str)
    if 'التاريخ' not in df.columns:
        df['التاريخ'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols

# 4. النافذة المنبثقة
@st.dialog("تقرير حالة الموقع التفصيلي 🏕️")
def show_tent_details(row):
    score = int(row['Overall_Score'])
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('،') if item.strip()]
    
    st.write(f"## موقع: {row['Unified_ID']}")
    st.write(f"**الشركة:** {row['شركة']}")
    st.write(f"### جاهزية الموقع: {score}%")
    st.progress(score / 100.0)

    st.markdown("### 📝 ملاحظات المراقب")
    notes = row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) and str(row['ملاحظات المراقب']).strip() != "" else "لا توجد ملاحظات مسجلة."
    st.markdown(f"<div class='observer-notes-box'><span class='date-badge'>{row['التاريخ']}</span><br><br>{notes}</div>", unsafe_allow_html=True)

    st.markdown(f"### ⚠️ الأنشطة المتبقية ({len(missing_list)})")
    if not missing_list:
        st.success("🎉 مكتمل")
    else:
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 5. واجهة التطبيق الرئيسية
try:
    df, checklist_cols = load_data()

    # --- القائمة العلوية البديلة للسيدبار ---
    top_menu_1, top_menu_2, top_menu_3 = st.columns([2, 3, 1])
    
    with top_menu_1:
        st.subheader("🚀 لوحة التحكم")
    
    with top_menu_2:
        # أزرار التنقل في المنتصف
        page = st.radio("اختر العرض:", ["📊 الإحصائيات", "🏕️ الخريطة"], horizontal=True, label_visibility="collapsed")
    
    with top_menu_3:
        if st.button("🔄 تحديث"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()

    # صفحة الإحصائيات
    if page == "📊 الإحصائيات":
        st.title("📊 التحليل البياني للقطاع")
        
        df_sana = df[df['شركة'].str.contains('سنا', na=False)]
        df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

        # عرض سنا
        st.subheader("🔴 شركة سنا")
        c1, c2 = st.columns([1, 4])
        c1.metric("متوسط الإنجاز", f"{round(df_sana['Overall_Score'].mean())}%")
        fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', color_discrete_sequence=['#b91c1c'], text='Overall_Score')
        fig_sana.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_sana.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        c2.plotly_chart(fig_sana, use_container_width=True)

        # عرض ركين
        st.subheader("🟤 شركة ركين")
        r1, r2 = st.columns([1, 4])
        r1.metric("متوسط الإنجاز", f"{round(df_rakeen['Overall_Score'].mean())}%")
        fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', color_discrete_sequence=['#8b5e3c'], text='Overall_Score')
        fig_rakeen.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_rakeen.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        r2.plotly_chart(fig_rakeen, use_container_width=True)

    # صفحة خريطة المواقع
    elif page == "🏕️ الخريطة":
        st.title("🏕️ توزيع المواقع الميدانية")
        df_sorted = df.sort_values(by=['شركة', 'Unified_ID'])
        
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
            with grid_cols[idx % 6]:
                label = f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%"
                if st.button(label, key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row)

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
