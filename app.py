# -*- coding: utf-8 -*-
import streamlit as st
import json
import re
import pandas as pd
import google.generativeai as genai
from supabase import create_client, Client

# ================== Secrets ==================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
ADMIN_SECRET = st.secrets.get("ADMIN_SECRET", "admin123")

# ================== Clients ==================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_LIST = ["gemini-2.5-flash"]

# ================== Helper Functions ==================
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
    raise Exception(f"No model available. Last error: {last_exception}")

def safe_extract_json(text):
    if not text:
        raise ValueError("AI returned empty.")
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
            raise ValueError(f"No JSON found. First 200 chars: {text[:200]}")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Bad JSON. First 200 chars: {text[:200]}")

# ================== Core DNA Functions ==================
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

def generate_content(title, description, dna_json, human_tone=False):
    prompt = f"""
نیچے دیئے گئے خیال کے عنوان، تفصیل اور DNA کی بنیاد پر ایک تخلیقی مواد (کہانی، مضمون، نظم، یا کاروباری تجویز) اردو میں تحریر کریں۔
خیال کا عنوان: {title}
تفصیل: {description}
DNA: {json.dumps(dna_json, ensure_ascii=False)}

صرف مواد لکھیں، کوئی اضافی وضاحت یا عنوان نہ دیں۔
"""
    if human_tone:
        prompt += "\nبراہ کرم ایک عام انسان جیسا سادہ اور دوستانہ لہجہ استعمال کریں۔"
    return call_generative_model(prompt)

# ================== New Feature Functions ==================
def suggest_mutations(dna):
    prompt = f"""
ایک خیال کا DNA (JSON) درج ذیل ہے:
{json.dumps(dna, ensure_ascii=False)}

برائے مہربانی اس خیال میں 5 ممکنہ تبدیلیاں (میوٹیشنز) تجویز کریں۔
ہر تجویز ایک مختصر جملے میں ہو، اور نئی تجاویز اصل تخلیقیت کو بڑھانے والی ہوں۔
فہرست واپس کریں۔
"""
    response = call_generative_model(prompt)
    return response.strip()

def random_idea():
    prompt = """
ایک بالکل نیا، منفرد اور دلچسپ کاروباری یا سماجی آئیڈیا پیش کریں۔
JSON فارمیٹ میں واپس کریں:
{
  "title": "عنوان",
  "description": "مختصر تفصیل",
  "dna": { "tags": [...], "intent": "...", "domains": [...], "emotional_tone": "...", "complexity": عدد }
}
"""
    resp = call_generative_model(prompt)
    return safe_extract_json(resp)

def survival_simulation(idea_title, idea_desc, dna):
    prompt = f"""
ایک کاروباری آئیڈیا کے زندہ رہنے کی ممکنہ صورتحال کا 5 سالہ جائزہ پیش کریں۔
خیال کا عنوان: {idea_title}
تفصیل: {idea_desc}
DNA: {json.dumps(dna, ensure_ascii=False)}

ہر سال کے لیے اہم واقعات، چیلنجز، کامیابیاں اور آخری نتیجہ لکھیں۔ کہانی کی شکل میں لکھیں۔
"""
    return call_generative_model(prompt)

def ethics_check(idea_title, idea_desc, dna):
    prompt = f"""
مندرجہ ذیل خیال کے اخلاقی پہلوؤں کا تجزیہ کریں:
خیال: {idea_title}
تفصیل: {idea_desc}
DNA: {json.dumps(dna, ensure_ascii=False)}

ممکنہ خطرات، سماجی اثرات، رازداری کے مسائل، اور بہتری کی تجاویز دیں۔
"""
    return call_generative_model(prompt)

def popularity_contest(idea_title, idea_desc, dna):
    prompt = f"""
فرض کریں کہ 100 افراد اس خیال کو دیکھتے ہیں۔
خیال: {idea_title}
تفصیل: {idea_desc}

ان میں سے کتنے لوگ اسے پسند کریں گے، کتنے ناپسند، اور کتنے غیر جانبدار رہیں گے؟
مختلف اقسام کے لوگوں کے تبصرے بھی لکھیں۔ ایک مختصر پول نتیجہ پیش کریں۔
"""
    return call_generative_model(prompt)

