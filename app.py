import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة - وضع "wide" مع تحسينات للموبايل
st.set_page_config(page_title="Mina Readiness Dashboard", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS مخصص لضمان تجاوب الواجهة مع الجوال (Mobile Optimized CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"], .stText, .stMarkdown {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }

    /* تحسين شكل البطاقات للجوال */
    .ai-card {
        background: #ffffff;
        border-right: 5px solid #10ac84;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* تكبير الأزرار لتسهيل اللمس على الجوال */
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-size: 18px !important;
        margin-top: 10px;
    }

    /* تحسين عرض التبويبات Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 15px;
        background-color: #f8f9fa;
        border-radius: 8px 8px 0 0;
    }

    /* إخفاء المسافات الزائدة في الجوال */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. وظيفة المعالجة الذكية لاستخراج النواقص
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        val = str(row[col]).strip()
        current_score = None
        if '%' in val:
            try: current_score = float(val.replace('%', ''))
            except: pass
        elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم']):
            current_score = 100.0
        elif any(n in val for n in ['لا', 'غير مطابق', 'لم يتم']):
            current_score = 0.0

        if current_score is not None:
            scores.append(current_score)
            if current_score < 100:
                missing_items.append(col)
                
    avg_score = np.mean(scores) if scores else 0
    return pd.Series([round(avg_score), ", ".join(missing_items)])

# 4. جلب البيانات
SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير محدد").astype(str)
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols

COMPANY_COLORS = {'سنا (مشارق الذهبية)': '#e74c3c', 'ركين (مشارق المتميزة)': '#795548'}

# --- البداية ---
try:
    df, checklist_cols = load_data()

    # العنوان الرئيسي بشكل مبسط للجوال
    st.title("🕋 جاهزية مخيمات منى")
    
    # تبويبات علوية سهلة التصفح
    tab1, tab2, tab3 = st.tabs(["📊 عام", "🤖 النواقص", "📋 المواقع"])

    with tab1:
        # المؤشر العام بحجم متجاوب
        avg_total = int(df['Overall_Score'].mean())
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = avg_total,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#10ac84"}},
            title = {'text': "الإنجاز العام", 'font': {'family': 'Cairo', 'size': 20}}
        ))
        fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with tab2:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("💡 أين نحتاج للتدخل؟")
        
        # تحليل النواقص وربطها بالمواقع
        missing_list = []
        for col in checklist_cols:
            sites = df[df[col].astype(str).str.contains('لا|غير مطابق|لم يتم|0%', na=False)]['Unified_ID'].tolist()
            if sites:
                missing_list.append({"البند": col, "المواقع": " ، ".join(sites)})
        
        if missing_list:
            for item in missing_list[:8]: # عرض أهم 8 نواقص لتجنب الإطالة في الجوال
                with st.expander(f"🔴 {item['البند']}"):
                    st.write(f"المواقع المتأثرة: **{item['المواقع']}**")
        else:
            st.success("جميع المتطلبات مكتملة!")
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("🔍 ابحث عن موقع")
        site_id = st.selectbox("رقم الموقع:", df['Unified_ID'].unique())
        s_data = df[df['Unified_ID'] == site_id].iloc[0]
        
        st.metric("نسبة الجاهزية", f"{s_data['Overall_Score']}%")
        if s_data['Missing_Details']:
            st.error(f"⚠️ النواقص: {s_data['Missing_Details']}")
        else:
            st.success("✅ الموقع جاهز")

    with tab3:
        # جدول مبسط وسهل التمرير عرضياً للجوال
        st.subheader("📋 قائمة المواقع")
        mini_df = df[['Unified_ID', 'Overall_Score', 'Missing_Details']].rename(
            columns={'Unified_ID': 'الموقع', 'Overall_Score': '%', 'Missing_Details': 'النواقص'}
        )
        st.dataframe(mini_df, use_container_width=True, hide_index=True)

    # مخطط الأعمدة في الأسفل
    st.divider()
    fig_bar = px.bar(
        df.sort_values('Overall_Score'), x='Overall_Score', y='Unified_ID', 
        color='شركة', orientation='h', # تحويله لأفقي لسهولة القراءة في الجوال
        color_discrete_map=COMPANY_COLORS
    )
    fig_bar.update_layout(height=max(400, len(df)*30), font_family="Cairo", margin=dict(l=10, r=10))
    st.plotly_chart(fig_bar, use_container_width=True)

except Exception as e:
    st.error(f"خطأ: {e}")

# زر التحديث في الأسفل لسهولة الوصول بالإبهام
if st.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
