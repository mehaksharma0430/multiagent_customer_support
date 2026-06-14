import streamlit as st
import requests
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import db

# ==========================================
# CONFIG
# ==========================================

API_URL = "http://127.0.0.1:8000/chat"
STREAM_URL = "http://127.0.0.1:8000/chat/stream"

st.set_page_config(
    page_title="IntelliSupport",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# ==========================================
# AGENT TAGGING
# ==========================================

AGENT_STYLES = {
    "billing":       {"label": "Billing agent",       "color": "#818CF8", "bg": "rgba(129,140,248,0.12)"},
    "refunds":       {"label": "Refunds agent",       "color": "#F472B6", "bg": "rgba(244,114,182,0.12)"},
    "orders":        {"label": "Orders agent",        "color": "#FBBF24", "bg": "rgba(251,191,36,0.12)"},
    "technical":     {"label": "Technical support",   "color": "#34D399", "bg": "rgba(52,211,153,0.12)"},
    "shipping":      {"label": "Shipping agent",      "color": "#60A5FA", "bg": "rgba(96,165,250,0.12)"},
    "policy":        {"label": "Policy agent",        "color": "#A78BFA", "bg": "rgba(167,139,250,0.12)"},
    "knowledge_base":{"label": "Knowledge base",      "color": "#5EEAD4", "bg": "rgba(94,234,212,0.12)"},
    "router":        {"label": "Router",              "color": "#9CA3AF", "bg": "rgba(156,163,175,0.12)"},
    "default":       {"label": "Assistant",           "color": "#9CA3AF", "bg": "rgba(156,163,175,0.10)"},
}


def agent_badge_html(agent_key):
    style = AGENT_STYLES.get(agent_key, AGENT_STYLES["default"])
    return (
        f'<span class="agent-badge" '
        f'style="color:{style["color"]}; background:{style["bg"]}; '
        f'border:1px solid {style["color"]}33;">'
        f'{style["label"]}</span>'
    )


# ==========================================
# SESSION STATE
# ==========================================

if "current_session" not in st.session_state:
    existing = db.list_sessions()
    if existing:
        st.session_state.current_session = existing[0]["id"]
    else:
        st.session_state.current_session = db.create_session()

if "renaming_session" not in st.session_state:
    st.session_state.renaming_session = None

if "history_search" not in st.session_state:
    st.session_state.history_search = ""

if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

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
    --danger: #F87171;
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
    padding: 4px 0 14px 0;
}

.sidebar-brand .icon {
    font-size: 28px;
    line-height: 1;
}

.sidebar-brand .brand-text {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.01em;
}

.sidebar-section-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary) !important;
    margin: 16px 0 8px 2px;
}

/* Status / stat cards */
.status-card {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
}

.status-card .label {
    font-size: 12px;
    color: var(--text-secondary) !important;
    margin-bottom: 4px;
}

.status-card .value {
    font-size: 14px;
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

/* ---------- Buttons ---------- */
.stButton button {
    width: 100%;
    border-radius: 10px;
    border: 1px solid var(--border-subtle);
    background: var(--bg-elevated);
    color: var(--text-primary) !important;
    font-weight: 500;
    font-size: 14px;
    padding: 0.5rem 0.9rem;
    transition: background 0.15s ease, border-color 0.15s ease;
}

.stButton button:hover {
    background: var(--accent);
    border-color: var(--accent);
}

.stButton button p {
    color: inherit !important;
    font-size: inherit !important;
}

[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: var(--accent);
    border-color: var(--accent);
    color: #FFFFFF !important;
}

/* Delete confirm button styling */
.danger-btn .stButton button {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    background: rgba(248,113,113,0.08) !important;
}

.danger-btn .stButton button:hover {
    background: var(--danger) !important;
    color: #FFFFFF !important;
}

/* Search input */
[data-testid="stSidebar"] [data-testid="stTextInput"] input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
}

/* ---------- Header ---------- */
.app-header {
    text-align: center;
    margin-top: 6px;
    margin-bottom: 24px;
}

.app-header .title {
    color: var(--text-primary);
    font-size: 56px;
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
    font-size: 16px;
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
    font-size: 22px;
    font-weight: 600;
    margin: 0 0 8px 0;
}