def plagiarism_check(idea_title, idea_desc, dna):
    prompt = f"""
اس خیال کی انفرادیت کا جائزہ لیں:
خیال: {idea_title}
تفصیل: {idea_desc}
DNA: {json.dumps(dna, ensure_ascii=False)}

کیا یہ خیال اصلی ہے؟ کن پہلوؤں میں یہ دوسرے موجودہ خیالات سے مختلف ہے؟
ایک originality score (0-100%) دیں اور مختصر وضاحت کریں۔
"""
    return call_generative_model(prompt)

def collaborative_session(idea_title, idea_desc, dna):
    prompt = f"""
پانچ فرضی ماہرین (ایک انجینئر، ایک مارکیٹر، ایک اخلاقیات کا پروفیسر، ایک سرمایہ کار، اور ایک ڈیزائنر) اس خیال پر بحث کر رہے ہیں:
خیال: {idea_title}
تفصیل: {idea_desc}
DNA: {json.dumps(dna, ensure_ascii=False)}

ہر ماہر اپنی رائے، خدشات، اور بہتری کی تجاویز پیش کرتا ہے۔ یہ بحث ڈرامائی اور معلوماتی انداز میں لکھیں۔
"""
    return call_generative_model(prompt)

def daily_challenge():
    prompt = """
ایک تخلیقی سوچ بڑھانے والا مختصر چیلنج پیش کریں۔
یہ چیلنج AI، کاروبار، یا سماجی مسائل سے متعلق ہو سکتا ہے۔
ایک جملے میں مسئلہ یا کام بیان کریں، اور ساتھ میں اشارہ دیں کہ اسے کیسے حل کیا جا سکتا ہے۔
"""
    return call_generative_model(prompt)

def idea_mood_board(idea_title, idea_desc, dna):
    prompt = f"""
اس خیال کے لیے ایک بصری موڈ بورڈ تصور کریں:
خیال: {idea_title}
تفصیل: {idea_desc}
DNA: {json.dumps(dna, ensure_ascii=False)}

مندرجہ ذیل کی وضاحت کریں:
- رنگ پیلیٹ (3-4 رنگ)
- ٹائپوگرافی کا انداز
- تصاویر کی نوعیت (کیا دکھائی جائے)
- مجموعی جذباتی فضا
"""
    return call_generative_model(prompt)

def learning_path(idea_title, idea_desc, dna):
    prompt = f"""
اس خیال کو حقیقت میں بدلنے کے لیے ایک مرحلہ وار سیکھنے کا راستہ تجویز کریں۔
خیال: {idea_title}
تفصیل: {idea_desc}
DNA: {json.dumps(dna, ensure_ascii=False)}

مراحل:
1. ضروری مہارتیں
2. تجویز کردہ آن لائن کورسز
3. عملی مشقیں
4. پروٹوٹائپ ڈیولپمنٹ
5. لانچ پلان
"""
    return call_generative_model(prompt)

# ================== Database helpers ==================
def delete_all_ideas():
    # Delete all ideas to reset
    supabase.table("mutations").delete().neq("id", 0).execute()   # delete all mutations
    supabase.table("ideas").delete().neq("id", 0).execute()       # delete all ideas

# ================== Streamlit UI ==================
st.set_page_config(page_title="آئیڈیا ایوولوشن انجن", layout="wide")

# ---------- Header ----------
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

# ---------- Sidebar ----------
menu_list = [
    "🌱 نیا خیال + رینڈم",
    "🧪 میوٹیشن (تجاویز+ریورس)",
    "🔀 ادغام",
    "✍️ تخلیقی مواد",
    "🔬 تجزیہ سنٹر",
    "🎨 تخلیقی معاون",
    "📋 تمام خیالات",
    "📚 لرننگ پاتھ",
    "🔄 ری سیٹ",
    "⚙️ ایڈوانسڈ"
]

