import streamlit as st
import main as agent

st.set_page_config(
    page_title="AI Business Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# VISUAL STYLE
# --------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        --brand: #2563eb;
        --brand-hover: #1d4ed8;
        --page: #f5f7fb;
        --surface: #ffffff;
        --text: #172033;
        --muted: #64748b;
        --border: #e2e8f0;
    }

    /* Main page and default text */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: var(--page) !important;
        color: var(--text) !important;
    }

    html, body, [class*="css"], p, label, li,
    [data-testid="stMarkdownContainer"] {
        color: var(--text);
    }

    .main .block-container {
        max-width: 920px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    /* Sidebar remains collapsible using Streamlit's built-in control */
    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * {
        color: var(--text);
    }

    .brand-title {
        color: var(--text) !important;
        font-size: 1.08rem;
        font-weight: 750;
        margin-bottom: .25rem;
    }
    .muted {
        color: var(--muted) !important;
        font-size: .88rem;
        line-height: 1.5;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1rem 1.15rem;
        margin-bottom: .85rem;
        box-shadow: 0 3px 12px rgba(15, 23, 42, .035);
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: var(--text) !important;
    }

    /* Chat composer at the bottom */
    [data-testid="stChatInput"] {
        background: var(--surface);
        border: 1px solid #cbd5e1;
        border-radius: 22px;
        box-shadow: 0 5px 24px rgba(15, 23, 42, .08);
    }
    [data-testid="stChatInput"] textarea {
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        background: transparent !important;
        caret-color: var(--brand);
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] button {
        color: var(--brand) !important;
    }

    /* Buttons and controls */
    .stButton > button {
        border-radius: 12px;
        border: 1px solid var(--border);
        min-height: 2.6rem;
        font-weight: 600;
    }
    .stButton > button[kind="primary"] {
        background: var(--brand) !important;
        border-color: var(--brand) !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--brand-hover) !important;
        border-color: var(--brand-hover) !important;
    }

    /* Links */
    a, [data-testid="stMarkdownContainer"] a {
        color: var(--brand) !important;
        text-underline-offset: 2px;
    }

    /* Reduce excess visual noise */
    hr { border-color: var(--border); }
    h1 { letter-spacing: -0.035em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown('<div class="brand-title">🤖 AI Business Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Business research, calculations, and planning.</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    if st.button(
        "New chat",
        icon=":material/add_comment:",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.chat_history = []
        agent.messages.clear()
        st.rerun()

    st.markdown("**Session**")
    st.markdown(
        f'<div class="muted">{len(st.session_state.chat_history) // 2} '
        'completed turn(s)</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("**Agent limits**")
    st.markdown('<div class="muted">Web searches: up to 3 per request</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Tool calls: up to 5 per request</div>', unsafe_allow_html=True)

    st.divider()
    st.caption("More appearance and avatar options can be added later.")

# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown(
    '<div class="muted" style="color:#2563eb !important; font-weight:700; '
    'letter-spacing:.12em; text-transform:uppercase;">Your AI workspace</div>',
    unsafe_allow_html=True,
)
st.title("AI Business Agent")
st.markdown(
    '<div class="muted">Research ideas, calculate options, and plan your next move.</div>',
    unsafe_allow_html=True,
)

# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------

for item in st.session_state.chat_history:
    avatar = "🧑‍💼" if item["role"] == "user" else "🤖"
    with st.chat_message(item["role"], avatar=avatar):
        st.markdown(item["content"])

# --------------------------------------------------
# BOTTOM CHAT COMPOSER
# --------------------------------------------------

prompt = st.chat_input(
    "Message AI Business Agent...",
    key="chat_composer",
)

if prompt:
    cleaned_request = prompt.strip()
    if cleaned_request:
        st.session_state.chat_history.append(
            {"role": "user", "content": cleaned_request}
        )

        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(cleaned_request)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking and working on your request..."):
                try:
                    answer = agent.run_agent(cleaned_request)
                except Exception as exc:
                    answer = (
                        f"**Something went wrong:** `{type(exc).__name__}: {exc}`\n\n"
                        "Check the terminal running Streamlit for details."
                    )
            st.markdown(answer)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )
