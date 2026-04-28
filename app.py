# -*- coding: utf-8 -*-
import streamlit as st
import json
import re
import pandas as pd
import google.generativeai as genai
from supabase import create_client, Client

# ================== اپنی کیز (Streamlit Secrets سے) ==================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
ADMIN_SECRET = st.secrets.get("ADMIN_SECRET", "admin123")  # ایڈمن پاسورڈ، ڈیفالٹ admin123

# ================== کلائینٹس تیار ==================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_LIST = ["gemini-2.5-flash"]

# ================== مددگار فنکشنز ==================
def call_generative_model(prompt):
    """ماڈل کی فہرست میں سے پہلے قابلِ استعمال ماڈل کو آزما کر جواب لوٹائے۔"""
    last_exception = None
    for model_name in MODEL_LIST:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_exception = e
            if "429" in str(e) or "quota" in str(e).lower() or "not found" in str(e).lower() or "404" in str(e):
                continue
            else:
                raise e
    raise Exception(f"کوئی بھی ماڈل دستیاب نہیں۔ آخری خرابی: {last_exception}")

def safe_extract_json(text):
    if not text:
        raise ValueError("AI نے کوئی جواب نہیں دیا۔ شاید کوٹہ ختم ہو گیا۔")
    if "```json" in text:
        parts = text.split("```json")
        if len(parts) > 1:
            after = parts[1].split("```")
            if after:
                text = after[0].strip()
    if not text.startswith("{"):
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        else:
            raise ValueError(f"جواب میں JSON نہیں ملا۔ پہلے 200 حروف: {text[:200]}")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"AI نے ناقص JSON بھیجا۔ پہلے 200 حروف: {text[:200]}")

def extract_dna(title, description):
    prompt = f"""
آپ کو ایک خیال دیا گیا ہے۔ اس خیال کا "ڈی این اے" نکال کر صرف JSON فارمیٹ میں واپس کریں۔
کوئی اور وضاحت نہ لکھیں۔
JSON میں یہ فیلڈز ہونی چاہئیں:
- tags: [list] (تین سے پانچ اردو کلیدی الفاظ)
- intent: string (مقصد، جیسے "مسئلہ حل کرنا"، "تفریح"، "تعلیم")
- domains: [list] (شعبے، جیسے ["صحت", "ٹیکنالوجی"])
- emotional_tone: string (جذباتی لہجہ، جیسے "پرجوش", "غمگین", "باغیانہ")
- complexity: عدد (1 سے 10)

خیال کا عنوان: {title}
تفصیل: {description}
"""
    response_text = call_generative_model(prompt)
    return safe_extract_json(response_text)

def mutate_dna(original_dna, change):
    prompt = f"""
ایک خیال کا DNA (JSON) درج ذیل ہے:
{json.dumps(original_dna, ensure_ascii=False)}

برائے مہربانی اس DNA میں یہ تبدیلی کریں: {change}
صرف ترمیم شدہ JSON واپس کریں، بغیر کسی وضاحت کے۔
"""
    response_text = call_generative_model(prompt)
    return safe_extract_json(response_text)

def merge_dna(dna1, dna2):
    prompt = f"""
دو خیالات کے DNA (JSON):
خیال 1: {json.dumps(dna1, ensure_ascii=False)}
خیال 2: {json.dumps(dna2, ensure_ascii=False)}

ان دونوں کو یکجا کر کے ایک نیا ہائبرڈ خیال بنائیں، اور اس کا DNA JSON میں واپس کریں۔
"""
    response_text = call_generative_model(prompt)
    return safe_extract_json(response_text)

def generate_content(title, description, dna_json):
    prompt = f"""
نیچے دیئے گئے خیال کے عنوان، تفصیل اور DNA کی بنیاد پر ایک تخلیقی مواد (کہانی، مضمون، نظم، یا کاروباری تجویز) اردو میں تحریر کریں۔
خیال کا عنوان: {title}
تفصیل: {description}
DNA: {json.dumps(dna_json, ensure_ascii=False)}

صرف مواد لکھیں، کوئی اضافی وضاحت یا عنوان نہ دیں۔
"""
    return call_generative_model(prompt)