with st.sidebar:
    menu = st.radio("نیویگیشن", menu_list)
    # Admin secret for admin panel later if needed
    admin_input = st.text_input("ایڈمن سیکرٹ (Admin)", type="password")
    if admin_input == ADMIN_SECRET:
        st.success("ایڈمن موڈ فعال")

# ================== Page Routing ==================
if menu == "🌱 نیا خیال + رینڈم":
    st.header("🌱 نیا خیال بویں یا رینڈم لیں")
    col_form, col_btn = st.columns([3, 1])
    with col_form:
        with st.form("seed_form"):
            title = st.text_input("عنوان")
            desc = st.text_area("تفصیل")
            submitted = st.form_submit_button("بیج بوئیں")
    with col_btn:
        if st.button("🎲 رینڈم آئیڈیا"):
            with st.spinner("جنریٹ ہو رہا ہے..."):
                idea = random_idea()
                title = idea["title"]
                desc = idea["description"]
                # Auto-fill the fields (we need to set session state)
                st.session_state.random_title = title
                st.session_state.random_desc = desc
                st.rerun()
        # Use session state to fill form if random was clicked
        if "random_title" in st.session_state:
            title = st.session_state.random_title
            desc = st.session_state.random_desc

    if 'title' in locals() and 'desc' in locals():
        if st.button("اس آئیڈیا کو بوئیں"):
            with st.spinner("DNA نکال رہا ہے..."):
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
                    # Clear random state
                    for key in ["random_title", "random_desc"]:
                        if key in st.session_state:
                            del st.session_state[key]
                except Exception as e:
                    st.error(f"خرابی: {e}")

elif menu == "🧪 میوٹیشن (تجاویز+ریورس)":
    st.header("🧪 خیال میں تبدیلی کریں")
    res = supabase.table("ideas").select("id,title,dna_json").execute()
    ideas = res.data if res.data else []
    if not ideas:
        st.warning("پہلے کوئی خیال بوئیں")
    else:
        idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
        selected = st.selectbox("خیال چنیں", list(idea_options.keys()))
        original = idea_options[selected]
        original_dna = json.loads(original['dna_json']) if isinstance(original['dna_json'], str) else original['dna_json']

        # Suggestions
        if st.button("💡 میوٹیشن کی تجاویز دیکھیں"):
            with st.spinner("تجاویز لائی جا رہی ہیں..."):
                suggestions = suggest_mutations(original_dna)
                st.session_state.mutation_suggestions = suggestions
        if "mutation_suggestions" in st.session_state:
            st.markdown("### ممکنہ تبدیلیاں")
            st.write(st.session_state.mutation_suggestions)

        # Custom change
        change = st.text_input("اپنی تبدیلی لکھیں (یا تجاویز میں سے منتخب کریں)", 
                               value="emotional_tone کو 'پرجوش' کر دیں")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧪 میوٹیشن کریں"):
                with st.spinner("تبدیلی ہو رہی ہے..."):
                    try:
                        new_dna = mutate_dna(original_dna, change)
                        new_title = original['title'] + " (میوٹیشن)"
                        data = {
                            "title": new_title,
                            "description": f"تبدیلی: {change}",
                            "dna_json": json.dumps(new_dna, ensure_ascii=False),
                            "parent_id": original['id'],
                            "fitness_score": 0
                        }
                        result = supabase.table("ideas").insert(data).execute()
                        supabase.table("mutations").insert({
                            "original_idea_id": original['id'],
                            "mutated_idea_id": result.data[0]['id'],
                            "change_description": change
                        }).execute()
                        st.success("نیا خیال بن گیا!")
                        st.json(new_dna)
                    except Exception as e:
                        st.error(str(e))
        with col2:
            if st.button("🔄 ریورس (اُلٹ) میوٹیشن"):
                with st.spinner("اُلٹ خیال تیار ہو رہا ہے..."):
                    try:
                        # Reverse: just invert emotional tone? Better: call a custom reverse prompt
                        prompt = f"""
ایک خیال کا DNA (JSON) درج ذیل ہے:
{json.dumps(original_dna, ensure_ascii=False)}

اس خیال کا مکمل اُلٹ (opposite) خیال بنائیں۔ صرف تبدیل شدہ DNA JSON واپس کریں۔
"""
                        rev_text = call_generative_model(prompt)
                        rev_dna = safe_extract_json(rev_text)
                        rev_title = original['title'] + " (الٹ)"
                        data = {
                            "title": rev_title,
                            "description": f"اُلٹ خیال: {('تبدیلی: ' + change) if change else ''}",
                            "dna_json": json.dumps(rev_dna, ensure_ascii=False),
                            "parent_id": original['id'],
                            "fitness_score": 0
                        }
                        result = supabase.table("ideas").insert(data).execute()
                        st.success("اُلٹ خیال بن گیا!")
                        st.json(rev_dna)
                    except Exception as e:
                        st.error(str(e))

