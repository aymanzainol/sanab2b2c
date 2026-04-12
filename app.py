import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة والتنسيق المتجاوب
st.set_page_config(page_title="Mina Readiness Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stText, .stMarkdown {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .ai-card {
        background: #ffffff;
        border-right: 6px solid #10ac84;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-size: 18px !important;
        background-color: #10ac84;
        color: white;
    }
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        gap: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. منطق التحليل الذكي
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

# 3. تحميل البيانات
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

SANA_NAME = 'سنا (مشارق الذهبية)'
RAKEEN_NAME = 'ركين (مشارق المتميزة)'
COMPANY_COLORS = {SANA_NAME: '#e74c3c', RAKEEN_NAME: '#795548'}

# --- الواجهة الرئيسية ---
try:
    df, checklist_cols = load_data()

    st.title("🕋 لوحة جاهزية مخيمات منى")
    
    tab1, tab2, tab3 = st.tabs(["📊 الملخص", "🤖 التحليل الذكي", "📋 التقارير"])

    with tab1:
        avg_total = int(df['Overall_Score'].mean())
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = avg_total,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#10ac84"}},
            title = {'text': "الإنجاز الكلي", 'font': {'family': 'Cairo'}}
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20), dragmode=False)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("💡 نواقص بنود العمل")
        missing_summary = []
        for col in checklist_cols:
            bad_sites = df[df[col].astype(str).str.contains('لا|غير مطابق|لم يتم|0%', na=False)]['Unified_ID'].tolist()
            if bad_sites:
                missing_summary.append({"البند": col, "المواقع": " ، ".join(bad_sites)})
        
        if missing_summary:
            for item in missing_summary:
                with st.expander(f"❌ {item['البند']}"):
                    st.write(f"المواقع الناقصة: **{item['المواقع']}**")
        else:
            st.success("جميع البنود مكتملة!")
        st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("🔍 استعلام سريع")
        selected_id = st.selectbox("اختر رقم الموقع:", df['Unified_ID'].unique())
        site_row = df[df['Unified_ID'] == selected_id].iloc[0]
        st.metric("الجاهزية", f"{site_row['Overall_Score']}%")
        if site_row['Missing_Details']:
            st.warning(f"النواقص: {site_row['Missing_Details']}")

    with tab3:
        st.subheader("📋 تفاصيل المواقع")
        st.data_editor(
            df[['Unified_ID', 'Overall_Score', 'Missing_Details']].rename(
                columns={'Unified_ID': 'الموقع', 'Overall_Score': 'إنجاز %', 'Missing_Details': 'النواقص'}
            ),
            column_config={"إنجاز %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%")},
            hide_index=True, use_container_width=True
        )

    # --- المخطط البياني المحسن والمقفل ---
    st.divider()
    st.subheader("📊 مقارنة الجاهزية لكل موقع")
    
    filter_option = st.radio("عرض المواقع حسب الشركة:", ["الكل", "سنا", "ركين"], horizontal=True)

    if filter_option == "سنا":
        chart_df = df[df['شركة'] == SANA_NAME]
    elif filter_option == "ركين":
        chart_df = df[df['شركة'] == RAKEEN_NAME]
    else:
        chart_df = df

    fig_bar = px.bar(
        chart_df.sort_values('Overall_Score', ascending=False), 
        x='Unified_ID', 
        y='Overall_Score', 
        color='شركة', 
        text='Overall_Score',
        color_discrete_map=COMPANY_COLORS
    )
    
    fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
    
    # تحسينات المحاور لمنع التداخل وقفل الزووم
    fig_bar.update_xaxes(
        fixedrange=True, 
        tickangle=-45, 
        automargin=True,
        title={'text': 'رقم الموقع', 'standoff': 60} # 🟢 دفع العنوان للأسفل بعيداً عن الكلمات المائلة
    )
    
    fig_bar.update_yaxes(
        fixedrange=True,
        title='نسبة الجاهزية %', 
        range=[0, 120]
    )
    
    fig_bar.update_layout(
        font_family="Cairo",
        height=600, # زيادة الطول الكلي لاستيعاب النصوص بالأسفل
        dragmode=False,
        margin=dict(l=20, r=20, t=30, b=180), # 🟢 هامش سفلي كبير جداً لمنع التداخل
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"خطأ: {e}")

if st.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
