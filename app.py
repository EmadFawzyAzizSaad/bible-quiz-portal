import streamlit as st
import pandas as pd
import os
import psycopg2
from datetime import datetime
import pytz  # 🌍 مكتبة التوقيت العالمي لضبط فرق الساعات أونلاين

# إعدادات الصفحة
st.set_page_config(page_title="بورتال مسابقة الكتاب المقدس", page_icon="⛪", layout="centered")

# 🔒 رابط الـ Transaction pooler المأمن والشغال أونلاين في مصر 10/10
DB_CONN_STRING = "postgresql://postgres.krcowyrafgznvpdhenvw:P%40ssw0rd_123654e@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

# دالة مأمنة لحفظ النتيجة والهيستوري والموبايل في السيرفر مباشرة أونلاين
def save_result_to_postgres(name, group, mobile, chapter, score, total, history_string):
    try:
        conn = psycopg2.connect(DB_CONN_STRING, client_encoding='utf8')
        cursor = conn.cursor()
        
        score_string = f"{score}from {total}"
        full_history = f"الموبايل: {mobile} | {history_string}"
        
        insert_query = """
        INSERT INTO kpis_bible_study (name, group_name, chapter, score, user_history) 
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (str(name).strip(), str(group).strip(), str(chapter).strip(), score_string, str(full_history).strip()))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"🚨 خطأ في ضخ البيانات للسيرفر: {e}")

# دالة للتحقق من عدم التكرار أونلاين
def check_if_already_solved_postgres(name, chapter):
    try:
        conn = psycopg2.connect(DB_CONN_STRING, client_encoding='utf8')
        cursor = conn.cursor()
        
        select_query = "SELECT id FROM kpis_bible_study WHERE name = %s AND chapter = %s;"
        cursor.execute(select_query, (str(name).strip(), str(chapter).strip()))
        
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return len(result) > 0
    except:
        return False

# دالة لجلب أسئلة اليوم من الشيت المحلي بالتوقيت المصري المظبوط
def get_today_questions():
    file_name = "questions_bank.csv"
    egypt_timezone = pytz.timezone("Africa/Cairo")
    today_str = datetime.now(egypt_timezone).strftime("%Y-%m-%d")
    
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name, encoding='utf-8-sig', on_bad_lines='skip')
            today_df = df[df['التاريخ'] == today_str]
            if not today_df.empty:
                current_chapter = today_df["الإصحاح"].iloc[0]
                questions_list = []
                for _, row in today_df.iterrows():
                    questions_list.append({
                        "question": row['السؤال'],
                        "options": str(row['الاختيارات']).split('|'),
                        "answer": str(row['الإجابة الصحيحة']).strip()
                    })
                return current_chapter, questions_list
        except Exception as e:
            st.error(f"خطأ في قراءة بنك الأسئلة: {e}")
    return None, []

# واجهة الموقع
st.title("⛪ بورتال مسابقة الكتاب المقدس اليومية")
st.write("---")

# 1️⃣ أولاً: خانات البيانات الأساسية فوق خالص
st.markdown("### 📝 دخل بياناتك أولاً للدخول للمسابقة:")
student_name = st.text_input("اسمك بالكامل:", key="student_name_input")

col1, col2 = st.columns(2)
with col1:
    student_group = st.selectbox("المرحلة الدراسية:", ["اختر المرحلة", "أولى إعدادي", "تانية إعدادي", "تالتة إعدادي"], key="student_group_input")
with col2:
    student_mobile = st.text_input("رقم الموبايل (واتساب):", key="student_mobile_input", max_chars=11)

st.write("---")

# التحقق من إدخال الـ 3 بيانات كاملة
is_data_complete = student_name.strip() != "" and student_group != "اختر المرحلة" and student_mobile.strip() != ""

if not is_data_complete:
    st.info("👋 مرحباً بك! من فضلك اكتب اسمك، واختر مرحلتك، واكتب رقم موبايلك لتظهر لك أسئلة اليوم. ✨")
else:
    # 2️⃣ ثانياً: فلترة المرحلة الدراسية (تانية إعدادي فقط حالياً)
    if student_group != "تانية إعدادي":
        st.warning(f"✨ مسابقة مرحلة ({student_group}) مش متوفرة لسه، بنجهزها وهتنزل قريب جداً يا بطل! ✨")
    else:
        chapter_name, today_questions = get_today_questions()

        if "current_loaded_chapter" not in st.session_state:
            st.session_state.current_loaded_chapter = chapter_name

        if st.session_state.current_loaded_chapter != chapter_name:
            st.session_state.quiz_submitted = False
            st.session_state.calculated_score = 0
            st.session_state.submitted_chapter = ""
            st.session_state.saved_user_answers = {}
            st.session_state.current_loaded_chapter = chapter_name

        if today_questions:
            st.subheader(f"📖 جاهز لمسابقة اليوم؟ إصحاح: ({chapter_name}) ✨")
            
            if "quiz_submitted" not in st.session_state:
                st.session_state.quiz_submitted = False
            if "calculated_score" not in st.session_state:
                st.session_state.calculated_score = 0
            if "submitted_chapter" not in st.session_state:
                st.session_state.submitted_chapter = ""
            if "saved_user_answers" not in st.session_state:
                st.session_state.saved_user_answers = {}

            st.markdown("### 📖 أسئلة إصحاح اليوم:")
            user_answers = {}
            for i, q in enumerate(today_questions):
                is_disabled = st.session_state.quiz_submitted and st.session_state.submitted_chapter == chapter_name
                user_answers[i] = st.radio(q["question"], q["options"], index=None, key=f"q_{i}", disabled=is_disabled)
                st.write("")
                
            st.write("---")
            
            # 3️⃣ ثالثاً: زر الإرسال وحساب النتيجة
            if not (st.session_state.quiz_submitted and st.session_state.submitted_chapter == chapter_name):
                if st.button("🚀 إرسال الإجابات وعرض الدرجة", type="primary"):
                    if None in user_answers.values():
                        st.error("⚠️ فيه أسئلة لسه محلتهاش، جاوب على كل الأسئلة الأول!")
                    else:
                        if check_if_already_solved_postgres(student_name, chapter_name):
                            st.error(f"🚨 يا {student_name}، إنت حليت مسابقة ({chapter_name}) قبل كده! مسموح بمرة واحدة بس.")
                        else:
                            score = 0
                            total_questions = len(today_questions)
                            temp_answers = {}
                            history_parts = []
                            
                            for i, q in enumerate(today_questions):
                                chosen = str(user_answers[i]).strip()
                                correct_ans = q["answer"]
                                temp_answers[i] = chosen
                                
                                if chosen == correct_ans:
                                    history_parts.append(f"س{i+1}: {chosen} (صح ✅)")
                                    score += 1
                                else:
                                    history_parts.append(f"س{i+1}: {chosen} [والصح ❌: {correct_ans}]")

                            final_history_string = " | ".join(history_parts)
                            
                            st.session_state.quiz_submitted = True
                            st.session_state.calculated_score = score
                            st.session_state.submitted_chapter = chapter_name
                            st.session_state.saved_user_answers = temp_answers
                            
                            save_result_to_postgres(student_name, student_group, student_mobile, chapter_name, score, total_questions, final_history_string)
                            st.rerun()
                            
            if st.session_state.quiz_submitted and st.session_state.submitted_chapter == chapter_name:
                total_questions = len(today_questions)
                st.success(f"🎉 ممتاز يا {student_name}! تم حفظ إجاباتك بنجاح في قاعدة البيانات أونلاين.")
                st.metric(label="درجتك النهائية هي:", value=f"{st.session_state.calculated_score}from {total_questions}")
                if st.session_state.calculated_score == total_questions:
                    st.balloons()
                    
                st.write("---")
                st.markdown("### 📋 نموذج تصحيح إجاباتك ومراجعة الآيات:")
                
                for i, q in enumerate(today_questions):
                    student_ans = st.session_state.saved_user_answers.get(i, "")
                    correct_ans = q["answer"]
                    
                    with st.container():
                        st.markdown(f"**{q['question']}**")
                        if student_ans == correct_ans:
                            st.markdown(f"🟢 **إجابتك:** {student_ans} (صح برافو عليك! ✅)")
                        else:
                            st.markdown(f"🔴 **إجابتك:** {student_ans} (غلط للاسف ❌)")
                            st.markdown(f"🔵 **الإجابة الصحيحة هي:** `{correct_ans}`")
                        st.write("")
        else:
            st.subheader("✨ مفيش مسابقة متوفرة للنهاردة لثانية إعدادي، ارجع بكرة يا بطل! ✨")

# 4️⃣ رابعاً: لوحة تحكم الخادم (تعديل المسافات البادئة بالكامل)
st.write("---")
with st.expander("🔐 لوحة تحكم الخادم (خاص بالخدام فقط)"):
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        admin_user = st.text_input("اسم المستخدم (Username):", key="admin_user_input")
        admin_pass = st.text_input("كلمة السر (Password):", type="password", key="admin_pass_input")
        if st.button("🔓 تسجيل الدخول"):
            if admin_user == "admin" and admin_pass == "P@ssw0rd_123654":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة السر غير صحيحة!")
    else:
        st.success("🔓 مرحباً يا غالي، تم تسجيل الدخول بنجاح!")
        if st.button("🔒 تسجيل الخروج", type="primary", key="logout_admin_btn"):
            st.session_state.admin_logged_in = False
            st.rerun()
            
        st.write("---")
        st.write("📊 الدرجات الحية مسحوبة مباشرة بنظام Postgres Connection أونلاين:")
        
        try:
            conn = psycopg2.connect(DB_CONN_STRING, client_encoding='utf8')
            cursor = conn.cursor()
            
            query = """
            SELECT 
                name AS "الاسم", 
                group_name AS "المرحلة", 
                chapter AS "الإصحاح", 
                score AS "الدرجة", 
                user_history AS "تفاصيل الإجابات [الموبايل والولد والصح]",
                to_char(created_at + interval '2 hours', 'YYYY-MM-DD HH24:MI:SS') AS "تاريخ ووقت التسجيل" 
            FROM kpis_bible_study 
            ORDER BY created_at DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            colnames = [desc.name for desc in cursor.description]
            
            cursor.close()
            conn.close()
            
            df_display = pd.DataFrame(rows, columns=colnames)
            
            if not df_display.empty:
                st.dataframe(df_display, width="stretch")
                
                st.download_button(
                    label="📥 تحميل شيت الدرجات كـ Excel",
                    data=df_display.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"bible_results_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                    key="download_btn_postgres_final_v11"
                )
            else:
                st.info("قاعدة البيانات فاضية لسه، مفيش أي طالب حل المسابقة لغاية دلوقتي.")
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال المباشر بـ Postgres: {e}")
