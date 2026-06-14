import streamlit as st
import requests
import uuid

import os
import streamlit as st

css_path = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "style.css"
)

if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )
else:
    st.warning(f"CSS not found: {css_path}")

css_path = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "style.css"
)



with open(css_path, "r", encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

# ==========================================
# CONFIG
# ==========================================

API_URL = "https://multiagent-customer-support.onrender.com/chat"
st.set_page_config(
    page_title="IntelliSupport AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LOAD CSS
# ==========================================





# ==========================================
# SESSION STATE
# ==========================================

if "sessions" not in st.session_state:
    st.session_state.sessions = {}

if "current_session" not in st.session_state:
    sid = str(uuid.uuid4())

    st.session_state.sessions[sid] = {
        "title": "New Chat",
        "messages": []
    }

    st.session_state.current_session = sid

active_chat = st.session_state.sessions[
    st.session_state.current_session
]

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown("""
    <div class="logo">
        <h1>🤖 Intelli<span>Support</span></h1>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ New Chat"):
        sid = str(uuid.uuid4())

        st.session_state.sessions[sid] = {
            "title": "New Chat",
            "messages": []
        }

        st.session_state.current_session = sid
        st.rerun()

    st.markdown("### 💬 Chat History")

    for sid in reversed(list(st.session_state.sessions.keys())):

        title = st.session_state.sessions[sid]["title"]

        if st.button(
            title,
            key=f"session_{sid}"
        ):
            st.session_state.current_session = sid
            st.rerun()

    st.markdown("---")

    st.metric(
        "Messages",
        len(active_chat["messages"])
    )

    st.success("Backend Connected")

# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="main-header">
    <h1>IntelliSupport AI</h1>
    <p>
        Multi-Agent Customer Support Platform
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# WELCOME CARD
# ==========================================

if len(active_chat["messages"]) == 0:

    st.markdown("""
    <div class="welcome-card">
        <h2>🚀 Welcome</h2>
        <p>
        Ask about billing, refunds, orders,
        shipping and technical issues.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# CHAT HISTORY
# ==========================================

for msg in active_chat["messages"]:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# CHAT INPUT
# ==========================================

prompt = st.chat_input(
    "Ask IntelliSupport..."
)

if prompt:

    active_chat["messages"].append(
        {
            "role": "user",
            "content": prompt
        }
    )

    if active_chat["title"] == "New Chat":
        active_chat["title"] = prompt[:30]

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        typing_placeholder = st.empty()

        typing_placeholder.markdown("""
        <div class="typing">
            <span></span>
            <span></span>
            <span></span>
        </div>
        """, unsafe_allow_html=True)

        try:

            response = requests.post(
                API_URL,
                json={"query": prompt},
                timeout=60
            )

            if response.status_code == 200:
                answer = response.json().get(
                    "response",
                    "No response generated."
                )
            else:
                answer = (
                    f"Server Error: "
                    f"{response.status_code}"
                )

        except Exception as e:

            answer = (
                f"Connection Error: {str(e)}"
            )

        typing_placeholder.empty()

        st.markdown(answer)

    active_chat["messages"].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    st.rerun()