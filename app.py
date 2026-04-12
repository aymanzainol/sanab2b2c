import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر b2b2c 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) لدعم الـ RTL والتصميم الاحترافي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    .main .block-container { direction: rtl; text-align: right; }
    html, body, [data-testid="stSidebar"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* تنسيق فقاعات الدردشة في الصفحة الجديدة */
    .chat-container {
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        padding: 20px;
        background-color: #ffffff;
        margin-bottom: 20px;
    }
    .bot-msg { background: #f0f2f6; border-radius: 15px; padding: 15px; margin: 10px 0; border-right: 5px solid #10ac84; }
    .user-msg { background: #e3f2fd; border-radius: 15px; padding: 15px; margin: 10px 0; border-right: 5px solid #1976d2; }
    
    /* تنسيق بطاقات الحالة */
    .status-card { padding: 20px; border-radius: 15px; margin-bottom: 15px; text-align: center; border-right: 10px solid; }
    .ok-bg { background-color: #d4edda; border-right-color: #28a745; color: #155724; }
    .warning-bg { background-color: #fff3cd; border-right-color: #ffc107; color: #856404; }
    .danger-bg { background-color: #f8d7da; border-right-color: #dc3545; color: #721c24; }
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
    return pd.Series([round(avg_score), ", ".join(missing_items)])

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

def chat_logic(query, df):
    query = query.lower()
    match = df[df['Unified_ID'].str.contains(query, na=False)]
    if not match.empty:
        row = match.iloc[0]
        msg = f"📍 **بيانات الموقع: {row['Unified_ID']}**\n\n"
        msg += f"• الشركة: {row['شركة']}\n"
        msg += f"• نسبة الإنجاز: {row['Overall_Score']}%\n"
        msg += f"• النواقص: {row['Missing_Details'] if row['Missing_Details'] else 'لا يوجد نواقص ✨'}"
        return msg
    return "عذراً، لم أجد بيانات لهذا الرقم. تأكد من كتابة الرقم الصحيح للموقع 🧐"

# 4. إدارة التنقل بين الصفحات
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/null/manager.png") # أيقونة بسيطة
    st.title("القائمة الرئيسية")
    page = st.radio("انتقل إلى:", ["📊 لوحة الإحصائيات", "🤖 المساعد الذكي (Chatbot)"])
    st.divider()
    if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

# تحميل البيانات
try:
    df, checklist_cols = load_data()

    # --- الصفحة الأولى: لوحة الإحصائيات ---
    if page == "📊 لوحة الإحصائيات":
        st.title("🕋 لوحة قطاع المشاعر b2b2c")
        avg_total = int(df['Overall_Score'].mean())
        
        # كروت الحالة
        if avg_total >= 90:
            st.markdown(f'<div class="status-card ok-bg"><h2>الوضع ممتاز ✅</h2>معدل الجاهزية العام: {avg_total}%</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-card warning-bg"><h2>يحتاج متابعة ⚠️</h2>معدل الجاهزية العام: {avg_total}%</div>', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)
        with col_left:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=avg_total,
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#10ac84"}},
                title={'text': "مؤشر الإنجاز الكلي"}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col_right:
            st.subheader("📋 ملخص المواقع")
            st.dataframe(df[['Unified_ID', 'Overall_Score']].rename(columns={'Unified_ID': 'الموقع', 'Overall_Score': '%'}))

        # المخطط البياني
        st.divider()
        fig_bar = px.bar(df, x='Unified_ID', y='Overall_Score', color='Overall_Score', text='Overall_Score', title="مقارنة الجاهزية بين المواقع")
        fig_bar.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- الصفحة الثانية: المساعد الذكي ---
    elif page == "🤖 المساعد الذكي (Chatbot)":
        st.title("🤖 مساعد Masterdata الذكي")
        st.write("أهلاً بك في صفحة المساعد. يمكنك السؤال عن أي موقع أو الاستفسار عن تفاصيل Masterdata.")
        
        # تهيئة تاريخ الرسائل
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "bot", "content": "أهلاً بك! أنا بطل قطاع المشاعر الذكي، أعطني رقم الموقع وسأزودك بكل تفاصيله."}]

        # عرض الرسائل
        for m in st.session_state.messages:
            cls = "bot-msg" if m["role"] == "bot" else "user-msg"
            icon = "🤖" if m["role"] == "bot" else "👤"
            st.markdown(f'<div class="{cls}">{icon} {m["content"]}</div>', unsafe_allow_html=True)

        # مدخل الدردشة
        if prompt := st.chat_input("اكتب رقم الموقع هنا (مثال: الهند 20)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = chat_logic(prompt, df)
            st.session_state.messages.append({"role": "bot", "content": response})
            st.rerun()

except Exception as e:
    st.error(f"خطأ في تحميل البيانات: {e}")
