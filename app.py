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

    .stButton>button { border-radius: 8px; width: 100%; height: 50px; font-weight: bold; border: 1px solid #e0e0e0; }
    
    .observer-notes-box {
        background-color: #fdf2f2;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #dc2626;
        margin-bottom: 20px;
    }
    
    .date-badge {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }

    .checklist-item-popup { 
        background-color: #fff5f5; 
        padding: 10px; 
        border-radius: 8px; 
        margin-bottom: 5px; 
        border-right: 4px solid #ef4444; 
        font-size: 13px;
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
    # نستخدم عمود التاريخ إذا وجد، وإلا نضع تاريخ اليوم كافتراضي
    if 'التاريخ' not in df.columns:
        df['التاريخ'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols

# 4. وظيفة النافذة المنبثقة (المحدثة ببيانات الملاحظات والأنشطة)
@st.dialog("تقرير حالة الموقع 🏕️")
def show_tent_details(row):
    score = int(row['Overall_Score'])
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('،') if item.strip()]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"### موقع: {row['Unified_ID']}")
        st.caption(f"الشركة: {row['شركة']}")
    with col2:
        st.markdown(f"<div style='text-align:center;'>نسبة الإنجاز<br><h2 style='color:#10b981;'>{score}%</h2></div>", unsafe_allow_html=True)

    st.progress(score / 100.0)

    # عرض أحدث الملاحظات بالتاريخ
    st.markdown("---")
    st.subheader("📝 أحدث ملاحظات المراقب")
    notes = row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) else "لا توجد ملاحظات مسجلة حالياً."
    date_val = row['التاريخ']
    st.markdown(f"""
    <div class="observer-notes-box">
        <span class="date-badge">تاريخ التحديث: {date_val}</span><br><br>
        {notes}
    </div>
    """, unsafe_allow_html=True)

    # الأنشطة المتبقية
    st.subheader(f"⚠️ متبقي أنشطة ({len(missing_list)})")
    if not missing_list:
        st.success("✅ جميع الأنشطة مكتملة!")
    else:
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>• {item}</div>", unsafe_allow_html=True)

# 5. بناء واجهة المستخدم
try:
    df, checklist_cols = load_data()

    with st.sidebar:
        st.header("⚙️ التحكم")
        page = st.radio("انتقل إلى:", ["📊 الإحصائيات والتحليل", "🏕️ خريطة المواقع"])
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()

    if page == "📊 الإحصائيات والتحليل":
        st.title("📊 التحليل البياني للقطاع")
        
        df_sana = df[df['شركة'].str.contains('سنا', na=False)]
        df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

        # --- قسم شركة سنا (بني) ---
        st.markdown("### 🟤 شركة سنا (الباقة الذهبية)")
        s1, s2 = st.columns([1, 3])
        with s1:
            st.metric("متوسط الإنجاز", f"{int(df_sana['Overall_Score'].mean())}%")
            st.metric("مواقع مكتملة", f"{len(df_sana[df_sana['Overall_Score'] == 100])} / {len(df_sana)}")
        with s2:
            fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', 
                             title="مستوى الجاهزية - سنا", 
                             color_discrete_sequence=['#8B4513']) # بني
            st.plotly_chart(fig_sana, use_container_width=True)

        st.divider()

        # --- قسم شركة ركين (أحمر) ---
        st.markdown("### 🔴 شركة ركين (الباقة المتميزة)")
        r1, r2 = st.columns([1, 3])
        with r1:
            st.metric("متوسط الإنجاز", f"{int(df_rakeen['Overall_Score'].mean())}%")
            st.metric("مواقع مكتملة", f"{len(df_rakeen[df_rakeen['Overall_Score'] == 100])} / {len(df_rakeen)}")
        with r2:
            fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', 
                               title="مستوى الجاهزية - ركين", 
                               color_discrete_sequence=['#CC0000']) # أحمر
            st.plotly_chart(fig_rakeen, use_container_width=True)

    elif page == "🏕️ خريطة المواقع":
        st.title("🏕️ توزيع المواقع والجاهزية")
        st.write("انقر على الموقع لعرض **الملاحظات اليومية** و **الأنشطة المتبقية**.")
        
        st.markdown("🟤 سنا | 🔴 ركين")
        
        grid_cols = st.columns(5)
        for idx, row in df.iterrows():
            company_color = "🟤" if "سنا" in str(row['شركة']) else "🔴"
            with grid_cols[idx % 5]:
                # الزر يعرض المعرف والنسبة بشكل مختصر
                btn_label = f"{company_color} {row['Unified_ID']}\n({row['Overall_Score']}%)"
                if st.button(btn_label, key=f"btn_{idx}"):
                    show_tent_details(row)

except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
