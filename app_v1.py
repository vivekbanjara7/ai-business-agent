import streamlit as st
import main as agent

st.set_page_config(
    page_title="AI Business Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --brand-blue: #2563eb;
        --brand-blue-hover: #1d4ed8;
        --page-bg: #f6f8fc;
        --panel-bg: #ffffff;
        --text-main: #172033;
        --text-muted: #64748b;
        --border: #e5eaf2;
    }
    .stApp { background: var(--page-bg); color: var(--text-main); }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    .main .block-container {
        max-width: 1000px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }
    .app-eyebrow {
        color: var(--brand-blue);
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .11em;
        text-transform: uppercase;
        margin-bottom: .45rem;
    }
    .app-subtitle {
        color: var(--text-muted);
        font-size: 1rem;
        margin-top: -.35rem;
        margin-bottom: 1.8rem;
    }
    [data-testid="stChatMessage"] {
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1rem 1.15rem;
        margin-bottom: .8rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, .035);
    }
    [data-testid="stTextArea"] textarea {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 12px;
        color: var(--text-main);
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--brand-blue);
        box-shadow: 0 0 0 1px var(--brand-blue);
    }
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 2.7rem;
    }
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: var(--brand-blue);
        border-color: var(--brand-blue);
        color: #ffffff;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--brand-blue-hover);
        border-color: var(--brand-blue-hover);
        color: #ffffff;
    }
    .sidebar-note {
        color: var(--text-muted);
        font-size: .88rem;
        line-height: 1.5;
    }
    .sidebar-brand {
        color: var(--text-main);
        font-size: 1.15rem;
        font-weight: 750;
        margin-bottom: .2rem;
    }
    div[data-testid="stMarkdownContainer"] a {
        color: var(--brand-blue);
        text-decoration: underline;
        text-underline-offset: 2px;
    }
    hr { border-color: var(--border); }
    </style>
    """,
    unsafe_allow_html=True,
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">🤖 AI Business Agent</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sidebar-note">Your workspace for business research, '
        'calculations, and practical planning.</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    if st.button("＋  New conversation", use_container_width=True, type="primary"):
        st.session_state.chat_history = []
        agent.messages.clear()
        st.rerun()

    st.markdown("#### Session")
    st.markdown(
        f'<div class="sidebar-note">{len(st.session_state.chat_history) // 2} '
        'completed conversation turn(s) in this session.</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("#### Agent limits")
    st.caption("Web searches: up to 3 per request")
    st.caption("Tool calls: up to 5 per request")
    st.divider()
    st.markdown(
        '<div class="sidebar-note">Theme, layout, and avatar choices can be '
        'added as personal settings in a future update.</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="app-eyebrow">Your AI workspace</div>', unsafe_allow_html=True)
st.title("AI Business Agent")
st.markdown(
    '<div class="app-subtitle">Research ideas, make calculations, and turn '
    'business questions into practical next steps.</div>',
    unsafe_allow_html=True,
)

if not st.session_state.chat_history:
    st.info(
        "What are you working on today? Ask a business question, request "
        "research, or run a calculation."
    )

for item in st.session_state.chat_history:
    avatar = "🧑‍💼" if item["role"] == "user" else "🤖"
    with st.chat_message(item["role"], avatar=avatar):
        st.markdown(item["content"])

with st.form("request_form", clear_on_submit=True):
    user_request = st.text_area(
        "Your message",
        height=120,
        placeholder=(
            "Describe what you need help with...\n\n"
            "You can include context, goals, constraints, and multiple questions."
        ),
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button(
        "Send request  →",
        type="primary",
        use_container_width=True,
    )

if submitted:
    cleaned_request = user_request.strip()
    if not cleaned_request:
        st.warning("Please enter a request first.")
    else:
        st.session_state.chat_history.append(
            {"role": "user", "content": cleaned_request}
        )
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(cleaned_request)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking, researching, and preparing your answer..."):
                try:
                    answer = agent.run_agent(cleaned_request)
                except Exception as exc:
                    answer = (
                        f"**Something went wrong:** `{type(exc).__name__}: {exc}`\n\n"
                        "Check the terminal running Streamlit for more details."
                    )
            st.markdown(answer)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )
