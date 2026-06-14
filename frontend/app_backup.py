import streamlit as st
import requests
import uuid

# ==========================================
# CONFIG
# ==========================================

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(
    page_title="IntelliSupport",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# SESSION STATE
# ==========================================

if "sessions" not in st.session_state:
    st.session_state.sessions = {}

if "current_session" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {"title": "New chat", "messages": []}
    st.session_state.current_session = new_id

# Convenience alias for the active conversation
st.session_state.messages = st.session_state.sessions[st.session_state.current_session]["messages"]

# ==========================================
# CSS
# ==========================================

st.markdown("""
<style>

/* ---------- Hide Streamlit chrome ---------- */
#MainMenu, footer, header {
    visibility: hidden;
}

/* ---------- Palette ---------- */
:root {
    --bg-app: #0B0F19;
    --bg-panel: #141A2A;
    --bg-elevated: #1B2333;
    --border-subtle: rgba(255,255,255,0.07);
    --text-primary: #E5E7EB;
    --text-secondary: #94A3B8;
    --accent: #4F46E5;
    --accent-2: #06B6D4;
    --accent-hover: #4338CA;
    --success: #34D399;
}

.stApp {
    background: var(--bg-app);
}

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 7rem;
    max-width: 900px;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: var(--bg-panel);
    border-right: 1px solid var(--border-subtle);
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption {
    color: var(--text-secondary) !important;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0 18px 0;
}

.sidebar-brand .icon {
    font-size: 56px;
    line-height: 1;
}

.sidebar-brand .brand-text {
    font-size: 52px;
    font-weight: 700;
    letter-spacing: -0.01em;
}

.sidebar-section-label {
    font-size: 50px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary) !important;
    margin: 18px 0 8px 2px;
}

/* Status / stat cards */
.status-card {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.status-card .label {
    font-size: 50px;
    color: var(--text-secondary) !important;
    margin-bottom: 4px;
}

.status-card .value {
    font-size: 50px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    flex-shrink: 0;
}

.history-item {
    display: block;
    padding: 10px 12px;
    border-radius: 12px;
    font-size: 50px;
    color: var(--text-secondary) !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 6px;
    border: 1px solid transparent;
}

.history-item.active {
    background: var(--bg-elevated);
    color: var(--text-primary) !important;
    border-color: var(--border-subtle);
}

/* ---------- Buttons ---------- */
.stButton button {
    width: 100%;
    border-radius: 12px;
    border: 1px solid var(--border-subtle);
    background: var(--bg-elevated);
    color: var(--text-primary) !important;
    font-weight: 500;
    font-size: 50px;
    padding: 0.55rem 1rem;
    transition: background 0.15s ease, border-color 0.15s ease;
}

.stButton button:hover {
    background: var(--accent);
    border-color: var(--accent);
}

.stButton button p {
    color: inherit !important;
}

[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: var(--bg-elevated);
    border-color: var(--accent);
    color: var(--text-primary) !important;
}

/* ---------- Header ---------- */
.app-header {
    text-align: center;
    margin-top: 6px;
    margin-bottom: 24px;
}

.app-header .title {
    color: var(--text-primary);
    font-size: 80px;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin: 0;
}

.app-header .accent-word {
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.app-header .subtitle {
    color: var(--text-secondary);
    font-size: 30px;
    margin-top: 4px;
}

/* ---------- Welcome card ---------- */
.welcome-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 18px;
    padding: 24px;
    margin: 24px 0 8px 0;
    text-align: center;
}

.welcome-card h2 {
    color: var(--text-primary);
    font-size: 36px;
    font-weight: 600;
    margin: 0 0 8px 0;
}

.welcome-card p {
    color: var(--text-secondary);
    font-size: 25px;
    line-height: 1.6;
    margin: 0;
}

/* ---------- Chat messages ---------- */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    margin-bottom: 4px;
    padding: 6px 0 !important;
}

[data-testid="stChatMessageContent"] {
    color: var(--text-primary) !important;
}

[data-testid="stChatMessageContent"] p {
    font-size: 15px;
    line-height: 1.2;
}

/* User bubble: right-aligned */
[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    display: flex;
    flex-direction: row-reverse;
}

[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 10px 16px;
    max-width: 80%;
}

/* Assistant message: full width, no bubble */
[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    padding: 2px 0;
}

[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatarUser"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-subtle);
}

/* ---------- Chat input ---------- */

/* Fixed bottom container Streamlit wraps the chat input in */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    background: var(--bg-app) !important;
}

[data-testid="stBottom"] {
    border-top: 1px solid var(--border-subtle);
}

[data-testid="stBottomBlockContainer"] {
    max-width: 900px;
    padding-top: 1rem;
    padding-bottom: 1.25rem;
}

div[data-testid="stChatInput"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 26px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35);
    overflow: hidden;
}

div[data-testid="stChatInput"] > div {
    background: var(--bg-panel) !important;
}

div[data-testid="stChatInput"] textarea {
    background: var(--bg-panel) !important;
    color: var(--text-primary) !important;
    font-size: 20px !important;
    padding: 0.85rem 1.1rem !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-secondary) !important;
}

/* Send button */
div[data-testid="stChatInput"] button {
    background: var(--accent) !important;
    border: none !important;
    border-radius: 50% !important;
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    margin: 10px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background 0.15s ease, opacity 0.15s ease;
}

div[data-testid="stChatInput"] button:hover {
    background: var(--accent-hover) !important;
}

div[data-testid="stChatInput"] button svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    width: 28px !important;
    height: 28px !important;
}

div[data-testid="stChatInput"] button:disabled {
    background: var(--bg-elevated) !important;
    opacity: 0.6;
}

div[data-testid="stChatInput"] button:disabled svg {
    fill: var(--text-secondary) !important;
    color: var(--text-secondary) !important;
}

/* ---------- Misc ---------- */
hr {
    border-color: var(--border-subtle) !important;
}

.stSpinner > div {
    color: var(--text-secondary) !important;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <span class="icon">🛡️</span>
            <span class="brand-text">IntelliSupport</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("New chat", key="new_chat_btn"):
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {"title": "New chat", "messages": []}
        st.session_state.current_session = new_id
        st.rerun()

    st.markdown('<div class="sidebar-section-label">History</div>', unsafe_allow_html=True)

    # Most recently created chats first
    for sid in reversed(list(st.session_state.sessions.keys())):
        session = st.session_state.sessions[sid]
        is_active = sid == st.session_state.current_session
        label = session["title"]
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"hist_{sid}", type=btn_type):
            st.session_state.current_session = sid
            st.rerun()

    st.markdown('<div class="sidebar-section-label">Status</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="status-card">
            <div class="label">System</div>
            <div class="value"><span class="status-dot"></span>Backend online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="status-card">
            <div class="label">Conversation</div>
            <div class="value">{len(st.session_state.messages)} messages</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("Enterprise customer support intelligence platform")


# ==========================================
# HEADER
# ==========================================

st.markdown(
    """
    <div class="app-header">
        <p class="title">Intelli<span class="accent-word">Support</span></p>
        <p class="subtitle">Enterprise AI customer support platform</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# WELCOME CARD (only on empty chat)
# ==========================================

if len(st.session_state.messages) == 0:
    st.markdown(
        """
        <div class="welcome-card">
            <h2>How can we help?</h2>
            <p>Ask about orders, billing, refunds, technical issues, or company
            policies. IntelliSupport routes your question to the right source
            of knowledge automatically.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# CHAT HISTORY
# ==========================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ==========================================
# CHAT INPUT
# ==========================================

prompt = st.chat_input("Ask IntelliSupport...")

if prompt:
    active = st.session_state.sessions[st.session_state.current_session]

    active["messages"].append({"role": "user", "content": prompt})

    if active["title"] == "New chat":
        active["title"] = prompt[:30] + ("…" if len(prompt) > 30 else "")

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing request..."):
            try:
                response = requests.post(API_URL, json={"query": prompt}, timeout=60)

                if response.status_code == 200:
                    answer = response.json().get("response", "No response generated.")
                else:
                    answer = f"Server error: {response.status_code}"

            except Exception as e:
                answer = f"Connection error: {str(e)}"

            st.markdown(answer)

    active["messages"].append({"role": "assistant", "content": answer})
    st.rerun()