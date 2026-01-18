import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import extra_streamlit_components as stx

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="LEVIATHAN OS", page_icon="🐋", layout="centered")

# --- COOKIE MANAGER PER MEMORIA ACCESSO ---
@st.cache_resource
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# --- CSS: DASHBOARD MODERNA & PULITA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@300;400&display=swap');
    
    html, body, [class*="css"], .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', sans-serif !important;
        color: #B0BCCB !important;
    }

    header, footer, #MainMenu {visibility: hidden;}

    /* Dashboard Header */
    .dash-header {
        background: rgba(16, 20, 28, 0.8);
        padding: 15px 25px;
        border-radius: 12px;
        border: 1px solid #1E2530;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(10px);
    }

    .node-status {
        color: #00D1FF;
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        text-shadow: 0 0 10px rgba(0, 209, 255, 0.3);
    }

    /* Messaggi Stile Chat Moderna */
    [data-testid="stChatMessage"] {
        background-color: #10141C !important;
        border-radius: 15px !important;
        border: 1px solid #1E2530 !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
    }

    .user-label { color: #00D1FF; font-weight: 600; font-size: 0.75rem; margin-bottom: 5px; display: block;}
    .lib-label { color: #708090; font-weight: 600; font-size: 0.75rem; margin-bottom: 5px; display: block;}

    /* Input Moderno */
    .stChatInputContainer {
        background-color: transparent !important;
        border: none !important;
    }
    
    textarea {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 12px !important;
        color: #E6EDF3 !important;
    }

    /* Sidebar a scomparsa */
    [data-testid="stSidebar"] {
        background-color: #0B0E14 !important;
        border-right: 1px solid #1E2530 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA COOKIE (RICORDA ACCESSO) ---
saved_pwd = cookie_manager.get("auth_key")
saved_node = cookie_manager.get("node_id")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = True if saved_pwd == st.secrets["APP_PASSWORD"] else False
if "user_id" not in st.session_state:
    st.session_state.user_id = saved_node if saved_node else None

# --- AUTH & LOGIN ---
if not st.session_state.auth_ok:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3;'>LEVIATHAN LOGIN</h2>", unsafe_allow_html=True)
    pwd = st.text_input("ACCESS KEY:", type="password")
    if st.button("CONNECT"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("auth_key", pwd, expires_at=None)
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

if not st.session_state.user_id:
    st.markdown("<h2 style='text-align:center; color:#E6EDF3;'>SELECT NODE</h2>", unsafe_allow_html=True)
    u_id = st.text_input("NODE NAME:")
    if st.button("INITIALIZE"):
        if u_id:
            u_id_clean = u_id.strip().upper()
            cookie_manager.set("node_id", u_id_clean, expires_at=None)
            st.session_state.user_id = u_id_clean
            st.rerun()
    st.stop()

# --- INTERFACCIA DASHBOARD ---
user_current = st.session_state.user_id
st.markdown(f"""
    <div class="dash-header">
        <span style="font-weight:700; color:#E6EDF3;">LEVIATHAN OS</span>
        <span class="node-status">● {user_current} ACTIVE</span>
    </div>
""", unsafe_allow_html=True)

# Database
conn = st.connection("gsheets", type=GSheetsConnection)

def load_mem():
    try:
        df = conn.read(ttl=0)
        user_df = df[df['user_id'].astype(str) == str(user_current)]
        return user_df.dropna(how="all").to_dict('records')
    except: return []

def save_mem(role, content):
    try:
        df = conn.read(ttl=0).dropna(how="all")
        new = pd.DataFrame([{"timestamp": time.strftime("%H:%M"), "role": role, "content": content, "user_id": user_current}])
        conn.update(data=pd.concat([df, new], ignore_index=True))
    except: pass

if "messages" not in st.session_state:
    history = load_mem()
    st.session_state.messages = [{"role": "system", "content": "Sei il Bibliotecario del sistema Leviathan. Analitico, moderno, accogliente ma risoluto. Usa un linguaggio pulito."}]
    if history:
        st.session_state.messages += [{"role": m["role"], "content": m["content"]} for m in history]

# Chat
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<span class='user-label'>YOU</span><div>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<span class='lib-label'>LEVIATHAN</span><div>{msg['content']}</div>", unsafe_allow_html=True)

if prompt := st.chat_input("Invia messaggio..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<span class='user-label'>YOU</span><div>{prompt}</div>", unsafe_allow_html=True)
    save_mem("user", prompt)

    with st.empty():
        full_res = ""
        st.markdown(f"<span class='lib-label'>LEVIATHAN</span>", unsafe_allow_html=True)
        placeholder = st.empty()
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(f"<div>{full_res}</div>", unsafe_allow_html=True)
        save_mem("assistant", full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})

with st.sidebar:
    if st.button("LOGOUT / CLEAR COOKIES"):
        cookie_manager.delete("auth_key")
        cookie_manager.delete("node_id")
        st.session_state.clear()
        st.rerun()
