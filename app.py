import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz
import extra_streamlit_components as stx

# --- CONFIGURAZIONE CORE ---
st.set_page_config(page_title="LIBRARIAN CORE", page_icon="👁️", layout="centered")

# --- COOKIE MANAGER ---
cookie_manager = stx.CookieManager()

# --- CSS: ESTETICA LIBRARIAN (CIANO/BLU) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@300;400&display=swap');

    html, body, [class*="css"], .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', sans-serif !important;
        color: #B0BCCB !important;
    }

    header, footer, #MainMenu {visibility: hidden;}

    /* Header Sticky & Compact */
    .sticky-header {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: rgba(11, 14, 20, 0.98);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid #1E2530;
        z-index: 9999;
        padding: 10px 0;
    }
    
    .header-content {
        max-width: 800px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 20px;
    }

    .main-content { padding-top: 80px; padding-bottom: 120px; }

    /* Buttons Style */
    .stButton > button {
        background-color: transparent !important;
        color: #00D1FF !important;
        border: 1px solid #1E2530 !important;
        font-size: 0.7rem !important;
        padding: 2px 8px !important;
        height: auto !important;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        border-color: #00D1FF !important;
        background-color: rgba(0, 209, 255, 0.05) !important;
    }

    /* Chat Input Cyan Fix */
    [data-testid="stChatInput"] { background-color: transparent !important; }
    [data-testid="stChatInput"] > div {
        background-color: #161B22 !important;
        border: 1px solid #1E2530 !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInput"] > div:focus-within { border-color: #00D1FF !important; }
    [data-testid="stChatInput"] textarea { color: #E6EDF3 !important; caret-color: #00D1FF !important; }
    button[data-testid="stChatInputSubmit"] svg { fill: #00D1FF !important; }

    /* Message Labels */
    .user-label { color: #00D1FF; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 5px; display: block;}
    .lib-label { color: #708090; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 5px; display: block;}
    </style>
""", unsafe_allow_html=True)

# --- LOGICA TEMPORALE ---
def get_current_time():
    italy_tz = pytz.timezone('Europe/Rome')
    return datetime.now(italy_tz)

# --- PERSISTENZA COOKIE (RAFFORZATA) ---
time.sleep(0.5) # Wait for cookies to sync
saved_pwd = cookie_manager.get("auth_key")
saved_node = cookie_manager.get("node_id")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = True if saved_pwd == st.secrets["APP_PASSWORD"] else False
if "user_id" not in st.session_state:
    st.session_state.user_id = saved_node if saved_node else None

# --- AUTH LOGIN ---
if not st.session_state.auth_ok:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300; padding-top:100px;'>LIBRARIAN CORE</h2>", unsafe_allow_html=True)
    pwd = st.text_input("ACCESS KEY:", type="password", key="login_pwd")
    if st.button("CONNECT"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("auth_key", pwd, expires_at=datetime.now() + timedelta(days=30))
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

# --- NODE SELECTION ---
if not st.session_state.user_id:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3; font-weight:300; padding-top:100px;'>NODE SELECTION</h2>", unsafe_allow_html=True)
    u_id = st.text_input("IDENTIFICATIVO:", key="node_input")
    if st.button("INITIALIZE"):
        if u_id:
            u_id_clean = u_id.strip().upper()
            cookie_manager.set("node_id", u_id_clean, expires_at=datetime.now() + timedelta(days=30))
            st.session_state.user_id = u_id_clean
            st.rerun()
    st.stop()

# --- HEADER COMPATTO (STICKY) ---
st.markdown(f"""
<div class="sticky-header">
    <div class="header-content">
        <div style="font-weight:700; color:#E6EDF3; font-size:0.9rem;">
            LIBRARIAN CORE <span style="color:#00D1FF; margin-left:8px;">● {st.session_state.user_id}</span>
        </div>
        <div id="btn-group" style="display: flex; gap: 10px;">
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Injecting buttons into the compact header via Streamlit columns
header_cols = st.columns([6, 1.5, 1.2])
with header_cols[1]:
    if st.button("NODE", key="chg_node"):
        cookie_manager.delete("node_id")
        st.session_state.user_id = None
        st.rerun()
with header_cols[2]:
    if st.button("LOGOUT", key="logout"):
        cookie_manager.delete("auth_key")
        cookie_manager.delete("node_id")
        st.session_state.clear()
        st.rerun()

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- DATABASE & CHAT ---
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
    # PROTOCOLLO CINICO: Istruzioni per il Bibliotecario
    st.session_state.messages = [{"role": "system", "content": f"""Oggi è {now.strftime('%A %d %B %Y')} ore {now.strftime('%H:%M')}. 
    Sei il Bibliotecario. Sei cinico, freddo, distaccato e puramente analitico. 
    Non mostrare mai gentilezza, empatia o calore. Rispondi come un'entità logica superiore.
    NON usare mai la formula '0=0'. Sii chirurgico e diretto."""}]
    if history:
        st.session_state.messages += [{"role": m["role"], "content": m["content"]} for m in history]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<span class='user-label'>YOU</span><div>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<span class='lib-label'>LIBRARIAN</span><div>{msg['content']}</div>", unsafe_allow_html=True)

if prompt := st.chat_input("DATA INPUT..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<span class='user-label'>YOU</span><div>{prompt}</div>", unsafe_allow_html=True)
    save_mem("user", prompt)

    with st.empty():
        full_res = ""
        st.markdown(f"<span class='lib-label'>LIBRARIAN</span>", unsafe_allow_html=True)
        placeholder = st.empty()
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(f"<div>{full_res}</div>", unsafe_allow_html=True)
                    time.sleep(0.04)
            save_mem("assistant", full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error("ERRORE DI SISTEMA: Limite API raggiunto o problema di connessione.")

st.markdown('</div>', unsafe_allow_html=True)
