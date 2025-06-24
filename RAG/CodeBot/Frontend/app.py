from code_editor import code_editor
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Rust Code Assistant", page_icon="🦀")

st.title("Rust Code Assistant")
st.write("Type your Rust code below and get suggestions from your codebase!")

result = code_editor(
    "",                         # initial content
    lang="rust",                # your language
    height=300,
    key="user_code",
    response_mode="debounce",
)

code = result["text"]  # 'text' is the key for the editor content

suggestion = None

if st.button("Suggest Completion"):
    if code.strip():
        with st.spinner("Getting Completion..."):
            resp = requests.post(f"{API_URL}/complete", json={"code": code})
            try:
                if resp.status_code == 200 and resp.content:
                    suggestion = resp.json().get("suggestion", "")
                else:
                    st.error(f"Backend error: {resp.status_code} - {resp.text}")
                    suggestion = ""
            except Exception as e:
                st.error(f"Could not decode backend response: {e}")
                suggestion = ""
    else:
        st.warning("Please enter some code first.")

if suggestion:
    st.markdown("#### 💡 Suggestion:")
    st.markdown(suggestion, unsafe_allow_html=True)

with st.expander("ℹ️ Backend Details"):
    if st.button("Refresh backend info"):
        details = requests.get(f"{API_URL}/details").json()
        st.json(details)

st.markdown("---")
st.caption("Backend: FastAPI • Frontend: Streamlit")
