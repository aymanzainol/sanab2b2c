import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة والتنسيق العربي الاحترافي
st.set_page_config(page_title="Mina Readiness Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stText {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    /* تحسين شكل البطاقات والتحليلات */
    .ai-card {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        border-right: 6px solid #10ac84;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-weight: bold;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. منطق التحليل الذكي (Extracting Missing Details)
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    
    for col in checklist_cols:
        val = str(row[col]).strip()
        
        current_score = None
        # منطق تحديد النسبة المئوية
        if '%' in val:
            try: current_score = float(val.replace('%', ''))
            except: pass
        # منطق الكلمات التأكيدية
        elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم']):
            current_score = 100.0
        # منطق الكلمات السلبية
        elif any(n in val for n in ['لا', 'غير مطابق', 'لم يتم']):
            current_score = 0.0

        if current_score is not None:
            scores.append(current_score)
            if current_score < 100:
                missing_items.append(col)
                
    avg_score = np.mean(scores) if scores else 0
    return pd.Series([round(avg_score), ", ".join(missing_items)])

# 3. جلب البيانات من Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    
    # تحديد نطاق بنود الفحص (من العمود 7 إلى 37)
    checklist_start, checklist_end = 7, 37
    cols_to_check = df.columns[checklist_start:checklist_end]
    
    # تنفيذ التحليل الذكي
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, cols_to_check), axis=1)
    
    # إنشاء المعرف الموحد للموقع (Unified_ID)
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير محدد").astype(str)
    
    # إزالة التكرار مع الإبقاء على آخر تحديث
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), cols_to_check

# الألوان المعتمدة للشركات
COMPANY_COLORS = {'سنا (مشارق الذهبية)': '#e74c3c', 'ركين (مشارق المتميزة)': '#795548'}

# --- الواجهة الرئيسية ---
with st.sidebar:
    st.title("⚙️ الإدارة")
    if st.button("🔄 تحديث البيانات الآن"):
        st.cache_data.clear()
        st.rerun()
    st.write("---")
    st.info("النظام يحلل الآن 30 بنداً مختلفاً لكل موقع لاستخراج النواقص.")

st.title("🕋 لوحة متابعة جاهزية مخيمات منى")

try:
    df, checklist_cols = load_data()
    
    # إنشاء التبويبات
    tab1, tab2, tab3 = st.tabs(["📊 الملخص العام", "🤖 التحليل الذكي للنواقص", "📋 تقرير المواقع"])

    # --- التبويب الأول: الملخص ---
    with tab1:
        avg_total = int(df['Overall_Score'].mean())
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = avg_total,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#10ac84"}},
            title = {'text': "الإنجاز الكلي لجميع المواقع", 'font': {'family': 'Cairo'}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # --- التبويب الثاني: التحليل الذكي (طلبك الأساسي) ---
    with tab2:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("💡 تفاصيل النواقص حسب المتطلبات")
        st.write("الجدول أدناه يوضح كل 'بند ناقص' وما هي أرقام المواقع التي تحتاج العمل عليه:")
        
        # تحليل عكسي: ربط كل نقص بالمواقع المرتبطة به
        missing_analysis = []
        for col in checklist_cols:
            # البحث عن المواقع التي لديها مشكلة في هذا البند
            sites_needing_this = df[df[col].astype(str).str.contains('لا|غير مطابق|لم يتم|0%', na=False)]['Unified_ID'].tolist()
            if sites_needing_this:
                missing_analysis.append({
                    "البند الناقص": col,
                    "عدد المواقع المتعثرة": len(sites_needing_this),
                    "أرقام المواقع": " ، ".join(sites_needing_this)
                })
        
        if missing_analysis:
            summary_df = pd.DataFrame(missing_analysis).sort_values(by="عدد المواقع المتعثرة", ascending=False)
            st.table(summary_df) # عرض كجدول ثابت وواضح
        else:
            st.success("✅ مذهل! لا توجد نواقص فنية مسجلة حالياً.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("🔍 استعلام سريع عن موقع محدد")
        selected_site = st.selectbox("اختر رقم الموقع لرؤية قائمة مهامه:", df['Unified_ID'].unique())
        site_info = df[df['Unified_ID'] == selected_site].iloc[0]
        
        c1, c2 = st.columns([1, 2])
        c1.metric("نسبة الجاهزية", f"{site_info['Overall_Score']}%")
        if site_info['Missing_Details']:
            c2.error(f"📋 النواقص المطلوب معالجتها: \n\n {site_info['Missing_Details']}")
        else:
            c2.success("🎉 هذا الموقع مكتمل الجاهزية بنسبة 100%")

    # --- التبويب الثالث: التقارير ---
    with tab3:
        st.subheader("📋 حالة المواقع والملاحظات الميدانية")
        display_df = df[['Unified_ID', 'شركة', 'Overall_Score', 'Missing_Details', 'ملاحظات المراقب']].copy()
        st.data_editor(
            display_df.rename(columns={
                'Unified_ID': 'الموقع', 
                'Overall_Score': 'نسبة الإنجاز', 
                'Missing_Details': 'النواقص الفنية',
                'ملاحظات المراقب': 'ملاحظات الميدان'
            }),
            column_config={
                "نسبة الإنجاز": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100),
                "النواقص الفنية": st.column_config.TextColumn(width="large")
            },
            hide_index=True, use_container_width=True
        )

    # المخطط البياني في الأسفل
    st.divider()
    st.subheader("📊 مقارنة الأداء بين المواقع")
    fig_bar = px.bar(
        df.sort_values('Overall_Score', ascending=False),
        x='Unified_ID', y='Overall_Score', color='شركة', text='Overall_Score',
        color_discrete_map=COMPANY_COLORS
    )
    fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
    fig_bar.update_layout(font_family="Cairo", yaxis={'range': [0, 120]}, xaxis={'title': 'رقم الموقع'})
    st.plotly_chart(fig_bar, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ حدث خطأ فني: {e}")