import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="THE LIBRARIAN", page_icon="👁️", layout="centered")

# --- CSS: ESTETICA TERMINALE BRUTALISTA (Senza Icone) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        background-color: #000000 !important;
        font-family: 'Courier Prime', monospace !important;
        color: #888888 !important;
    }

    header, footer, #MainMenu {visibility: hidden;}
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {display: none !important;}

    .status-bar {
        font-size: 0.75rem;
        color: #C41E3A;
        border-bottom: 1px solid #1A1A1A;
        margin-bottom: 2rem;
        padding-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 1.2rem !important;
    }

    .msg-label {
        font-weight: bold;
        font-size: 0.8rem;
        margin-bottom: 2px;
        display: block;
    }
    
    .user-text { color: #C41E3A !important; }
    .lib-text { color: #E0E0E0 !important; }

    .stChatInputContainer {
        background-color: #000000 !important;
        border-top: 1px solid #1A1A1A !important;
    }
    
    textarea {
        background-color: #000000 !important;
        border: 1px solid #1A1A1A !important;
        color: #C41E3A !important;
        font-family: 'Courier Prime', monospace !important;
    }

    .stButton>button {
        background-color: transparent !important;
        color: #444 !important;
        border: 1px solid #222 !important;
        border-radius: 0 !important;
        font-size: 0.7rem;
    }
    .stButton>button:hover {
        border-color: #C41E3A !important;
        color: #C41E3A !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_memory(user_id):
    try:
        df = conn.read(ttl=0)
        if df.empty: return []
        user_df = df[df['user_id'].astype(str) == str(user_id)]
        return user_df.dropna(how="all").to_dict('records')
    except: return []

def save_to_memory(role, content, user_id):
    try:
        current_df = conn.read(ttl=0).dropna(how="all")
        new_row = pd.DataFrame([{"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "role": role, "content": content, "user_id": user_id}])
        updated_df = pd.concat([current_df, new_row], ignore_index=True)
        conn.update(data=updated_df)
    except: pass

# --- AUTH ---
if "auth_ok" not in st.session_state: st.session_state.auth_ok = False
if not st.session_state.auth_ok:
    st.markdown("<h3 style='color:#C41E3A; text-align:center;'>ACCESS_DENIED</h3>", unsafe_allow_html=True)
    pwd = st.text_input("KEY:", type="password")
    if st.button("UNLOCK"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state.auth_ok = True
            st.rerun()
    st.stop()

# --- ID STANZA ---
if "user_id" not in st.session_state:
    st.markdown("<h3 style='color:#C41E3A; text-align:center;'>IDENTIFICATION_REQUIRED</h3>", unsafe_allow_html=True)
    u_id = st.text_input("NODE_ID:", placeholder="Assign identity...")
    if st.button("CONNECT"):
        if u_id:
            st.session_state.user_id = u_id.strip().upper()
            st.rerun()
    st.stop()

# --- INTERFACCIA ---
user_current = st.session_state.user_id
st.markdown(f"<div class='status-bar'>TERMINAL: {user_current} | MEMORY: ENABLED | PROTOCOL: 0=0</div>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    history = load_memory(user_current)
    system_prompt = {"role": "system", "content": "PROTOCOLLO 0=0. Analisi cinica e breve. Rispondi come un terminale freddo. Chiudi con 0=0."}
    st.session_state.messages = [system_prompt]
    if history:
        st.session_state.messages += [{"role": m["role"], "content": m["content"]} for m in history]

# Display Chat personalizzato
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<span class='msg-label user-text'>> USER:</span><div class='user-text'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<span class='msg-label lib-text'>> LIBRARIAN:</span><div class='lib-text'>{msg['content']}</div>", unsafe_allow_html=True)

# Input & Stream
if prompt := st.chat_input("DATA INPUT..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<span class='msg-label user-text'>> USER:</span><div class='user-text'>{prompt}</div>", unsafe_allow_html=True)
    
    save_to_memory("user", prompt, user_current)

    full_response = ""
    st.markdown(f"<span class='msg-label lib-text'>> LIBRARIAN:</span>", unsafe_allow_html=True)
    placeholder = st.empty()
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
            placeholder.markdown(f"<div class='lib-text'>{full_response} █</div>", unsafe_allow_html=True)
    
    placeholder.markdown(f"<div class='lib-text'>{full_response}</div>", unsafe_allow_html=True)
    save_to_memory("assistant", full_response, user_current)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

with st.sidebar:
    if st.button("TERMINATE SESSION"):
        st.session_state.clear()
        st.rerun()
