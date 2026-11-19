import streamlit as st
import main as agent

st.set_page_config(page_title="AI Business Agent", page_icon="🤖", layout="wide")

st.markdown("""
<style>
:root {
  --brand:#2563eb; --page:#f5f7fb; --surface:#fff;
  --user:#e8f0ff; --text:#172033; --muted:#64748b; --border:#e2e8f0;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.stApp {
  background:var(--page)!important; color:var(--text)!important;
}
.main .block-container {max-width:1050px;padding-top:2rem;padding-bottom:7rem}
h1,h2,h3,p,label,li {color:var(--text)}
[data-testid="stSidebar"] {background:#fff!important;border-right:1px solid var(--border)}
[data-testid="stSidebar"] * {color:var(--text)}
.sidebar-brand {font-size:1.08rem;font-weight:750;color:var(--text)!important}
.muted {color:var(--muted)!important;font-size:.9rem;line-height:1.5}
.eyebrow {color:var(--brand)!important;font-size:.76rem;font-weight:750;letter-spacing:.13em;margin-bottom:.55rem}
.hero-subtitle {color:var(--muted)!important;font-size:1.02rem;margin-top:-.4rem;margin-bottom:1.6rem}
.section-label {font-size:.95rem;font-weight:700;margin:1.3rem 0 .65rem}
div.stButton>button {
  border-radius:22px!important;border:1px solid var(--border)!important;
  background:#fff!important;color:var(--text)!important;min-height:88px;
  white-space:pre-wrap;transition:all .15s ease;
}
div.stButton>button:hover {border-color:#93b4f8!important;box-shadow:0 6px 20px #2563eb17;transform:translateY(-1px)}
div.stButton>button[kind="primary"] {background:var(--brand)!important;border-color:var(--brand)!important;color:#fff!important}

/* Each keyed message container is a separate rounded chat bubble. */
.st-key-msg_user, .st-key-msg_assistant {
  border-radius:26px!important;padding:1rem 1.25rem!important;
  margin:.7rem 0 1rem!important;overflow-wrap:anywhere;
  box-shadow:0 3px 12px rgba(15,23,42,.045);
}
.st-key-msg_user {background:var(--user)!important;border:1px solid #d4e2ff!important}
.st-key-msg_assistant {background:#fff!important;border:1px solid var(--border)!important}
.st-key-msg_user p,.st-key-msg_assistant p,
.st-key-msg_user li,.st-key-msg_assistant li,
.st-key-msg_user strong,.st-key-msg_assistant strong {color:var(--text)!important}
.chat-label {font-size:.7rem;font-weight:750;letter-spacing:.06em;color:var(--muted)!important;margin-bottom:.3rem}

/* Narrow, centered composer docked at the bottom. */
[data-testid="stBottom"] {background:linear-gradient(180deg,rgba(245,247,251,0),#f5f7fb 28%)!important}
[data-testid="stBottom"] [data-testid="stChatInput"] {
  max-width:820px!important;margin-left:auto!important;margin-right:auto!important;
  background:#fff!important;border:1px solid #d7dfeb!important;
  border-radius:28px!important;box-shadow:0 6px 24px rgba(15,23,42,.09);
}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] textarea:focus {
  background:#fff!important;color:#172033!important;-webkit-text-fill-color:#172033!important;
  caret-color:var(--brand)!important;border:0!important;box-shadow:none!important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color:#64748b!important;-webkit-text-fill-color:#64748b!important;opacity:1!important;
}
[data-testid="stChatInput"] button {color:var(--brand)!important}
[data-testid="stMarkdownContainer"] a {color:var(--brand)!important;text-underline-offset:2px}
hr {border-color:var(--border)}
@media(max-width:700px) {
  .main .block-container {padding-left:1rem;padding-right:1rem}
  [data-testid="stBottom"] [data-testid="stChatInput"] {max-width:100%!important}
}
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

def render_message(role, content, index):
    """Render user messages on the right and agent messages on the left."""
    if role == "user":
        spacer, message_col = st.columns([1.0, 3.0])
        label, key = "YOU", f"msg_user_{index}"
    else:
        message_col, spacer = st.columns([3.0, 1.0])
        label, key = "AI BUSINESS AGENT", f"msg_assistant_{index}"

    with message_col:
        with st.container(key=key):
            st.markdown(f'<div class="chat-label">{label}</div>', unsafe_allow_html=True)
            st.markdown(content)

with st.sidebar:
    st.markdown('<div class="sidebar-brand">🤖 AI Business Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Research, calculations, and business planning.</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("＋  New chat", type="primary", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pending_prompt = None
        agent.messages.clear()
        st.rerun()
    st.markdown("**This session**")
    st.markdown(f'<div class="muted">{len(st.session_state.chat_history)//2} completed conversation turn(s)</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**Agent limits**")
    st.markdown('<div class="muted">Up to 3 web searches per request</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Up to 5 tool calls per request</div>', unsafe_allow_html=True)

st.markdown('<div class="eyebrow">YOUR AI WORKSPACE</div>', unsafe_allow_html=True)

if not st.session_state.chat_history:
    st.title("What are we building today?")
    st.markdown('<div class="hero-subtitle">Your AI partner for research, numbers, and practical business decisions.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Start with a task</div>', unsafe_allow_html=True)
    starters = [
        ("💡  Business ideas", "Suggest 3 realistic digital product business ideas I can start with a ₹0 budget. Explain the audience and how to validate demand."),
        ("🧮  Calculate profit", "Help me calculate revenue, costs, profit, and the number of sales needed to reach my monthly income target. Ask me for any missing numbers."),
        ("🔎  Market research", "Research a business niche, identify its target customers, competitors, and problems customers are willing to pay to solve."),
        ("📈  Growth strategy", "Create a practical beginner-friendly marketing and growth plan for a small online business with a very limited budget."),
    ]
    col1, col2 = st.columns(2, gap="medium")
    for i, (label, prompt) in enumerate(starters):
        with (col1 if i % 2 == 0 else col2):
            if st.button(label, key=f"starter_{i}", use_container_width=True):
                st.session_state.pending_prompt = prompt
                st.rerun()
else:
    st.title("Your conversation")
    for i, message in enumerate(st.session_state.chat_history):
        render_message(message["role"], message["content"], i)

typed_prompt = st.chat_input("Message AI Business Agent...")
request = st.session_state.pending_prompt or typed_prompt

if request:
    st.session_state.pending_prompt = None
    request = request.strip()
    if request:
        user_index = len(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "user", "content": request})
        render_message("user", request, user_index)

        with st.spinner("Thinking and working on your request..."):
            try:
                answer = agent.run_agent(request)
            except Exception as exc:
                answer = f"**Something went wrong:** `{type(exc).__name__}: {exc}`\n\nCheck the terminal running Streamlit for details."

        assistant_index = len(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        render_message("assistant", answer, assistant_index)