.welcome-card p {
    color: var(--text-secondary);
    font-size: 15px;
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
    font-size: 16px;
    line-height: 1.6;
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

/* Agent badge */
.agent-badge {
    display: inline-block;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    margin-bottom: 8px;
    letter-spacing: 0.01em;
}

/* Message action row (retry / regenerate) */
.msg-actions .stButton button {
    width: auto;
    font-size: 12px;
    padding: 0.3rem 0.7rem;
    background: var(--bg-elevated);
}

/* ---------- Chat input ---------- */

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
    font-size: 16px !important;
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
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    margin: 8px !important;
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
# HELPERS
# ==========================================

def split_agent_and_text(answer, data):
    agent_key = None
    if isinstance(data, dict):
        agent_key = data.get("agent") or data.get("agent_name") or data.get("handled_by")
    if agent_key:
        agent_key = str(agent_key).strip().lower().replace(" ", "_")
    return agent_key, answer


def stream_response(prompt, placeholder):
    """
    Streams from STREAM_URL (expects SSE: lines like 'data: <chunk>' or
    'data: {"token": "...", "agent": "..."}', ending with 'data: [DONE]').
    Falls back to non-streaming API_URL if the stream endpoint fails.
    Returns (full_text, agent_key).
    """
    full_text = ""
    agent_key = None

    try:
        with requests.post(STREAM_URL, json={"query": prompt}, stream=True, timeout=120) as resp:
            if resp.status_code != 200:
                raise RuntimeError(f"Stream returned {resp.status_code}")

            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data:"):
                    payload = line[len("data:"):].strip()
                    if payload == "[DONE]":
                        break
                    token = payload
                    try:
                        parsed = json.loads(payload)
                        if isinstance(parsed, dict):
                            token = parsed.get("token", parsed.get("response", ""))
                            if parsed.get("agent"):
                                agent_key = str(parsed["agent"]).strip().lower().replace(" ", "_")
                    except (json.JSONDecodeError, TypeError):
                        pass

                    full_text += token
                    badge = agent_badge_html(agent_key) if agent_key else ""
                    placeholder.markdown(badge + full_text + " ▌", unsafe_allow_html=True)

        if full_text:
            placeholder.markdown(
                (agent_badge_html(agent_key) if agent_key else "") + full_text,
                unsafe_allow_html=True,
            )
            return full_text, agent_key

        raise RuntimeError("Empty stream")

    except Exception:
        try:
            response = requests.post(API_URL, json={"query": prompt}, timeout=120)
            data = response.json()
            answer = data.get("response", "No response generated.")
            agent_key, answer = split_agent_and_text(answer, data)
            placeholder.markdown(
                (agent_badge_html(agent_key) if agent_key else "") + answer,
                unsafe_allow_html=True,
            )
            return answer, agent_key
        except Exception as e:
            err = f"Connection error: {str(e)}"
            placeholder.markdown(err)
            return err, None


def render_message(msg, is_last_assistant=False):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("agent"):
            st.markdown(agent_badge_html(msg["agent"]), unsafe_allow_html=True)
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and is_last_assistant:
            st.markdown('<div class="msg-actions">', unsafe_allow_html=True)
            if st.button("Regenerate", key=f"regen_{msg['id']}"):
                st.session_state["__regenerate__"] = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


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
        st.session_state.current_session = db.create_session()
        st.session_state.renaming_session = None
        st.session_state.confirm_delete = None
        st.rerun()

    st.markdown('<div class="sidebar-section-label">History</div>', unsafe_allow_html=True)

    st.session_state.history_search = st.text_input(
        "Search chats",
        value=st.session_state.history_search,
        placeholder="Search chats...",
        label_visibility="collapsed",
    )

    sessions = db.list_sessions(search=st.session_state.history_search or None)

    if not sessions:
        st.caption("No chats found")

    for session in sessions:
        sid = session["id"]
        is_active = sid == st.session_state.current_session
        is_renaming = st.session_state.renaming_session == sid
        is_confirming_delete = st.session_state.confirm_delete == sid

        if is_renaming:
            new_title = st.text_input(
                "Rename",
                value=session["title"],
                key=f"rename_input_{sid}",
                label_visibility="collapsed",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Save", key=f"save_{sid}"):
                    db.rename_session(sid, new_title.strip() or "Untitled chat")
                    st.session_state.renaming_session = None
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_{sid}"):
                    st.session_state.renaming_session = None
                    st.rerun()

        elif is_confirming_delete:
            st.caption(f"Delete '{session['title']}'?")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("Delete", key=f"confirm_del_{sid}"):
                    db.delete_session(sid)
                    if st.session_state.current_session == sid:
                        remaining = db.list_sessions()
                        st.session_state.current_session = (
                            remaining[0]["id"] if remaining else db.create_session()
                        )
                    st.session_state.confirm_delete = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                if st.button("Cancel", key=f"cancel_del_{sid}"):
                    st.session_state.confirm_delete = None
                    st.rerun()

        else:
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                btn_type = "primary" if is_active else "secondary"
                label = session["title"] if len(session["title"]) <= 28 else session["title"][:27] + "…"
                if st.button(label, key=f"open_{sid}", type=btn_type):
                    st.session_state.current_session = sid
                    st.rerun()
            with c2:
                if st.button("✎", key=f"rename_btn_{sid}"):
                    st.session_state.renaming_session = sid
                    st.rerun()
            with c3:
                if st.button("🗑", key=f"delete_btn_{sid}"):
                    st.session_state.confirm_delete = sid
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

    current_messages = db.get_messages(st.session_state.current_session)
    st.markdown(
        f"""
        <div class="status-card">
            <div class="label">Conversation</div>
            <div class="value">{len(current_messages)} messages</div>
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

messages = db.get_messages(st.session_state.current_session)

if len(messages) == 0:
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

last_assistant_idx = None
for i, m in enumerate(messages):
    if m["role"] == "assistant":
        last_assistant_idx = i

for i, message in enumerate(messages):
    render_message(message, is_last_assistant=(i == last_assistant_idx))


# ==========================================
# REGENERATE HANDLING
# ==========================================

if st.session_state.get("__regenerate__"):
    st.session_state["__regenerate__"] = False
    sid = st.session_state.current_session
    last_user_prompt = db.get_last_user_message(sid)

    if last_user_prompt:
        db.delete_last_assistant_message(sid)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Regenerating response...")
            full_text, agent_key = stream_response(last_user_prompt, placeholder)

        db.add_message(sid, "assistant", full_text, agent=agent_key)
        st.rerun()


# ==========================================
# CHAT INPUT
# ==========================================

prompt = st.chat_input("Ask IntelliSupport...")

if prompt:
    sid = st.session_state.current_session

    db.add_message(sid, "user", prompt)

    session_row = next((s for s in db.list_sessions() if s["id"] == sid), None)
    if session_row and session_row["title"] == "New chat":
        db.rename_session(sid, prompt[:30] + ("…" if len(prompt) > 30 else ""))

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Analyzing request...")
        full_text, agent_key = stream_response(prompt, placeholder)

    db.add_message(sid, "assistant", full_text, agent=agent_key)
    st.rerun()