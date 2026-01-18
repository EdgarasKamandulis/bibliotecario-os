import streamlit as st
from openai import OpenAI
import extra_streamlit_components as stx
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="THE LIBRARIAN",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap');
    html, body, [class*="css"] {
        font-family: 'Courier Prime', monospace !important;
        color: #E0E0E0;
        background-color: #000000;
    }
    .stApp { background-color: #000000; }
    h1, h2, h3 {
        color: #C41E3A !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #C41E3A;
        padding-bottom: 10px;
    }
    .stTextInput > div > div > input {
        background-color: #111111;
        color: #E0E0E0;
        border: 1px solid #C41E3A;
        font-family: 'Courier Prime', monospace;
    }
    .stButton > button {
        background-color: #000000;
        color: #C41E3A;
        border: 1px solid #C41E3A;
        text-transform: uppercase;
        width: 100%;
        margin-top: 10px;
    }
    .stButton > button:hover {
        background-color: #C41E3A;
        color: #000000;
    }
    [data-testid="stChatMessage"] {
        background-color: #050505;
        border-left: 2px solid #333;
    }
    [data-testid="stChatMessage"][data-testid="stChatMessageUser"] {
        border-left: 2px solid #C41E3A;
    }
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- COOKIE MANAGER (NO CACHE) ---
# Rimossa la cache che causava l'errore
cookie_manager = stx.CookieManager()

# --- SESSION & SYSTEM PROMPT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
Sei Il Bibliotecario. Protocollo 0=0.
Non sei un assistente. Sei un Oracolo Analitico.
Lingua principale: ITALIANO.
Tono: Freddo, Visionario, Tagliente.
Smonta le banalità. Cerca i glitch logici.
Chiudi i concetti chiave con: "0=0".
"""}
    ]

# --- AUTHENTICATION LOGIC ---
# 1. Tenta di leggere il cookie
time.sleep(0.1) # Piccola pausa per stabilità lettura cookie
cookie_val = cookie_manager.get(cookie="access_granted")

# 2. Se il cookie non c'è, mostra login
if not cookie_val:
    st.title("SECURE GATEWAY")
    st.write("IDENTITY VERIFICATION REQUIRED.")
    
    password = st.text_input("ENTER PASSPHRASE:", type="password")
    
    if st.button("AUTHENTICATE"):
        if password == st.secrets["APP_PASSWORD"]:
            # Salva il cookie (durata 30 giorni)
            cookie_manager.set("access_granted", "true", key="set_auth")
            st.success("ACCESS GRANTED.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("ACCESS DENIED.")
    
    st.markdown("---")
    st.stop()

# --- MAIN INTERFACE ---
st.title("THE LIBRARIAN /// PROTOCOL 0=0")

# Logout nascosto
with st.sidebar:
    st.write("SYSTEM CONTROLS")
    if st.button("LOGOUT"):
        cookie_manager.delete("access_granted")
        st.rerun()

# Chat History Display
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input & Logic
if prompt := st.chat_input("INPUT DATA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + " █")
            
            message_placeholder.markdown(full_response)
        
        except Exception as e:
            st.error(f"SYSTEM ERROR: {e}")
            full_response = "CONNECTION SEVERED. 0=0"
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
