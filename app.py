# -*- coding: utf-8 -*-
import streamlit as st
import json
import re
import google.generativeai as genai
from supabase import create_client, Client

# ================== اپنی کیز (Streamlit Secrets سے) ==================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# ================== کلائینٹس تیار ==================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")   # مستحکم ماڈل، اگر ضرورت ہو تو بدل لیں

# ================== مددگار فنکشن: AI کے جواب سے JSON نکالنا ==================
def safe_extract_json(text):
    """AI کے جواب سے خالص JSON نکالیں، چاہے جواب میں اضافی بات چیت ہی کیوں نہ ہو۔"""
    if not text:
        raise ValueError("AI نے کوئی جواب نہیں دیا۔")
    # اگر جواب ```json ... ``` میں لپٹا ہے تو اسے نکالیں
    if "```json" in text:
        parts = text.split("```json")
        if len(parts) > 1:
            after = parts[1].split("```")
            if after:
                text = after[0].strip()
    # اگر تب بھی براہِ راست JSON نہ ہو تو پہلا { سے لے کر آخری } تک نکالیں
    if not text.startswith("{"):
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        else:
            raise ValueError(f"جواب میں JSON نہیں ملا۔ پہلے 200 حروف: {text[:200]}")
    # اب صاف JSON کو پارس کریں
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"AI نے ناقص JSON بھیجا۔ پہلے 200 حروف: {text[:200]}")

# ================== فنکشن: ڈی این اے نکالنا ==================
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
    response = model.generate_content(prompt)
    return safe_extract_json(response.text)

# ================== فنکشن: میوٹیشن ==================
def mutate_dna(original_dna, change):
    prompt = f"""
ایک خیال کا DNA (JSON) درج ذیل ہے:
{json.dumps(original_dna, ensure_ascii=False)}

برائے مہربانی اس DNA میں یہ تبدیلی کریں: {change}
صرف ترمیم شدہ JSON واپس کریں، بغیر کسی وضاحت کے۔
"""
    response = model.generate_content(prompt)
    return safe_extract_json(response.text)

# ================== فنکشن: دو خیالات کا ادغام ==================
def merge_dna(dna1, dna2):
    prompt = f"""
دو خیالات کے DNA (JSON):
خیال 1: {json.dumps(dna1, ensure_ascii=False)}
خیال 2: {json.dumps(dna2, ensure_ascii=False)}

ان دونوں کو یکجا کر کے ایک نیا ہائبرڈ خیال بنائیں، اور اس کا DNA JSON میں واپس کریں۔
"""
    response = model.generate_content(prompt)
    return safe_extract_json(response.text)

# ================== Streamlit UI ==================
st.set_page_config(page_title="آئیڈیا ایوولوشن انجن", layout="wide")
st.title("🧬 آئیڈیا ایوولوشن انجن")
st.markdown("### خیال زندہ ہے — اسے ارتقا دیں")

menu = st.sidebar.radio("نیویگیشن", ["نیا خیال بوئیں", "تمام خیالات", "میوٹیشن / ادغام"])

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
                        data = {"title": title, "description": desc, "dna_json": json.dumps(dna, ensure_ascii=False), "fitness_score": 0}
                        result = supabase.table("ideas").insert(data).execute()
                        st.success("آپ کا خیال تخم ہوگیا!")
                        st.json(dna)
                    except Exception as e:
                        st.error(f"خرابی: {e}")

elif menu == "تمام خیالات":
    st.header("🌟 آئیڈیا کائنات")
    try:
        res = supabase.table("ideas").select("*").order("fitness_score", desc=True).execute()
        ideas = res.data
        if not ideas:
            st.info("ابھی کوئی خیال نہیں")
        else:
            for idea in ideas:
                with st.expander(f"{idea['title']} (فٹنس: {idea['fitness_score']})"):
                    st.write("تفصیل:", idea.get('description'))
                    if idea.get('dna_json'):
                        dna = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']
                        st.json(dna)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"❤️ پسند ##{idea['id']}", key=f"like_{idea['id']}"):
                            supabase.table("ideas").update({"fitness_score": idea['fitness_score'] + 1}).eq("id", idea['id']).execute()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ حذف ##{idea['id']}", key=f"delete_{idea['id']}"):
                            # متعلقہ میوٹیشنز ڈیلیٹ کریں
                            supabase.table("mutations").delete().eq("original_idea_id", idea['id']).execute()
                            supabase.table("mutations").delete().eq("mutated_idea_id", idea['id']).execute()
                            supabase.table("ideas").delete().eq("id", idea['id']).execute()
                            st.success("خیال حذف ہوگیا!")
                            st.rerun()
    except Exception as e:
        st.error(f"ڈیٹا لوڈ کرنے میں خرابی: {e}")

elif menu == "میوٹیشن / ادغام":
    st.header("🧬 ارتقا کے اوزار")
    operation = st.radio("عمل منتخب کریں", ["میوٹیشن (تبدیلی)", "دو خیالات کا ادغام"])

    if operation == "میوٹیشن (تبدیلی)":
        st.subheader("کسی ایک خیال میں تبدیلی کریں")
        res = supabase.table("ideas").select("id,title,dna_json").execute()
        ideas = res.data
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
        ideas = res.data
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
                            result = supabase.table("ideas").insert(new_data).execute()
                            st.success("ہائبرڈ خیال پیدا ہوگیا!")
                            st.json(merged)
                        except Exception as e:
                            st.error(f"خرابی: {e}")
        else:
            st.warning("ادغام کے لیے کم از کم دو خیالات چاہیں")

st.sidebar.markdown("---")
st.sidebar.info("یہ ایک زندہ تخلیقی مشین ہے — خیالات مر سکتے ہیں، بڑھ سکتے ہیں اور یکجا ہو سکتے ہیں۔")
