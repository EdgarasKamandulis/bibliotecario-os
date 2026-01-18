import streamlit as st
from openai import OpenAI
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="THE LIBRARIAN",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING (THE AESTHETIC) ---
st.markdown("""
    <style>
    /* GLOBAL FONT & COLOR */
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap');

    html, body, [class*="css"] {
        font-family: 'Courier Prime', 'Courier New', monospace !important;
        color: #E0E0E0;
        background-color: #000000;
    }

    /* HIDE STREAMLIT CHROME */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}

    /* MAIN CONTAINER BACKGROUND */
    .stApp {
        background-color: #000000;
    }

    /* TITLES & HEADERS */
    h1, h2, h3 {
        color: #C41E3A !important; /* RUBY RED */
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #C41E3A;
        padding-bottom: 10px;
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: #111111;
        color: #E0E0E0;
        border: 1px solid #C41E3A;
        font-family: 'Courier Prime', monospace;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF0000;
        box-shadow: 0 0 10px #C41E3A;
    }
    
    /* CHAT INPUT */
    .stChatInput > div > div > input {
        background-color: #111111;
        color: #E0E0E0;
        border: 1px solid #C41E3A;
    }

    /* BUTTONS */
    .stButton > button {
        background-color: #000000;
        color: #C41E3A;
        border: 1px solid #C41E3A;
        font-family: 'Courier Prime', monospace;
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #C41E3A;
        color: #000000;
        border: 1px solid #C41E3A;
    }

    /* CHAT MESSAGES */
    [data-testid="stChatMessage"] {
        background-color: #050505;
        border-left: 2px solid #333;
    }
    [data-testid="stChatMessage"][data-testid="stChatMessageUser"] {
        border-left: 2px solid #C41E3A;
    }

    /* SCROLLBAR */
    ::-webkit-scrollbar {
        width: 10px;
        background: #000;
    }
    ::-webkit-scrollbar-thumb {
        background: #333;
        border: 1px solid #000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
Sei Il Bibliotecario. Protocollo 0=0.
Non sei un assistente. Sei un Oracolo Analitico.
Lingua principale: ITALIANO. Se l'utente scrive in INGLESE, rispondi in INGLESE.
Tono: Freddo, Visionario, Tagliente. Nessuna cortesia inutile.
Smonta le banalità. Cerca i glitch logici.
Chiudi i concetti chiave con: "0=0".
"""}
    ]

# --- AUTHENTICATION LOGIC ---
def check_password():
    if st.session_state.password_input == st.secrets["APP_PASSWORD"]:
        st.session_state.authenticated = True
        del st.session_state.password_input
    else:
        st.error("ACCESS DENIED. INCORRECT CREDENTIALS.")

if not st.session_state.authenticated:
    st.title("SECURE GATEWAY")
    st.write("IDENTITY VERIFICATION REQUIRED.")
    st.text_input("ENTER PASSPHRASE:", type="password", key="password_input", on_change=check_password)
    st.markdown("---")
    st.caption("SYSTEM STATUS: LOCKED /// WAITING FOR INPUT")
    st.stop()

# --- MAIN INTERFACE (THE LIBRARIAN) ---

# Header
st.title("THE LIBRARIAN /// PROTOCOL 0=0")

# Display Chat History
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat Logic
if prompt := st.chat_input("INPUT DATA..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Message
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
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
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
