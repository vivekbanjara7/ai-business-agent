import streamlit as st
import main as agent

st.set_page_config(page_title="AI Business Agent", page_icon="🤖", layout="wide")

st.markdown("""
<style>
:root{--brand:#2563eb;--brand-hover:#1d4ed8;--page:#f5f7fb;--surface:#fff;--text:#172033;--muted:#64748b;--border:#e2e8f0}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.stApp{background:var(--page)!important;color:var(--text)!important}
.main .block-container{max-width:960px;padding-top:2.2rem;padding-bottom:7rem}
h1,h2,h3,p,label,li{color:var(--text)}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--border)}
[data-testid="stSidebar"] *{color:var(--text)}
.sidebar-brand{font-size:1.08rem;font-weight:750;color:var(--text)!important;margin-bottom:.25rem}
.muted{color:var(--muted)!important;font-size:.9rem;line-height:1.5}
.eyebrow{color:var(--brand)!important;font-size:.76rem;font-weight:750;letter-spacing:.13em;margin-bottom:.55rem}
.hero-subtitle{color:var(--muted)!important;font-size:1.02rem;margin-top:-.45rem;margin-bottom:1.6rem}
.section-label{color:var(--text)!important;font-size:.95rem;font-weight:700;margin:1.3rem 0 .65rem}
div.stButton>button{border-radius:15px;border:1px solid var(--border);background:#fff;color:var(--text)!important;min-height:88px;text-align:left;white-space:pre-wrap;transition:all .15s ease}
div.stButton>button:hover{border-color:#93b4f8;box-shadow:0 5px 18px #2563eb17;transform:translateY(-1px)}
div.stButton>button[kind="primary"]{background:var(--brand)!important;border-color:var(--brand)!important;color:#fff!important}
[data-testid="stChatMessage"]{background:#fff!important;border:1px solid var(--border);border-radius:18px;padding:1rem 1.15rem;margin-bottom:.8rem;box-shadow:0 3px 12px #0f172a09}
[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li,[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"]{color:var(--text)!important}
[data-testid="stChatInput"]{background:#fff!important;border:1px solid #d7dfeb!important;border-radius:22px!important;box-shadow:0 5px 22px #0f172a14}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] textarea:focus{background:#fff!important;color:#172033!important;-webkit-text-fill-color:#172033!important;caret-color:#2563eb!important;border:0!important;box-shadow:none!important}
[data-testid="stChatInput"] textarea::placeholder{color:#64748b!important;-webkit-text-fill-color:#64748b!important;opacity:1!important}
[data-testid="stChatInput"] button{color:#2563eb!important}
[data-testid="stMarkdownContainer"] a{color:#2563eb!important;text-underline-offset:2px}
hr{border-color:var(--border)}
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

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
    for i, (label, starter_prompt) in enumerate(starters):
        with (col1 if i % 2 == 0 else col2):
            if st.button(label, key=f"starter_{i}", use_container_width=True):
                st.session_state.pending_prompt = starter_prompt
                st.rerun()
else:
    st.title("Your conversation")

for message in st.session_state.chat_history:
    avatar = "🧑‍💼" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

typed_prompt = st.chat_input("Message AI Business Agent...")
request = st.session_state.pending_prompt or typed_prompt

if request:
    st.session_state.pending_prompt = None
    request = request.strip()
    if request:
        st.session_state.chat_history.append({"role": "user", "content": request})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(request)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking and working on your request..."):
                try:
                    answer = agent.run_agent(request)
                except Exception as exc:
                    answer = f"**Something went wrong:** `{type(exc).__name__}: {exc}`\\n\\nCheck the terminal running Streamlit for details."
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
