import streamlit as st

# Import the existing agent logic. The terminal interface is not started
# because main.py runs main() only when executed directly.
import main as agent


st.set_page_config(
    page_title="AI Business Agent",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 AI Business Agent")
st.caption("Research, calculations, and business assistance powered by your existing agent.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.subheader("Session")
    st.write("Your conversation is kept for this running app session.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        agent.messages.clear()
        st.rerun()
    st.divider()
    st.caption("Search limit: 3 searches per request")
    st.caption("Tool-call limit: 5 per request")

for item in st.session_state.chat_history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

with st.form("request_form", clear_on_submit=True):
    user_request = st.text_area(
        "What would you like me to work on?",
        height=150,
        placeholder=(
            "Enter your request here. You can write multiple paragraphs,\n"
            "add blank lines, and include all your instructions."
        ),
    )
    submitted = st.form_submit_button("Send request", type="primary", use_container_width=True)

if submitted:
    cleaned_request = user_request.strip()

    if not cleaned_request:
        st.warning("Please enter a request first.")
    else:
        st.session_state.chat_history.append(
            {"role": "user", "content": cleaned_request}
        )
        with st.chat_message("user"):
            st.markdown(cleaned_request)

        with st.chat_message("assistant"):
            with st.spinner("Working on your request..."):
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
