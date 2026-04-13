import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر b2b2c 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) - تركيز على وضوح النواقص
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    .main .block-container { direction: rtl; text-align: right; }
    html, body, [data-testid="stSidebar"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* أزرار المخيمات */
    .stButton>button { 
        border-radius: 12px; 
        width: 100%; 
        height: 55px; 
        font-weight: bold; 
        border: 2px solid #f0f2f6;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button:hover { border-color: #10ac84; background-color: #f9fafb; }

    /* حاوية النواقص داخل الـ Pop-up */
    .missing-header {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 15px;
        border: 1px solid #fecaca;
    }
    
    .incomplete-item {
        background-color: #ffffff;
        padding: 12px 15px;
        border-radius: 10px;
        margin-bottom: 8px;
        border-right: 6px solid #ef4444;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        font-size: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
        color: #374151;
    }

    .stat-badge {
        background: #f3f4f6;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. جلب وتحليل البيانات
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
            if current_score < 100: missing_items.append(col) # تخزين اسم العمود كبند ناقص
            
    avg_score = np.mean(scores) if scores else 0
    return pd.Series([round(avg_score), " | ".join(missing_items)])

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

# 4. النافذة المنبثقة (Pop-up Dialog)
@st.dialog("📋 مراجعة بنود العمل")
def show_missing_items(row):
    score = int(row['Overall_Score'])
    # تحويل النص إلى قائمة
    raw_missing = str(row['Missing_Details']).split('|')
    missing_list = [item.strip() for item in raw_missing if item.strip()]
    
    st.markdown(f"### 📍 موقع: {row['Unified_ID']}")
    st.markdown(f"<span class='stat-badge'>🏢 الشركة: {row['شركة']}</span> <span class='stat-badge'>📊 الجاهزية: {score}%</span>", unsafe_allow_html=True)
    
    st.progress(score / 100.0)
    st.divider()

    if not missing_list:
        st.balloons()
        st.success("✨ مبروك! هذا الموقع مكتمل تماماً ولا توجد به أي نواقص.")
    else:
        st.markdown("<div class='missing-header'>⚠️ البنود غير المكتملة (تحتاج تدخل)</div>", unsafe_allow_html=True)
        
        # عرض كل بند ناقص في بطاقة مستقلة سهلة القراءة
        for item in missing_list:
            st.markdown(f"""
                <div class='incomplete-item'>
                    <span style='color: #ef4444; font-size: 20px;'>❌</span>
                    <span>{item}</span>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    if st.button("إغلاق النافذة"):
        st.rerun()

# 5. بناء الصفحة الرئيسية
try:
    df, checklist_cols = load_data()

    with st.sidebar:
        st.title("⚙️ لوحة التحكم")
        page = st.radio("القائمة:", ["📊 الإحصائيات", "🏕️ خريطة النواقص"])
        if st.button("🔄 تحديث البيانات الآن"):
            st.cache_data.clear()
            st.rerun()

    if page == "📊 الإحصائيات":
        st.title("🕋 قطاع المشاعر - نظرة عامة")
        avg_total = int(df['Overall_Score'].mean())
        st.metric("المعدل العام للإنجاز", f"{avg_total}%", delta=f"{avg_total-70}% من المستهدف")
        
        fig = px.bar(df, x='Unified_ID', y='Overall_Score', color='Overall_Score', 
                     text='Overall_Score', color_continuous_scale='Greens')
        fig.update_xaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    elif page == "🏕️ خريطة النواقص":
        st.title("🏕️ نظام تتبع المخيمات")
        st.write("اضغط على اسم المخيم لفتح قائمة **النواقص** فوراً.")
        
        st.markdown("🟡 سنا (الذهبية) | 🔵 ركين (المتميزة)")
        st.divider()

        # عرض المخيمات كأزرار في شبكة (Grid)
        grid_cols = st.columns(4)
        for idx, row in df.iterrows():
            icon = "🟡" if "سنا" in str(row['شركة']) else "🔵"
            with grid_cols[idx % 4]:
                # عند الضغط على الزر، يفتح الـ Dialog
                if st.button(f"{icon} {row['Unified_ID']}", key=f"tent_{idx}"):
                    show_missing_items(row)

except Exception as e:
    st.error(f"حدث خطأ في عرض البيانات: {e}")
