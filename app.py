import streamlit as st
from openai import OpenAI
import extra_streamlit_components as stx
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- CONFIG ---
st.set_page_config(page_title="THE LIBRARIAN", page_icon="👁️", layout="centered")

# --- CSS ---
st.markdown("<style>html, body, [class*='css'] { font-family: 'Courier Prime', monospace !important; color: #E0E0E0; background-color: #000000; } .stApp { background-color: #000000; } h1 { color: #C41E3A !important; }</style>", unsafe_allow_html=True)

# --- CONNECTIONS ---
cookie_manager = stx.CookieManager()
conn = st.connection("gsheets", type=GSheetsConnection)

def load_memory(user_id):
    try:
        df = conn.read(ttl=0)
        if df.empty: return []
        # Filtra solo i messaggi di questo specifico utente
        user_df = df[df['user_id'] == user_id]
        return user_df.dropna(how="all").to_dict('records')
    except:
        return []

def save_to_memory(role, content, user_id):
    try:
        current_df = conn.read(ttl=0).dropna(how="all")
        new_row = pd.DataFrame([{
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), 
            "role": role, 
            "content": content,
            "user_id": user_id
        }])
        updated_df = pd.concat([current_df, new_row], ignore_index=True)
        conn.update(data=updated_df)
    except Exception as e:
        st.error(f"ERRORE ARCHIVIO: {e}")

# --- AUTH & IDENTIFICATION ---
cookie_val = cookie_manager.get(cookie="access_granted")
if not cookie_val:
    st.title("SECURE GATEWAY")
    pwd = st.text_input("ENTER PASSPHRASE:", type="password")
    if st.button("AUTHENTICATE"):
        if pwd == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("access_granted", "true", key="set_auth")
            st.rerun()
    st.stop()

# --- USER SELECTION (LA STANZA) ---
if "user_id" not in st.session_state:
    st.title("IDENTIFICAZIONE")
    u_id = st.text_input("INSERISCI IL TUO NOME O CODICE STANZA:", placeholder="es: Edgar, Jules, Ospite...")
    if st.button("ACCEDI ALL'ARCHIVIO"):
        if u_id:
            st.session_state.user_id = u_id.strip().upper()
            st.rerun()
    st.stop()

# --- THE LIBRARIAN CORE ---
user_current = st.session_state.user_id
st.title(f"THE LIBRARIAN /// STANZA: {user_current}")

# Logout/Cambio Stanza
with st.sidebar:
    if st.button("CAMBIA UTENTE / LOGOUT"):
        st.session_state.clear()
        st.rerun()

if "messages" not in st.session_state:
    history = load_memory(user_current)
    if not history:
        st.session_state.messages = [{"role": "system", "content": "Sei Il Bibliotecario. Protocollo 0=0. Tono freddo. Chiudi con 0=0."}]
    else:
        st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in history]

# Display
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input
if prompt := st.chat_input("INPUT DATA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    save_to_memory("user", prompt, user_current)

    with st.chat_message("assistant"):
        full_response = ""
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
        placeholder = st.empty()
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                placeholder.markdown(full_response + " █")
        placeholder.markdown(full_response)
        
        save_to_memory("assistant", full_response, user_current)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

