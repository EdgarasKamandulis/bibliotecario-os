import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
import extra_streamlit_components as stx

# --- CONFIGURAZIONE CORE ---
st.set_page_config(page_title="LEVIATHAN OS", page_icon="🐋", layout="centered")

# --- COOKIE MANAGER ---
cookie_manager = stx.CookieManager()

# --- CSS: DASHBOARD FIXES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@300;400&display=swap');
    
    html, body, [class*="css"], .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', sans-serif !important;
        color: #B0BCCB !important;
    }

    header, footer, #MainMenu {visibility: hidden;}

    /* Header Fisso Immutabile */
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

    .node-status { color: #00D1FF; font-family: 'Fira Code', monospace; font-size: 0.8rem; }

    .main-content { padding-top: 100px; padding-bottom: 120px; }

    [data-testid="stChatMessage"] {
        background-color: #10141C !important;
        border-radius: 12px !important;
        border: 1px solid #1E2530 !important;
        padding: 20px !important;
    }

    .user-label { color: #00D1FF; font-weight: 600; font-size: 0.7rem; display: block; text-transform: uppercase;}
    .lib-label { color: #708090; font-weight: 600; font-size: 0.7rem; display: block; text-transform: uppercase;}

    /* Input Moderna Blu */
    .stChatInputContainer { background-color: transparent !important; border: none !important; }
    textarea {
        background-color: #161B22 !important;
        border: 1px solid #00D1FF !important;
        border-radius: 12px !important;
        color: #E6EDF3 !important;
    }
    button[data-testid="stChatInputSubmit"] { color: #00D1FF !important; }

    /* Sidebar Logout */
    [data-testid="stSidebar"] { background-color: #0B0E14 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PERSISTENZA ---
time.sleep(0.6)
saved_pwd = cookie_manager.get("auth_key")
saved_node = cookie_manager.get("node_id")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = True if saved_pwd == st.secrets["APP_PASSWORD"] else False
if "user_id" not in st.session_state:
    st.session_state.user_id = saved_node if saved_node else None

# --- AUTH & NODE ---
if not st.session_state.auth_ok:
    st.markdown("<h2 style='text-align:center;'>LEVIATHAN LOGIN</h2>", unsafe_allow_html=True)
    pwd = st.text_input("KEY:", type="password")
    if st.button("CONNECT"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("auth_key", pwd)
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

if not st.session_state.user_id:
    st.markdown("<h2 style='text-align:center;'>SELECT NODE</h2>", unsafe_allow_html=True)
    u_id = st.text_input("NOME STANZA:")
    if st.button("INITIALIZE"):
        if u_id:
            cookie_manager.set("node_id", u_id.strip().upper())
            st.session_state.user_id = u_id.strip().upper()
            st.rerun()
    st.stop()

# --- INTERFACCIA ---
st.markdown(f'<div class="dash-header"><b>LEVIATHAN CORE</b><span class="node-status">● {st.session_state.user_id}</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
user_current = st.session_state.user_id

def load_mem():
    try:
        df = conn.read(ttl=0)
        return df[df['user_id'].astype(str) == str(user_current)].dropna(how="all").to_dict('records')
    except: return []

if "messages" not in st.session_state:
    history = load_mem()
    # Iniezione data corrente e istruzioni rigide
    current_date = datetime.now().strftime("%d %B %Y")
    st.session_state.messages = [{"role": "system", "content": f"Sei il Bibliotecario. Oggi è il {current_date}. NON usare mai '0=0'. Tono cinico e breve."}]
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
                time.sleep(0.06) # Digitazione cerimoniale
        
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    # Salvataggio asincrono per non bloccare la UI
    new_row = pd.DataFrame([{"timestamp": time.strftime("%H:%M"), "role": "user", "content": prompt, "user_id": user_current},
                            {"timestamp": time.strftime("%H:%M"), "role": "assistant", "content": full_res, "user_id": user_current}])
    df = conn.read(ttl=0).dropna(how="all")
    conn.update(data=pd.concat([df, new_row], ignore_index=True))

st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    if st.button("TERMINATE & LOGOUT"):
        cookie_manager.delete("auth_key")
        cookie_manager.delete("node_id")
        st.session_state.clear()
        st.rerun()