# ================== Streamlit UI ==================
st.set_page_config(page_title="آئیڈیا ایوولوشن انجن", layout="wide")

# ✨ ہیڈر (Layyah Jobs کے بٹن کے ساتھ)
st.markdown("""
<div style="text-align:center; padding:20px; background:linear-gradient(135deg, #1a0a0a, #b30047); border-radius:20px; border:1px solid #ff9f43; margin-bottom:20px;">
    <h1 style="color:#f0d9d9;">🧬 آئیڈیا ایوولوشن انجن</h1>
    <p style="color:#ff9f43;">خیال زندہ ہے — اسے ارتقا دیں</p>
    <a href="https://layyahjobs.streamlit.app/" target="_blank" 
       style="display:inline-block; margin-top:12px; background:gold; color:#1a0a0a; 
              padding:10px 30px; border-radius:50px; text-decoration:none; 
              font-weight:bold; font-size:18px; box-shadow:0 0 10px gold;">
       💼 Layyah Jobs 💼
    </a>
</div>
""", unsafe_allow_html=True)

# سائڈبار
with st.sidebar:
    menu_options = ["نیا خیال بوئیں", "تمام خیالات", "میوٹیشن / ادغام"]
    admin_input = st.text_input("ایڈمن سیکرٹ", type="password")
    if admin_input == ADMIN_SECRET:
        menu_options.append("👑 ایڈمن")
    menu = st.radio("نیویگیشن", menu_options)

# ================== صفحات ==================
if menu == "نیا خیال بوئیں":
    st.header("🌱 تخم ریزی")
    with st.form("seed_form"):
        title = st.text_input("عنوان")
        desc = st.text_area("تفصیل")
        submitted = st.form_submit_button("بیج بوئیں")
        if submitted:
            if title.strip() == "":
                st.error("عنوان لازمی ہے")
            else:
                with st.spinner("🧠 AI ڈی این اے نکال رہا ہے..."):
                    try:
                        dna = extract_dna(title, desc)
                        data = {
                            "title": title,
                            "description": desc,
                            "dna_json": json.dumps(dna, ensure_ascii=False),
                            "fitness_score": 0
                        }
                        supabase.table("ideas").insert(data).execute()
                        st.success("آپ کا خیال تخم ہوگیا!")
                        st.json(dna)
                    except Exception as e:
                        st.error(f"خرابی: {e}")

elif menu == "تمام خیالات":
    st.header("🌟 آئیڈیا کائنات")
    try:
        res = supabase.table("ideas").select("*").order("fitness_score", desc=True).execute()
        ideas = res.data if res.data else []
        if not ideas:
            st.info("ابھی کوئی خیال نہیں")
        else:
            for idea in ideas:
                with st.expander(f"{idea['title']} (فٹنس: {idea['fitness_score']})"):
                    st.write("تفصیل:", idea.get('description'))
                    if idea.get('dna_json'):
                        dna = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']
                        st.json(dna)
                    if idea.get('generated_content'):
                        st.markdown("### 🤖 AI کا تخلیق کردہ مواد")
                        st.write(idea['generated_content'])

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"❤️ پسند ##{idea['id']}", key=f"like_{idea['id']}"):
                            supabase.table("ideas").update({"fitness_score": idea['fitness_score'] + 1}).eq("id", idea['id']).execute()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ حذف ##{idea['id']}", key=f"delete_{idea['id']}"):
                            # پہلے بچوں کا parent_id NULL کریں
                            supabase.table("ideas").update({"parent_id": None}).eq("parent_id", idea['id']).execute()
                            supabase.table("mutations").delete().eq("original_idea_id", idea['id']).execute()
                            supabase.table("mutations").delete().eq("mutated_idea_id", idea['id']).execute()
                            supabase.table("ideas").delete().eq("id", idea['id']).execute()
                            st.success("خیال حذف ہوگیا!")
                            st.rerun()
                    with col3:
                        if st.button(f"🧠 AI مواد ##{idea['id']}", key=f"gen_{idea['id']}"):
                            with st.spinner("AI لکھ رہا ہے..."):
                                try:
                                    dna_obj = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']
                                    content = generate_content(idea['title'], idea['description'], dna_obj)
                                    supabase.table("ideas").update({"generated_content": content}).eq("id", idea['id']).execute()
                                    st.success("مواد تیار ہوگیا! اسے دیکھنے کے لیے دوبارہ کھولیں۔")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"مواد تخلیق کرتے وقت خرابی: {e}")
    except Exception as e:
        st.error(f"ڈیٹا لوڈ کرنے میں خرابی: {e}")

