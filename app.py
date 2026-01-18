import streamlit as st
from openai import OpenAI
import extra_streamlit_components as stx
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="THE LIBRARIAN", page_icon="👁️", layout="centered")

# --- CSS (Stile Nero/Rosso) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');
    html, body, [class*="css"] { font-family: 'Courier Prime', monospace !important; color: #E0E0E0; background-color: #000000; }
    .stApp { background-color: #000000; }
    h1 { color: #C41E3A !important; text-transform: uppercase; border-bottom: 2px solid #C41E3A; }
    [data-testid="stChatMessage"] { background-color: #050505; border-left: 2px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNECTIONS ---
cookie_manager = stx.CookieManager()
# Collegamento a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
# --- MEMORY FUNCTIONS (L'Archivio) ---
def load_memory():
    try:
        # Usiamo l'URL direttamente dai secrets per sicurezza
        df = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], ttl=0)
        return df.to_dict('records')
    except Exception as e:
        print(f"Errore lettura: {e}")
        return []

def save_to_memory(role, content):
    try:
        # Carica lo storico attuale
        existing_data = load_memory()
        new_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "role": role, "content": content}
        existing_data.append(new_entry)
        # Sovrascrive il foglio con i nuovi dati
        conn.update(data=pd.DataFrame(existing_data))
    except Exception as e:
        st.error(f"Memory Write Error: {e}")

# --- AUTHENTICATION ---
cookie_val = cookie_manager.get(cookie="access_granted")

if not cookie_val:
    st.title("SECURE GATEWAY")
    password = st.text_input("ENTER PASSPHRASE:", type="password")
    if st.button("AUTHENTICATE"):
        if password == st.secrets["APP_PASSWORD"]:
            cookie_manager.set("access_granted", "true", key="set_auth")
            st.rerun()
    st.stop()

# --- THE LIBRARIAN CORE ---
st.title("THE LIBRARIAN /// MEMORY ENABLED")

# Inizializzazione sessione (Carica da Google Sheets solo all'inizio)
if "messages" not in st.session_state:
    history = load_memory()
    if not history:
        st.session_state.messages = [{"role": "system", "content": "Sei Il Bibliotecario. Protocollo 0=0. Tono freddo e analitico. Chiudi con 0=0."}]
    else:
        # Trasforma i dati di Google Sheets nel formato per la chat
        st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in history]

# Mostra la cronologia
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Logica di Input
if prompt := st.chat_input("INPUT DATA..."):
    # 1. Salva l'input dell'utente in RAM e su Google Sheets
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_to_memory("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + " █")
        
        message_placeholder.markdown(full_response)
        
        # 2. Salva la risposta del Bibliotecario su Google Sheets
        save_to_memory("assistant", full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

