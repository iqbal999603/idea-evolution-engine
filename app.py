# -*- coding: utf-8 -*-
import streamlit as st
import json
import re
import pandas as pd
from io import StringIO
import google.generativeai as genai
from supabase import create_client, Client

# ================== اپنی کیز (Streamlit Secrets سے) ==================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
ADMIN_SECRET = st.secrets.get("ADMIN_SECRET", "admin123")  # ایڈمن پینل کے لیے خفیہ لفظ

# ================== کلائینٹس تیار ==================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_LIST = ["gemini-2.5-flash"]

# ================== مددگار فنکشنز (وہی جو پہلے تھے) ==================
def call_generative_model(prompt):
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
        raise ValueError("AI نے کوئی جواب نہیں دیا۔")
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
    prompt = f"""..."""  # وہی پرانا پرامپٹ
    response_text = call_generative_model(prompt)
    return safe_extract_json(response_text)

def mutate_dna(original_dna, change):
    prompt = f"""..."""  # وہی
    response_text = call_generative_model(prompt)
    return safe_extract_json(response_text)

def merge_dna(dna1, dna2):
    prompt = f"""..."""  # وہی
    response_text = call_generative_model(prompt)
    return safe_extract_json(response_text)

def generate_content(title, description, dna_json):
    prompt = f"""..."""  # وہی
    return call_generative_model(prompt)

# ================== Streamlit UI ==================
st.set_page_config(page_title="آئیڈیا ایوولوشن انجن", layout="wide")

# ہیڈر (پہلے سے موجود)
st.markdown("""...""")  # وہی سنہری بٹن والا ہیڈر

# سائڈبار
with st.sidebar:
    menu_options = ["نیا خیال بوئیں", "تمام خیالات", "میوٹیشن / ادغام"]
    admin_input = st.text_input("ایڈمن سیکرٹ", type="password")
    if admin_input == ADMIN_SECRET:
        menu_options.append("👑 ایڈمن")
    menu = st.radio("نیویگیشن", menu_options)

# --------------------- صفحات (وہی) ---------------------
if menu == "نیا خیال بوئیں":
    # ... (پہلے جیسا)
elif menu == "تمام خیالات":
    # ... (پہلے جیسا)
elif menu == "میوٹیشن / ادغام":
    # ... (پہلے جیسا)

# --------------------- نیا ایڈمن پینل ---------------------
elif menu == "👑 ایڈمن":
    if admin_input != ADMIN_SECRET:
        st.error("ایڈمن سیکرٹ درکار ہے")
        st.stop()
    st.success("👑 ایڈمن پینل")
    tab1, tab2 = st.tabs(["📥 ایکسپورٹ خیالات", "📤 امپورٹ خیالات"])

    # ---- ایکسپورٹ ----
    with tab1:
        st.subheader("تمام خیالات CSV میں ڈاؤن لوڈ کریں")
        try:
            res = supabase.table("ideas").select("*").order("created_at", desc=True).execute()
            ideas = res.data if res.data else []
            if ideas:
                df = pd.DataFrame(ideas)
                # کالم منتخب کریں (id چھوڑ سکتے ہیں)
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

    # ---- امپورٹ ----
    with tab2:
        st.subheader("CSV سے خیالات واپس لائیں")
        st.caption("CSV میں کم از کم `title` کالم ضروری ہے۔ `dna_json` کالم (JSON فارمیٹ) موجود ہو تو استعمال ہوگا، ورنہ خالی DNA لگے گا۔")
        uploaded_file = st.file_uploader("CSV فائل منتخب کریں", type="csv")
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file)
                import_df.columns = [str(col).strip().lower() for col in import_df.columns]
                if 'title' not in import_df.columns:
                    st.error("CSV میں title کالم ضروری ہے۔")
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
                            # DNA JSON کو پارس کرنے کی کوشش
                            try:
                                if dna_raw and isinstance(dna_raw, str):
                                    dna_obj = json.loads(dna_raw)
                                elif dna_raw and not isinstance(dna_raw, str):
                                    dna_obj = dna_raw  # اگر پہلے سے dict
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
                            except Exception as e:
                                skipped += 1
                        st.success(f"✅ {imported} خیالات امپورٹ ہوگئے۔ ⏭️ {skipped} چھوڑ دیے گئے۔")
                        st.rerun()
            except Exception as e:
                st.error(f"فائل پڑھنے میں خرابی: {e}")

# (سائڈبار کا اختتامی پیغام)