elif menu == "میوٹیشن / ادغام":
    st.header("🧬 ارتقا کے اوزار")
    operation = st.radio("عمل منتخب کریں", ["میوٹیشن (تبدیلی)", "دو خیالات کا ادغام"])

    if operation == "میوٹیشن (تبدیلی)":
        st.subheader("کسی ایک خیال میں تبدیلی کریں")
        res = supabase.table("ideas").select("id,title,dna_json").execute()
        ideas = res.data if res.data else []
        if ideas:
            idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
            selected = st.selectbox("خیال چنیں", list(idea_options.keys()))
            change = st.text_input("کیا تبدیلی کرنی ہے؟", "emotional_tone کو 'پرجوش' کر دیں")
            if st.button("میوٹیشن کریں"):
                with st.spinner("🧬 میوٹیشن ہو رہی ہے..."):
                    try:
                        original = idea_options[selected]
                        original_dna = json.loads(original['dna_json']) if isinstance(original['dna_json'], str) else original['dna_json']
                        new_dna = mutate_dna(original_dna, change)
                        new_title = original['title'] + " (میوٹیشن)"
                        new_data = {
                            "title": new_title,
                            "description": f"تبدیلی: {change}",
                            "dna_json": json.dumps(new_dna, ensure_ascii=False),
                            "parent_id": original['id'],
                            "fitness_score": 0
                        }
                        result = supabase.table("ideas").insert(new_data).execute()
                        supabase.table("mutations").insert({
                            "original_idea_id": original['id'],
                            "mutated_idea_id": result.data[0]['id'],
                            "change_description": change
                        }).execute()
                        st.success("میوٹیشن کامیاب، نیا خیال بن گیا!")
                        st.json(new_dna)
                    except Exception as e:
                        st.error(f"خرابی: {e}")
        else:
            st.warning("پہلے کوئی خیال بوئیں")

    else:
        st.subheader("دو خیالات کو یکجا کریں")
        res = supabase.table("ideas").select("id,title,dna_json").execute()
        ideas = res.data if res.data else []
        if len(ideas) >= 2:
            idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
            col1, col2 = st.columns(2)
            with col1:
                sel1 = st.selectbox("پہلا خیال", list(idea_options.keys()), key="s1")
            with col2:
                sel2 = st.selectbox("دوسرا خیال", list(idea_options.keys()), key="s2")
            if st.button("ادغام کریں"):
                if sel1 == sel2:
                    st.error("ایک ہی خیال نہیں چلے گا")
                else:
                    with st.spinner("🧬 ہائبرڈ بن رہا ہے..."):
                        try:
                            dna1 = idea_options[sel1]['dna_json']
                            dna2 = idea_options[sel2]['dna_json']
                            if isinstance(dna1, str): dna1 = json.loads(dna1)
                            if isinstance(dna2, str): dna2 = json.loads(dna2)
                            merged = merge_dna(dna1, dna2)
                            new_title = f"{idea_options[sel1]['title']} + {idea_options[sel2]['title']} (ہائبرڈ)"
                            new_data = {
                                "title": new_title,
                                "description": "دو خیالات کا امتزاج",
                                "dna_json": json.dumps(merged, ensure_ascii=False),
                                "fitness_score": 0
                            }
                            supabase.table("ideas").insert(new_data).execute()
                            st.success("ہائبرڈ خیال پیدا ہوگیا!")
                            st.json(merged)
                        except Exception as e:
                            st.error(f"خرابی: {e}")
        else:
            st.warning("ادغام کے لیے کم از کم دو خیالات چاہیں")

