import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر b2b2c 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    .main .block-container { direction: rtl; text-align: right; }
    html, body, [data-testid="stSidebar"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* تنسيق أزرار المخيمات */
    .stButton>button { border-radius: 8px; width: 100%; height: 50px; font-weight: bold; border: 1px solid #e0e0e0; }
    
    /* بطاقات الإحصائيات داخل النافذة المنبثقة */
    .stat-box-popup {
        background: #f8fafc;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
    }
    .val-green { color: #10b981; font-size: 24px; font-weight: bold; }
    .val-red { color: #ef4444; font-size: 24px; font-weight: bold; }
    
    /* تنسيق النواقص */
    .checklist-item-popup { 
        background-color: #fff5f5; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 8px; 
        border-right: 4px solid #ef4444; 
        font-size: 14px;
        color: #991b1b;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. دوال تحليل وجلب البيانات
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
    df['Unified_ID'] = df['Unified_ID'].fillna("موقع غير معروف").astype(str)
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols

# 4. وظيفة النافذة المنبثقة (Pop-up Dialog)
@st.dialog("تفاصيل بنود العمل 🏕️")
def show_tent_details(row):
    score = int(row['Overall_Score'])
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('،') if item.strip()]
    
    st.write(f"### موقع: {row['Unified_ID']}")
    st.caption(f"الشركة: {row['شركة']}")
    st.progress(score / 100.0)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='stat-box-popup'>نسبة الإنجاز<br><span class='val-green'>{score}%</span></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='stat-box-popup'>النواقص<br><span class='val-red'>{len(missing_list)}</span></div>", unsafe_allow_html=True)
    
    st.divider()
    if not missing_list:
        st.success("🌟 العمل مكتمل بنسبة 100%!")
    else:
        st.write("**البنود غير المكتملة:**")
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 5. بناء واجهة المستخدم
try:
    df, checklist_cols = load_data()

    # نظام التنقل في القائمة الجانبية
    with st.sidebar:
        st.header("⚙️ التحكم")
        page = st.radio("انتقل إلى:", ["📊 لوحة التحكم", "🤖 المساعد الذكي"])
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()

    if page == "📊 لوحة التحكم":
        st.title("🕋 قطاع المشاعر b2b2c")
        
        tab1, tab2 = st.tabs(["📊 الإحصائيات", "🏕️ خريطة المخيمات (Pop-up)"])
        
        with tab1:
            avg_total = int(df['Overall_Score'].mean())
            st.metric("متوسط الجاهزية العام", f"{avg_total}%")
            fig = px.bar(df, x='Unified_ID', y='Overall_Score', color='Overall_Score', color_continuous_scale='RdYlGn')
            fig.update_xaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("انقر على أي مخيم لمشاهدة التفاصيل في نافذة منبثقة")
            st.markdown("🟡 سنا (الذهبية) | 🔵 ركين (المتميزة)")
            
            # عرض المخيمات كأزرار
            grid_cols = st.columns(5)
            for idx, row in df.iterrows():
                company_icon = "🟡" if "سنا" in str(row['شركة']) else "🔵"
                with grid_cols[idx % 5]:
                    if st.button(f"{company_icon} {row['Unified_ID']}", key=f"tent_{idx}"):
                        show_tent_details(row) # استدعاء النافذة المنبثقة

    elif page == "🤖 المساعد الذكي":
        st.title("🤖 المساعد الذكي")
        st.chat_message("assistant").write("أهلاً بك! يمكنك سؤالي عن أي موقع مباشرة.")
        if prompt := st.chat_input("اكتب رقم الموقع..."):
            st.chat_message("user").write(prompt)
            # هنا يمكنك إضافة منطق البحث البسيط كما في النسخ السابقة

except Exception as e:
    st.error(f"حدث خطأ: {e}")
