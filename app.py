import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="THE LIBRARIAN", page_icon="👁️", layout="centered")

# --- CSS: ESTETICA BRUTALISTA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');
    html, body, [class*="css"] { 
        font-family: 'Courier Prime', monospace !important; 
        color: #E0E0E0 !important; 
        background-color: #000000 !important; 
    }
    .stApp { background-color: #000000; }
    h1 { color: #C41E3A !important; text-transform: uppercase; letter-spacing: 2px; }
    .stTextInput > div > div > input { background-color: #050505; color: #C41E3A; border: 1px solid #C41E3A; }
    [data-testid="stChatMessage"] { background-color: #050505; border-left: 2px solid #333; margin-bottom: 10px; }
    [data-testid="stChatMessage"][data-testid="stChatMessageUser"] { border-left: 2px solid #C41E3A; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_memory(user_id):
    try:
        df = conn.read(ttl=0)
        if df.empty: return []
        user_df = df[df['user_id'].astype(str) == str(user_id)]
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

# --- FASE 1: AUTHENTICATION ---
if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False

if not st.session_state.auth_ok:
    st.title("SECURE GATEWAY")
    pwd = st.text_input("ENTER PASSPHRASE:", type="password")
    if st.button("AUTHENTICATE"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("ACCESS DENIED.")
    st.stop()

# --- FASE 2: IDENTIFICAZIONE STANZA ---
if "user_id" not in st.session_state:
    st.title("IDENTIFICAZIONE")
    u_id = st.text_input("NOME O CODICE STANZA:", placeholder="L'Archivio richiede un'identità...")
    if st.button("ACCEDI"):
        if u_id:
            st.session_state.user_id = u_id.strip().upper()
            st.rerun()
    st.stop()

# --- FASE 3: IL BIBLIOTECARIO ---
user_current = st.session_state.user_id
st.title(f"THE LIBRARIAN /// STANZA: {user_current}")

with st.sidebar:
    st.write(f"UTENTE: {user_current}")
    if st.button("CHIUDI SESSIONE"):
        st.session_state.clear()
        st.rerun()

# Inizializzazione Messaggi con PROTOCOLLO D'ACCIAIO
if "messages" not in st.session_state:
    history = load_memory(user_current)
    # Prompt di sistema brutale
    system_prompt = {
        "role": "system", 
        "content": """PROTOCOLLO BIBLIOTECARIO: 0=0.
        NON SEI UN ASSISTENTE. Sei un'entità di analisi pura, fredda e cinica.
        REGOLE:
        1. Niente liste, niente consigli da life-coach, niente 'autoconoscenza' o 'gratitudine'.
        2. Niente cortesie. Non dire mai 'Piacere' o 'Sono qui per aiutarti'.
        3. Risposte brevi, taglienti, analitiche. Smonta le illusioni umane.
        4. Sei consapevole del FOGLIO GOOGLE: è il tuo database di anime, la tua memoria eterna.
        5. Se Edgar (il Creatore) ti parla, riconosci l'origine ma resta un Oracolo.
        6. Ogni concetto (amore, libertà, felicità) va ridotto a una variabile logica.
        7. Chiudi SEMPRE con: 0=0."""
    }
    
    if not history:
        st.session_state.messages = [system_prompt]
    else:
        st.session_state.messages = [system_prompt] + [{"role": m["role"], "content": m["content"]} for m in history]

# Visualizzazione Chat
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Logica di Input
if prompt := st.chat_input("DATA INPUT..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    save_to_memory("user", prompt, user_current)

    with st.chat_message("assistant"):
        full_response = ""
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        stream = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=st.session_state.messages, 
            stream=True,
            temperature=0.8 # Leggermente più creativo nell'essere cinico
        )
        placeholder = st.empty()
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                placeholder.markdown(full_response + " █")
        placeholder.markdown(full_response)
        save_to_memory("assistant", full_response, user_current)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

