
import streamlit as st
import main as agent

st.set_page_config(
    page_title="AI Business Agent",
    page_icon="🤖",
    layout="wide",
)

# ==========================================
# 1. UI THEME AND STYLING
# ==========================================

st.markdown("""
<style>
:root {
    --blue: #2563eb;
    --blue-dark: #1d4ed8;
    --page: #f5f7fb;
    --white: #ffffff;
    --text: #172033;
    --muted: #64748b;
    --border: #e2e8f0;
}

/* Main background */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--page) !important;
    color: var(--text) !important;
}

/* Center the application content */
.main .block-container {
    max-width: 1050px;
    padding: 2rem 2rem 7rem;
}

h1, h2, h3, p, label, li {
    color: var(--text);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text);
}

.sidebar-brand {
    font-size: 1.08rem;
    font-weight: 750;
}

.muted {
    color: var(--muted) !important;
    font-size: .9rem;
    line-height: 1.5;
}

/* Headings */
.eyebrow {
    color: var(--blue) !important;
    font-size: .76rem;
    font-weight: 750;
    letter-spacing: .13em;
    margin-bottom: .55rem;
}

.hero-subtitle {
    color: var(--muted) !important;
    font-size: 1.02rem;
    margin-top: -.4rem;
    margin-bottom: 1.6rem;
}

.section-label {
    font-size: .95rem;
    font-weight: 700;
    margin: 1.3rem 0 .65rem;
}

/* Starter cards and buttons */
div.stButton > button {
    border-radius: 22px !important;
    border: 1px solid var(--border) !important;
    background: var(--white) !important;
    color: var(--text) !important;
    min-height: 88px;
    white-space: pre-wrap;
    transition: all .15s ease;
}

div.stButton > button:hover {
    border-color: #93b4f8 !important;
    box-shadow: 0 6px 20px #2563eb17;
    transform: translateY(-1px);
}

div.stButton > button[kind="primary"] {
    background: var(--blue) !important;
    border-color: var(--blue) !important;
    color: white !important;
}

/* ==========================================
   2. CHAT MESSAGE BUBBLES
   ========================================== */

/* Shared bubble styling */
[class*="st-key-msg_user_"],
[class*="st-key-msg_assistant_"] {
    padding: 1rem 1.25rem !important;
    margin: .6rem 0 1rem !important;
    border-radius: 26px !important;
    overflow-wrap: anywhere;
    box-shadow: 0 3px 12px rgba(15, 23, 42, .045);
}

/* User message: blue with white text */
[class*="st-key-msg_user_"] {
    background: var(--blue) !important;
    border: 1px solid var(--blue-dark) !important;
}

[class*="st-key-msg_user_"] p,
[class*="st-key-msg_user_"] li,
[class*="st-key-msg_user_"] strong,
[class*="st-key-msg_user_"] em,
[class*="st-key-msg_user_"] code {
    color: white !important;
    -webkit-text-fill-color: white !important;
}

[class*="st-key-msg_user_"] a {
    color: white !important;
    text-decoration: underline;
}

/* AI message: white with dark text */
[class*="st-key-msg_assistant_"] {
    background: white !important;
    border: 1px solid var(--border) !important;
}

[class*="st-key-msg_assistant_"] p,
[class*="st-key-msg_assistant_"] li,
[class*="st-key-msg_assistant_"] strong,
[class*="st-key-msg_assistant_"] em {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}

/* Message labels */
.chat-label {
    font-size: .7rem;
    font-weight: 750;
    letter-spacing: .06em;
    margin-bottom: .3rem;
    opacity: .78;
}

[class*="st-key-msg_user_"] .chat-label {
    color: white !important;
}

[class*="st-key-msg_assistant_"] .chat-label {
    color: var(--muted) !important;
}

/* ==========================================
   3. BOTTOM CHAT INPUT
   ========================================== */

[data-testid="stBottom"] {
    background: linear-gradient(
        180deg,
        rgba(245, 247, 251, 0),
        #f5f7fb 28%
    ) !important;
}

[data-testid="stBottom"] [data-testid="stChatInput"] {
    max-width: 760px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    background: white !important;
    border: 1px solid #d7dfeb !important;
    border-radius: 30px !important;
    box-shadow: 0 6px 24px rgba(15, 23, 42, .09);
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus {
    background: white !important;
    color: #172033 !important;
    -webkit-text-fill-color: #172033 !important;
    caret-color: var(--blue) !important;
    border: 0 !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #64748b !important;
    -webkit-text-fill-color: #64748b !important;
    opacity: 1 !important;
}

[data-testid="stChatInput"] button {
    color: var(--blue) !important;
}

/* Links and dividers */
[data-testid="stMarkdownContainer"] a {
    color: var(--blue) !important;
    text-underline-offset: 2px;
}

hr {
    border-color: var(--border);
}

/* Mobile layout */
@media (max-width: 700px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] {
        max-width: 100% !important;
    }

    [class*="st-key-msg_user_"],
    [class*="st-key-msg_assistant_"] {
        padding: .85rem 1rem !important;
        border-radius: 22px !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. SESSION STATE
# ==========================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ==========================================
# 5. MESSAGE DISPLAY
# ==========================================

def render_message(role, content, index):

    if role == "user":
        spacer, message_col = st.columns([1.15, 2.85])
        label = "YOU"
        key = f"msg_user_{index}"

    else:
        message_col, spacer = st.columns([2.85, 1.15])
        label = "AI BUSINESS AGENT"
        key = f"msg_assistant_{index}"

    with message_col:
        with st.container(key=key):

            st.markdown(
                f'<div class="chat-label">{label}</div>',
                unsafe_allow_html=True
            )

            st.markdown(content)


# ==========================================
# 6. SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-brand">🤖 AI Business Agent</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="muted">Research, calculations, and business planning.</div>',
        unsafe_allow_html=True
    )

    st.divider()

    if st.button(
        "＋  New chat",
        type="primary",
        use_container_width=True
    ):

        st.session_state.chat_history = []
        st.session_state.pending_prompt = None

        agent.messages.clear()

        st.rerun()

    st.markdown("**This session**")

    st.markdown(
        f'<div class="muted">'
        f'{len(st.session_state.chat_history) // 2} '
        'completed conversation turn(s)</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("**Agent limits**")

    st.markdown(
        '<div class="muted">Up to 3 web searches per request</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="muted">Up to 5 tool calls per request</div>',
        unsafe_allow_html=True
    )


# ==========================================
# 7. MAIN WORKSPACE
# ==========================================

st.markdown(
    '<div class="eyebrow">YOUR AI WORKSPACE</div>',
    unsafe_allow_html=True
)

if not st.session_state.chat_history:

    st.title("What are we building today?")

    st.markdown(
        '<div class="hero-subtitle">'
        'Your AI partner for research, numbers, and practical business decisions.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-label">Start with a task</div>',
        unsafe_allow_html=True
    )

    starters = [

        (
            "💡  Business ideas",
            "Suggest 3 realistic digital product business ideas I can start with a ₹0 budget. Explain the audience and how to validate demand."
        ),

        (
            "🧮  Calculate profit",
            "Help me calculate revenue, costs, profit, and the number of sales needed to reach my monthly income target. Ask me for any missing numbers."
        ),

        (
            "🔎  Market research",
            "Research a business niche, identify its target customers, competitors, and problems customers are willing to pay to solve."
        ),

        (
            "📈  Growth strategy",
            "Create a practical beginner-friendly marketing and growth plan for a small online business with a very limited budget."
        )

    ]

    col1, col2 = st.columns(2, gap="medium")

    for i, (label, prompt) in enumerate(starters):

        with (col1 if i % 2 == 0 else col2):

            if st.button(
                label,
                key=f"starter_{i}",
                use_container_width=True
            ):

                st.session_state.pending_prompt = prompt
                st.rerun()

else:

    st.title("Your conversation")

    for i, message in enumerate(st.session_state.chat_history):

        render_message(
            message["role"],
            message["content"],
            i
        )


# ==========================================
# 8. CHAT INPUT AND AGENT EXECUTION
# ==========================================

typed_prompt = st.chat_input("Message AI Business Agent...")

request = st.session_state.pending_prompt or typed_prompt

if request:

    st.session_state.pending_prompt = None

    request = request.strip()

    if request:

        user_index = len(st.session_state.chat_history)

        st.session_state.chat_history.append({
            "role": "user",
            "content": request
        })

        render_message("user", request, user_index)

        assistant_index = len(st.session_state.chat_history)
        streamed_answer = [""]

        # Reserve the assistant message area before generation starts.
        assistant_col, spacer = st.columns([2.85, 1.15])
        with assistant_col:
            with st.container(key=f"msg_assistant_{assistant_index}"):
                st.markdown(
                    '<div class="chat-label">AI BUSINESS AGENT</div>',
                    unsafe_allow_html=True
                )
                answer_placeholder = st.empty()

        def display_token(token):
            streamed_answer[0] += token
            answer_placeholder.markdown(streamed_answer[0])

        try:
            with st.status(
                "Working on your request...",
                expanded=False
            ) as work_status:
                answer = agent.run_agent(
                    request,
                    on_token=display_token
                )
                work_status.update(
                    label="Response complete",
                    state="complete",
                    expanded=False
                )

        except Exception as exc:
            answer = (
                f"**Something went wrong:** "
                f"`{type(exc).__name__}: {exc}`\\n\\n"
                "Check the terminal running Streamlit for details."
            )
            answer_placeholder.markdown(answer)

        # Preserve the complete answer in history for later reruns.
        if not streamed_answer[0]:
            answer_placeholder.markdown(answer)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer
        })
