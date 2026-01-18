import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
import pytz
import extra_streamlit_components as stx

# --- CONFIGURAZIONE CORE ---
st.set_page_config(page_title="LIBRARIAN CORE", page_icon="👁️", layout="centered")

# --- COOKIE MANAGER ---
cookie_manager = stx.CookieManager()

# --- CSS: ESTETICA LIBRARIAN (CIANO/BLU) - NO RED ALLOWED ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@300;400&display=swap');
    
    html, body, [class*="css"], .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', sans-serif !important;
        color: #B0BCCB !important;
    }

    header, footer, #MainMenu {visibility: hidden;}

    /* Sticky Header Logic removed for native buttons - Custom styling for top bar */
    .top-bar {
        background: rgba(11, 14, 20, 0.95);
        padding: 10px 0;
        border-bottom: 1px solid #1E2530;
        margin-bottom: 20px;
    }

    .node-status {
        color: #00D1FF;
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        text-shadow: 0 0 10px rgba(0, 209, 255, 0.4);
    }

    /* Layout Content */
    .main-content { padding-bottom: 120px; }

    /* Chat Messages - BLUE THEME */
    [data-testid="stChatMessage"] {
        background-color: #10141C !important;
        border-radius: 12px !important;
        border: 1px solid #1E2530 !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stChatMessage"]:focus { border: 1px solid #00D1FF !important; }

    .user-label { color: #00D1FF; font-weight: 600; font-size: 0.7rem; margin-bottom: 5px; display: block; text-transform: uppercase;}
    .lib-label { color: #708090; font-weight: 600; font-size: 0.7rem; margin-bottom: 5px; display: block; text-transform: uppercase;}

    /* Input Moderna: NO RED BORDERS */
    .stChatInputContainer { background-color: transparent !important; border: none !important; }
    .stChatInputContainer textarea {
        background-color: #161B22 !important;
        border: 1px solid #1E2530 !important;
        border-radius: 10px !important;
        color: #E6EDF3 !important;
    }
    .stChatInputContainer textarea:focus {
        border: 1px solid #00D1FF !important;
        box-shadow: 0 0 10px rgba(0, 209, 255, 0.2) !important;
    }
    
    /* TARGETING TEXT INPUTS (Login / Node) to remove Red */
    div[data-baseweb="input"] {
        background-color: #161B22 !important;
        border: 1px solid #1E2530 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #00D1FF !important;
        box-shadow: 0 0 0 1px #00D1FF !important;
    }
    div[data-testid="stTextInput"] label {
        color: #B0BCCB !important;
    }

    /* Submit Button Cyan */
    button[data-testid="stChatInputSubmit"] {
        color: #00D1FF !important;
        background-color: transparent !important;
        right: 10px !important;
    }

    /* Sidebar & Buttons - PURGE RED */
    [data-testid="stSidebar"] { background-color: #0B0E14 !important; border-right: 1px solid #1E2530 !important; }
    .stButton>button {
        background-color: transparent !important;
        color: #00D1FF !important;
        border: 1px solid #1E2530 !important;
        border-radius: 8px !important;
    }
    .stButton>button:hover {
        border-color: #00D1FF !important;
        color: #00D1FF !important;
        background-color: rgba(0, 209, 255, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA TEMPORALE ---
def get_current_time():
    italy_tz = pytz.timezone('Europe/Rome')
    return datetime.now(italy_tz)

# --- LOGICA PERSISTENZA ---
# Tentativo robusto di recupero cookie
saved_pwd = cookie_manager.get("auth_key")
saved_node = cookie_manager.get("node_id")

if not saved_pwd:
    time.sleep(0.5)
    saved_pwd = cookie_manager.get("auth_key")
    saved_node = cookie_manager.get("node_id")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = True if saved_pwd == st.secrets["APP_PASSWORD"] else False
if "user_id" not in st.session_state:
    st.session_state.user_id = saved_node if saved_node else None

# --- AUTH (LIBRARIAN CORE) ---
if not st.session_state.auth_ok:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300; padding-top:50px;'>LIBRARIAN CORE</h2>", unsafe_allow_html=True)
    pwd = st.text_input("ACCESS KEY:", type="password")
    if st.button("CONNECT"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("auth_key", pwd)
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

# --- NODE SELECTION (LIBRARIAN CORE) ---
if not st.session_state.user_id:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300; padding-top:50px;'>NODE SELECTION</h2>", unsafe_allow_html=True)
    u_id = st.text_input("IDENTIFICATIVO:")
    if st.button("INITIALIZE"):
        if u_id:
            u_id_clean = u_id.strip().upper()
            cookie_manager.set("node_id", u_id_clean)
            st.session_state.user_id = u_id_clean
            st.rerun()
    st.stop()

# --- UI PRINCIPALE (HEADER FUNZIONALE) ---
c1, c2, c3 = st.columns([5, 2, 2])
with c1:
    st.markdown(f"<div style='padding-top:5px; font-weight:700; color:#E6EDF3; letter-spacing:1px;'>LIBRARIAN CORE <span style='color:#00D1FF; margin-left:10px;'>● {st.session_state.user_id}</span></div>", unsafe_allow_html=True)

with c2:
    if st.button("CHANGE NODE", key="btn_node"):
        try:
            cookie_manager.delete("node_id")
        except KeyError:
            pass
        st.session_state.user_id = None
        st.rerun()

with c3:
    if st.button("LOGOUT", key="btn_logout"):
        try:
            cookie_manager.delete("auth_key")
        except KeyError:
            pass
        try:
            cookie_manager.delete("node_id")
        except KeyError:
            pass
        st.session_state.clear()
        st.rerun()

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Database Connection
conn = st.connection("gsheets", type=GSheetsConnection)
user_current = st.session_state.user_id

def load_mem():
    try:
        df = conn.read(ttl=0)
        return df[df['user_id'].astype(str) == str(user_current)].dropna(how="all").to_dict('records')
    except: return []

def save_mem(role, content):
    try:
        now = get_current_time()
        df = conn.read(ttl=0).dropna(how="all")
        new = pd.DataFrame([{"timestamp": now.strftime("%d/%m/%Y %H:%M"), "role": role, "content": content, "user_id": user_current}])
        conn.update(data=pd.concat([df, new], ignore_index=True))
    except: pass

if "messages" not in st.session_state:
    history = load_mem()
    now = get_current_time()
    # Prompt di sistema pulito
    st.session_state.messages = [{"role": "system", "content": f"""Oggi è {now.strftime('%A %d %B %Y')} e sono le {now.strftime('%H:%M')}. 
    Sei il Bibliotecario. Sei analitico, distaccato e professionale.
    Rispondi sempre sapendo l'ora esatta fornita."""}]
    if history:
        st.session_state.messages += [{"role": m["role"], "content": m["content"]} for m in history]

# Rendering Chat
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<span class='user-label'>YOU</span><div>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<span class='lib-label'>LIBRARIAN</span><div>{msg['content']}</div>", unsafe_allow_html=True)

# Input Logica
if prompt := st.chat_input("DATA INPUT..."):
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

