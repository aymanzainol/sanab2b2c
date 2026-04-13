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

    /* بطاقات الإحصائيات الملونة */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        text-align: center;
    }
    
    .stButton>button { border-radius: 8px; width: 100%; height: 50px; font-weight: bold; border: 1px solid #e0e0e0; }
    
    .observer-notes {
        background-color: #eff6ff;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #3b82f6;
        margin-bottom: 20px;
        font-size: 14px;
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

# 4. وظيفة النافذة المنبثقة
@st.dialog("تفاصيل بنود العمل 🏕️")
def show_tent_details(row):
    score = int(row['Overall_Score'])
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('،') if item.strip()]
    st.write(f"### موقع: {row['Unified_ID']}")
    if 'ملاحظات المراقب' in row and pd.notna(row['ملاحظات المراقب']):
        st.markdown(f"<div class='observer-notes'><b>📝 ملاحظات المراقب:</b><br>{row['ملاحظات المراقب']}</div>", unsafe_allow_html=True)
    st.progress(score / 100.0)
    st.divider()
    if not missing_list: st.success("🌟 العمل مكتمل بنسبة 100%!")
    else:
        st.write("**البنود غير المكتملة:**")
        for item in missing_list: st.error(f"❌ {item}")

# 5. بناء واجهة المستخدم
try:
    df, checklist_cols = load_data()

    with st.sidebar:
        st.header("⚙️ التحكم")
        page = st.radio("انتقل إلى:", ["📊 لوحة التحكم", "🤖 المساعد الذكي"])
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()

    if page == "📊 لوحة التحكم":
        st.title("🕋 متابعة جاهزية قطاع المشاعر")
        
        tab1, tab2 = st.tabs(["📊 الإحصائيات والتحليل", "🏕️ خريطة المواقع"])
        
        with tab1:
            # تقسيم البيانات حسب الشركة
            df_sana = df[df['شركة'].str.contains('سنا', na=False)]
            df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

            # --- قسم شركة سنا ---
            st.markdown("### 🟡 شركة سنا (الباقة الذهبية)")
            m1, m2, m3 = st.columns(3)
            m1.metric("عدد المواقع", len(df_sana))
            m2.metric("متوسط الجاهزية", f"{int(df_sana['Overall_Score'].mean())}%")
            m3.metric("مواقع مكتملة", len(df_sana[df_sana['Overall_Score'] == 100]))
            
            fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', 
                             color='Overall_Score', color_continuous_scale='RdYlGn',
                             title="جاهزية مواقع سنا", labels={'Overall_Score':'النسبة', 'Unified_ID':'رقم الموقع'})
            st.plotly_chart(fig_sana, use_container_width=True)
            
            with st.expander("🔍 تفاصيل بيانات مواقع سنا والنواقص"):
                st.dataframe(df_sana[['Unified_ID', 'Overall_Score', 'Missing_Details', 'ملاحظات المراقب']], 
                             column_config={"Overall_Score": st.column_config.ProgressColumn("نسبة الإنجاز", min_value=0, max_value=100)},
                             hide_index=True)

            st.divider()

            # --- قسم شركة ركين ---
            st.markdown("### 🔵 شركة ركين (الباقة المتميزة)")
            r1, r2, r3 = st.columns(3)
            r1.metric("عدد المواقع", len(df_rakeen))
            r2.metric("متوسط الجاهزية", f"{int(df_rakeen['Overall_Score'].mean())}%")
            r3.metric("مواقع مكتملة", len(df_rakeen[df_rakeen['Overall_Score'] == 100]))

            fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', 
                               color='Overall_Score', color_continuous_scale='Blues',
                               title="جاهزية مواقع ركين", labels={'Overall_Score':'النسبة', 'Unified_ID':'رقم الموقع'})
            st.plotly_chart(fig_rakeen, use_container_width=True)

            with st.expander("🔍 تفاصيل بيانات مواقع ركين والنواقص"):
                st.dataframe(df_rakeen[['Unified_ID', 'Overall_Score', 'Missing_Details', 'ملاحظات المراقب']], 
                             column_config={"Overall_Score": st.column_config.ProgressColumn("نسبة الإنجاز", min_value=0, max_value=100)},
                             hide_index=True)

        with tab2:
            st.subheader("انقر على أي مخيم لمشاهدة التفاصيل")
            st.markdown("🟡 سنا | 🔵 ركين")
            grid_cols = st.columns(5)
            for idx, row in df.iterrows():
                company_icon = "🟡" if "سنا" in str(row['شركة']) else "🔵"
                with grid_cols[idx % 5]:
                    if st.button(f"{company_icon} {row['Unified_ID']}", key=f"tent_{idx}"):
                        show_tent_details(row)

    elif page == "🤖 المساعد الذكي":
        st.title("🤖 المساعد الذكي")
        st.chat_message("assistant").write("أهلاً بك! يمكنك سؤالي عن أي موقع مباشرة.")
        if prompt := st.chat_input("اكتب رقم الموقع..."):
            st.chat_message("user").write(prompt)

except Exception as e:
    st.error(f"حدث خطأ: {e}")
