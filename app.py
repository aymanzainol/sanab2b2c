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
    html, body, [data-testid="stSidebar"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* تنسيق فقاعات الدردشة */
    .bot-msg { background: #f0f2f6; border-radius: 15px; padding: 15px; margin: 10px 0; border-right: 5px solid #10ac84; text-align: right; }
    .user-msg { background: #e3f2fd; border-radius: 15px; padding: 15px; margin: 10px 0; border-right: 5px solid #1976d2; text-align: right; }
    
    /* تنسيق بطاقات الحالة العلوية */
    .status-card { padding: 20px; border-radius: 15px; margin-bottom: 15px; text-align: center; border-right: 10px solid; }
    .ok-bg { background-color: #d4edda; border-right-color: #28a745; color: #155724; }
    .warning-bg { background-color: #fff3cd; border-right-color: #ffc107; color: #856404; }
    
    /* تنسيق أزرار المخيمات */
    .stButton>button { border-radius: 8px; width: 100%; transition: 0.3s; font-weight: bold; }
    .stButton>button:hover { transform: scale(1.02); border-color: #10ac84; }

    /* التصميم الجديد لبطاقات الإحصائيات أسفل الخريطة */
    .stat-box {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }
    .stat-label { color: #6b7280; font-size: 16px; font-weight: bold; }
    .val-green { color: #10b981; font-size: 28px; font-weight: bold; margin: 10px 0; }
    .val-red { color: #ef4444; font-size: 28px; font-weight: bold; margin: 10px 0; }
    .val-orange { color: #f59e0b; font-size: 28px; font-weight: bold; margin: 10px 0; }

    /* التصميم الجديد للنواقص (مريحة للعين) */
    .checklist-item { 
        background-color: #fdf2f2; 
        padding: 15px 20px; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border-right: 5px solid #ef4444; 
        color: #991b1b;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .perfect-card { background: #f0fff4; border: 1px solid #68d391; border-radius: 10px; padding: 20px; border-right: 8px solid #38a169; margin-top: 15px; text-align: center;}
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

# 4. نظام التنقل
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
        
        if avg_total >= 90:
            st.markdown(f'<div class="status-card ok-bg"><h2>الوضع العام: ممتاز ✅</h2>المعدل التراكمي: {avg_total}%</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-card warning-bg"><h2>الوضع العام: يحتاج متابعة ⚠️</h2>المعدل التراكمي: {avg_total}%</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📈 المؤشرات البيانية", "🏕️ خريطة المخيمات والنواقص (محدثة)"])
        
        with tab1:
            col1, col2 = st.columns([2, 1])
            with col1:
                fig_bar = px.bar(df, x='Unified_ID', y='Overall_Score', color='Overall_Score', text='Overall_Score', 
                                 color_continuous_scale='Greens', title="مستوى الجاهزية لكل موقع")
                fig_bar.update_xaxes(autorange="reversed")
                st.plotly_chart(fig_bar, use_container_width=True)
            with col2:
                st.subheader("🔍 تفاصيل سريعة")
                st.dataframe(df[['Unified_ID', 'Overall_Score']].rename(columns={'Unified_ID': 'الموقع', 'Overall_Score': '%'}))

        # --- خريطة المخيمات (النسخة المريحة للعين) ---
        with tab2:
            st.subheader("إضغط على أي مخيم لمعرفة النواقص الخاصة به 🔍")
            st.markdown("**دليل الألوان:** 🟡 سنا (الذهبية) | 🔵 ركين (المتميزة)")
            
            if 'selected_tent' not in st.session_state:
                st.session_state.selected_tent = None

            cols = st.columns(4) 
            for idx, row in df.iterrows():
                tent_id = row['Unified_ID']
                company = str(row['شركة'])
                color_code = "🟡" if "سنا" in company else "🔵"
                
                col_idx = idx % 4
                with cols[col_idx]:
                    if st.button(f"{color_code} {tent_id}", key=f"btn_{idx}"):
                        st.session_state.selected_tent = row
            
            # --- منطقة عرض التفاصيل الجديدة (Dashboard Style) ---
            if st.session_state.selected_tent is not None:
                selected = st.session_state.selected_tent
                score = int(selected['Overall_Score'])
                missing_str = selected['Missing_Details']
                missing_list = [item.strip() for item in missing_str.split('،') if item.strip()]
                missing_count = len(missing_list)
                
                st.divider()
                st.markdown(f"### 📍 تفاصيل موقع: `{selected['Unified_ID']}`")
                st.caption(f"الشركة المنفذة: **{selected['شركة']}**")
                
                # 1. شريط التقدم المرئي
                st.progress(score / 100.0)
                
                # 2. بطاقات الأرقام السريعة
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"<div class='stat-box'><div class='stat-label'>✅ الإنجاز المكتمل</div><div class='val-green'>{score}%</div></div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='stat-box'><div class='stat-label'>⏳ العمل المتبقي</div><div class='val-orange'>{100 - score}%</div></div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='stat-box'><div class='stat-label'>⚠️ عدد النواقص</div><div class='val-red'>{missing_count} بنود</div></div>", unsafe_allow_html=True)
                
                st.write("") # مسافة فارغة
                
                # 3. قائمة النواقص (مربعات واضحة ومريحة)
                if missing_count == 0:
                    st.markdown('<div class="perfect-card"><h3>🌟 عمل ممتاز! جميع البنود مكتملة 100%.</h3></div>', unsafe_allow_html=True)
                else:
                    st.markdown("#### 📋 بنود العمل التي تحتاج إلى إكمال:")
                    for item in missing_list:
                        # تحويل كل نص إلى بطاقة أنيقة مستقلة
                        st.markdown(f"<div class='checklist-item'>⭕ <span>{item}</span></div>", unsafe_allow_html=True)


    # --- الصفحة الثانية: المساعد الذكي (Chatbot) ---
    elif page == "🤖 المساعد الذكي (الدردشة)":
        st.title("🤖 المساعد الذكي للبيانات")
        st.info("اكتب رقم الموقع في الأسفل وسأقوم بسحب البيانات لك فوراً من الـ Masterdata.")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "bot", "content": "أهلاً بك! أنا مساعدك الذكي لقطاع المشاعر. كيف يمكنني مساعدتك اليوم؟"}]

        for m in st.session_state.messages:
            cls = "bot-msg" if m["role"] == "bot" else "user-msg"
            icon = "🤖" if m["role"] == "bot" else "👤"
            st.markdown(f'<div class="{cls}">{icon} {m["content"]}</div>', unsafe_allow_html=True)

        if prompt := st.chat_input("أدخل رقم الموقع (مثال: الهند 20)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = chat_logic(prompt, df)
            st.session_state.messages.append({"role": "bot", "content": response})
            st.rerun()

except Exception as e:
    st.error(f"⚠️ حدث خطأ أثناء الاتصال بالبيانات: {e}")
