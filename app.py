import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة والهوية البصرية (تم تحديث عنوان المتصفح)
st.set_page_config(page_title="لوحة قطاع المشاعر b2b2c 🚀", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stText, .stMarkdown {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    /* بطاقات الحالة الذكية */
    .status-card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .ok-bg { background-color: #d4edda; border-right: 10px solid #28a745; color: #155724; }
    .warning-bg { background-color: #fff3cd; border-right: 10px solid #ffc107; color: #856404; }
    .danger-bg { background-color: #f8d7da; border-right: 10px solid #dc3545; color: #721c24; }
    
    /* تنسيق المحادثة */
    .bot-bubble { background: #f0f2f6; border-radius: 15px; padding: 12px; margin: 8px 0; border-right: 5px solid #10ac84; }
    .user-bubble { background: #e3f2fd; border-radius: 15px; padding: 12px; margin: 8px 0; border-left: 5px solid #1976d2; }
    
    .stButton>button { width: 100%; border-radius: 25px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. منطق تحليل البيانات
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
    return pd.Series([round(avg_score), ", ".join(missing_items)])

# 3. جلب البيانات
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

# 4. محرك الردود للمساعد الذكي
def chat_with_masterdata(query, df):
    query = query.lower()
    match = df[df['Unified_ID'].str.contains(query, na=False)]
    if not match.empty:
        row = match.iloc[0]
        status_emoji = "✅" if row['Overall_Score'] == 100 else "⚠️"
        msg = f"{status_emoji} **الموقع: {row['Unified_ID']}**\n\n"
        msg += f"• الشركة: {row['شركة']}\n"
        msg += f"• الجاهزية: {row['Overall_Score']}%\n"
        if row['Missing_Details']:
            msg += f"• النواقص: {row['Missing_Details']}"
        return msg
    return "لم أجد هذا الموقع في الـ Masterdata 🧐.. جرب كتابة الرقم فقط."

# --- بناء واجهة التطبيق ---
try:
    df, checklist_cols = load_data()
    avg_total = int(df['Overall_Score'].mean())

    # تم تحديث العنوان الرئيسي هنا
    st.title("🕋 لوحة قطاع المشاعر b2b2c")

    # 5. قسم التقييم الفوري
    st.write("### 📢 حالة الجاهزية الحالية")
    if avg_total >= 90:
        st.markdown(f'<div class="status-card ok-bg"><h2>الوضع ممتاز (OK) ✅</h2>المعدل العام: {avg_total}%</div>', unsafe_allow_html=True)
    elif avg_total >= 70:
        st.markdown(f'<div class="status-card warning-bg"><h2>يحتاج تدخل بسيط (Semi-OK) ⚠️</h2>المعدل العام: {avg_total}%</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-card danger-bg"><h2>وضع حرج جداً (NOT OK) 🚨</h2>المعدل العام: {avg_total}%</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 الإحصائيات", "🤖 مساعد البيانات", "📋 التقارير"])

    with tab1:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = avg_total,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#10ac84"}},
            title = {'text': "مؤشر الإنجاز الكلي 📈"}
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=50, b=20), dragmode=False)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        st.info("قم بفتح الشريط الجانبي (Sidebar) للتحدث مع Masterdata Bot! 🤖")

    with tab3:
        st.subheader("📋 تفاصيل جميع المواقع")
        st.dataframe(df[['Unified_ID', 'Overall_Score', 'Missing_Details']].rename(columns={'Unified_ID': '📍 الموقع', 'Overall_Score': '🏁 %'}), use_container_width=True, hide_index=True)

    # --- المخطط المقارن ---
    st.divider()
    st.subheader("📊 مقارنة المواقع حسب الفريق")
    
    choice = st.radio("تصفية الفرق: 🛠️", ["الكل 🌍", "سنا (الذهبية) ✨", "ركين (المتميزة) 🏆"], horizontal=True)
    
    chart_df = df
    if "سنا" in choice: chart_df = df[df['شركة'].str.contains('سنا', na=False)]
    elif "ركين" in choice: chart_df = df[df['شركة'].str.contains('ركين', na=False)]

    fig_bar = px.bar(
        chart_df.sort_values('Overall_Score', ascending=False), 
        x='Unified_ID', y='Overall_Score', 
        text='Overall_Score', color='Overall_Score',
        color_continuous_scale='YlGnBu'
    )
    
    fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
    fig_bar.update_xaxes(fixedrange=True, tickangle=-45, automargin=True, title={'text': 'رقم الموقع 📍', 'standoff': 50})
    fig_bar.update_yaxes(fixedrange=True, range=[0, 120], title='نسبة الجاهزية')
    fig_bar.update_layout(height=600, dragmode=False, margin=dict(b=180), showlegend=False)
    
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    # --- نظام الدردشة الجانبي ---
    with st.sidebar:
        st.title("🤖 المساعد الذكي")
        if 'messages' not in st.session_state:
            st.session_state.messages = [{"role": "bot", "content": "أهلاً! اكتب رقم الموقع وسأعطيك حالته فوراً. 🔎"}]
        
        for msg in st.session_state.messages:
            bubble_class = "bot-bubble" if msg["role"] == "bot" else "user-bubble"
            st.markdown(f'<div class="{bubble_class}">{msg["content"]}</div>', unsafe_allow_html=True)
        
        if prompt := st.chat_input("عن أي موقع تبحث؟"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "bot", "content": chat_with_masterdata(prompt, df)})
            st.rerun()

except Exception as e:
    st.error(f"⚠️ حدث خطأ في النظام: {e}")

if st.button("🔄 تحديث البيانات الآن"):
    st.cache_data.clear()
    st.rerun()
