import json
from pathlib import Path

import streamlit as st
import main as agent

st.set_page_config(
    page_title="AI Business Agent",
    page_icon="🤖",
    layout="wide",
)

# ==========================================
# 1. THEME PREFERENCE
# ==========================================

PREFERENCE_FILE = Path(__file__).with_name("ui_preferences.json")
THEME_OPTIONS = ["System", "Light", "Dark"]


def load_theme_preference():
    try:
        if PREFERENCE_FILE.exists():
            saved = json.loads(PREFERENCE_FILE.read_text(encoding="utf-8")).get(
                "theme", "System"
            )
            if saved in THEME_OPTIONS:
                return saved
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    return "System"


def save_theme_preference():
    try:
        PREFERENCE_FILE.write_text(
            json.dumps(
                {"theme": st.session_state.get("theme_mode", "System")}, indent=2
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = load_theme_preference()


# ==========================================
# 1. UI THEME AND STYLING
# ==========================================


LIGHT_VARS = """
    --blue: #2563eb; --blue-dark: #1d4ed8; --page: #f5f7fb;
    --surface: #ffffff; --text: #172033; --muted: #64748b;
    --border: #e2e8f0; --input: #ffffff; --user-text: #ffffff;
    --shadow: rgba(15, 23, 42, .07);
    --background-color: #f5f7fb; --secondary-background-color: #ffffff;
    --text-color: #172033; --primary-color: #2563eb;
    --toggle-bg: #f1f5f9;
    --toggle-border: #cbd5e1;
    --toggle-icon: #334155; 
"""
DARK_VARS = """
    --blue: #60a5fa; --blue-dark: #3b82f6; --page: #171717;
    --surface: #222222; --text: #f3f4f6; --muted: #b8bec8;
    --border: #3a3a3a; --input: #252525; --user-text: #ffffff;
    --shadow: rgba(0, 0, 0, .30);
    --background-color: #171717; --secondary-background-color: #222222;
    --text-color: #f3f4f6; --primary-color: #60a5fa;
    --toggle-bg: #383838;
    --toggle-border: #666666;
    --toggle-icon: #ffffff;
"""

if st.session_state.theme_mode == "Dark":
    theme_vars, system_css = DARK_VARS, ""
elif st.session_state.theme_mode == "System":
    theme_vars = LIGHT_VARS
    system_css = """
    @media (prefers-color-scheme: dark) {
      :root {
        --blue: #60a5fa; --blue-dark: #3b82f6; --page: #171717;
        --surface: #222222; --text: #f3f4f6; --muted: #b8bec8;
        --border: #3a3a3a; --input: #252525; --user-text: #ffffff;
        --shadow: rgba(0, 0, 0, .30);
        --background-color: #171717; --secondary-background-color: #222222;
        --text-color: #f3f4f6; --primary-color: #60a5fa;
        --toggle-bg: #383838;
        --toggle-border: #666666;
        --toggle-icon: #ffffff;
      }
    }
    """
else:
    theme_vars, system_css = LIGHT_VARS, ""

css_template = r"""
<style>
:root { THEME_VARS color-scheme: light; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--page) !important; color: var(--text) !important;
}
.main .block-container { max-width: 1050px; padding: 2rem 2rem 7rem; }
h1, h2, h3, p, label, li { color: var(--text); }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text); }
/* Sidebar collapse and expand controls */
/* Keep sidebar controls visible even without hovering */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarExpandButton"],
[data-testid="stSidebarExpandButton"] button,
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] button,
button[aria-label="Collapse sidebar"],
button[aria-label="Expand sidebar"] {
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    background: var(--toggle-bg) !important;
    border: 1px solid var(--toggle-border) !important;
    border-radius: 8px !important;
    color: var(--toggle-icon) !important;
    box-shadow: none !important;
}

[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarExpandButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
button[aria-label="Collapse sidebar"] svg,
button[aria-label="Expand sidebar"] svg {
    opacity: 1 !important;
    visibility: visible !important;
    color: var(--toggle-icon) !important;
    fill: var(--toggle-icon) !important;
    stroke: var(--toggle-icon) !important;
}

[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] svg *,
[data-testid="stSidebarExpandButton"] svg,
[data-testid="stSidebarExpandButton"] svg *,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg * {
    color: var(--toggle-icon) !important;
    fill: var(--toggle-icon) !important;
    stroke: var(--toggle-icon) !important;
}

[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebarExpandButton"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {
    background: var(--surface) !important;
    border-color: var(--blue) !important;
}
.sidebar-brand { font-size: 1.08rem; font-weight: 750; }
.muted { color: var(--muted) !important; font-size: .9rem; line-height: 1.5; }
.eyebrow { color: var(--blue) !important; font-size: .76rem; font-weight: 750; letter-spacing: .13em; margin-bottom: .55rem; }
.hero-subtitle { color: var(--muted) !important; font-size: 1.02rem; margin-top: -.4rem; margin-bottom: 1.6rem; }
.section-label { font-size: .95rem; font-weight: 700; margin: 1.3rem 0 .65rem; }

div.stButton > button {
    border-radius: 22px !important; border: 1px solid var(--border) !important;
    background: var(--surface) !important; color: var(--text) !important;
    min-height: 88px; white-space: pre-wrap; transition: all .15s ease;
}
div.stButton > button:hover { border-color: var(--blue) !important; box-shadow: 0 6px 20px var(--shadow); transform: translateY(-1px); }
div.stButton > button[kind="primary"] { background: var(--blue) !important; border-color: var(--blue) !important; color: white !important; }

[class*="st-key-msg_user_"], [class*="st-key-msg_assistant_"] {
    padding: 1rem 1.25rem !important; margin: .6rem 0 1rem !important;
    border-radius: 26px !important; overflow-wrap: anywhere; box-shadow: 0 3px 12px var(--shadow);
}
[class*="st-key-msg_user_"] { background: var(--blue) !important; border: 1px solid var(--blue-dark) !important; }
[class*="st-key-msg_user_"] p, [class*="st-key-msg_user_"] li,
[class*="st-key-msg_user_"] strong, [class*="st-key-msg_user_"] em,
[class*="st-key-msg_user_"] code { color: var(--user-text) !important; -webkit-text-fill-color: var(--user-text) !important; }
[class*="st-key-msg_user_"] a { color: var(--user-text) !important; text-decoration: underline; }
[class*="st-key-msg_assistant_"] { background: var(--surface) !important; border: 1px solid var(--border) !important; }
[class*="st-key-msg_assistant_"] p, [class*="st-key-msg_assistant_"] li,
[class*="st-key-msg_assistant_"] strong, [class*="st-key-msg_assistant_"] em {
    color: var(--text) !important; -webkit-text-fill-color: var(--text) !important;
}
.chat-label { font-size: .7rem; font-weight: 750; letter-spacing: .06em; margin-bottom: .3rem; opacity: .78; }
[class*="st-key-msg_user_"] .chat-label { color: var(--user-text) !important; }
[class*="st-key-msg_assistant_"] .chat-label { color: var(--muted) !important; }

[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div {
    background: var(--page) !important;
}
[data-testid="stBottom"] [data-testid="stChatInput"] {
    max-width: 760px !important; margin-left: auto !important; margin-right: auto !important;
    background: var(--input) !important; border: 1px solid var(--border) !important;
    border-radius: 30px !important; box-shadow: 0 6px 24px var(--shadow);
}
[data-testid="stChatInput"] textarea, [data-testid="stChatInput"] textarea:focus {
    background: var(--input) !important; color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important; caret-color: var(--blue) !important;
    border: 0 !important; box-shadow: none !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; opacity: 1 !important; }
[data-testid="stChatInput"] button { color: var(--blue) !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; }

/* Theme selector: readable control and readable opened menu */
[data-testid="stSelectbox"] label,
[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] {
    color: var(--text) !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
[data-testid="stSelectbox"] input,
[data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSelectbox"] [role="combobox"] * {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
ul[role="listbox"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
}
li[role="option"],
li[role="option"] *,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li * {
    background: transparent !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}
li[role="option"]:hover,
[data-baseweb="menu"] li:hover {
    background: var(--surface-soft, #303030) !important;
}

[data-testid="stMarkdownContainer"] a { color: var(--blue) !important; text-underline-offset: 2px; }
hr { border-color: var(--border); }
[data-testid="stStatusWidget"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 12px; }
@media (max-width: 700px) {
    .main .block-container { padding-left: 1rem; padding-right: 1rem; }
    [data-testid="stBottom"] [data-testid="stChatInput"] { max-width: 100% !important; }
    [class*="st-key-msg_user_"], [class*="st-key-msg_assistant_"] { padding: .85rem 1rem !important; border-radius: 22px !important; }
}
/* Broad Streamlit surface coverage: prevent built-in blue/white panels from leaking through. */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stBottom"],
[data-testid="stBottom"] > div, [data-testid="stBottom"] > div > div,
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background-color: var(--page) !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background-color: var(--surface) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] div,
[data-testid="stSidebar"] svg {
    color: var(--text) !important;
}
/* Theme selector: style the control and its popover, which Streamlit mounts outside the sidebar. */
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [role="combobox"] {
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
[data-testid="stSelectbox"] [role="combobox"] *,
[data-testid="stSelectbox"] svg {
    color: var(--text) !important;
    fill: var(--text) !important;
}
body [data-baseweb="popover"], body [data-baseweb="popover"] > div,
body [data-baseweb="popover"] ul, body ul[role="listbox"] {
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}
body li[role="option"], body li[role="option"] *,
body [data-baseweb="popover"] [role="option"] {
    background-color: transparent !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}
body li[role="option"]:hover, body li[role="option"][aria-selected="true"],
body [data-baseweb="popover"] [role="option"]:hover {
    background-color: #353535 !important;
}
/* Chat composer and its surrounding fixed footer are painted consistently. */
[data-testid="stBottom"] * { background-color: transparent; }
[data-testid="stBottom"] { background-color: var(--page) !important; }
[data-testid="stChatInput"] {
    background-color: var(--input) !important;
    border-color: var(--border) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] textarea::placeholder {
    background-color: var(--input) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] button svg { background: transparent !important; }

SYSTEM_THEME
</style>
"""
if st.session_state.theme_mode == "Dark":
    css_template = css_template.replace("color-scheme: light;", "color-scheme: dark;")
elif st.session_state.theme_mode == "System":
    system_css += """
    @media (prefers-color-scheme: dark) {
        :root { color-scheme: dark; }
    }
    """
css = css_template.replace("THEME_VARS", theme_vars).replace("SYSTEM_THEME", system_css)
st.markdown(css, unsafe_allow_html=True)


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
                f'<div class="chat-label">{label}</div>', unsafe_allow_html=True
            )

            st.markdown(content)


# ==========================================
# 6. SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-brand">🤖 AI Business Agent</div>', unsafe_allow_html=True
    )

    st.markdown(
        '<div class="muted">Research, calculations, and business planning.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Appearance**")
    st.selectbox(
        "Choose theme",
        options=THEME_OPTIONS,
        key="theme_mode",
        on_change=save_theme_preference,
        label_visibility="collapsed",
    )

    st.divider()

    if st.button("＋  New chat", type="primary", use_container_width=True):

        st.session_state.chat_history = []
        st.session_state.pending_prompt = None

        agent.messages.clear()

        st.rerun()

    st.markdown("**This session**")

    st.markdown(
        f'<div class="muted">'
        f"{len(st.session_state.chat_history) // 2} "
        "completed conversation turn(s)</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("**Agent limits**")

    st.markdown(
        '<div class="muted">Up to 3 web searches per request</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="muted">Up to 5 tool calls per request</div>',
        unsafe_allow_html=True,
    )


# ==========================================
# 7. MAIN WORKSPACE
# ==========================================

st.markdown('<div class="eyebrow">YOUR AI WORKSPACE</div>', unsafe_allow_html=True)

if not st.session_state.chat_history:

    st.title("What are we building today?")

    st.markdown(
        '<div class="hero-subtitle">'
        "Your AI partner for research, numbers, and practical business decisions."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-label">Start with a task</div>', unsafe_allow_html=True
    )

    starters = [
        (
            "💡  Business ideas",
            "Suggest 3 realistic digital product business ideas I can start with a ₹0 budget. Explain the audience and how to validate demand.",
        ),
        (
            "🧮  Calculate profit",
            "Help me calculate revenue, costs, profit, and the number of sales needed to reach my monthly income target. Ask me for any missing numbers.",
        ),
        (
            "🔎  Market research",
            "Research a business niche, identify its target customers, competitors, and problems customers are willing to pay to solve.",
        ),
        (
            "📈  Growth strategy",
            "Create a practical beginner-friendly marketing and growth plan for a small online business with a very limited budget.",
        ),
    ]

    col1, col2 = st.columns(2, gap="medium")

    for i, (label, prompt) in enumerate(starters):

        with col1 if i % 2 == 0 else col2:

            if st.button(label, key=f"starter_{i}", use_container_width=True):

                st.session_state.pending_prompt = prompt
                st.rerun()

else:

    st.title("Your conversation")

    for i, message in enumerate(st.session_state.chat_history):

        render_message(message["role"], message["content"], i)


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

        st.session_state.chat_history.append({"role": "user", "content": request})

        render_message("user", request, user_index)

        assistant_index = len(st.session_state.chat_history)
        streamed_answer = [""]

        # Reserve the assistant message area before generation starts.
        assistant_col, spacer = st.columns([2.85, 1.15])
        with assistant_col:
            with st.container(key=f"msg_assistant_{assistant_index}"):
                st.markdown(
                    '<div class="chat-label">AI BUSINESS AGENT</div>',
                    unsafe_allow_html=True,
                )
                answer_placeholder = st.empty()

        def display_token(token):
            streamed_answer[0] += token
            answer_placeholder.markdown(streamed_answer[0])

        try:
            with st.status("Working on your request...", expanded=False) as work_status:
                answer = agent.run_agent(request, on_token=display_token)
                work_status.update(
                    label="Response complete", state="complete", expanded=False
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

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
