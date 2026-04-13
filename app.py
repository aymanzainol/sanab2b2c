import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) - تحسين وضوح المنيو العلوي والألوان
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* ضبط الاتجاه العام */
    [data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
    }

    html, body, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
    }

    /* --- تحسين المنيو العلوي (Tabs) ليكون بارزاً جداً --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        justify-content: center;
        background-color: #f1f5f9;
        padding: 10px;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        background-color: #ffffff;
        border-radius: 10px;
        padding: 0px 50px;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }

    /* شكل التبويب عند الاختيار */
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important; /* لون كحلي غامق */
        color: white !important;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* تغيير لون النص داخل التبويب غير النشط */
    .stTabs [data-baseweb="tab"] p {
        font-size: 18px;
    }

    /* تنسيق أزرار المواقع */
    .stButton>button { 
        border-radius: 12px; 
        width: 100%; 
        height: 75px; 
        font-weight: bold; 
        border: 2px solid #f1f5f9;
        background-color: white;
        transition: all 0.3s ease;
        white-space: pre-line;
    }
    .stButton>button:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
    }
    
    /* صناديق المعلومات */
    .observer-notes-box {
        background-color: #fefce8;
        padding: 20px;
        border-radius: 12px;
        border-right: 6px solid #eab308;
    }
    
    .checklist-item-popup { 
        background-color: #fef2f2; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 6px; 
        border-right: 4px solid #ef4444; 
        color: #991b1b;
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
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [col.strip() for col in df.columns]
        checklist_cols = df.columns[7:37]
        df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
        df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
        df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str)
        if 'التاريخ' not in df.columns:
            df['التاريخ'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols
    except:
        return pd.DataFrame(), []

# 4. النافذة المنبثقة
@st.dialog("تقرير حالة الموقع الميداني 🏕️")
def show_tent_details(row):
    score = int(row['Overall_Score'])
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('،') if item.strip()]
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"## موقع: {row['Unified_ID']}")
        st.write(f"**الشركة:** {row['شركة']}")
    with c2:
        st.markdown(f"<div style='text-align:center;'>الجاهزية<br><h1 style='color:#059669;'>{score}%</h1></div>", unsafe_allow_html=True)

    st.progress(score / 100.0)
    st.markdown("### 📝 ملاحظات المراقب")
    notes = row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) else "لا توجد ملاحظات."
    st.markdown(f"<div class='observer-notes-box'><b>تاريخ التقرير: {row['التاريخ']}</b><br><br>{notes}</div>", unsafe_allow_html=True)

    st.markdown(f"### ⚠️ متبقي الأنشطة ({len(missing_list)})")
    if not missing_list: st.success("🎉 مكتمل بالكامل")
    else:
        for item in missing_list: st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 5. بناء الواجهة
try:
    df, checklist_cols = load_data()

    # السطر العلوي
    head_col1, head_col2 = st.columns([5, 1.2])
    with head_col1:
        st.title("🕋 لوحة جاهزية قطاع المشاعر 2026")
    with head_col2:
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()

    # القائمة العلوية المحدثة
    tab_stats, tab_map = st.tabs(["📊 الإحصائيات والتحليل", "🏕️ خريطة المواقع الميدانية"])

    with tab_stats:
        df_sana = df[df['شركة'].str.contains('سنا', na=False)]
        df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

        # --- سنا (أحمر) ---
        st.subheader("🔴 شركة سنا (الباقة الذهبية)")
        fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', text='Overall_Score',
                         color_discrete_sequence=['#B91C1C']) # أحمر
        fig_sana.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_sana.update_layout(yaxis=dict(range=[0, 125]), margin=dict(t=30))
        st.plotly_chart(fig_sana, use_container_width=True)

        st.divider()

        # --- ركين (بني) ---
        st.subheader("🟤 شركة ركين (الباقة المتميزة)")
        fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', text='Overall_Score',
                           color_discrete_sequence=['#5D4037']) # بني
        fig_rakeen.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_rakeen.update_layout(yaxis=dict(range=[0, 125]), margin=dict(t=30))
        st.plotly_chart(fig_rakeen, use_container_width=True)

    with tab_map:
        st.write("### توزيع المواقع")
        st.markdown("🔴 سنا | 🟤 ركين")
        
        df_display = df.sort_values('Unified_ID')
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df_display.iterrows()):
            icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
            with grid_cols[idx % 6]:
                if st.button(f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%", key=f"btn_nav_{idx}"):
                    show_tent_details(row)

except Exception as e:
    st.error(f"حدث خطأ: {e}")