elif menu == "👑 ایڈمن":
    if admin_input != ADMIN_SECRET:
        st.error("ایڈمن سیکرٹ درکار ہے")
        st.stop()
    st.success("👑 ایڈمن پینل")
    tab1, tab2 = st.tabs(["📥 ایکسپورٹ خیالات", "📤 امپورٹ خیالات"])

    with tab1:
        st.subheader("تمام خیالات CSV میں ڈاؤن لوڈ کریں")
        try:
            res = supabase.table("ideas").select("*").order("created_at", desc=True).execute()
            ideas = res.data if res.data else []
            if ideas:
                df = pd.DataFrame(ideas)
                # مفید کالم منتخب کریں (id سمیت)
                export_cols = ["id", "title", "description", "dna_json", "parent_id", "fitness_score", "created_at"]
                df_export = df[[col for col in export_cols if col in df.columns]]
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 ڈاؤن لوڈ CSV",
                    data=csv,
                    file_name="ideas_backup.csv",
                    mime="text/csv"
                )
            else:
                st.info("کوئی خیال نہیں۔")
        except Exception as e:
            st.error(f"ایکسپورٹ میں خرابی: {e}")

    with tab2:
        st.subheader("CSV سے خیالات واپس لائیں")
        st.caption("CSV میں کم از کم `title` کالم ضروری ہے۔ `dna_json` کالم (JSON فارمیٹ) موجود ہو تو استعمال ہوگا، ورنہ خالی DNA لگے گا۔")
        uploaded_file = st.file_uploader("CSV فائل منتخب کریں", type="csv")
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file)
                import_df.columns = [str(col).strip().lower() for col in import_df.columns]
                if 'title' not in import_df.columns:
                    st.error("CSV میں `title` کالم ضروری ہے۔")
                else:
                    if st.button("📤 امپورٹ شروع کریں"):
                        imported = 0
                        skipped = 0
                        for _, row in import_df.iterrows():
                            title = str(row['title']).strip()
                            if not title:
                                skipped += 1
                                continue
                            desc = str(row.get('description', '')).strip()
                            dna_raw = row.get('dna_json', None)
                            # DNA JSON نکالنے کی کوشش
                            try:
                                if dna_raw and isinstance(dna_raw, str):
                                    dna_obj = json.loads(dna_raw)
                                elif dna_raw and not isinstance(dna_raw, str):
                                    dna_obj = dna_raw  # پہلے سے dict
                                else:
                                    dna_obj = {"tags":[], "intent":"", "domains":[], "emotional_tone":"", "complexity":1}
                            except:
                                dna_obj = {"tags":[], "intent":"", "domains":[], "emotional_tone":"", "complexity":1}
                            parent_id = row.get('parent_id', None)
                            fitness = row.get('fitness_score', 0)
                            try:
                                data = {
                                    "title": title,
                                    "description": desc,
                                    "dna_json": json.dumps(dna_obj, ensure_ascii=False),
                                    "parent_id": int(parent_id) if parent_id and str(parent_id).isdigit() else None,
                                    "fitness_score": float(fitness) if fitness else 0
                                }
                                supabase.table("ideas").insert(data).execute()
                                imported += 1
                            except:
                                skipped += 1
                        st.success(f"✅ {imported} خیالات امپورٹ ہوگئے۔ ⏭️ {skipped} چھوڑ دیے گئے۔")
                        st.rerun()
            except Exception as e:
                st.error(f"فائل پڑھنے میں خرابی: {e}")

st.sidebar.markdown("---")
st.sidebar.info("یہ ایک زندہ تخلیقی مشین ہے — خیالات مر سکتے ہیں، بڑھ سکتے ہیں اور یکجا ہو سکتے ہیں۔")
