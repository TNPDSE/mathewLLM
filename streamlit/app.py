import streamlit as st
from pathlib import Path
import requests
import streamlit.components.v1 as components
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).parent

load_dotenv()

API_URL = os.getenv("API_URL")
RESET_URL = os.getenv("RESET_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

LOGO_PATH = BASE_DIR / "assets" / "tnplogo.png"

# =====================================================
# Page Config
# =====================================================

st.set_page_config(
    page_title="Audit AI Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# Session State
# =====================================================

if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
    
# =====================================================
# Custom CSS
# =====================================================

st.markdown("""
<style>

/* Hide Streamlit chrome */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

/* Main app */
.stApp{
    background-color:#0b1220;
}

/* Main content */
.block-container{
    padding-top:1rem;
}

/* Sidebar */
[data-testid="stSidebar"]{
    background-color:black;
    min-width:280px;
    max-width:280px;
}

/* Sidebar title */
.sidebar-title{
    color:white;
    text-align:left;
    font-size:24px;
    font-weight:700;
    margin-top:15px;
    margin-bottom:25px;
    margin-left:12px;
}

[data-testid="stSidebar"] img{
    margin-top:-40px;
    margin-bottom:10px;
}
                       
/* Welcome */
.welcome-title{
    color:#d0d0d0;
    text-align:center;
    font-size:58px;
    font-weight:700;
    margin-top:120px;
}

.welcome-subtitle{
    color:#8a8a8a;
    text-align:center;
    font-size:22px;
    margin-bottom:35px;
}

/* Buttons */
div.stButton > button{
    border:none;
    border-radius:10px;
    height:3rem;
    font-weight:600;
}

/* Hide avatars */
[data-testid="stChatMessageAvatarUser"]{
    display:none;
}

[data-testid="stChatMessageAvatarAssistant"]{
    display:none;
}

/* Main chat area width */
.main .block-container{
    max-width:900px;
    margin:auto;
}

/* Chat input spacing */
[data-testid="stChatInput"]{
    margin-top:30px;
}

/* Sidebar logo spacing */
[data-testid="stSidebar"] img{
    margin-top:15px;
    margin-bottom:15px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# Sidebar
# =====================================================

with st.sidebar:

    st.image(
        str(LOGO_PATH),
        width=180
    )

    st.markdown(
        """
        <div class="sidebar-title">
            AI Assistant
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "➕ New Chat",
        width="stretch"
    ):

        try:

            requests.post(
                RESET_URL,
                headers={
                    "x-api-key": INTERNAL_API_KEY
                },
                timeout=10
            )

        except Exception:
            pass

        st.session_state.messages = []
        st.session_state.pending_question = None

        st.rerun()

# =====================================================
# Welcome Screen
# =====================================================

if not st.session_state.chat_started:

    st.markdown(
        """
        <div class="welcome-title">
            Welcome!
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="welcome-subtitle">
            Ask me about Audits
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([3, 1.5, 3])

    with col2:

        if st.button(
            "Start Chat",
            width="stretch"
        ):
            st.session_state.chat_started = True
            st.rerun()

# =====================================================
# Chat Screen
# =====================================================

else:

    # Landing Page

    if len(st.session_state.messages) == 0:

        st.markdown(
            """
            <div style="
                text-align:center;
                margin-top:150px;
                color:#d0d0d0;
                font-size:40px;
                font-weight:700;
            ">
                Audit AI Assistant
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div style="
                text-align:center;
                color:#8a8a8a;
                font-size:18px;
                margin-top:10px;
            ">
                Ask questions about audits
            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # Chat History
    # =====================================================

    for message in st.session_state.messages:

        if message["role"] == "assistant":

            st.markdown(
                """
                <div style="
                    color:#8a8a8a;
                    font-size:13px;
                    margin-top:25px;
                    margin-bottom:6px;
                ">
                    Assistant
                </div>
                """,
                unsafe_allow_html=True
            )

            if message.get("type") == "svg":

                components.html(
                    message["content"],
                    height=450,
                    scrolling=False
                )

            else:

                st.markdown(
                    message["content"]
                )

        else:

            st.markdown(
                """
                <div style="
                    text-align:right;
                    color:#8a8a8a;
                    font-size:13px;
                    margin-top:25px;
                    margin-bottom:6px;
                ">
                    You
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div style="
                    text-align:right;
                    font-size:18px;
                    color:white;
                ">
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True
            )

 
    # =====================================================
    # Process Pending Question
    # =====================================================

    if st.session_state.pending_question:

        question = st.session_state.pending_question
        st.session_state.pending_question = None

        with st.spinner("Analyzing audit data..."):

            try:

                response = requests.post(
                    API_URL,
                    headers={
                        "x-api-key": INTERNAL_API_KEY
                    },
                    json={
                        "question": question
                    },
                    timeout=120
                )

                result = response.json()

                assistant_response = result.get(
                    "LLM_answer",
                    "No response returned."
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_response
                    }
                )

                if result.get("svg_string"):

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "type": "svg",
                            "content": result["svg_string"]
                        }
                    )

                st.rerun()

            except Exception as e:

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Connection Error: {str(e)}"
                    }
                )

                st.rerun()


    # =====================================================
    # Chat Input
    # =====================================================

    user_question = st.chat_input(
        "Ask a question about the audit..."
    )

    if user_question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_question
            }
        )

        st.session_state.pending_question = user_question

        st.rerun()