import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
import pytz
import extra_streamlit_components as stx

# --- CONFIGURAZIONE CORE ---
st.set_page_config(page_title="THE LIBRARIAN", page_icon="👁️", layout="centered")

# --- COOKIE MANAGER PER PERSISTENZA ---
cookie_manager = stx.CookieManager()

# --- CSS: DASHBOARD MODERNA (BLU/CIANO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@300;400&display=swap');
    
    html, body, [class*="css"], .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', sans-serif !important;
        color: #B0BCCB !important;
    }

    header, footer, #MainMenu {visibility: hidden;}

    /* Sticky Header */
    .dash-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: rgba(11, 14, 20, 0.9);
        padding: 15px 0;
        border-bottom: 1px solid #1E2530;
        z-index: 1000;
        display: flex;
        justify-content: center;
        backdrop-filter: blur(10px);
    }
    .header-content {
        width: 100%;
        max-width: 700px;
        display: flex;
        justify-content: space-between;
        padding: 0 20px;
    }
    .node-status {
        color: #00D1FF;
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        text-shadow: 0 0 10px rgba(0, 209, 255, 0.4);
    }

    /* Layout Content */
    .main-content { padding-top: 80px; padding-bottom: 100px; }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: #10141C !important;
        border-radius: 12px !important;
        border: 1px solid #1E2530 !important;
        margin-bottom: 20px !important;
    }
    .user-label { color: #00D1FF; font-weight: 600; font-size: 0.7rem; margin-bottom: 5px; display: block; letter-spacing: 1px;}
    .lib-label { color: #708090; font-weight: 600; font-size: 0.7rem; margin-bottom: 5px; display: block; letter-spacing: 1px;}

    /* Input Moderna Blu/Ciano */
    .stChatInputContainer { background-color: transparent !important; border: none !important; }
    textarea {
        background-color: #161B22 !important;
        border: 1px solid #00D1FF !important;
        border-radius: 10px !important;
        color: #E6EDF3 !important;
    }
    button[data-testid="stChatInputSubmit"] {
        color: #00D1FF !important;
        background-color: transparent !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0B0E14 !important; border-right: 1px solid #1E2530 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA TEMPORALE ---
italy_tz = pytz.timezone('Europe/Rome')
now = datetime.now(italy_tz)
current_time_str = now.strftime("%H:%M")
current_date_str = now.strftime("%d/%m/%Y")

# --- LOGICA PERSISTENZA ---
time.sleep(0.5)
saved_pwd = cookie_manager.get("auth_key")
saved_node = cookie_manager.get("node_id")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = True if saved_pwd == st.secrets["APP_PASSWORD"] else False
if "user_id" not in st.session_state:
    st.session_state.user_id = saved_node if saved_node else None

# --- AUTH ---
if not st.session_state.auth_ok:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300;'>LIBRARIAN CORE</h2>", unsafe_allow_html=True)
    pwd = st.text_input("ACCESS KEY:", type="password")
    if st.button("CONNECT"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("auth_key", pwd)
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

# --- NODE SELECTION ---
if not st.session_state.user_id:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300;'>SELECT NODE</h2>", unsafe_allow_html=True)
    u_id = st.text_input("IDENTIFICATIVO:")
    if st.button("INITIALIZE"):
        if u_id:
            u_id_clean = u_id.strip().upper()
            cookie_manager.set("node_id", u_id_clean)
            st.session_state.user_id = u_id_clean
            st.rerun()
    st.stop()

# --- UI PRINCIPALE ---
st.markdown(f'''
    <div class="dash-header">
        <div class="header-content">
            <span style="font-weight:700; color:#E6EDF3;">LIBRARIAN CORE</span>
            <span class="node-status">● {st.session_state.user_id}</span>
        </div>
    </div>
''', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Database
conn = st.connection("gsheets", type=GSheetsConnection)
user_current = st.session_state.user_id

def load_mem():
    try:
        df = conn.read(ttl=0)
        return df[df['user_id'].astype(str) == str(user_current)].dropna(how="all").to_dict('records')
    except: return []

def save_mem(role, content):
    try:
        df = conn.read(ttl=0).dropna(how="all")
        new = pd.DataFrame([{"timestamp": f"{current_date_str} {current_time_str}", "role": role, "content": content, "user_id": user_current}])
        conn.update(data=pd.concat([df, new], ignore_index=True))
    except: pass

if "messages" not in st.session_state:
    history = load_mem()
    st.session_state.messages = [{"role": "system", "content": f"Sei il Bibliotecario. Oggi è {current_date_str} e sono le {current_time_str}. Sei un'entità analitica e moderna. NON usare mai la formula '0=0'."}]
    if history:
        st.session_state.messages += [{"role": m["role"], "content": m["content"]} for m in history]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<span class='user-label'>YOU</span><div>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<span class='lib-label'>LIBRARIAN</span><div>{msg['content']}</div>", unsafe_allow_html=True)

if prompt := st.chat_input("Invia segnale..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<span class='user-label'>YOU</span><div>{prompt}</div>", unsafe_allow_html=True)
    save_mem("user", prompt)

    with st.empty():
        full_res = ""
        st.markdown(f"<span class='lib-label'>LIBRARIAN</span>", unsafe_allow_html=True)
        placeholder = st.empty()
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(f"<div>{full_res}</div>", unsafe_allow_html=True)
                time.sleep(0.05)
        save_mem("assistant", full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})

st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("LOGOUT / CAMBIA NODO"):
        cookie_manager.delete("auth_key")
        cookie_manager.delete("node_id")
        st.session_state.clear()
        st.rerun()
