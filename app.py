import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="Mina Readiness Dashboard", layout="wide", initial_sidebar_state="collapsed")

# 2. التنسيق الجمالي (CSS) - تصميم عصري، متجاوب، ويدعم واجهة الدردشة
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
    /* تنسيق أزرار الاختيار (Radio) */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        gap: 20px;
    }
    /* تنسيق بطاقات الدردشة */
    .bot-card {
        background: #f1f2f6;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border-right: 5px solid #10ac84;
        color: #2f3542;
    }
    .user-card {
        background: #e1f5fe;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border-left: 5px solid #0288d1;
        color: #2f3542;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. منطق تحليل البيانات
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

# 4. تحميل البيانات من Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    # توحيد معرفات المواقع بناءً على الشركة
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير محدد").astype(str)
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols

# ثابت الألوان والأسماء
SANA_NAME = 'سنا (مشارق الذهبية)'
RAKEEN_NAME = 'ركين (مشارق المتميزة)'
COMPANY_COLORS = {SANA_NAME: '#e74c3c', RAKEEN_NAME: '#795548'}

# 5. منطق المساعد الذكي (Chatbot)
def get_bot_response(user_input, df):
    user_input = user_input.lower()
    # البحث برقم الموقع
    match = df[df['Unified_ID'].str.contains(user_input, na=False)]
    if not match.empty:
        row = match.iloc[0]
        resp = f"📊 **تقرير الموقع {row['Unified_ID']}:**\n\n"
        resp += f"• **الشركة:** {row['شركة']}\n"
        resp += f"• **نسبة الإنجاز:** {row['Overall_Score']}%\n"
        if row['Missing_Details']:
            resp += f"• ⚠️ **النواقص:** {row['Missing_Details']}"
        else:
            resp += "• ✨ **الحالة:** مكتمل وجاهز تماماً."
        return resp
    
    # استعلام عن الشركات
    if any(x in user_input for x in ['سنا', 'ذهبية']):
        avg = df[df['شركة'] == SANA_NAME]['Overall_Score'].mean()
        return f"متوسط جاهزية شركة **سنا** حالياً هو **{round(avg)}%**."
    if any(x in user_input for x in ['ركين', 'متميزة']):
        avg = df[df['شركة'] == RAKEEN_NAME]['Overall_Score'].mean()
        return f"متوسط جاهزية شركة **ركين** حالياً هو **{round(avg)}%**."
        
    return "يمكنك كتابة رقم الموقع (مثل: الهند 20) أو اسم الشركة وسأزودك بالتفاصيل فوراً."

# --- بناء الواجهة ---
try:
    df, checklist_cols = load_data()

    st.title("🕋 لوحة جاهزية مخيمات منى")

    # نظام التبويبات الرئيسي
    tab1, tab2, tab3 = st.tabs(["📊 الملخص العام", "🤖 التحليل الذكي", "📋 التقارير"])

    with tab1:
        avg_total = int(df['Overall_Score'].mean())
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = avg_total,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#10ac84"}},
            title = {'text': "الجاهزية الكلية", 'font': {'family': 'Cairo'}}
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20), dragmode=False)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("💡 بنود لم تكتمل بعد")
        missing_summary = []
        for col in checklist_cols:
            bad_sites = df[df[col].astype(str).str.contains('لا|غير مطابق|لم يتم|0%', na=False)]['Unified_ID'].tolist()
            if bad_sites:
                missing_summary.append({"البند": col, "المواقع": " ، ".join(bad_sites)})
        
        if missing_summary:
            for item in missing_summary:
                with st.expander(f"❌ {item['البند']}"):
                    st.write(f"المواقع: **{item['المواقع']}**")
        else:
            st.success("جميع بنود العمل في جميع المواقع مكتملة!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("📋 كشف تفصيلي")
        st.data_editor(
            df[['Unified_ID', 'Overall_Score', 'Missing_Details']].rename(
                columns={'Unified_ID': 'الموقع', 'Overall_Score': 'إنجاز %', 'Missing_Details': 'النواقص'}
            ),
            column_config={"إنجاز %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%")},
            hide_index=True, use_container_width=True
        )

    # --- المساعد الذكي (Floating Chat logic) ---
    if 'chat_open' not in st.session_state: st.session_state.chat_open = False
    if 'messages' not in st.session_state: 
        st.session_state.messages = [{"role": "bot", "content": "أهلاً بك! أنا مساعد Masterdata، اسألني عن أي موقع."}]

    with st.sidebar:
        st.markdown("### 🤖 المساعد الذكي")
        if st.button("💬 فتح محادثة البيانات"):
            st.session_state.chat_open = not st.session_state.chat_open
        
        if st.session_state.chat_open:
            st.divider()
            for msg in st.session_state.messages:
                cls = "bot-card" if msg["role"] == "bot" else "user-card"
                st.markdown(f'<div class="{cls}">{msg["content"]}</div>', unsafe_allow_html=True)
            
            if prompt := st.chat_input("رقم الموقع..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "bot", "content": get_bot_response(prompt, df)})
                st.rerun()

    # --- المخطط البياني (المقارنة) - تم معالجة التداخل وقفل الجوال ---
    st.divider()
    st.subheader("📊 مقارنة الجاهزية لكل موقع")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_option = st.radio("الشركة:", ["الكل", "سنا", "ركين"], horizontal=True)

    chart_df = df
    if filter_option == "سنا": chart_df = df[df['شركة'] == SANA_NAME]
    elif filter_option == "ركين": chart_df = df[df['شركة'] == RAKEEN_NAME]

    fig_bar = px.bar(
        chart_df.sort_values('Overall_Score', ascending=False), 
        x='Unified_ID', 
        y='Overall_Score', 
        color='شركة', 
        text='Overall_Score',
        color_discrete_map=COMPANY_COLORS
    )
    
    fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
    
    # الحل النهائي لتداخل النصوص (SVG Fix)
    fig_bar.update_xaxes(
        fixedrange=True, 
        tickangle=-45, 
        automargin=True,
        title={'text': 'رقم الموقع', 'standoff': 60}
    )
    
    fig_bar.update_yaxes(fixedrange=True, title='نسبة الجاهزية %', range=[0, 120])
    
    fig_bar.update_layout(
        font_family="Cairo",
        height=600,
        dragmode=False,
        margin=dict(l=20, r=20, t=30, b=180),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")

# زر التحديث الكلي
if st.button("🔄 تحديث البيانات من المصدر"):
    st.cache_data.clear()
    st.rerun()