elif menu == "🔀 ادغام":
    st.header("🔀 دو خیالات کو یکجا کریں")
    res = supabase.table("ideas").select("id,title,dna_json").execute()
    ideas = res.data if res.data else []
    if len(ideas) < 2:
        st.warning("کم از کم دو خیالات چاہیں")
    else:
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
                with st.spinner("ہائبرڈ بن رہا ہے..."):
                    try:
                        i1 = idea_options[sel1]
                        i2 = idea_options[sel2]
                        dna1 = json.loads(i1['dna_json']) if isinstance(i1['dna_json'], str) else i1['dna_json']
                        dna2 = json.loads(i2['dna_json']) if isinstance(i2['dna_json'], str) else i2['dna_json']
                        merged = merge_dna(dna1, dna2)
                        new_title = f"{i1['title']} + {i2['title']} (ہائبرڈ)"
                        data = {
                            "title": new_title,
                            "description": "دو خیالات کا امتزاج",
                            "dna_json": json.dumps(merged, ensure_ascii=False),
                            "fitness_score": 0
                        }
                        supabase.table("ideas").insert(data).execute()
                        st.success("ہائبرڈ خیال پیدا ہوگیا!")
                        st.json(merged)
                    except Exception as e:
                        st.error(str(e))

elif menu == "✍️ تخلیقی مواد":
    st.header("✍️ تخلیقی مواد تیار کریں")
    res = supabase.table("ideas").select("id,title,description,dna_json").execute()
    ideas = res.data if res.data else []
    if not ideas:
        st.warning("کوئی خیال نہیں")
    else:
        idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
        selected = st.selectbox("خیال چنیں", list(idea_options.keys()))
        idea = idea_options[selected]
        content_type = st.selectbox("مواد کی قسم", ["بلاگ پوسٹ", "کہانی", "نظم", "کاروباری تجویز"])
        human_tone = st.checkbox("🧑 عام انسان جیسا لہجہ")
        if st.button("مواد تیار کریں"):
            with st.spinner("AI لکھ رہا ہے..."):
                dna = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']
                # Modify prompt based on content_type
                prompt = f"""
نیچے دیئے گئے خیال کے عنوان، تفصیل اور DNA کی بنیاد پر ایک {content_type} تحریر کریں۔ اردو میں۔
خیال کا عنوان: {idea['title']}
تفصیل: {idea['description']}
DNA: {json.dumps(dna, ensure_ascii=False)}
"""
                if human_tone:
                    prompt += "\nعام انسان جیسا سادہ اور دوستانہ لہجہ استعمال کریں۔"
                try:
                    content = call_generative_model(prompt)
                    st.markdown(content)
                except Exception as e:
                    st.error(str(e))

