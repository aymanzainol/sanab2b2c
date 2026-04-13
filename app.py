import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) - كسر اللون الأبيض وإعادة التصميم الكلاسيكي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* تغيير خلفية التطبيق لكسر اللون الأبيض */
    .stApp {
        background-color: #f4f7f9;
        direction: rtl;
        text-align: right;
    }

    /* ضبط القائمة الجانبية لتكون واضحة ومنفصلة */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid #e2e8f0;
    }

    html, body, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
    }

    /* تنسيق أزرار المواقع (الخريطة) */
    .stButton>button { 
        border-radius: 10px; 
        width: 100%; 
        height: 70px; 
        font-weight: bold; 
        background-color: white;
        border: 1px solid #cbd5e1;
        transition: all 0.2s;
        white-space: pre-line;
        color: #1e293b;
    }
    .stButton>button:hover {
        border-color: #3b82f6;
        background-color: #f8fafc;
    }
    
    /* صندوق ملاحظات المراقب المطور */
    .observer-notes-box {
        background-color: #fffbeb;
        padding: 20px;
        border-radius: 12px;
        border-right: 6px solid #d97706;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .date-badge {
        background-color: #fef3c7;
        color: #92400e;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        border: 1px solid #fbbf24;
    }

    .checklist-item-popup { 
        background-color: #fef2f2; 
        padding: 10px; 
        border-radius: 8px; 
        margin-bottom: 6px; 
        border-right: 4px solid #ef4444; 
        font-size: 14px;
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
        df['Unified_ID'] = df['Unified_ID'].fillna("غير معروف").astype(str)
        if 'التاريخ' not in df.columns:
            df['التاريخ'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame(), []

# 4. النافذة المنبثقة (Pop-up)
@st.dialog("تفاصيل الموقع والملاحظات 🏕️")
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
    
    st.markdown("### 📝 ملاحظات المراقب الميداني")
    notes = row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) else "لا توجد ملاحظات حالية."
    st.markdown(f"""
    <div class="observer-notes-box">
        <span class="date-badge">تحديث بتاريخ: {row['التاريخ']}</span><br><br>
        {notes}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### ⚠️ الأنشطة المتبقية ({len(missing_list)})")
    if not missing_list: 
        st.success("✅ العمل مكتمل بنسبة 100%")
    else:
        for item in missing_list: 
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 5. بناء واجهة التطبيق
try:
    df, checklist_cols = load_data()

    # القائمة الجانبية (Sidebar) عادت كما كانت
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1041/1041916.png", width=100)
        st.header("لوحة التحكم")
        page = st.radio("القائمة الرئيسية:", ["📊 الإحصائيات العامة", "🏕️ خريطة المخيمات"])
        st.divider()
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()

    # محتوى الصفحات
    if page == "📊 الإحصائيات العامة":
        st.title("🕋 تحليل جاهزية قطاع المشاعر")
        
        df_sana = df[df['شركة'].str.contains('سنا', na=False)]
        df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

        # --- شركة سنا (بني) مع النسب المئوية ---
        st.subheader("🟤 شركة سنا (الباقة الذهبية)")
        fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', text='Overall_Score',
                         color_discrete_sequence=['#5D4037']) # اللون البني
        fig_sana.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_sana.update_layout(yaxis=dict(range=[0, 120]), margin=dict(t=30))
        st.plotly_chart(fig_sana, use_container_width=True)

        st.divider()

        # --- شركة ركين (أحمر) مع النسب المئوية ---
        st.subheader("🔴 شركة ركين (الباقة المتميزة)")
        fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', text='Overall_Score',
                           color_discrete_sequence=['#B91C1C']) # اللون الأحمر
        fig_rakeen.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_rakeen.update_layout(yaxis=dict(range=[0, 120]), margin=dict(t=30))
        st.plotly_chart(fig_rakeen, use_container_width=True)

    elif page == "🏕️ خريطة المخيمات":
        st.title("🏕️ خريطة توزيع المواقع")
        st.write("انقر على أي موقع لمراجعة التفاصيل والملاحظات اليومية.")
        
        # عرض المربعات (الأزرار)
        df_display = df.sort_values('Unified_ID')
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df_display.iterrows()):
            icon = "🟤" if "سنا" in str(row['شركة']) else "🔴"
            with grid_cols[idx % 6]:
                label = f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%"
                if st.button(label, key=f"camp_btn_{idx}"):
                    show_tent_details(row)

except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
