import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) - تم إصلاح مشاكل الـ Sidebar وتحسين استجابة العرض
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* إصلاح الاتجاه العام وتجاوب القائمة الجانبية */
    [data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
    }

    /* إصلاح محتوى السايدبار عند التصغير */
    [data-testid="stSidebarContent"] {
        direction: rtl !important;
        text-align: right !important;
    }

    html, body, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
    }

    /* تنسيق أزرار المواقع */
    .stButton>button { 
        border-radius: 12px; 
        width: 100%; 
        height: 65px; 
        font-weight: bold; 
        border: 1px solid #d1d5db;
        transition: all 0.2s;
        white-space: pre-line; /* للسماح بنزول السطر داخل الزر */
    }
    
    /* صندوق ملاحظات المراقب */
    .observer-notes-box {
        background-color: #fefce8;
        padding: 18px;
        border-radius: 12px;
        border-right: 6px solid #eab308;
        margin-bottom: 20px;
    }
    
    .date-badge {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
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
        df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str)
        if 'التاريخ' not in df.columns:
            df['التاريخ'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols
    except Exception as e:
        st.error(f"خطأ في الاتصال بالبيانات: {e}")
        return pd.DataFrame(), []

# 4. النافذة المنبثقة التفصيلية
@st.dialog("تقرير حالة الموقع 🏕️")
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
    st.markdown(f"<div class='observer-notes-box'><span class='date-badge'>{row['التاريخ']}</span><br><br>{notes}</div>", unsafe_allow_html=True)

    st.markdown(f"### ⚠️ متبقي الأنشطة ({len(missing_list)})")
    if not missing_list: st.success("🎉 مكتمل بالكامل")
    else:
        for item in missing_list: st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 5. واجهة التطبيق
try:
    df, checklist_cols = load_data()

    with st.sidebar:
        st.header("⚙️ القائمة")
        page = st.radio("انتقل إلى:", ["📊 الإحصائيات", "🏕️ خريطة المواقع"])
        if st.button("🔄 تحديث"):
            st.cache_data.clear()
            st.rerun()

    if page == "📊 الإحصائيات":
        st.title("📊 تحليل الجاهزية")
        
        df_sana = df[df['شركة'].str.contains('سنا', na=False)]
        df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

        # --- سنا (بني) ---
        st.subheader("🟤 شركة سنا")
        fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', text='Overall_Score',
                         color_discrete_sequence=['#5D4037'])
        fig_sana.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_sana.update_layout(yaxis=dict(range=[0, 115])) # مساحة إضافية للنسبة
        st.plotly_chart(fig_sana, use_container_width=True)

        # --- ركين (أحمر) ---
        st.subheader("🔴 شركة ركين")
        fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', text='Overall_Score',
                           color_discrete_sequence=['#B91C1C'])
        fig_rakeen.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_rakeen.update_layout(yaxis=dict(range=[0, 115]))
        st.plotly_chart(fig_rakeen, use_container_width=True)

    elif page == "🏕️ خريطة المواقع":
        st.title("🏕️ مواقع المشاعر")
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df.sort_values('Unified_ID').iterrows()):
            icon = "🟤" if "سنا" in str(row['شركة']) else "🔴"
            with grid_cols[idx % 6]:
                if st.button(f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%", key=f"btn_{idx}"):
                    show_tent_details(row)

except Exception as e:
    st.error(f"حدث خطأ: {e}")