elif menu == "🔬 تجزیہ سنٹر":
    st.header("🔬 خیال کا تجزیہ")
    res = supabase.table("ideas").select("id,title,description,dna_json").execute()
    ideas = res.data if res.data else []
    if not ideas:
        st.warning("کوئی خیال نہیں")
    else:
        idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
        selected = st.selectbox("خیال چنیں", list(idea_options.keys()))
        idea = idea_options[selected]
        dna = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']

        tab1, tab2, tab3, tab4 = st.tabs(["🔮 سروائیول", "🧠 ایتھکس", "📈 مقبولیت", "🔍 پلیجیارزم"])

        with tab1:
            if st.button("دیکھیں یہ خیال زندہ رہے گا؟"):
                with st.spinner("تخمینہ لگایا جا رہا ہے..."):
                    sim = survival_simulation(idea['title'], idea['description'], dna)
                    st.markdown(sim)
        with tab2:
            if st.button("اخلاقی جائزہ"):
                with st.spinner("تجزیہ..."):
                    eth = ethics_check(idea['title'], idea['description'], dna)
                    st.markdown(eth)
        with tab3:
            if st.button("پول کروائیں"):
                with st.spinner("ووٹنگ ہو رہی ہے..."):
                    pop = popularity_contest(idea['title'], idea['description'], dna)
                    st.markdown(pop)
        with tab4:
            if st.button("انفرادیت چیک کریں"):
                with st.spinner("چیک ہو رہا ہے..."):
                    pl = plagiarism_check(idea['title'], idea['description'], dna)
                    st.markdown(pl)

elif menu == "🎨 تخلیقی معاون":
    st.header("🎨 تخلیقی معاون")
    res = supabase.table("ideas").select("id,title,description,dna_json").execute()
    ideas = res.data if res.data else []
    if not ideas:
        st.warning("کوئی خیال نہیں")
    else:
        idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
        selected = st.selectbox("خیال چنیں", list(idea_options.keys()))
        idea = idea_options[selected]
        dna = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']

        tab1, tab2, tab3 = st.tabs(["💬 ماہرین کی گفتگو", "📅 ڈیلی چیلنج", "🖼️ موڈ بورڈ"])

        with tab1:
            if st.button("گفتگو شروع کریں"):
                with st.spinner("ماہرین بحث کر رہے ہیں..."):
                    collab = collaborative_session(idea['title'], idea['description'], dna)
                    st.markdown(collab)
        with tab2:
            if st.button("آج کا چیلنج دکھائیں"):
                with st.spinner():
                    challenge = daily_challenge()
                    st.markdown(challenge)
        with tab3:
            if st.button("موڈ بورڈ دیکھیں"):
                with st.spinner():
                    mood = idea_mood_board(idea['title'], idea['description'], dna)
                    st.markdown(mood)

elif menu == "📋 تمام خیالات":
    st.header("📋 تمام خیالات")
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
                        # Clean up children
                        supabase.table("ideas").update({"parent_id": None}).eq("parent_id", idea['id']).execute()
                        supabase.table("mutations").delete().eq("original_idea_id", idea['id']).execute()
                        supabase.table("mutations").delete().eq("mutated_idea_id", idea['id']).execute()
                        supabase.table("ideas").delete().eq("id", idea['id']).execute()
                        st.success("حذف ہوگیا!")
                        st.rerun()
                with col3:
                    if st.button(f"🧠 AI مواد ##{idea['id']}", key=f"gen_{idea['id']}"):
                        with st.spinner("AI لکھ رہا ہے..."):
                            dna_obj = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']
                            content = generate_content(idea['title'], idea['description'], dna_obj)
                            supabase.table("ideas").update({"generated_content": content}).eq("id", idea['id']).execute()
                            st.success("مواد تیار ہوگیا!")
                            st.rerun()

elif menu == "📚 لرننگ پاتھ":
    st.header("📚 لرننگ پاتھ")
    res = supabase.table("ideas").select("id,title,description,dna_json").execute()
    ideas = res.data if res.data else []
    if not ideas:
        st.warning("کوئی خیال نہیں")
    else:
        idea_options = {f"{i['title']} (ID:{i['id']})": i for i in ideas}
        selected = st.selectbox("خیال چنیں", list(idea_options.keys()))
        idea = idea_options[selected]
        dna = json.loads(idea['dna_json']) if isinstance(idea['dna_json'], str) else idea['dna_json']
        if st.button("سیکھنے کا راستہ دکھائیں"):
            with st.spinner("راستہ تیار ہو رہا ہے..."):
                path = learning_path(idea['title'], idea['description'], dna)
                st.markdown(path)

