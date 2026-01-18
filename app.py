import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import extra_streamlit_components as stx

# --- CONFIGURAZIONE CORE ---
st.set_page_config(page_title="LEVIATHAN OS", page_icon="🐋", layout="centered")

# --- COOKIE MANAGER PER PERSISTENZA ---
cookie_manager = stx.CookieManager()

# --- CSS: LEVIATHAN DASHBOARD DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@300;400&display=swap');
    
    html, body, [class*="css"], .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', sans-serif !important;
        color: #B0BCCB !important;
    }

    header, footer, #MainMenu {visibility: hidden;}

    /* Sticky Header Design */
    .dash-header {
        position: fixed;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 700px;
        background: rgba(11, 14, 20, 0.95);
        padding: 20px 30px;
        border-bottom: 1px solid #1E2530;
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(15px);
    }

    .node-status {
        color: #00D1FF;
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        text-shadow: 0 0 10px rgba(0, 209, 255, 0.4);
    }

    /* Layout Content */
    .main-content {
        padding-top: 100px;
        padding-bottom: 120px;
    }

    [data-testid="stChatMessage"] {
        background-color: #10141C !important;
        border-radius: 12px !important;
        border: 1px solid #1E2530 !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
    }

    .user-label { color: #00D1FF; font-weight: 600; font-size: 0.7rem; margin-bottom: 6px; display: block; letter-spacing: 1px;}
    .lib-label { color: #708090; font-weight: 600; font-size: 0.7rem; margin-bottom: 6px; display: block; letter-spacing: 1px;}

    /* Modern Input Area */
    .stChatInputContainer {
        background-color: #0B0E14 !important;
        border: none !important;
        padding-bottom: 20px !important;
    }
    
    textarea {
        background-color: #161B22 !important;
        border: 1px solid #00D1FF !important;
        border-radius: 12px !important;
        color: #E6EDF3 !important;
        padding: 12px !important;
    }

    /* Submit Button Blue */
    button[data-testid="stChatInputSubmit"] {
        color: #00D1FF !important;
    }

    /* Sidebar & Buttons */
    [data-testid="stSidebar"] {
        background-color: #0B0E14 !important;
        border-right: 1px solid #1E2530 !important;
    }
    .stButton>button {
        background-color: transparent !important;
        color: #B0BCCB !important;
        border: 1px solid #1E2530 !important;
        border-radius: 8px !important;
        font-size: 0.8rem;
    }
    .stButton>button:hover {
        border-color: #C41E3A !important;
        color: #C41E3A !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA PERSISTENZA ---
time.sleep(0.6)
saved_pwd = cookie_manager.get("auth_key")
saved_node = cookie_manager.get("node_id")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = True if saved_pwd == st.secrets["APP_PASSWORD"] else False
if "user_id" not in st.session_state:
    st.session_state.user_id = saved_node if saved_node else None

# --- FASE 1: AUTH ---
if not st.session_state.auth_ok:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300; letter-spacing:2px;'>LEVIATHAN CORE</h2>", unsafe_allow_html=True)
    pwd = st.text_input("ACCESS KEY:", type="password")
    if st.button("CONNECT"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("auth_key", pwd)
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

# --- FASE 2: NODE SELECTION ---
if not st.session_state.user_id:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300;'>IDENTIFY NODE</h2>", unsafe_allow_html=True)
    u_id = st.text_input("NOME STANZA:")
    if st.button("INITIALIZE"):
        if u_id:
            u_id_clean = u_id.strip().upper()
            cookie_manager.set("node_id", u_id_clean)
            st.session_state.user_id = u_id_clean
            st.rerun()
    st.stop()

# --- INTERFACCIA PRINCIPALE ---
user_current = st.session_state.user_id
st.markdown(f'<div class="dash-header"><span style="font-weight:700; color:#E6EDF3; letter-spacing:1px;">LEVIATHAN CORE</span><span class="node-status">● {user_current}</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Database
conn = st.connection("gsheets", type=GSheetsConnection)

def load_mem():
    try:
        df = conn.read(ttl=0)
        return df[df['user_id'].astype(str) == str(user_current)].dropna(how="all").to_dict('records')
    except: return []

def save_mem(role, content):
    try:
        df = conn.read(ttl=0).dropna(how="all")
        new = pd.DataFrame([{"timestamp": time.strftime("%H:%M"), "role": role, "content": content, "user_id": user_current}])
        conn.update(data=pd.concat([df, new], ignore_index=True))
    except: pass

if "messages" not in st.session_state:
    history = load_mem()
    st.session_state.messages = [{"role": "system", "content": "Sei il Bibliotecario di Leviathan. Analitico e risoluto. NON usare mai la chiusura 0=0."}]
    if history:
        st.session_state.messages += [{"role": m["role"], "content": m["content"]} for m in history]

# Rendering Chat
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<span class='user-label'>YOU</span><div>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<span class='lib-label'>LIBRARIAN</span><div>{msg['content']}</div>", unsafe_allow_html=True)

# Input Logica
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
                time.sleep(0.05) # Digitazione rallentata per autorità estetica
        save_mem("assistant", full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})

st.markdown('</div>', unsafe_allow_html=True)

# Sidebar per Logout
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("TERMINATE & LOGOUT"):
        cookie_manager.delete("auth_key")
        cookie_manager.delete("node_id")
        st.session_state.clear()
        st.rerun()
