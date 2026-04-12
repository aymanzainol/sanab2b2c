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
    .bot-msg { 
        background: #f0f2f6; 
        border-radius: 15px; 
        padding: 15px; 
        margin: 10px 0; 
        border-right: 5px solid #10ac84; 
        text-align: right;
    }
    .user-msg { 
        background: #e3f2fd; 
        border-radius: 15px; 
        padding: 15px; 
        margin: 10px 0; 
        border-right: 5px solid #1976d2; 
        text-align: right;
    }
    
    /* تنسيق بطاقات الحالة */
    .status-card { padding: 20px; border-radius: 15px; margin-bottom: 15px; text-align: center; border-right: 10px solid; }
    .ok-bg { background-color: #d4edda; border-right-color: #28a745; color: #155724; }
    .warning-bg { background-color: #fff3cd; border-right-color: #ffc107; color: #856404; }
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
        msg += f"• الفريق: {row['شركة']}\n"
        msg += f"• نسبة الإنجاز: {row['Overall_Score']}%\n"
        msg += f"• النواقص الحالية: {row['Missing_Details'] if row['Missing_Details'] else 'لا يوجد نواقص، العمل مكتمل! ✨'}"
        return msg
    return "عذراً، لم أجد هذا الموقع في الـ Masterdata. تأكد من إدخال الرقم الصحيح. 🧐"

# 4. نظام التنقل (Sidebar Navigation)
with st.sidebar:
    st.title("🧭 التنقل")
    page = st.radio("اختر الصفحة:", ["📊 الإحصائيات والتقارير", "🤖 المساعد الذكي (الدردشة)"])
    st.divider()
    if st.button("🔄 تحديث البيانات الحية"):
        st.cache_data.clear()
        st.rerun()

# تحميل البيانات
try:
    df, checklist_cols = load_data()

    # --- الصفحة الأولى: لوحة الإحصائيات ---
    if page == "📊 الإحصائيات والتقارير":
        st.title("🕋 لوحة قطاع المشاعر b2b2c")
        avg_total = int(df['Overall_Score'].mean())
        
        # كروت الحالة السريعة
        if avg_total >= 90:
            st.markdown(f'<div class="status-card ok-bg"><h2>الوضع العام: ممتاز ✅</h2>المعدل التراكمي: {avg_total}%</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-card warning-bg"><h2>الوضع العام: يحتاج متابعة ⚠️</h2>المعدل التراكمي: {avg_total}%</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            fig_bar = px.bar(df, x='Unified_ID', y='Overall_Score', color='Overall_Score', text='Overall_Score', 
                             color_continuous_scale='Greens', title="مستوى الجاهزية لكل موقع")
            fig_bar.update_xaxes(autorange="reversed")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.subheader("🔍 تفاصيل سريعة")
            st.dataframe(df[['Unified_ID', 'Overall_Score']].rename(columns={'Unified_ID': 'الموقع', 'Overall_Score': '%'}))

    # --- الصفحة الثانية: المساعد الذكي (Chatbot) ---
    elif page == "🤖 المساعد الذكي (الدردشة)":
        st.title("🤖 المساعد الذكي للبيانات")
        st.info("اكتب رقم الموقع في الأسفل وسأقوم بسحب البيانات لك فوراً من الـ Masterdata.")
        
        # حاوية المحادثة
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "bot", "content": "أهلاً بك! أنا مساعدك الذكي لقطاع المشاعر. كيف يمكنني مساعدتك اليوم؟"}]

        for m in st.session_state.messages:
            cls = "bot-msg" if m["role"] == "bot" else "user-msg"
            icon = "🤖" if m["role"] == "bot" else "👤"
            st.markdown(f'<div class="{cls}">{icon} {m["content"]}</div>', unsafe_allow_html=True)

        # منطقة إدخال المستخدم
        if prompt := st.chat_input("أدخل رقم الموقع (مثال: الهند 20)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = chat_logic(prompt, df)
            st.session_state.messages.append({"role": "bot", "content": response})
            st.rerun()

except Exception as e:
    st.error(f"⚠️ حدث خطأ أثناء الاتصال بالبيانات: {e}")