elif menu == "🔄 ری سیٹ":
    st.header("🔄 ری سیٹ")
    st.warning("یہ تمام خیالات کو حذف کر دے گا۔ یہ عمل واپس نہیں لیا جا سکتا۔")
    if st.button("واقعی ری سیٹ کریں"):
        with st.spinner("حذف کیا جا رہا ہے..."):
            delete_all_ideas()
            st.success("تمام خیالات مٹا دیے گئے۔ پروجیکٹ خالی ہے۔")
            st.rerun()

elif menu == "⚙️ ایڈوانسڈ":
    st.header("⚙️ ایڈوانسڈ")
    st.markdown("یہاں آپ کوئی خاص درخواست لکھ سکتے ہیں، جیسے 'اس خیال کا بزنس ماڈل کینوس بنا دو'")
    custom_request = st.text_area("اپنی درخواست لکھیں")
    if st.button("انجام دیں"):
        with st.spinner("کارروائی ہو رہی ہے..."):
            # Use AI to handle any request
            prompt = f"صارف کی درخواست: {custom_request}\nبراہ کرم اس پر عمل کریں اور نتیجہ پیش کریں۔"
            try:
                result = call_generative_model(prompt)
                st.markdown(result)
            except Exception as e:
                st.error(str(e))

# Admin panel (only if admin secret entered)
if admin_input == ADMIN_SECRET:
    with st.sidebar:
        pass   # already shown success
    st.sidebar.markdown("---")
    if st.sidebar.button("👑 ایڈمن پینل کھولیں"):
        st.session_state.show_admin = True
if st.session_state.get("show_admin"):
    st.markdown("## 👑 ایڈمن پینل")
    tab_exp, tab_imp = st.tabs(["ایکسپورٹ", "امپورٹ"])
    with tab_exp:
        res = supabase.table("ideas").select("*").order("created_at", desc=True).execute()
        ideas = res.data if res.data else []
        if ideas:
            df = pd.DataFrame(ideas)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("ڈاؤن لوڈ CSV", csv, "ideas_backup.csv", mime="text/csv")
        else:
            st.info("کوئی خیال نہیں")
    with tab_imp:
        uploaded = st.file_uploader("CSV فائل منتخب کریں", type="csv")
        if uploaded:
            df = pd.read_csv(uploaded)
            df.columns = df.columns.str.strip().str.lower()
            if 'title' not in df.columns:
                st.error("title کالم ضروری ہے")
            else:
                if st.button("امپورٹ شروع کریں"):
                    imported = 0
                    for _, row in df.iterrows():
                        title = str(row['title']).strip()
                        if not title:
                            continue
                        desc = str(row.get('description', ''))
                        dna_raw = row.get('dna_json', None)
                        try:
                            if dna_raw and isinstance(dna_raw, str):
                                dna_obj = json.loads(dna_raw)
                            elif dna_raw and not isinstance(dna_raw, str):
                                dna_obj = dna_raw
                            else:
                                dna_obj = {"tags": [], "intent": "", "domains": [], "emotional_tone": "", "complexity": 1}
                        except:
                            dna_obj = {"tags": [], "intent": "", "domains": [], "emotional_tone": "", "complexity": 1}
                        parent_id = row.get('parent_id', None)
                        fitness = row.get('fitness_score', 0)
                        data = {
                            "title": title,
                            "description": desc,
                            "dna_json": json.dumps(dna_obj, ensure_ascii=False),
                            "parent_id": int(parent_id) if parent_id and str(parent_id).isdigit() else None,
                            "fitness_score": float(fitness) if fitness else 0
                        }
                        supabase.table("ideas").insert(data).execute()
                        imported += 1
                    st.success(f"{imported} خیالات امپورٹ ہوگئے")
                    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("یہ ایک زندہ تخلیقی مشین ہے — خیالات مر سکتے ہیں، بڑھ سکتے ہیں اور یکجا ہو سکتے ہیں۔")
