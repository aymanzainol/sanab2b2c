import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

# 2. التنسيق الجمالي (CSS) - تخصيص الخطوط والألوان والاتجاهات
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* ضبط الاتجاه للعربية */
    .main .block-container { direction: rtl; text-align: right; }
    html, body, [data-testid="stSidebar"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, button {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* تنسيق أزرار المواقع */
    .stButton>button { 
        border-radius: 12px; 
        width: 100%; 
        height: 65px; 
        font-weight: bold; 
        border: 1px solid #d1d5db;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* صندوق ملاحظات المراقب */
    .observer-notes-box {
        background-color: #fefce8;
        padding: 18px;
        border-radius: 12px;
        border-right: 6px solid #eab308;
        margin-bottom: 20px;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
    }
    
    .date-badge {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        border: 1px solid #fde68a;
    }

    /* تنسيق قائمة الأنشطة المتبقية */
    .checklist-item-popup { 
        background-color: #fef2f2; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 6px; 
        border-right: 4px solid #ef4444; 
        font-size: 14px;
        color: #991b1b;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. دوال تحليل البيانات
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        val = str(row[col]).strip()
        current_score = None
        # منطق تحويل النصوص إلى نسب
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
    
    # تحديد أعمدة الفحص (تعدل حسب هيكلة شيت قوقل)
    checklist_cols = df.columns[7:37]
    
    # حساب النتائج
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    
    # توحيد معرف الموقع بناءً على الشركة
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df.iloc[:, 5], df.iloc[:, 6])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str)
    
    # التعامل مع التاريخ
    if 'التاريخ' not in df.columns:
        df['التاريخ'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        
    return df.drop_duplicates(subset=['Unified_ID'], keep='last'), checklist_cols

# 4. النافذة المنبثقة التفصيلية
@st.dialog("تقرير حالة الموقع التفصيلي 🏕️")
def show_tent_details(row):
    score = int(row['Overall_Score'])
    missing_list = [item.strip() for item in str(row['Missing_Details']).split('،') if item.strip()]
    
    # العنوان والنسبة
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"## موقع: {row['Unified_ID']}")
        st.write(f"**الشركة:** {row['شركة']}")
    with c2:
        st.markdown(f"<div style='text-align:center;'>جاهزية الموقع<br><h1 style='color:#059669; margin-top:0;'>{score}%</h1></div>", unsafe_allow_html=True)

    st.progress(score / 100.0)

    # 1. ملاحظات المراقب (بالتاريخ)
    st.markdown("### 📝 أحدث ملاحظات المراقب")
    notes = row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) and str(row['ملاحظات المراقب']).strip() != "" else "لا توجد ملاحظات مسجلة لهذا الموقع."
    date_val = row['التاريخ']
    st.markdown(f"""
    <div class="observer-notes-box">
        <span class="date-badge">تاريخ التقرير: {date_val}</span><br><br>
        {notes}
    </div>
    """, unsafe_allow_html=True)

    # 2. الأنشطة المتبقية (النواقص)
    st.markdown(f"### ⚠️ متبقي الأنشطة ({len(missing_list)})")
    if not missing_list:
        st.success("🎉 ممتاز! تم اكتمال كافة الأنشطة في هذا الموقع.")
    else:
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)
    
    st.divider()
    st.caption("يتم تحديث هذه البيانات بناءً على آخر تقرير مرفوع من المراقب الميداني.")

# 5. واجهة التطبيق الرئيسية
try:
    df, checklist_cols = load_data()

    # القائمة الجانبية
    with st.sidebar:
        st.header("📊 نظام المتابعة")
        page = st.radio("القائمة الرئيسية:", ["📊 الإحصائيات والتحليل", "🏕️ خريطة المواقع"])
        st.divider()
        if st.button("🔄 تحديث البيانات الآن"):
            st.cache_data.clear()
            st.rerun()

    # صفحة الإحصائيات
    if page == "📊 الإحصائيات والتحليل":
        st.title("📊 التحليل البياني لجاهزية القطاع")
        
        # تصفية البيانات لكل شركة
        df_sana = df[df['شركة'].str.contains('سنا', na=False)]
        df_rakeen = df[df['شركة'].str.contains('ركين', na=False)]

        # --- شركة سنا (بني) ---
        st.markdown("---")
        st.subheader("🟤 شركة سنا (الباقة الذهبية)")
        col_s1, col_s2 = st.columns([1, 4])
        with col_s1:
            st.metric("متوسط الإنجاز", f"{round(df_sana['Overall_Score'].mean())}%")
            st.metric("مواقع مكتملة", f"{len(df_sana[df_sana['Overall_Score'] == 100])}")
        with col_s2:
            fig_sana = px.bar(df_sana, x='Unified_ID', y='Overall_Score', 
                             color_discrete_sequence=['#5D4037'], # لون بني داكن
                             labels={'Overall_Score':'نسبة الإنجاز %', 'Unified_ID':'رقم الموقع'})
            fig_sana.update_layout(height=350, margin=dict(t=10, b=10))
            st.plotly_chart(fig_sana, use_container_width=True)

        # --- شركة ركين (أحمر) ---
        st.markdown("---")
        st.subheader("🔴 شركة ركين (الباقة المتميزة)")
        col_r1, col_r2 = st.columns([1, 4])
        with col_r1:
            st.metric("متوسط الإنجاز", f"{round(df_rakeen['Overall_Score'].mean())}%")
            st.metric("مواقع مكتملة", f"{len(df_rakeen[df_rakeen['Overall_Score'] == 100])}")
        with col_r2:
            fig_rakeen = px.bar(df_rakeen, x='Unified_ID', y='Overall_Score', 
                               color_discrete_sequence=['#B91C1C'], # لون أحمر
                               labels={'Overall_Score':'نسبة الإنجاز %', 'Unified_ID':'رقم الموقع'})
            fig_rakeen.update_layout(height=350, margin=dict(t=10, b=10))
            st.plotly_chart(fig_rakeen, use_container_width=True)

    # صفحة خريطة المواقع (الأزرار)
    elif page == "🏕️ خريطة المواقع":
        st.title("🏕️ خريطة توزيع المواقع الميدانية")
        st.info("قم بالنقر على رقم الموقع لمراجعة (ملاحظات المراقب اليومية) وقائمة (الأنشطة المتبقية).")
        
        # فرز البيانات لعرضها بشكل منظم
        df_sorted = df.sort_values(by=['شركة', 'Unified_ID'])
        
        # عرض الأزرار في شبكة (Grid)
        grid_cols = st.columns(6) # 6 أعمدة في الصف الواحد
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🟤" if "سنا" in str(row['شركة']) else "🔴"
            color_hex = "#5D4037" if "سنا" in str(row['شركة']) else "#B91C1C"
            
            with grid_cols[idx % 6]:
                # كتابة نص الزر: المعرف + النسبة
                label = f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%"
                if st.button(label, key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row)

except Exception as e:
    st.error(f"⚠️ خطأ في تحميل البيانات: {e}")
    st.info("تأكد من أن رابط Google Sheets متاح للجميع (Anyone with the link can view).")
